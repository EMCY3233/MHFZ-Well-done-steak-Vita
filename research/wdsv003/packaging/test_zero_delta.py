import struct,unittest
from zero_delta import thumb_immediate,compare
class Zero(unittest.TestCase):
    def test_fixed_thumb_vectors(self):
        self.assertEqual(thumb_immediate(struct.pack('<HH',0xf240,0),47),0)
        self.assertEqual(thumb_immediate(struct.pack('<HH',0xf2c0,0),48),0)
        self.assertEqual(thumb_immediate(struct.pack('<HH',0xf64f,0x70ff),47),65535)
    def test_wrong_opcode_and_short_input(self):
        for raw,code in [(bytes(4),47),(struct.pack('<HH',0xf240,0),48),(b'x',47)]:
            with self.assertRaises(ValueError):thumb_immediate(raw,code)
    def test_abs32_expected_and_mismatch(self):
        p={0:dict(type=1,vaddr=0x1000,offset=0,filesz=4,memsz=4)}
        reloc=struct.pack('<III',2<<8,0x20,0)
        self.assertEqual(compare(struct.pack('<I',0x1020),p,reloc)['issues'],{})
        self.assertEqual(compare(bytes(4),p,reloc)['issues'],{'stored_value_mismatch':1})
    def test_symbol_addition_wraps_32bits(self):
        p={0:dict(type=1,vaddr=0xfffffff0,offset=0,filesz=4,memsz=4)}
        reloc=struct.pack('<III',2<<8,0x30,0)
        self.assertEqual(compare(struct.pack('<I',0x20),p,reloc)['issues'],{})
if __name__=='__main__':unittest.main()
