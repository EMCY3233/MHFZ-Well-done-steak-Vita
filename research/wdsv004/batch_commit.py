"""Callback-only publication reference. No filesystem or Vita APIs."""
from batch_plan import prepare
from snapshot import recover
from batch_manifest import read_manifest


class Coordinator:
    """One exclusive writer epoch; any exception permanently blocks this instance.

    read_all returns immutable manifests plus records under an externally held
    exclusive lock. write_record/write_manifest return exactly True only after
    their adapter acknowledges completion. Readback does not prove durability.
    Reconstruct an epoch only after independent recovery and ownership checks.
    """
    def __init__(self, read_all, write_record, write_manifest):
        self.read_all = read_all
        self.write_record = write_record
        self.write_manifest = write_manifest
        self.blocked = False

    def _observe(self):
        manifests, records = self.read_all()
        manifests, records = tuple(manifests), dict(records)
        if len(manifests) != 2 or any(x is not None and type(x) is not bytes for x in manifests):
            raise ValueError('two immutable manifest slots required')
        if any(type(x) is not bytes for x in records.values()):
            raise ValueError('immutable record bytes required')
        return manifests, records

    def commit(self, replacements):
        if self.blocked:
            raise RuntimeError('writer epoch blocked; independent recovery required')
        try:
            manifests, records = self._observe()
            plan = prepare(manifests, records, replacements)
            for logical, slot, raw in plan.writes:
                if self.write_record(logical, slot, raw) is not True:
                    raise RuntimeError('record completion uncertain')
            observed_m, observed_r = self._observe()
            if tuple(observed_m) != manifests:
                raise RuntimeError('baseline changed during preparation')
            for logical, slot, raw in plan.writes:
                if observed_r.get((logical,slot)) != raw:
                    raise RuntimeError('record readback mismatch')
            candidate = list(manifests)
            candidate[plan.manifest_slot] = plan.manifest
            # Validate unchanged members too, using observed, not expected bytes.
            selected = recover(candidate, observed_r)
            generation = read_manifest(plan.manifest)['generation']
            if selected.generation != generation:
                raise RuntimeError('candidate incomplete')
            if self.write_manifest(plan.manifest_slot,plan.manifest) is not True:
                raise RuntimeError('manifest completion uncertain')
            final_m, final_r = self._observe()
            if tuple(final_m) != tuple(candidate):
                raise RuntimeError('manifest readback mismatch')
            final = recover(final_m,final_r)
            if final != selected:
                raise RuntimeError('snapshot readback mismatch')
            return final
        except Exception:
            self.blocked = True
            raise