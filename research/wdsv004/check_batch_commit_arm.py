"""Native plan vs Python reference; synthetic records, no I/O or VitaOS."""
import pathlib,sys,subprocess,struct,json,hashlib
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sys.path.insert(0,str(HERE))
from test_snapshot import record,manifest
from batch_plan import prepare
from snapshot import recover
from arm_tools import sdk_bin
sdk=sdk_bin();target=HERE/'batch-commit-test.elf'
(HERE/'batch-store-stub.c').write_text('#include '+chr(34)+'batch_commit.h'+chr(34)+'\nint test_read(void*c,wdsv004_buffer*m,wdsv004_buffer r[3][2]){(void)c;(void)m;(void)r;return -1;}\nint test_record(void*c,uint32_t a,uint32_t b,const wdsv004_buffer*d){(void)c;(void)a;(void)b;(void)d;return -1;}\nint test_manifest(void*c,uint32_t a,const wdsv004_buffer*d){(void)c;(void)a;(void)d;return -1;}\n')
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_commit,--build-id=none',*[str(HERE/(name+'.c')) for name in ['batch_commit','batch_plan','snapshot_reader','manifest_reader','record_ref','sha256','batch-store-stub']],'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
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
state={}
def hook(cpu,address,size,user):
 args=[cpu.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
 result=0
 if address==symbols['test_read']:
  state['reads']+=1;phase=state['reads'];fault=state['fault']
  if fault=='read'+str(phase):result=-1
  else:
   if phase==2 and fault=='baseline':state['m'][1]=bytes(188)
   if phase==2 and fault=='unchanged':state['r'][1,0]=state['r'][1,0][:-1]
   cursor=base+0x10000
   def alloc(raw):
    nonlocal cursor
    if raw is None:return [0,0]
    p=cursor;cpu.mem_write(p,raw or b'\0');cursor+=len(raw)+32;cursor=(cursor+15)&~15
    return [p,len(raw)]
   mt=sum([alloc(x) for x in state['m']],[])
   rt=sum([alloc(state['r'].get((i,j))) for i in range(3) for j in range(2)],[])
   cpu.mem_write(args[1],struct.pack('<4I',*mt));cpu.mem_write(args[2],struct.pack('<12I',*rt))
 elif address==symbols['test_record']:
  ptr,n=struct.unpack('<2I',cpu.mem_read(args[3],8));raw=bytes(cpu.mem_read(ptr,n));state['events'].append('record')
  state['r'][args[1],args[2]]=raw[:-1] if state['fault']=='record-readback' else raw
  if state['fault']=='record-ack':result=-1
 else:
  ptr,n=struct.unpack('<2I',cpu.mem_read(args[2],8));raw=bytes(cpu.mem_read(ptr,n));state['events'].append('manifest')
  state['m'][args[1]]=raw[:-1] if state['fault']=='manifest-readback' else raw
  if state['fault']=='manifest-ack':result=-1
 cpu.reg_write(UC_ARM_REG_R0,result&0xffffffff);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
for name in ('test_read','test_record','test_manifest'):
 u.hook_add(UC_HOOK_CODE,hook,begin=symbols[name],end=symbols[name])
def invoke():
 for reg,val in [(UC_ARM_REG_R0,base),(UC_ARM_REG_R1,base+0x100),(UC_ARM_REG_R2,base+0x200),(UC_ARM_REG_R3,out),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.emu_start(symbols['wdsv004_commit']|1,stop,timeout=30000000,count=150000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop
 return u.reg_read(UC_ARM_REG_R0)
for fault in [None,'read1','read2','read3','record-ack','record-readback','baseline','unchanged','manifest-ack','manifest-readback']:
 a,bv=record(b'A'),record(b'B');state=dict(m=[manifest(members={0:(1,0,1,a),1:(1,0,1,bv)}),None],r={(0,0):a,(1,0):bv},events=[],reads=0,fault=fault)
 u.mem_write(base,bytes(4));u.mem_write(base+0x100,struct.pack('<4I',0,*[symbols[x]|1 for x in ('test_read','test_record','test_manifest')]))
 change=record(b'new',2);u.mem_write(base+0x1000,change);u.mem_write(base+0x200,struct.pack('<6I',base+0x1000,len(change),0,0,0,0));u.mem_write(out,b'\xa5'*44)
 result=invoke();blocked=struct.unpack('<I',u.mem_read(base,4))[0]
 assert result==(0 if fault is None else 0xffffffff),(fault,result)
 assert blocked==(0 if fault is None else 1)
 if fault:
  assert bytes(u.mem_read(out,44))==b'\xa5'*44
  events=list(state['events']);reads=state['reads'];assert invoke()==0xffffffff
  assert state['events']==events and state['reads']==reads
  if fault in ('read1','read2','record-ack','record-readback','baseline','unchanged'):assert 'manifest' not in events
  if fault=='manifest-ack':assert recover(state['m'],state['r']).generation==2
 else:
  generation,slot=struct.unpack('<2I',u.mem_read(out,8));assert (generation,slot)==(2,1)
  st,n,p=struct.unpack('<3I',u.mem_read(out+8,12));assert st==1 and bytes(u.mem_read(p,n))==b'new'
  assert state['events']==['record','manifest']
 cases.append(dict(fault=fault,result=-1 if fault else 0,events=state['events']))
report=dict(scope='Native coordinator/planner/recovery/SHA under ARM; only store callbacks mocked; no OS/client/Vita',passed=len(cases),cases=cases,elf_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),undefined_symbols=[])
(HERE/'batch-commit-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))