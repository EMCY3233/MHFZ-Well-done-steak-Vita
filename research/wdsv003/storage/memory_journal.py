"""Two-record recovery reference. Bytes in RAM model durable media, not Vita I/O.

This private format is not Frontier savedata or the existing C journal format.
Snapshot/restart models process interruption only, not hardware durability.
"""
import struct
import zlib
from storage_policy import destination, NAMES

MAGIC = b"WDSV3M01"
LIMIT = 0x28000
PATHS = frozenset(destination(n) for n in NAMES)
HEADER = struct.Struct("<8sIIII")

def encode(sequence, deleted, payload):
    if not 1 <= sequence <= 0xffffffff or not isinstance(payload,bytes):
        raise ValueError("record")
    if len(payload)>LIMIT or deleted and payload:
        raise ValueError("payload")
    prefix = struct.pack("<8sIII",MAGIC,sequence,int(deleted),len(payload))
    return prefix + struct.pack("<I",zlib.crc32(prefix+payload)) + payload

def decode(raw):
    if not isinstance(raw,bytes) or len(raw)<HEADER.size:
        return None
    magic,seq,flag,size,crc = HEADER.unpack_from(raw)
    if magic!=MAGIC or seq==0 or flag not in (0,1) or size>LIMIT:
        return None
    if len(raw)!=HEADER.size+size or flag and size:
        return None
    payload=raw[HEADER.size:]
    if zlib.crc32(raw[:20]+payload)!=crc:
        return None
    return seq,bool(flag),payload

class MemoryJournal:
    def __init__(self, image=None):
        self.image = {} if image is None else {p:list(pair) for p,pair in image.items()}
        if any(p not in PATHS or len(pair)!=2 for p,pair in self.image.items()):
            raise ValueError("invalid image namespace")
        self.failpoint = None
        self.fail_next_read = False
        self.calls = []

    def snapshot(self):
        return {p:tuple(pair) for p,pair in self.image.items()}

    def _latest(self,path):
        if path not in PATHS:
            raise OSError("destination denied")
        pair=self.image.get(path,[None,None])
        valid=[(i,decode(raw)) for i,raw in enumerate(pair) if raw is not None]
        valid=[(i,r) for i,r in valid if r is not None]
        if not valid:
            if any(raw is not None for raw in pair):
                raise OSError("no recoverable record")
            return None
        # Equal sequence with different records is ambiguous: never guess.
        if len(valid)==2 and valid[0][1][0]==valid[1][1][0] and pair[0]!=pair[1]:
            raise OSError("conflicting sequence")
        return max(valid,key=lambda item:(item[1][0],-item[0]))

    def read(self,path):
        self.calls.append(("read",path))
        if self.fail_next_read:
            self.fail_next_read=False
            raise OSError("injected before ACK")
        latest=self._latest(path)
        return None if latest is None or latest[1][1] else latest[1][2]

    def _write(self,path,payload,deleted):
        latest=self._latest(path)
        seq=0 if latest is None else latest[1][0]
        if seq==0xffffffff:
            return -1
        slot=0 if latest is None else 1-latest[0]
        raw=encode(seq+1,deleted,payload)
        failpoint=self.failpoint
        self.failpoint=None
        if failpoint=="before":
            return -1
        pair=self.image.setdefault(path,[None,None])
        if failpoint=="partial":
            pair[slot]=raw[:len(raw)//2]
            return -1
        pair[slot]=raw
        if failpoint=="afterwrite":
            return -1
        if failpoint=="beforeACK":
            self.fail_next_read=True
        return 0

    def commit(self,path,data):
        self.calls.append(("commit",path))
        if not isinstance(data,bytes) or len(data)>LIMIT:
            return -1
        return self._write(path,data,False)

    def remove(self,path):
        self.calls.append(("remove",path))
        # A newer empty tombstone is retained. Old payload slot is not exposed.
        return self._write(path,b"",True)
