"""Host reference policy only. Not a Vita hook or an AppUtil replacement.

Only capability-like logical names are accepted. Backend is an injected test
object; a future native implementation must enforce these constraints itself.
"""
from dataclasses import dataclass
from enum import IntEnum

ROOT = "ux0:data/MHFZL0001/wdsv003/"
NAMES = {"INI-DATA": "ini.bin", "PRI-DATA": "pri.bin", "character": "character.bin"}

class Result(IntEnum):
    OK = 0
    DENIED = -1
    STATE = -2
    IO = -3
    VERIFY = -4
    MISSING = -5

def destination(name):
    # No normalization/URL decoding: reject all but exact known logical names.
    if not isinstance(name, str) or name not in NAMES:
        raise ValueError("unknown logical name")
    return ROOT + NAMES[name]

@dataclass(frozen=True)
class Event:
    number: int
    operation: str
    logical_name: str
    result: int
    size: int

class Policy:
    def __init__(self, backend):
        self.backend = backend
        self.events = []
        self.uncertain = False

    def _finish(self, op, name, status, size=0):
        # Do not log hostile input, payloads, accounts or tokens.
        self.events.append(Event(len(self.events)+1, op,
                                 name if isinstance(name,str) and name in NAMES else "rejected",
                                 int(status), size))
        return status

    def save(self, name, data, client_state):
        try:
            path = destination(name)
        except ValueError:
            return self._finish("save", name, Result.DENIED)
        if client_state != 3 or self.uncertain:
            return self._finish("save", name, Result.STATE)
        if not isinstance(data, bytes) or len(data) > 0x28000:
            return self._finish("save", name, Result.DENIED)
        self.uncertain = True
        try:
            # Contract: backend commit must preserve a recoverable previous
            # record on interrupted writes. Policy itself is not a journal.
            if self.backend.commit(path, data) != 0:
                return self._finish("save", name, Result.IO, len(data))
            if self.backend.read(path) != data:
                return self._finish("save", name, Result.VERIFY, len(data))
        except OSError:
            return self._finish("save", name, Result.IO, len(data))
        self.uncertain = False
        return self._finish("save", name, Result.OK, len(data))

    def delete(self, name, client_state):
        try:
            path = destination(name)
        except ValueError:
            return self._finish("delete", name, Result.DENIED)
        if client_state != 6 or self.uncertain:
            return self._finish("delete", name, Result.STATE)
        try:
            if self.backend.read(path) is None:
                return self._finish("delete", name, Result.MISSING)
            self.uncertain = True
            if self.backend.remove(path) != 0:
                return self._finish("delete", name, Result.IO)
            if self.backend.read(path) is not None:
                return self._finish("delete", name, Result.VERIFY)
        except OSError:
            return self._finish("delete", name, Result.IO)
        self.uncertain = False
        return self._finish("delete", name, Result.OK)

    # No broad slot/tree deletion and no relaunch API are exposed here.
    # Uncertain state requires disposing this instance and explicit backend
    # recovery; calling success after a failed write/delete is forbidden.
