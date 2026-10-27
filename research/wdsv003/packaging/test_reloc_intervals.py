import unittest
from reloc_intervals import overlaps,intersects
def r(off,n=4,seg=0):return dict(segment=seg,offset=off,size=n)
class Intervals(unittest.TestCase):
    def test_touching_not_overlapping(self):self.assertEqual(overlaps([r(0),r(4)]),[])
    def test_nested_ranges(self):self.assertEqual(len(overlaps([r(0,20),r(2),r(10)])),2)
    def test_distinct_segments(self):self.assertEqual(overlaps([r(0),r(0,4,1)]),[])
    def test_query_boundaries(self):
        self.assertTrue(intersects(r(10),0,13,1));self.assertFalse(intersects(r(10),0,14,1));self.assertFalse(intersects(r(10),1,10,4))
if __name__=='__main__':unittest.main()
