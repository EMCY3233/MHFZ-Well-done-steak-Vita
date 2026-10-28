"""Pure preparation plan; no writes, initialization, or publication authority."""
from dataclasses import dataclass
import hashlib
import struct
import zlib
from snapshot import recover, resolve_member
from batch_manifest import read_manifest, MAGIC, ENTRY


@dataclass(frozen=True)
class Plan:
    manifest_slot: int
    manifest: bytes
    writes: tuple  # (logical, inactive slot, immutable raw record)


def prepare(manifests, records, replacements):
    """Preserve current references; callers must hold exclusive ownership.

    replacements maps logical IDs to already encoded private records. Existing
    committed snapshot required. Native payload limit remains 163840 bytes.
    Caller must write/read back all records BEFORE writing the manifest, then
    recover/read back the whole snapshot. This function performs none of that.
    """
    current = recover(manifests, records)
    if current is None or not replacements:
        raise ValueError('committed baseline and nonempty batch required')
    if any(type(k) is not int or k not in range(3) for k in replacements):
        raise ValueError('logical ID')
    baseline = read_manifest(manifests[current.manifest_slot])
    generations = [current.generation]
    for raw in manifests:
        if raw is not None:
            try: generations.append(read_manifest(raw)['generation'])
            except ValueError: pass
    generation = max(generations)+1
    if generation > 0xffffffff:
        raise ValueError('generation exhausted')
    rows, writes = [], []
    for old in baseline['entries']:
        logical = old['logical']
        if logical not in replacements:
            rows.append(ENTRY.pack(logical,old['state'],old['slot'],old['sequence'],old['record_bytes'],0,bytes.fromhex(old['sha256'])))
            continue
        raw = replacements[logical]
        if type(raw) is not bytes or not 36 <= len(raw) <= 163876:
            raise ValueError('immutable record/native capacity')
        sequence = struct.unpack_from('<I',raw,8)[0]
        if sequence != old['sequence']+1 or sequence > 0xffffffff:
            raise ValueError('sequence must advance without wrap')
        slot = 1-old['slot'] if old['state'] else 0
        state = struct.unpack_from('<I',raw,28)[0]+1
        ref = dict(logical=logical,state=state,slot=slot,sequence=sequence,record_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if state not in (1,2): raise ValueError('state')
        resolve_member(ref,{(logical,slot):raw})
        rows.append(ENTRY.pack(logical,state,slot,sequence,len(raw),0,bytes.fromhex(ref['sha256'])))
        writes.append((logical,slot,raw))
    body = MAGIC+struct.pack('<2I',generation,3)+b''.join(rows)
    return Plan(1-current.manifest_slot,body+struct.pack('<I',zlib.crc32(body)),tuple(writes))