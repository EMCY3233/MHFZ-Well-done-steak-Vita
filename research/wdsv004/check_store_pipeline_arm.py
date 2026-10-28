"""Native IO adapter with OS calls simulated; no real device filesystem."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from arm_tools import sdk_bin
sdk=sdk_bin();output=HERE/'store-pipeline-test.elf'
stub=HERE/'store-pipeline-test-stubs.c'
stub.write_text('#include <psp2/io/fcntl.h>\nSceUID sceIoOpen(const char *p,int f,SceMode m){(void)p;(void)f;(void)m;return 0;}\nSceSSize sceIoRead(SceUID f,void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nSceSSize sceIoWrite(SceUID f,const void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nint sceIoClose(SceUID f){(void)f;return 0;}\n')
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-ipa-icf','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_commit,--build-id=none',*[str(HERE/(name+'.c')) for name in ['private_store','batch_commit','batch_plan','snapshot_reader','manifest_reader','record_ref','sha256']],str(stub),'-o',str(output)]
subprocess.run(command,check=True,creationflags=subprocess.CREATE_NO_WINDOW);symbols={}
for l in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'--defined-only',str(output)],text=True).splitlines():
    p=l.split()
    if len(p)==3:symbols[p[2]]=int(p[0],16)
elf=output.read_bytes();po=struct.unpack_from('<I',elf,28)[0];ps,pn=struct.unpack_from('<HH',elf,42);segments=[]
for i in range(pn):
    t,o,v,_,fs,ms,_,_=struct.unpack_from('<8I',elf,po+i*ps)
    if t==1:segments.append((o,v,fs,ms))
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);lo=min(s[1] for s in segments)&~4095;hi=(max(s[1]+s[3] for s in segments)+4095)&~4095;u.mem_map(lo,hi-lo)
for o,v,fs,ms in segments:u.mem_write(v,elf[o:o+fs])

pool,buf,meta,stack,stop=0x400000,0x600000,0x700000,0x800000,0x900000
u.mem_map(pool,0x100000);u.mem_map(buf,0x40000);u.mem_map(meta,0x10000);u.mem_map(stack,0x20000);u.mem_map(stop,0x1000)
paths=['ux0:data/MHFZL0001/wdsv004/manifest-'+s+'.bin' for s in ['a','b']]+['ux0:data/MHFZL0001/wdsv004/'+n+'-'+s+'.bin' for n in ['ini','pri','character'] for s in ['a','b']]

sys.path.insert(0,str(HERE))
from test_snapshot import record,manifest
from snapshot import recover
reverse={symbols[n]&~1:n for n in ['sceIoOpen','sceIoRead','sceIoWrite','sceIoClose']}
state={}
def string_at(p):return bytes(u.mem_read(p,128)).split(b'\0')[0].decode()
def hook(cpu,address,size,user):
 name=reverse[address];a,b,c=[cpu.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]];result=0
 files,handles=state['files'],state['handles'];fault=state['fault']
 if name=='sceIoOpen':
  path=string_at(a);assert path in paths and b in [1,0x602];state['opens'].append((path,b))
  if b==0x602 and path==paths[5] and fault=='second-open':result=-5
  elif b==1 and state['published'] and fault=='final-read':result=-5
  elif b==1 and path not in files:result=0x80010002
  else:
   if b==0x602:files[path]=b''
   result=0x9000+4*len(state['opens']);handles[result]=dict(path=path,pos=0,writing=b==0x602)
 elif name in ('sceIoRead','sceIoWrite'):
  h=handles[a];path=h['path'];n=min(c,4)
  if name=='sceIoRead':
   chunk=files[path][h['pos']:h['pos']+min(c,4096)];result=len(chunk)
   if result:cpu.mem_write(b,chunk)
  elif h['pos']>=4 and ((path==paths[5] and fault=='second-partial') or (path==paths[1] and fault=='manifest-partial')):result=-5
  else:
   files[path]+=bytes(cpu.mem_read(b,n));result=n
  if result>0:h['pos']+=result
 else:
  h=handles.pop(a)
  if h['writing']:
   state['writes'].append(h['path'])
   if h['path']==paths[3] and fault=='record-readback':files[h['path']]=files[h['path']][:-1]
   if h['path']==paths[1]:
    state['published']=True
    if fault=='manifest-close':result=-5
 cpu.reg_write(UC_ARM_REG_R0,result&0xffffffff);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
for address in reverse:u.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
def invoke():
 for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[meta,meta+0x100,meta+0x200,meta+0x300]):u.reg_write(reg,val)
 u.reg_write(UC_ARM_REG_SP,stack+0x1fff0);u.reg_write(UC_ARM_REG_LR,stop|1)
 u.emu_start(symbols['wdsv004_commit']|1,stop,timeout=30000000,count=150000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop
 return u.reg_read(UC_ARM_REG_R0)
cases=[]
for fault in [None,'second-open','second-partial','record-readback','manifest-partial','manifest-close','final-read','unverified-parent','no-baseline']:
 a,b=record(b'oldA'),record(b'oldB')
 state=dict(files={paths[0]:manifest(members={0:(1,0,1,a),1:(1,0,1,b)}),paths[2]:a,paths[4]:b},handles={},opens=[],writes=[],published=False,fault=fault)
 if fault=='no-baseline':state['files']={}
 u.mem_write(pool,struct.pack('<I',0 if fault=='unverified-parent' else 1));u.mem_write(meta,bytes(4));u.mem_write(meta+0x300,b'\xa5'*44)
 u.mem_write(meta+0x100,struct.pack('<4I',pool,*[symbols[x]|1 for x in ['wdsv004_private_read','wdsv004_private_record','wdsv004_private_manifest']]))
 newa,newb=record(b'newA',2),record(b'newB',2);u.mem_write(buf,newa);u.mem_write(buf+0x1000,newb)
 u.mem_write(meta+0x200,struct.pack('<6I',buf,len(newa),buf+0x1000,len(newb),0,0))
 result=invoke();assert not state['handles']
 assert result==(0 if fault is None else 0xffffffff),(fault,result)
 if fault:
  assert bytes(u.mem_read(meta+0x300,44))==b'\xa5'*44
  before=list(state['opens']);assert invoke()==0xffffffff;assert state['opens']==before
 else:
  assert struct.unpack('<2I',u.mem_read(meta+0x300,8))==(2,1)
  for i,payload in enumerate([b'newA',b'newB']):
   s,n,p=struct.unpack('<3I',u.mem_read(meta+0x308+12*i,12));assert s==1 and bytes(u.mem_read(p,n))==payload
 ms=[state['files'].get(paths[i]) for i in range(2)]
 rs={(i,j):state['files'][paths[2+2*i+j]] for i in range(3) for j in range(2) if paths[2+2*i+j] in state['files']}
 snap=recover(ms,rs);generation=None if snap is None else snap.generation
 expected=None if fault=='no-baseline' else (2 if fault in (None,'manifest-close','final-read') else 1)
 assert generation==expected,(fault,generation)
 if fault in ('second-open','second-partial','record-readback','unverified-parent','no-baseline'):assert paths[1] not in state['writes']
 cases.append(dict(fault=fault,result=-1 if fault else 0,recovered_generation=generation,write_paths=state['writes']))
report=dict(scope='Combined native coordinator/private-store/planner/readers/SHA under ARM; only OS calls mocked; no client/Vita/durability proof',passed=len(cases),cases=cases,elf_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
(HERE/'store-pipeline-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))