"""Native plan vs Python reference; synthetic records, no I/O or VitaOS."""
import pathlib,sys,subprocess,struct,json,hashlib
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sys.path.insert(0,str(HERE))
from test_snapshot import record,manifest
from batch_plan import prepare
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';target=HERE/'batch-plan-test.elf'
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_prepare,--build-id=none',*[str(HERE/(name+'.c')) for name in ['batch_plan','snapshot_reader','manifest_reader','record_ref','sha256']],'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert not subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'-u',str(target)],text=True).strip()
symbols={}
for line in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'--defined-only',str(target)],text=True).splitlines():
 p=line.split()
 if len(p)==3:symbols[p[2]]=int(p[0],16)
b=target.read_bytes();off=struct.unpack_from('<I',b,28)[0];ent,n=struct.unpack_from('<HH',b,42)
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,0x40000);u.mem_map(0x400000,0x400000)
for i in range(n):
 typ,o,v,_,fs,ms,_,_=struct.unpack_from('<8I',b,off+i*ent)
 if typ==1:u.mem_write(v,b[o:o+fs])
base=0x400000;out=0x700000;stack=0x7ff000;stop=0x7fe000;cases=[]
def check(ms,records,changes,label):
 cursor=base+0x1000
 def allocate(raw):
  nonlocal cursor
  if raw is None:return [0,0]
  ptr=cursor;u.mem_write(ptr,raw or b'\0');cursor+=(len(raw)+15)//16*16+16
  return [ptr,len(raw)]
 mt=sum([allocate(raw) for raw in ms],[])
 rt=sum([allocate(records.get((i,j))) for i in range(3) for j in range(2)],[])
 ct=sum([allocate(changes.get(i)) for i in range(3)],[])
 u.mem_write(base,struct.pack('<4I',*mt));u.mem_write(base+0x100,struct.pack('<12I',*rt));u.mem_write(base+0x200,struct.pack('<6I',*ct));u.mem_write(out,b'\xa5'*208)
 try:expected=prepare(ms,records,changes);code=0
 except ValueError:expected=None;code=0xffffffff
 for reg,val in [(UC_ARM_REG_R0,base),(UC_ARM_REG_R1,base+0x100),(UC_ARM_REG_R2,base+0x200),(UC_ARM_REG_R3,symbols['wdsv004_sha256']|1),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.mem_write(stack,struct.pack('<I',out))
 u.emu_start(symbols['wdsv004_prepare']|1,stop,timeout=30000000,count=150000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop
 assert u.reg_read(UC_ARM_REG_R0)==code,label
 raw=bytes(u.mem_read(out,208))
 if expected:
  slots=[0xffffffff]*3;mask=0
  for logical,slot,_ in expected.writes:slots[logical]=slot;mask|=1<<logical
  assert raw==struct.pack('<5I',expected.manifest_slot,mask,*slots)+expected.manifest,label
 else:assert raw==b'\xa5'*208,label
 cases.append(label)
a,bv=record(b'A'),record(b'B');m=[manifest(members={0:(1,0,1,a),1:(1,1,1,bv)}),None];r={(0,0):a,(1,1):bv}
check(m,r,{0:record(b'next',2)},'one changed preserves other refs')
check(m,r,{0:record(b'next',2),1:record(b'other',2)},'two changes opposite slots')
check(m,r,{0:record(b'',2),1:record(b'',2,True),2:record(b'first')},'empty live tombstone first introduction')
check([None,None],{},{0:record()},'absence cannot initialize')
check(m,r,{},'empty batch rejected')
for raw in [record(b'wrong sequence'),record(b'bad',2)[:-1],record(b'X'*163841,2)]:check(m,r,{0:raw},'invalid replacement '+str(len(raw)))
check(m,r,{0:record(b'X'*163840,2)},'native capacity accepted')
check([manifest(0xffffffff),None],{},{0:record()},'generation exhausted')
check([m[0],manifest(9,{0:(1,1,8,record(b'orphan',8))})],r,{0:record(b'next',2)},'generation above incomplete newer')
check([m[0],manifest(1)],r,{0:record(b'next',2)},'conflicting baseline rejected')
last=record(b'last',0xffffffff)
check([manifest(members={0:(1,0,0xffffffff,last)}),None],{(0,0):last},{0:record(b'wrap',1)},'sequence exhausted')
report=dict(scope='Native batch preparation, recovery and SHA under ARM; Python parity oracle only; no writes/OS/client/Vita',passed=len(cases),cases=cases,elf_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),undefined_symbols=[])
(HERE/'batch-plan-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))