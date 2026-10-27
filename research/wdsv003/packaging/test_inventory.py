import struct, unittest
from inventory import elf,region,va_for_offset
class Bounds(unittest.TestCase):
    def test_truncation(self):
        with self.assertRaises(ValueError): elf(b'\x7fELF')
    def test_negative_bounds(self):
        with self.assertRaises(ValueError): region(b'123',-1,1)
    def test_elf64_rejected(self):
        with self.assertRaises(ValueError): elf(b'\x7fELF\x02\x01\x01'+bytes(45))
    def test_mapping_excludes_bss_and_nonload(self):
        p=[dict(type=1,offset=200,vaddr=0x81000000,filesz=10),dict(type=0x60000000,offset=300,vaddr=0,filesz=10)]
        self.assertEqual(va_for_offset(p,209),[0x81000009]);self.assertEqual(va_for_offset(p,210),[]);self.assertEqual(va_for_offset(p,300),[])
if __name__=='__main__':unittest.main()
