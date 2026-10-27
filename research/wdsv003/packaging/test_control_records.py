import struct
import unittest
from control_records import read_controls


class ControlsTests(unittest.TestCase):
    def test_exact_record_and_digest(self):
        record = struct.pack('<4I', 4, 80, 1, 0) + b'c'*20 + b'd'*32 + b'\0'*12
        row = read_controls(record, 0, 80)[0]
        self.assertEqual(row['elf_digest'], (b'd'*32).hex())
        self.assertEqual(row['size'], 80)

    def test_unknown_type_preserved(self):
        self.assertEqual(read_controls(struct.pack('<4I', 99, 16, 8, 9), 0, 16)[0]['padding'], 9)

    def test_malformed_regions(self):
        cases = [(b'', -1, 0), (b'', 0, 1), (b'\0'*15, 0, 15)]
        for length in [0, 15, 17, 0xffffffff]:
            cases.append((struct.pack('<4I', 1, length, 0, 0), 0, 16))
        for data, offset, size in cases:
            with self.subTest(length=len(data), size=size), self.assertRaises(ValueError):
                read_controls(data, offset, size)

    def test_wrong_type4_size(self):
        with self.assertRaises(ValueError):
            read_controls(struct.pack('<4I', 4, 16, 0, 0), 0, 16)

    def test_record_count_bounded(self):
        record = struct.pack('<4I', 1, 16, 0, 0)
        self.assertEqual(len(read_controls(record*128, 0, 2048)), 128)
        with self.assertRaises(ValueError):
            read_controls(record*129, 0, 2064)