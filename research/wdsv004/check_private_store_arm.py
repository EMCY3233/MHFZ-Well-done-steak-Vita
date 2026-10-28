"""Native IO adapter with OS calls simulated; no real device filesystem."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';output=HERE/'private-store-test.elf'
stub=HERE/'private-store-test-stubs.c'
stub.write_text('#include <psp2/io/fcntl.h>\nSceUID sceIoOpen(const char *p,int f,SceMode m){(void)p;(void)f;(void)m;return 0;}\nSceSSize sceIoRead(SceUID f,void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nSceSSize sceIoWrite(SceUID f,const void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nint sceIoClose(SceUID f){(void)f;return 0;}\n')
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-ipa-icf','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_private_read,--build-id=none',str(HERE/'private_store.c'),str(stub),'-o',str(output)]
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
files={};handles={};mode='normal';opens=[];closed=0
def text_at(a):return bytes(u.mem_read(a,128)).split(b'\0')[0].decode()
reverse={symbols[n]&~1:n for n in ['sceIoOpen','sceIoRead','sceIoWrite','sceIoClose']}
assert len(reverse)==4

def hook(cpu,address,size,user):
    global closed
    name=reverse[address];a,b,c=[cpu.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]];result=0
    if name=='sceIoOpen':
        path=text_at(a);assert path in paths and b in [1,0x602];opens.append((path,b))
        if mode=='open_error':result=0x8001000d
        elif b==1 and path not in files:result=0x80010002
        else:
            if b==0x602:files[path]=b''
            result=0x9000+len(opens)*4;handles[result]={'path':path,'pos':0}
    elif name in ['sceIoRead','sceIoWrite']:
        h=handles[a];path=h['path'];n=min(c,4096)
        if mode in ['read_error','write_error'] and h['pos']>=4096:result=-5
        elif mode=='oversize':result=c+1
        elif mode=='zero_write' and name=='sceIoWrite':result=0
        elif name=='sceIoRead':
            chunk=files[path][h['pos']:h['pos']+n];result=len(chunk)
            if result:u.mem_write(b,chunk)
        else:
            files[path]+=bytes(u.mem_read(b,n));result=n
        if result>0:h['pos']+=result
    elif name=='sceIoClose':closed+=1;handles.pop(a);result=-1 if mode=='close_error' else 0
    cpu.reg_write(UC_ARM_REG_R0,result&0xffffffff);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
for address in reverse:u.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)

tests=[]
def call(name,args,expected,label):
 before=len(opens)
 for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args+[0]*(4-len(args))):u.reg_write(reg,val)
 u.reg_write(UC_ARM_REG_SP,stack+0x1fff0);u.reg_write(UC_ARM_REG_LR,stop|1)
 u.emu_start(symbols[name]|1,stop,timeout=10000000,count=10000000);assert u.reg_read(UC_ARM_REG_PC)==stop
 result=u.reg_read(UC_ARM_REG_R0);result=result-(1<<32) if result&0x80000000 else result
 assert result==expected,(label,result);assert not handles,label
 tests.append(dict(label=label,opens=len(opens)-before))
def read(expected=0,label='read'):
 u.mem_write(meta,b'\xa5'*64)
 call('wdsv004_private_read',[pool,meta,meta+16],expected,label)
 if expected:assert bytes(u.mem_read(meta,64))==b'\xa5'*64
u.mem_write(pool,bytes(4));read(-1,'unverified parent blocks');assert not opens
u.mem_write(pool,struct.pack('<I',1));read(label='all missing distinct from error')
assert bytes(u.mem_read(meta,64))==bytes(64)
files[paths[0]]=b'';read(label='empty existing manifest is present');p,n=struct.unpack('<2I',u.mem_read(meta,8));assert p and not n
for i,path in enumerate(paths):files[path]=bytes([i])* (188 if i<2 else 36)
read(label='eight fixed slots')
for i in range(8):
 p,n=struct.unpack('<2I',u.mem_read(meta+i*8,8));assert n==(188 if i<2 else 36) and bytes(u.mem_read(p,n))==files[paths[i]]
u.mem_write(buf,b'Z'*163877)
def descriptor(n,ptr=buf):u.mem_write(meta+0x100,struct.pack('<2I',ptr,n))
for logical in range(3):
 for slot in range(2):
  descriptor(36);call('wdsv004_private_record',[pool,logical,slot,meta+0x100],0,'record namespace write')
for slot in range(2):
 descriptor(188);call('wdsv004_private_manifest',[pool,slot,meta+0x100],0,'manifest namespace write')
files[paths[0]]=b'X'*189;read(-1,'manifest overlong');files[paths[0]]=b'X'*188
files[paths[2]]=b'X'*163877;read(-1,'record overlong');files[paths[2]]=b'X'*163876
read(label='record capacity exact EOF')
for n in [0,35,163877]:
 descriptor(n);call('wdsv004_private_record',[pool,0,0,meta+0x100],-1,'record size rejected');assert tests[-1]['opens']==0
for n in [187,189]:
 descriptor(n);call('wdsv004_private_manifest',[pool,0,meta+0x100],-1,'manifest exact size required');assert tests[-1]['opens']==0
descriptor(36,pool+380);call('wdsv004_private_record',[pool,0,0,meta+0x100],-1,'pool alias rejected');assert tests[-1]['opens']==0
for logical,slot in [(3,0),(0,2)]:
 descriptor(36);call('wdsv004_private_record',[pool,logical,slot,meta+0x100],-1,'invalid identity rejected');assert tests[-1]['opens']==0
for mode in ['open_error','read_error','oversize','close_error']:read(-1,mode)
for mode in ['write_error','zero_write','oversize','close_error']:
 descriptor(8192);call('wdsv004_private_record',[pool,0,0,meta+0x100],-1,mode)
mode='normal'
report=dict(scope='Native eight-slot Vita I/O adapter under ARM; OS calls mocked, no physical filesystem/client',passed=len(tests),cases=tests,pool_bytes=983636,elf_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
(HERE/'private-store-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(tests),scope=report['scope'])))