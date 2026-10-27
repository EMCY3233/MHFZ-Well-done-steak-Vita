import hashlib
import json
import pathlib
import unittest
from storage_policy import Policy,Result,destination,ROOT
from memory_journal import MemoryJournal,encode,decode,LIMIT

class RecoveryTests(unittest.TestCase):
    def test_save_interruptions_recover_complete_old_or_new(self):
        for failpoint,expected in [("before",b"old"),("partial",b"old"),
                                   ("afterwrite",b"new"),("beforeACK",b"new")]:
            with self.subTest(failpoint=failpoint):
                b=MemoryJournal();p=Policy(b)
                self.assertEqual(p.save("character",b"old",3),Result.OK)
                b.failpoint=failpoint
                self.assertNotEqual(p.save("character",b"new",3),Result.OK)
                self.assertTrue(p.uncertain)
                restarted=MemoryJournal(b.snapshot())
                self.assertEqual(restarted.read(destination("character")),expected)
                self.assertTrue(all(path.startswith(ROOT) for _,path in b.calls))
    def test_delete_interruptions_recover_old_or_tombstone(self):
        for failpoint,expected in [("before",b"old"),("partial",b"old"),
                                   ("afterwrite",None),("beforeACK",None)]:
            with self.subTest(failpoint=failpoint):
                b=MemoryJournal();p=Policy(b)
                p.save("character",b"old",3)
                b.failpoint=failpoint
                self.assertNotEqual(p.delete("character",6),Result.OK)
                self.assertTrue(p.uncertain)
                restarted=MemoryJournal(b.snapshot())
                self.assertEqual(restarted.read(destination("character")),expected)
    def test_confirmed_tombstone_never_selects_older_payload_on_restart(self):
        b=MemoryJournal();p=Policy(b);path=destination("character")
        p.save("character",b"first",3);p.save("character",b"second",3)
        self.assertEqual(p.delete("character",6),Result.OK)
        for _ in range(5):
            b=MemoryJournal(b.snapshot())
            self.assertIsNone(b.read(path))
            self.assertEqual(Policy(b).delete("character",6),Result.MISSING)
        self.assertEqual(Policy(b).save("character",b"recreated",3),Result.OK)
        self.assertEqual(MemoryJournal(b.snapshot()).read(path),b"recreated")
    def test_partial_recreate_after_delete_keeps_tombstone(self):
        b=MemoryJournal();p=Policy(b);path=destination("character")
        p.save("character",b"old",3);p.delete("character",6)
        b.failpoint="partial"
        self.assertEqual(p.save("character",b"new",3),Result.IO)
        self.assertIsNone(MemoryJournal(b.snapshot()).read(path))
    def test_maximum_and_actual_character_size(self):
        for size in [0,0x24d24,LIMIT]:
            with self.subTest(size=size):
                data=bytes((i*17+3)&255 for i in range(size))
                b=MemoryJournal();p=Policy(b)
                self.assertEqual(p.save("character",data,3),Result.OK)
                self.assertEqual(MemoryJournal(b.snapshot()).read(destination("character")),data)
                self.assertEqual(p.save("character",data+b"x"*(LIMIT-size+1),3),Result.DENIED)
    def test_header_and_payload_corruption_rejected(self):
        raw=encode(4,False,b"data")
        for offset in [0,8,12,16,20,24]:
            damaged=bytearray(raw);damaged[offset]^=1
            self.assertIsNone(decode(bytes(damaged)))
        self.assertIsNone(decode(raw+b"extra"))
        self.assertIsNone(decode(raw[:-1]))
    def test_both_corrupt_blocks_writes(self):
        path=destination("character")
        b=MemoryJournal({path:(b"bad",b"bad")})
        self.assertEqual(Policy(b).save("character",b"new",3),Result.IO)
    def test_ambiguous_sequence_blocks_read(self):
        path=destination("character")
        b=MemoryJournal({path:(encode(2,False,b"a"),encode(2,False,b"b"))})
        with self.assertRaises(OSError): b.read(path)
    def test_sequence_wrap_refused_without_modification(self):
        path=destination("character")
        b=MemoryJournal({path:(encode(0xffffffff,False,b"old"),None)})
        before=b.snapshot()
        self.assertEqual(Policy(b).save("character",b"new",3),Result.IO)
        self.assertEqual(before,b.snapshot())
    def test_three_logical_names_remain_independent(self):
        b=MemoryJournal();p=Policy(b)
        for name in ["INI-DATA","PRI-DATA","character"]:
            self.assertEqual(p.save(name,name.encode(),3),Result.OK)
        self.assertEqual(p.delete("PRI-DATA",6),Result.OK)
        restarted=MemoryJournal(b.snapshot())
        self.assertEqual(restarted.read(destination("INI-DATA")),b"INI-DATA")
        self.assertEqual(restarted.read(destination("character")),b"character")
        self.assertIsNone(restarted.read(destination("PRI-DATA")))
    def test_backend_rejects_foreign_namespace(self):
        b=MemoryJournal()
        with self.assertRaises(OSError): b.commit("ux0:data/PCSG00350/x",b"x")
        self.assertEqual(b.snapshot(),{})
        with self.assertRaises(ValueError): MemoryJournal({"foreign":(None,None)})

if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RecoveryTests))
    here=pathlib.Path(__file__).resolve().parent
    report={"scope":"Host RAM durable-image model and snapshot restart only; not Vita I/O or existing C journal tests", "tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"failpoints":["before","partial","afterwrite","beforeACK"],"files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [here/"memory_journal.py",here/"test_memory_journal.py",here/"storage_policy.py"]}}
    (here/"recovery-test-results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
