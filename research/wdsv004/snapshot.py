"""Read-only batch snapshot recovery reference. No disk access or client hooks."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wdsv003' / 'storage'))
from batch_manifest import read_manifest


@dataclass(frozen=True)
class Member:
    state: int  # 0 absent, 1 live (possibly empty), 2 tombstone
    payload: bytes | None


@dataclass(frozen=True)
class Snapshot:
    generation: int
    manifest_slot: int
    members: tuple[Member, ...]


def resolve_member(entry, records):
    if entry['state'] == 0:
        return Member(0, None)
    raw = records.get((entry['logical'], entry['slot']))
    if raw is None or len(raw) != entry['record_bytes']:
        raise ValueError('missing/excess member bytes')
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError('member digest')
    if raw[:8] != b'MZSAV001' or len(raw) < 36:
        raise ValueError('member record magic/size')
    sequence, length, payload_crc, header_crc = struct.unpack_from('<4I', raw, 8)
    if sequence != entry['sequence'] or length != len(raw)-24:
        raise ValueError('member sequence/length')
    if zlib.crc32(raw[:20]) != header_crc or zlib.crc32(raw[24:]) != payload_crc:
        raise ValueError('member CRC')
    if raw[24:28] != b'MZV1':
        raise ValueError('member envelope')
    deleted, size = struct.unpack_from('<2I', raw, 28)
    if deleted not in (0, 1) or deleted+1 != entry['state'] or size != len(raw)-36:
        raise ValueError('member state/payload length')
    if deleted and size:
        raise ValueError('tombstone payload')
    return Member(entry['state'], raw[36:])


def recover(manifests, records):
    """Return a complete snapshot, None only if BOTH manifest slots are absent.

    records maps (logical, slot) to raw private record bytes. All unreferenced
    records, including higher-sequence preparations, stay invisible. No writes.
    A corrupt/incomplete newer snapshot may fall back to a complete older one;
    this is recovery of a snapshot, not independent fallback for each member.
    """
    if len(manifests) != 2:
        raise ValueError('exactly two manifest slots required')
    parsed = []
    for slot, raw in enumerate(manifests):
        if raw is None:
            continue
        try:
            parsed.append((slot, raw, read_manifest(raw)))
        except ValueError:
            pass
    if len(parsed) == 2 and parsed[0][2]['generation'] == parsed[1][2]['generation']:
        if parsed[0][1] != parsed[1][1]:
            raise ValueError('conflicting equal-generation manifests')
    candidates = []
    for slot, raw, manifest in parsed:
        try:
            members = tuple(resolve_member(e, records) for e in manifest['entries'])
        except ValueError:
            continue
        candidates.append(Snapshot(manifest['generation'], slot, members))
    if candidates:
        return max(candidates, key=lambda s: (s.generation, -s.manifest_slot))
    if all(raw is None for raw in manifests):
        return None
    raise ValueError('no complete valid snapshot; writes must remain blocked')