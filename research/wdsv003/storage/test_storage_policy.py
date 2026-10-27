import hashlib
import json
import pathlib
import unittest
from storage_policy import Policy, Result, ROOT, NAMES, destination

class MemoryBackend:
    """Fault-injection fixture, not a persistence implementation."""
    def __init__(self):
        self.data = {"ux0:user/00/savedata/PCSG00350/PRI-DATA": b"original sentinel"}
        self.calls = []
        self.mode = "ok"
    def read(self, path):
        self.calls.append(("read", path))
        if self.mode == "read-error":
            raise OSError("injected")
        return self.data.get(path)
    def commit(self, path, data):
        self.calls.append(("commit", path))
        if self.mode == "write-error":
            return -1
        self.data[path] = data[:-1] if self.mode == "short" else data
        if self.mode == "late-error":
            return -1
        return 0
    def remove(self, path):
        self.calls.append(("remove", path))
        if self.mode == "delete-error":
            return -1
        if self.mode != "delete-noop":
            self.data.pop(path, None)
        return 0

class Tests(unittest.TestCase):
    def setUp(self):
        self.backend = MemoryBackend()
        self.policy = Policy(self.backend)
        self.original = dict(self.backend.data)
    def tearDown(self):
        for path, data in self.original.items():
            self.assertEqual(self.backend.data[path], data)
        self.assertTrue(all(p.startswith(ROOT) for _,p in self.backend.calls))
    def test_hostile_names_never_reach_backend(self):
        names = ["../PRI-DATA", "INI-DATA/../PRI-DATA", "/PRI-DATA",
                 "ux0:data/PCSG00350/PRI-DATA", "savedata0:PRI-DATA",
                 "C:\\PRI-DATA", "..\\PRI-DATA", "%2e%2e/PRI-DATA",
                 "PRI-DATA\x00", "pri-data", "PCSG00350", "", None,
                 "INI-DATA ", "character/", "character.bin"]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.policy.save(name,b"x",3),Result.DENIED)
                self.assertEqual(self.policy.delete(name,6),Result.DENIED)
        self.assertEqual(self.backend.calls, [])
    def test_exact_destinations(self):
        self.assertEqual({destination(x) for x in NAMES},
                         {ROOT+"ini.bin",ROOT+"pri.bin",ROOT+"character.bin"})
    def test_state_mismatch_has_no_effect(self):
        for state in [0,1,2,4,5,6,7]:
            self.assertEqual(self.policy.save("character",b"x",state),Result.STATE)
        for state in [0,1,2,3,4,5,7]:
            self.assertEqual(self.policy.delete("character",state),Result.STATE)
        self.assertEqual(self.backend.calls, [])
    def test_save_and_delete_verified(self):
        self.assertEqual(self.policy.save("PRI-DATA",b"synthetic",3),Result.OK)
        self.assertEqual(self.policy.delete("PRI-DATA",6),Result.OK)
        self.assertEqual(len(self.policy.events),2)
    def test_missing_delete_not_success(self):
        self.assertEqual(self.policy.delete("INI-DATA",6),Result.MISSING)
    def test_failed_and_short_writes_not_acknowledged(self):
        for mode,status in [("write-error",Result.IO),("short",Result.VERIFY),
                            ("late-error",Result.IO),("read-error",Result.IO)]:
            with self.subTest(mode=mode):
                self.backend.mode = mode
                p = Policy(self.backend)
                self.assertEqual(p.save("character",b"abcdef",3),status)
                self.assertTrue(p.uncertain)
                self.backend.mode = "ok"
                self.assertEqual(p.save("character",b"next",3),Result.STATE)
                self.assertEqual(p.delete("character",6),Result.STATE)
    def test_failed_and_noop_deletes_not_acknowledged(self):
        for mode,status in [("delete-error",Result.IO),("delete-noop",Result.VERIFY)]:
            with self.subTest(mode=mode):
                self.backend.data[destination("character")] = b"old"
                self.backend.mode = mode
                p = Policy(self.backend)
                self.assertEqual(p.delete("character",6),status)
                self.assertTrue(p.uncertain)
    def test_size_and_type_rejected(self):
        for data in ["text",bytearray(b"x"),b"x"*(0x28000+1)]:
            self.assertEqual(self.policy.save("character",data,3),Result.DENIED)
        self.assertEqual(self.backend.calls, [])
    def test_events_do_not_leak_payload_or_hostile_name(self):
        self.policy.save("character",b"secret payload",3)
        self.policy.delete("ux0:private/account",6)
        s=repr(self.policy.events)
        self.assertNotIn("secret payload",s)
        self.assertNotIn("private/account",s)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    here = pathlib.Path(__file__).resolve().parent
    report = {"scope":"Host Python reference policy with memory fault injection; no Vita hooks or filesystem durability", "tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [here/"storage_policy.py",here/"test_storage_policy.py"]}}
    (here/"test-results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
