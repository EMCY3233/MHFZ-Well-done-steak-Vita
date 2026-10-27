import struct,unittest
from reloc_framing import SIZES,scan
class Frames(unittest.TestCase):
    def test_supported_forms(self):
        b=b''.join(struct.pack('<I',f)+bytes(n-4) for f,n in SIZES.items())
        r=scan(b);self.assertTrue(r['complete']);self.assertEqual(r['records'],10);self.assertEqual(r['bytes'],len(b))
    def test_all_truncations(self):
        for f,n in SIZES.items():
            b=struct.pack('<I',f)+bytes(n-4)
            for size in range(1,n):self.assertFalse(scan(b[:size])['complete'])
    def test_unknown_stops_at_exact_boundary(self):
        r=scan(bytes(12)+struct.pack('<I',15));self.assertFalse(r['complete']);self.assertEqual(r['offset'],12);self.assertEqual(r['forms'],{0:1})
    def test_empty_stream(self):self.assertEqual(scan(b'')['records'],0)
if __name__=='__main__':unittest.main()
