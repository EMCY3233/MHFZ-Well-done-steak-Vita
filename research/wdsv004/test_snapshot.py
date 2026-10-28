import hashlib
import struct
import unittest
import zlib
from snapshot import Member, recover
from batch_manifest import ENTRY, MAGIC


def record(payload=b'A', sequence=1, deleted=False):
    body = b'MZV1' + struct.pack('<2I', int(deleted), len(payload)) + payload
    header = b'MZSAV001' + struct.pack('<3I', sequence, len(body), zlib.crc32(body))
    return header + struct.pack('<I', zlib.crc32(header)) + body


def manifest(generation=1, members=None):
    rows = []
    for logical in range(3):
        member = (members or {}).get(logical)
        if member is None:
            rows.append(ENTRY.pack(logical, 0, 0xffffffff, 0, 0, 0, bytes(32)))
        else:
            state, slot, sequence, raw = member
            rows.append(ENTRY.pack(logical, state, slot, sequence, len(raw), 0, hashlib.sha256(raw).digest()))
    body = MAGIC + struct.pack('<2I', generation, 3) + b''.join(rows)
    return body + struct.pack('<I', zlib.crc32(body))


class Snapshots(unittest.TestCase):
    def test_absent_manifest_is_not_corruption(self):
        self.assertIsNone(recover([None, None], {}))
        with self.assertRaises(ValueError): recover([b'', None], {})

    def test_committed_empty_snapshot(self):
        self.assertEqual(recover([manifest(), None], {}).members, (Member(0, None),)*3)

    def test_orphan_higher_sequence_ignored(self):
        old, orphan = record(b'old'), record(b'new', 99)
        state = recover([manifest(members={0:(1,0,1,old)}), None], {(0,0):old, (0,1):orphan})
        self.assertEqual(state.members[0].payload, b'old')

    def test_whole_snapshot_fallback_no_mixed_members(self):
        a,b,newa,newb = record(b'A'),record(b'B'),record(b'NEW-A',2),record(b'NEW-B',2)
        old = manifest(1,{0:(1,0,1,a),1:(1,0,1,b)})
        new = manifest(2,{0:(1,1,2,newa),1:(1,1,2,newb)})
        records={(0,0):a,(1,0):b,(0,1):newa,(1,1):newb[:-1]}
        snap=recover([old,new],records)
        self.assertEqual((snap.generation,tuple(x.payload for x in snap.members[:2])),(1,(b'A',b'B')))

    def test_complete_new_generation_selected(self):
        a,b=record(b'old'),record(b'new',2)
        snap=recover([manifest(1,{0:(1,0,1,a)}),manifest(2,{0:(1,1,2,b)})],{(0,0):a,(0,1):b})
        self.assertEqual((snap.generation,snap.members[0].payload),(2,b'new'))

    def test_live_empty_tombstone_absent_are_distinct(self):
        live,deleted=record(b''),record(b'',deleted=True)
        snap=recover([manifest(members={0:(1,0,1,live),1:(2,1,1,deleted)}),None],{(0,0):live,(1,1):deleted})
        self.assertEqual(snap.members,(Member(1,b''),Member(2,b''),Member(0,None)))

    def test_wrong_slot_is_not_substituted(self):
        raw=record()
        with self.assertRaises(ValueError): recover([manifest(members={0:(1,0,1,raw)}),None],{(0,1):raw})

    def test_wrong_digest_is_rejected(self):
        raw=record()
        with self.assertRaises(ValueError): recover([manifest(members={0:(1,0,1,raw)}),None],{(0,0):record(b'B')})

    def test_sequence_state_crc_and_envelope_checked_independently(self):
        raw=record()
        broken_crc=raw[:20]+bytes([raw[20]^1])+raw[21:]
        broken_payload=raw[:-1]+b'Z'
        # Manifest hashes describe each supplied record; lower validation must reject it.
        for state,seq,value in [(1,2,raw),(2,1,raw),(1,1,broken_crc),(1,1,broken_payload)]:
            with self.subTest(state=state,seq=seq),self.assertRaises(ValueError):
                recover([manifest(members={0:(state,0,seq,value)}),None],{(0,0):value})

    def test_equal_generation_conflict_blocks(self):
        a,b=record(b'A'),record(b'B')
        with self.assertRaises(ValueError):
            recover([manifest(1,{0:(1,0,1,a)}),manifest(1,{0:(1,1,1,b)})],{(0,0):a,(0,1):b})

    def test_identical_equal_generation_uses_first_slot(self):
        raw=manifest()
        self.assertEqual(recover([raw,raw],{}).manifest_slot,0)

    def test_truncated_new_manifest_falls_back(self):
        self.assertEqual(recover([manifest(1),manifest(2)[:-1]],{}).generation,1)

    def test_no_complete_snapshot_blocks(self):
        a=record()
        with self.assertRaises(ValueError): recover([manifest(members={0:(1,0,1,a)}),None],{})

    def test_wrong_manifest_slot_count(self):
        with self.assertRaises(ValueError): recover([None],{})

    def test_larger_reference_does_not_change_native_backend(self):
        raw=record(b'L'*512000)
        self.assertEqual(len(recover([manifest(members={0:(1,0,1,raw)}),None],{(0,0):raw}).members[0].payload),512000)