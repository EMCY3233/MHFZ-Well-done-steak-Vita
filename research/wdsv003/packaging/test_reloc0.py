import struct,unittest
from reloc0 import decode,validate,summarize
class Form0(unittest.TestCase):
    def setUp(self):self.segs={0:dict(type=1,memsz=100,filesz=80),1:dict(type=1,memsz=200,filesz=160)}
    def make(self,code=2,patch=0,symbol=1,offset=96,code2=0,dist=0):return decode(struct.pack('<III',(symbol<<4)|(code<<8)|(patch<<16)|(code2<<20)|(dist<<28),0x87654321,offset))
    def test_fields(self):
        r=self.make(47,1,0,124,48,2);self.assertEqual((r['code'],r['code2'],r['dist2'],r['addend'],r['offset']),(47,48,2,0x87654321,124))
    def test_exact_and_overrun(self):
        self.assertEqual(validate(self.make(),self.segs),[])
        self.assertIn('target_range',validate(self.make(offset=97),self.segs))
        self.assertIn('target_range',validate(self.make(code2=44,dist=1),self.segs))
    def test_absolute_and_invalid_segments(self):
        self.assertEqual(validate(self.make(symbol=15),self.segs),[])
        self.assertIn('symbol_segment',validate(self.make(symbol=2),self.segs))
        self.assertIn('patch_segment',validate(self.make(patch=2),self.segs))
    def test_unknown_code(self):self.assertIn('unknown_code',validate(self.make(code=99),self.segs))
    def test_bad_records(self):
        for b in [b'',bytes(11),bytes(13),struct.pack('<III',1,0,0)]:
            with self.assertRaises(ValueError):decode(b)
        with self.assertRaises(ValueError):summarize(bytes(13),self.segs)
if __name__=='__main__':unittest.main()
