"""Own native handoff and synthetic allocator under ARM; no game/OS calls."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
from arm_tools import sdk_bin
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
HERE = Path(__file__).resolve().parent
sdk = sdk_bin()
output = HERE / 'text-handoff-test.elf'
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'), '-mthumb', '-mcpu=cortex-a9', '-mfloat-abi=soft', '-Os', '-Wall', '-Wextra', '-Werror', '-ffreestanding', '-fno-builtin', '-fno-ipa-icf', '-fno-stack-protector', '-nostdlib', '-Wl,-Ttext=0x10000,--entry=wdsv004_text_prepare,--build-id=none', str(HERE/'text_handoff.c'), str(HERE/'text_handoff_test.c'), '-o', str(output)], check=True)
assert not subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'), '-u', str(output)], text=True).strip()
symbols = {}
for line in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'), '--defined-only', str(output)], text=True).splitlines():
    row = line.split()
    if len(row) == 3:
        symbols[row[2]] = int(row[0], 16)
raw = output.read_bytes()
offset = struct.unpack_from('<I', raw, 28)[0]
size, count = struct.unpack_from('<HH', raw, 42)
segments = [struct.unpack_from('<8I', raw, offset+i*size) for i in range(count)]
segments = [s for s in segments if s[0] == 1]
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
low = min(s[2] for s in segments) & ~4095
high = (max(s[2]+s[5] for s in segments)+4095) & ~4095
u.mem_map(low, high-low)
for _, off, address, _, length, *_ in segments:
    u.mem_write(address, raw[off:off+length])
u.mem_map(0x400000, 0x400000)
source, owner, receiver = 0x410000, 0x600100, 0x600200
stack, stop = 0x7ff000, 0x7fe000
allocator = symbols['test_allocator']
original_allocator = bytes(u.mem_read(allocator, 12))
cases = []

def put(address, value):
    u.mem_write(address, struct.pack('<I', value & 0xffffffff))

def get(address):
    return struct.unpack('<I', u.mem_read(address, 4))[0]

def global_value(name):
    return get(symbols['test_'+name])

def call(name, *args):
    values = list(args[:4]) + [0]*max(0, 4-len(args))
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), values):
        u.reg_write(reg, value)
    for i, value in enumerate(args[4:]):
        put(stack+4*i, value)
    u.reg_write(UC_ARM_REG_SP, stack)
    u.reg_write(UC_ARM_REG_LR, stop | 1)
    u.emu_start(symbols['wdsv004_text_'+name] | 1, stop, timeout=30000000, count=30000000)
    assert u.reg_read(UC_ARM_REG_PC) == stop, 'execution did not finish'
    assert u.reg_read(UC_ARM_REG_SP) == stack, 'stack not restored'
    result = u.reg_read(UC_ARM_REG_R0)
    return result if result < 0x80000000 else result-0x100000000

def reset(payload=b'abc', mode=0):
    u.mem_write(source, payload or b'!')
    u.mem_write(owner, bytes(24))
    u.mem_write(receiver, bytes(24))
    u.mem_write(allocator, original_allocator)
    for name in ('mode','allocations','releases','requested','reentry','alias','freed'):
        put(symbols['test_'+name], 0)
    put(symbols['test_mode'], mode)
    put(symbols['test_owner'], owner)

def prepare(extent=3, expected=3, completed=3, capacity=3, ptr=source, target=owner, alloc=None):
    return call('prepare', target, ptr, extent, expected, completed, capacity, allocator if alloc is None else alloc)

def record(name):
    cases.append(name)

# Successful preparation, exact capacities and independent lifetimes.
for name, payload, length, ptr in [('exact',b'abc',3,source), ('empty',b'',0,0), ('maximum',b'x'*512000,512000,source), ('validated-prefix',b'ab\0tail',2,source)]:
    reset(payload)
    assert prepare(len(payload),length,length,length,ptr) == 0
    data = get(owner+4)
    assert data == symbols['test_arena'] and get(owner) == 2
    assert get(owner+8) == length and get(owner+12) == length+1
    assert bytes(u.mem_read(data,length+1)) == payload[:length]+b'\0'
    assert global_value('allocations') == 1 and global_value('releases') == 0
    u.mem_write(source,b'changed')
    assert bytes(u.mem_read(data,length+1)) == payload[:length]+b'\0'
    assert call('dispose',owner) == 0 and get(owner) == 4
    assert global_value('releases') == 1 and global_value('reentry') == 0xffffffff
    assert call('dispose',owner) == -1 and global_value('releases') == 1
    record(name)

invalid = [
 ('partial',dict(expected=3,completed=2)),
 ('over-completion',dict(expected=2,completed=3)),
 ('over-capacity',dict(capacity=2)),
 ('capacity-limit',dict(capacity=512001)),
 ('short-source',dict(extent=2)),
 ('null-source',dict(ptr=0)),
 ('source-range-wrap',dict(ptr=0xfffffff0,extent=32)),
 ('null-owner',dict(target=0)),
 ('null-allocator',dict(alloc=0)),
 ('source-owner-alias',dict(ptr=owner,extent=24,expected=0,completed=0,capacity=0)),
]
for name, kwargs in invalid:
    reset()
    assert prepare(**kwargs) == -1
    assert global_value('allocations') == global_value('releases') == 0
    record(name)
for name,payload in [('leading-zero',b'\0bc'),('interior-zero',b'a\0c'),('last-zero',b'ab\0')]:
    reset(payload)
    assert prepare() == -1 and global_value('allocations') == 0
    record(name)
for slot in (4,8):
    reset()
    put(allocator+slot,0)
    assert prepare() == -1 and global_value('allocations') == 0
    record('missing-callback-'+str(slot))
for state in range(1,6):
    reset()
    put(owner,state)
    assert prepare() == -1 and global_value('allocations') == 0
    record('reject-state-'+str(state))

reset(mode=1)
assert prepare() == -2 and get(owner) == 0
assert global_value('allocations') == 1 and global_value('releases') == 0
put(symbols['test_mode'],0)
assert prepare() == 0 and call('dispose',owner) == 0
record('allocation-failure-retry')
for mode in (2,3):
    reset(mode=mode)
    assert prepare() == -3 and get(owner) == 5
    assert global_value('releases') == 1 and global_value('reentry') == 0xffffffff
    assert call('dispose',owner) == -1 and prepare() == -1
    assert global_value('releases') == 1
    record('invalid-allocation-extent-'+str(mode))
reset(mode=5)
assert prepare() == -3 and get(owner) == 5 and global_value('releases') == 0
record('null-with-extent')
for name,pointer in [('borrowed-source',source),('partial-source-alias',source+2),('owner-alias',owner),('result-range-wrap',0xfffffffe)]:
    reset(mode=4)
    put(symbols['test_alias'],pointer)
    assert prepare() == -3 and get(owner) == 5 and global_value('releases') == 0
    assert bytes(u.mem_read(source,3)) == b'abc'
    record(name)
reset(mode=7)
put(symbols['test_alias'],source-3)
assert prepare() == -3 and get(owner) == 5
assert global_value('releases') == 1 and global_value('freed') == source-3
assert bytes(u.mem_read(source,3)) == b'abc'
record('wrong-extent-adjacent-independent-block')
reset(mode=8)
put(symbols['test_alias'],source)
assert prepare() == -3 and get(owner) == 5 and global_value('releases') == 0
record('zero-extent-source-alias')
reset(mode=4)
put(symbols['test_alias'],source)
assert prepare(0,0,0,0) == -3 and get(owner) == 5 and global_value('releases') == 0
record('empty-source-base-alias')
reset()
assert prepare(0,0,0,0,0) == 0
# Fixture arena is larger than the declared one-byte text allocation; make the
# deliberately overlapping destination look EMPTY to reach the range check.
u.mem_write(symbols['test_arena'],bytes(24))
assert get(symbols['test_arena']) == 0
assert call('move',symbols['test_arena'],owner) == -1 and get(owner) == 2
assert call('dispose',owner) == 0 and global_value('releases') == 1
record('move-into-owned-text-rejected')
reset(mode=6)
assert prepare() == 0 and global_value('reentry') == 0xffffffff
assert call('dispose',owner) == 0
record('busy-during-allocation')
reset()
assert prepare() == 0
before=bytes(u.mem_read(owner,24))
assert call('move',owner,owner) == -1 and bytes(u.mem_read(owner,24)) == before
assert call('move',0,owner) == -1
assert call('move',owner+4,owner) == -1 and bytes(u.mem_read(owner,24)) == before
assert call('move',receiver,owner) == 0
assert get(owner) == 3 and get(owner+4) == 0 and get(receiver) == 2
assert call('dispose',owner) == -1 and global_value('releases') == 0
assert call('move',owner,receiver) == -1  # moved-from handle is terminal
put(symbols['test_owner'],receiver)
assert call('dispose',receiver) == 0 and global_value('releases') == 1
assert call('dispose',receiver) == -1 and global_value('releases') == 1
record('move-and-exactly-once-release')
reset()
assert prepare() == 0
put(receiver,2)
before=bytes(u.mem_read(owner,24))
assert call('move',receiver,owner) == -1 and bytes(u.mem_read(owner,24)) == before
assert call('dispose',owner) == 0
record('move-to-occupied-rejected')
reset()
assert call('move',receiver,owner) == -1 and call('dispose',0) == -1
record('empty-and-null-dispose')
report=dict(scope='Own native text ownership/copy under ARM with native synthetic allocator; no commercial parser/client/OS/Vita ABI',passed=len(cases),cases=cases,elf_sha256=hashlib.sha256(raw).hexdigest(),undefined_symbols=[],source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'text_handoff.c',HERE/'text_handoff.h',HERE/'text_handoff_test.c',Path(__file__)]})
(HERE/'text-handoff-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))
