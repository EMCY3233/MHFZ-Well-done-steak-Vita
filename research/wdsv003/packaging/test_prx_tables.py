import struct,unittest
from prx_tables import descriptor,read_name,read_va

def fixture(size):
    b=bytearray(size);struct.pack_into('<6H',b,0,size,1,0,2,0,0)
    if size==0x24:struct.pack_into('<4I',b,12,0x1234,0x8000,0x8010,0x8020)
    elif size==0x34:struct.pack_into('<2I',b,16,0x1234,0x8000);struct.pack_into('<2I',b,28,0x8010,0x8020)
    else:struct.pack_into('<3I',b,16,0x8000,0x8010,0x8020)
    return b

class Tables(unittest.TestCase):
    def test_supported_layouts(self):
        for size in [0x24,0x34,0x2c]:
            d=descriptor(fixture(size));self.assertEqual((d['name_va'],d['nids_va'],d['functions_va']),(0x8000,0x8010,0x8020))
    def test_all_descriptor_truncations_rejected(self):
        for size in [0x24,0x34,0x2c]:
            b=fixture(size)
            for i in range(size):
                with self.assertRaises(ValueError):descriptor(b[:i])
            with self.assertRaises(ValueError):descriptor(b+b'x')
    def test_invalid_size_and_required_pointer(self):
        with self.assertRaises(ValueError):descriptor(bytes(36))
        b=fixture(0x34);b[1]=1
        with self.assertRaises(ValueError):descriptor(b)
        b=fixture(0x24);struct.pack_into('<I',b,20,0)
        with self.assertRaises(ValueError):descriptor(b)
    def test_load_boundaries_and_no_bss(self):
        p=[dict(type=1,vaddr=0x8000,offset=0,filesz=4,memsz=8)]
        self.assertEqual(read_va(b'ABCD',p,0x8003,1),b'D')
        for va,n in [(0x8003,2),(0x8004,1),(-1,1),(0x8000,-1),(0xffffffff,2)]:
            with self.assertRaises(ValueError):read_va(b'ABCD',p,va,n)
        with self.assertRaises(ValueError):read_va(b'ABC',p,0x8003,1)
    def test_name_terminator_at_last_backed_byte(self):
        p=[dict(type=1,vaddr=0x8000,offset=0,filesz=4)]
        self.assertEqual(read_name(lambda a,n:read_va(b'ABC\0',p,a,n),0x8000),'ABC')
    def test_malformed_names(self):
        for blob in [b'\0',b'\xff\0',b'X'*96]:
            def reader(a,n):
                pos=a-0x8000
                if pos+n>len(blob):raise ValueError('end')
                return blob[pos:pos+n]
            with self.assertRaises(ValueError):read_name(reader,0x8000)
        with self.assertRaises(ValueError):read_name(lambda a,n:b'\0',0)
if __name__=='__main__':unittest.main()
