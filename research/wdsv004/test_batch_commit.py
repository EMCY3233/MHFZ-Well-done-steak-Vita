import unittest
from batch_commit import Coordinator
from snapshot import recover
from test_snapshot import record, manifest


class Publication(unittest.TestCase):
    def run_case(self, fault=None):
        a,b=record(b'A'),record(b'B')
        m=[manifest(members={0:(1,0,1,a),1:(1,0,1,b)}),None]
        r={(0,0):a,(1,0):b}
        events=[];reads=0
        def read():
            nonlocal reads
            reads+=1
            if reads==2 and fault=='unchanged': r[1,0]=b[:-1]
            if reads==2 and fault=='baseline': m[1]=b'changed'
            return tuple(m),dict(r)
        def wr(logical,slot,raw):
            events.append('record')
            r[logical,slot]=raw[:-1] if fault=='record-readback' else raw
            return False if fault=='record-ack' else True
        def wm(slot,raw):
            events.append('manifest')
            m[slot]=raw[:-1] if fault=='manifest-readback' else raw
            return False if fault=='manifest-ack' else True
        c=Coordinator(read,wr,wm)
        if fault:
            with self.assertRaises((ValueError,RuntimeError)): c.commit({0:record(b'new',2)})
            count=len(events)
            with self.assertRaises(RuntimeError): c.commit({0:record(b'again',2)})
            self.assertEqual(len(events),count)
            if fault in ('record-readback','record-ack','unchanged','baseline'):
                self.assertNotIn('manifest',events)
            if fault=='manifest-ack': self.assertEqual(recover(m,r).generation,2)
        else:
            self.assertEqual(c.commit({0:record(b'new',2)}).generation,2)
            self.assertEqual(events,['record','manifest'])

    def test_success(self): self.run_case()

    def test_mutable_observations_rejected_before_publication(self):
        for phase in (1,2,3):
            for mutable_member in (False,True):
                with self.subTest(phase=phase,record=mutable_member):
                    original=record(b'A')
                    m=[manifest(members={0:(1,0,1,original)}),None]
                    r={(0,0):original}; calls=[]; reads=0
                    def read():
                        nonlocal reads
                        reads+=1
                        a,b=list(m),dict(r)
                        if reads==phase:
                            if mutable_member: b[0,0]=bytearray(original)
                            else: a[0]=bytearray(a[0])
                        return a,b
                    def wr(logical,slot,raw):
                        calls.append('record');r[logical,slot]=raw;return True
                    def wm(slot,raw):
                        calls.append('manifest');m[slot]=raw;return True
                    c=Coordinator(read,wr,wm)
                    with self.assertRaises(ValueError): c.commit({0:record(b'next',2)})
                    self.assertTrue(c.blocked)
                    if phase==1: self.assertEqual(calls,[])
                    if phase==2: self.assertEqual(calls,['record'])
                    if phase==3: self.assertEqual(calls,['record','manifest'])

    def test_faults_block_and_order_publication(self):
        for fault in ('record-ack','record-readback','baseline','unchanged','manifest-ack','manifest-readback'):
            with self.subTest(fault=fault): self.run_case(fault)