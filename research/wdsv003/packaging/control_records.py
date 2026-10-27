"""Bounded SELF control-record reader; never authenticates or rewrites."""
import struct


def read_controls(data, offset, size):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError('control region outside file')
    end = offset + size
    rows = []
    while offset < end:
        if end - offset < 16 or len(rows) >= 128:
            raise ValueError('truncated or excessive controls')
        kind, length, unknown, padding = struct.unpack_from('<4I', data, offset)
        if length < 16 or length > end - offset:
            raise ValueError('control length outside region')
        row = dict(offset=offset, type=kind, size=length, unknown=unknown, padding=padding)
        if kind == 4:
            if length != 80:
                raise ValueError('unsupported type4 size')
            row['elf_digest'] = data[offset + 36:offset + 68].hex()
        rows.append(row)
        offset += length
    return rows