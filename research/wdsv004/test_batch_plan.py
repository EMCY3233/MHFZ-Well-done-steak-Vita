import unittest
from batch_plan import prepare
from snapshot import recover
from batch_manifest import read_manifest
from test_snapshot import record, manifest


class Preparation(unittest.TestCase):
    def setUp(self):
        self.a,self.b=record(b'A'),record(b'B')
        self.m=[manifest(members={0:(1,0,1,self.a),1:(1,1,1,self.b)}),None]
        self.r={(0,0):self.a,(1,1):self.b}

    def test_prefixes_preserve_current_until_manifest(self):
        plan=prepare(self.m,self.r,{0:record(b'newA',2),1:record(b'newB',2)})
        records=dict(self.r)
        for logical,slot,raw in plan.writes:
            self.assertNotEqual(slot,read_manifest(self.m[0])['entries'][logical]['slot'])
            records[logical,slot]=raw
            self.assertEqual(recover(self.m,records).generation,1)
        manifests=list(self.m);manifests[plan.manifest_slot]=plan.manifest
        self.assertEqual(recover(manifests,records).generation,2)
        records[plan.writes[1][:2]]=plan.writes[1][2][:-1]
        self.assertEqual(recover(manifests,records).generation,1)

    def test_unchanged_reference_and_empty_live(self):
        plan=prepare(self.m,self.r,{0:record(b'',2)})
        self.assertEqual(read_manifest(plan.manifest)['entries'][1],read_manifest(self.m[0])['entries'][1])

    def test_delete_and_new_absent_member(self):
        plan=prepare(self.m,self.r,{0:record(b'',2,True),2:record(b'first')})
        self.assertEqual([e['state'] for e in read_manifest(plan.manifest)['entries']],[2,1,1])

    def test_missing_baseline_and_empty_batch(self):
        for m,r,c in [([None,None],{}, {0:record()}),(self.m,self.r,{})]:
            with self.assertRaises(ValueError): prepare(m,r,c)

    def test_invalid_record_and_capacity(self):
        for raw in [record(b'bad',1),record(b'X'*163841,2),record(b'ok',2)[:-1],bytearray(record(b'ok',2))]:
            with self.assertRaises(ValueError): prepare(self.m,self.r,{0:raw})

    def test_generation_exhaustion(self):
        with self.assertRaises(ValueError): prepare([manifest(0xffffffff),None],{}, {0:record()})

    def test_generation_above_incomplete_candidate(self):
        self.m[1]=manifest(9,{0:(1,1,8,record(b'orphan',8))})
        self.assertEqual(read_manifest(prepare(self.m,self.r,{0:record(b'next',2)}).manifest)['generation'],10)