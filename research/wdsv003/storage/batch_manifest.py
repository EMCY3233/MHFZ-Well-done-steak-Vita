"""Experimental private manifest v1 reader. No filesystem, writer or migration."""
import struct
import zlib

MAGIC = b'MZBAT001'
ENTRY = struct.Struct('<6I32s')
SIZE = 16 + 3 * ENTRY.size + 4


def read_manifest(raw):
    if len(raw) != SIZE or raw[:8] != MAGIC:
        raise ValueError('manifest size/magic')
    generation, count = struct.unpack_from('<2I', raw, 8)
    if not generation or count != 3:
        raise ValueError('generation/count')
    if zlib.crc32(raw[:-4]) != struct.unpack_from('<I', raw, SIZE-4)[0]:
        raise ValueError('manifest CRC')
    entries = []
    for expected in range(3):
        logical, state, slot, sequence, length, reserved, digest = ENTRY.unpack_from(raw, 16+expected*ENTRY.size)
        if logical != expected or state not in (0, 1, 2) or reserved:
            raise ValueError('member identity/state/reserved')
        if state == 0:
            if (slot, sequence, length, digest) != (0xffffffff, 0, 0, bytes(32)):
                raise ValueError('noncanonical absent member')
        elif slot not in (0, 1) or not sequence or not 36 <= length <= 512036:
            raise ValueError('record reference bounds')
        elif state == 2 and length != 36:
            raise ValueError('tombstone record size')
        entries.append(dict(logical=logical, state=state, slot=slot,
                            sequence=sequence, record_bytes=length, sha256=digest.hex()))
    return dict(generation=generation, entries=entries)