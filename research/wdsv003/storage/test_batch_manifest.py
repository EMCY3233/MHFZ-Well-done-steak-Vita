import struct
import unittest
import zlib
from batch_manifest import ENTRY, MAGIC, SIZE, read_manifest


def fixture(generation=1, count=3, changes=None):
    rows = [[i, 0, 0xffffffff, 0, 0, 0, bytes(32)] for i in range(3)]
    for index, values in (changes or {}).items():
        rows[index] = values
    body = MAGIC + struct.pack('<2I', generation, count) + b''.join(ENTRY.pack(*r) for r in rows)
    return body + struct.pack('<I', zlib.crc32(body))


class ManifestTests(unittest.TestCase):
    def test_empty_snapshot(self):
        self.assertEqual(SIZE, 188)
        self.assertEqual([x['state'] for x in read_manifest(fixture())['entries']], [0, 0, 0])

    def test_live_and_deleted_distinct(self):
        rows = {0: [0, 1, 0, 2, 36, 0, b'a'*32], 1: [1, 2, 1, 3, 36, 0, b'b'*32]}
        self.assertEqual([x['state'] for x in read_manifest(fixture(changes=rows))['entries']], [1, 2, 0])

    def test_size_magic_crc(self):
        raw = fixture()
        for bad in [raw[:-1], raw+b'X', b'X'+raw[1:], raw[:-1]+bytes([raw[-1]^1])]:
            with self.assertRaises(ValueError): read_manifest(bad)

    def test_generation_count(self):
        for gen, count in [(0, 3), (1, 2), (1, 4)]:
            with self.assertRaises(ValueError): read_manifest(fixture(gen, count))

    def test_duplicate_and_noncanonical_absence(self):
        for row in [[1,0,0xffffffff,0,0,0,bytes(32)], [0,0,0,0,0,0,bytes(32)], [0,0,0xffffffff,0,0,0,b'x'*32]]:
            with self.assertRaises(ValueError): read_manifest(fixture(changes={0:row}))

    def test_reference_bounds(self):
        base = [0,1,0,1,36,0,b'd'*32]
        for field, value in [(1,3),(2,2),(3,0),(4,35),(4,512037),(5,1)]:
            row=base.copy();row[field]=value
            with self.assertRaises(ValueError): read_manifest(fixture(changes={0:row}))
        row=base.copy();row[1]=2;row[4]=37
        with self.assertRaises(ValueError): read_manifest(fixture(changes={0:row}))