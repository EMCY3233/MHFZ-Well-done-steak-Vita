"""Cross-compiled own code under ARM emulation; no VitaOS or physical I/O."""
import pathlib,sys,subprocess,struct,json,hashlib,collections
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';target=HERE/'snapshot-reader-test.elf'
(HERE/'record-ref-test-stub.c').write_text('#include <stdint.h>\nint wdsv_test_digest(const uint8_t *p,uint32_t n,uint8_t *o){(void)p;(void)n;(void)o;return -1;}\n')
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_recover,--build-id=none',str(HERE/'snapshot_reader.c'),str(HERE/'manifest_reader.c'),str(HERE/'record_ref.c'),str(HERE/'record-ref-test-stub.c'),'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
symbols={}
for line in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'--defined-only',str(target)],text=True).splitlines():
 p=line.split()
 if len(p)==3:symbols[p[2]]=int(p[0],16)
b=target.read_bytes();off=struct.unpack_from('<I',b,28)[0];ent,n=struct.unpack_from('<HH',b,42)
segments=[struct.unpack_from('<8I',b,off+i*ent) for i in range(n)]
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,0x40000)
for typ,o,v,_,fs,ms,_,_ in segments:
 if typ==1:u.mem_write(v,b[o:o+fs])
base=0x400000;u.mem_map(base,0x200000)
inp,out,obj,stack,stop=[base+i*0x50000 for i in range(5)]


sys.path.insert(0,str(HERE))
from test_snapshot import record,manifest
from snapshot import recover
mode='normal';digest_calls=0

def digest_hook(cpu,address,size,user):
 global digest_calls
 a,n,d=[cpu.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]];digest_calls+=1
 if mode!='digest_failure':cpu.mem_write(d,hashlib.sha256(bytes(cpu.mem_read(a,n))).digest())
 cpu.reg_write(UC_ARM_REG_R0,0xffffffff if mode=='digest_failure' else 0)
 cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,digest_hook,begin=symbols['wdsv_test_digest'],end=symbols['wdsv_test_digest'])
cases=[]

def check(manifests,records,label,force_error=False):
 cursor=inp+0x10000;mt=[];rt=[];pointers={}
 for raw in manifests:
  if raw is None:mt.extend([0,0]);continue
  u.mem_write(cursor,raw or b'\0');mt.extend([cursor,len(raw)]);cursor+=0x1000
 for logical in range(3):
  for slot in range(2):
   raw=records.get((logical,slot))
   if raw is None:rt.extend([0,0]);continue
   u.mem_write(cursor,raw or b'\0');rt.extend([cursor,len(raw)]);pointers[(logical,slot)]=cursor;cursor+=0x1000
 u.mem_write(inp,struct.pack('<4I',*mt));u.mem_write(inp+0x100,struct.pack('<12I',*rt));u.mem_write(obj,b'\xa5'*44)
 try:expected=recover(manifests,records);code=0 if expected is None else 1
 except ValueError:expected=None;code=-1
 if force_error:code=-1
 for reg,val in [(UC_ARM_REG_R0,inp),(UC_ARM_REG_R1,inp+0x100),(UC_ARM_REG_R2,symbols['wdsv_test_digest']|1),(UC_ARM_REG_R3,obj),(UC_ARM_REG_SP,stack+0x4fff0),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.emu_start(symbols['wdsv004_recover']|1,stop,timeout=10000000,count=5000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop
 actual=struct.unpack('<i',struct.pack('<I',u.reg_read(UC_ARM_REG_R0)))[0];assert actual==code,(label,actual,code)
 if code!=1:assert bytes(u.mem_read(obj,44))==b'\xa5'*44
 else:
  generation,slot=struct.unpack('<2I',u.mem_read(obj,8));assert (generation,slot)==(expected.generation,expected.manifest_slot)
  for i,member in enumerate(expected.members):
   state,n,ptr=struct.unpack('<3I',u.mem_read(obj+8+12*i,12));assert state==member.state
   if state:assert bytes(u.mem_read(ptr,n))==member.payload
   else:assert (n,ptr)==(0,0)
 cases.append(label)

a,b,newa,newb=record(b'A'),record(b'B'),record(b'NEW-A',2),record(b'NEW-B',2)
old=manifest(1,{0:(1,0,1,a),1:(1,0,1,b)});new=manifest(2,{0:(1,1,2,newa),1:(1,1,2,newb)})
base={(0,0):a,(1,0):b};complete={**base,(0,1):newa,(1,1):newb}
check([None,None],{},'both absent')
check([manifest(),None],{},'committed empty')
check([old,None],{**base,(0,1):newa},'orphan remains invisible')
check([old,new],complete,'complete newer generation')
check([old,new],{**complete,(1,1):newb[:-1]},'whole older generation after second member truncation')
check([old,new[:-1]],base,'older after manifest truncation')
check([old,old],base,'identical tie first slot')
check([manifest(1,{0:(1,0,1,a)}),manifest(1,{0:(1,1,2,newa)})],complete,'conflicting equal generation rejected')
check([old,None],{},'no complete snapshot blocks')
check([b'',None],{},'corrupt is not absent')
check([manifest(members={0:(1,0,2,a)}),None],{(0,0):a},'wrong record sequence')
check([manifest(members={0:(1,1,1,a)}),None],{(0,0):a},'wrong record slot')
live,deleted=record(b''),record(b'',deleted=True)
check([manifest(members={0:(1,0,1,live),1:(2,1,1,deleted)}),None],{(0,0):live,(1,1):deleted},'absent empty live tombstone distinct')
for index in [0,8,12,16,20,24,28,32,36]:
 damaged=bytearray(a);damaged[index]^=1
 check([manifest(members={0:(1,0,1,bytes(damaged))}),None],{(0,0):bytes(damaged)},'bad record '+str(index))
mode='digest_failure';check([old,None],base,'digest callback failure',True)
report=dict(scope='Native complete-snapshot selection under ARM; digest uses Python callback, no native SHA/I/O/client/VitaOS',passed=len(cases),cases=cases,elf_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
# b is a synthetic record here; hash the ELF artifact explicitly.
report['elf_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(HERE/'snapshot-reader-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))