"""Two-slot journal with simulated I/O faults; no Vita filesystem execution."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';output=HERE/'value-journal-test.elf'
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=mhfz_journal_commit,--build-id=none',str(ROOT/'standalone/src/save_journal.c'),str(ROOT/'standalone/src/save_record.c'),str(HERE/'value_body.c'),str(HERE/'value_journal.c'),'-I'+str(ROOT/'standalone/src'),'-o',str(output)]
subprocess.run(command,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
symbols={}
for line in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'--defined-only',str(output)],text=True).splitlines():
    p=line.split()
    if len(p)==3:symbols[p[2]]=int(p[0],16)
elf=output.read_bytes();phoff=struct.unpack_from('<I',elf,28)[0];ps,pn=struct.unpack_from('<HH',elf,42);segments=[]
for i in range(pn):
    t,o,v,_,fs,ms,_,_=struct.unpack_from('<8I',elf,phoff+i*ps)
    if t==1:segments.append((o,v,fs,ms))
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);lo=min(s[1] for s in segments)&~4095;hi=(max(s[1]+s[3] for s in segments)+4095)&~4095;u.mem_map(lo,hi-lo)
for o,v,fs,ms in segments:u.mem_write(v,elf[o:o+fs])
journal,scratch,data,sizep,inp,stack,reader,writer,stop=[0x400000+i*0x20000 for i in range(9)]
for a in [journal,scratch,data,sizep,inp,stack,reader,writer,stop]:u.mem_map(a,0x20000)
slots={};mode='normal';writes=[];just_written=False
def hook(cpu,address,size,user):
    global just_written
    slot=cpu.reg_read(UC_ARM_REG_R1);pointer=cpu.reg_read(UC_ARM_REG_R2);n=cpu.reg_read(UC_ARM_REG_R3);assert slot in (0,1)
    if address==reader:
        if mode=='read_error' or (mode=='verify_error' and just_written):result=-2
        elif slot not in slots:result=-1
        elif len(slots[slot])>n:result=-2
        else:cpu.mem_write(pointer,slots[slot]);result=len(slots[slot])
    else:
        blob=bytes(cpu.mem_read(pointer,n));writes.append(slot);just_written=True
        slots[slot]=blob[:10] if mode=='partial_write' else blob
        result=-1 if mode in ('partial_write','after_write') else 0
    cpu.reg_write(UC_ARM_REG_R0,result&0xffffffff);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook,begin=reader,end=reader);u.hook_add(UC_HOOK_CODE,hook,begin=writer,end=writer)
def reset():u.mem_write(journal,struct.pack('<8I',scratch,4096,reader|1,writer|1,0,0,0,0))
def call(name,values):
    for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],values):u.reg_write(reg,val)
    u.reg_write(UC_ARM_REG_SP,stack+0x1fff0);u.reg_write(UC_ARM_REG_LR,stop|1)
    u.emu_start(symbols[name]|1,stop,timeout=2000000,count=1000000);assert u.reg_read(UC_ARM_REG_PC)==stop
    x=u.reg_read(UC_ARM_REG_R0);return x-(1<<32) if x&0x80000000 else x

tests=[]
value=sizep+64
def load(label,expected,payload=None):
    global just_written
    just_written=False;reset();u.mem_write(value,b'\xa5'*12)
    r=call('wdsv_load_value',[journal,data,4096,value]);assert r==expected,(label,r)
    if r in (1,2):
        flag,n,p=struct.unpack('<III',u.mem_read(value,12))
        assert flag==(r==2)
        assert bytes(u.mem_read(p,n))==(payload or b'')
    else:assert bytes(u.mem_read(value,12))==b'\xa5'*12
    tests.append(label)
def commit(label,payload,deleted,result):
    u.mem_write(inp,payload or b'\0');u.mem_write(value,struct.pack('<III',deleted,len(payload),inp))
    r=call('wdsv_commit_value',[journal,data,4096,value]);assert r==result,(label,r)
    tests.append(label)
load('absent',0)
commit('initial live',b'OLD',0,0);load('live restart',1,b'OLD')
commit('confirmed tombstone',b'',1,0);load('deleted restart',2)
mode='partial_write';commit('partial recreate rejected',b'NEW',0,-1)
mode='normal';load('partial recreate keeps deletion',2)
commit('recreate',b'NEXT',0,0);load('recreated',1,b'NEXT')
mode='partial_write';commit('partial deletion rejected',b'',1,-1)
mode='normal';load('partial deletion keeps live',1,b'NEXT')
mode='after_write';commit('unacknowledged deletion',b'',1,-1)
mode='normal';load('complete unacknowledged deletion recovered',2)
commit('empty live differs from deletion',b'',0,0);load('empty live recovered',1,b'')
mode='verify_error';commit('verify error no success',b'UNACK',0,-1)
mode='normal';load('unacknowledged live recovered',1,b'UNACK')
def record(seq,payload):
    h=b'MZSAV001'+struct.pack('<III',seq,len(payload),zlib.crc32(payload));return h+struct.pack('<I',zlib.crc32(h))+payload
slots={0:record(1,b'not-a-value')};load('valid outer invalid inner blocks',-1)
count=len(writes);commit('invalid inner cannot overwrite',b'X',0,-1);assert len(writes)==count
live=b'MZV1'+struct.pack('<II',0,1)+b'X'
tomb=b'MZV1'+struct.pack('<II',1,0)
slots={0:record(7,live),1:record(7,tomb)};load('same sequence live/deletion conflict rejected',-1)
count=len(writes);commit('conflict cannot overwrite',b'Y',0,-1);assert len(writes)==count
slots={0:record(7,live),1:record(7,live)};load('identical duplicate sequence accepted',1,b'X')
slots={0:record(7,live),1:record(7,live[:-1]+b'Y')};load('same size different contents rejected',-1)
slots={};load('fresh',0);commit('live for I/O failure',b'LAST',0,0)
mode='read_error';load('load I/O error',-2)
report={'scope':'Own C value envelope integrated with existing C journal under ARM emulation and simulated callbacks; no VitaOS or filesystem','passed':len(tests),'tests':tests,'elf_sha256':hashlib.sha256(elf).hexdigest()}
(HERE/'value-journal-arm-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(tests),'scope':report['scope']}))
