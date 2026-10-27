import unittest
from self_bounds import check_layout
def seg(i,off,n,tail=0,match=True):return dict(index=i,container_offset=off,container_length=n,unused_trailing_bytes=tail,matches_derived=match)
class Layout(unittest.TestCase):
    def test_valid_disjoint_and_touching(self):self.assertEqual(check_layout(30,30,[seg(0,10,10),seg(1,20,10)]),[])
    def test_stale_size(self):self.assertIn('DECLARED_SIZE_MISMATCH',check_layout(30,29,[seg(0,10,20)]))
    def test_overlap(self):self.assertIn('OVERLAPPING_SEGMENTS',check_layout(30,30,[seg(0,10,15),seg(1,20,10)]))
    def test_invalid_bounds(self):
        for o,n in [(-1,2),(0,-1),(29,2)]:self.assertIn('SEGMENT_OUTSIDE_FILE',check_layout(30,30,[seg(0,o,n)]))
    def test_decode_anomalies(self):
        self.assertEqual(check_layout(30,30,[seg(0,10,20,21,False)]),['COMPRESSED_TRAILING_DATA','DECODED_SEGMENT_MISMATCH'])
    def test_reordered_segments(self):self.assertEqual(check_layout(30,30,[seg(1,20,10),seg(0,10,10)]),[])
    def test_missing_segments(self):self.assertEqual(check_layout(30,30,[]),['NO_SEGMENTS'])
if __name__=='__main__':unittest.main()
