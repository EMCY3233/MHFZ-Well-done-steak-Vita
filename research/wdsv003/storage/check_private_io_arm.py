"""Native IO adapter with OS calls simulated; no real device filesystem."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';output=HERE/'private-io-test.elf'
stub=HERE/'private-io-test-stubs.c'
stub.write_text('#include <psp2/io/fcntl.h>\nSceUID sceIoOpen(const char *p,int f,SceMode m){(void)p;(void)f;(void)m;return 0;}\nSceSSize sceIoRead(SceUID f,void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nSceSSize sceIoWrite(SceUID f,const void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nint sceIoClose(SceUID f){(void)f;return 0;}\n')
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-ipa-icf','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv_io_read_slot,--build-id=none',str(HERE/'private_io.c'),str(HERE/'private_paths.c'),str(stub),'-o',str(output)]
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
buf,errp,stack,stop=0x400000,0x500000,0x600000,0x700000
for a in [buf,errp,stack,stop]:u.mem_map(a,0x20000)
paths=['ux0:data/MHFZL0001/wdsv003/'+name+'-'+slot+'.bin' for name in ['ini','pri','character'] for slot in ['a','b']];files={};handles={};mode='normal';opens=[];closed=0
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
        h=handles[a];path=h['path'];n=min(c,2)
        if mode in ['read_error','write_error'] and h['pos']>=2:result=-5
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
tests=[];logical=0;context=errp+256
def call(name,slot,n,expected,label,null=False):
    before=len(opens);u.mem_write(context,struct.pack('<I',logical))
    for reg,val in [(UC_ARM_REG_R0,0 if null else context),(UC_ARM_REG_R1,slot),(UC_ARM_REG_R2,buf),(UC_ARM_REG_R3,n),(UC_ARM_REG_SP,stack+0x1fff0),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
    u.emu_start(symbols[name]|1,stop,timeout=2000000,count=1000000);assert u.reg_read(UC_ARM_REG_PC)==stop
    code=u.reg_read(UC_ARM_REG_R0);code=code-(1<<32) if code&0x80000000 else code
    assert code==expected,(label,code);assert not handles,label
    tests.append({'name':label,'opens':len(opens)-before})
call('wdsv_io_read_slot',0,64,-1,'missing')
for logical in range(3):
 for slot in range(2):
    payload=bytes([logical*2+slot])*36;u.mem_write(buf,payload)
    call('wdsv_io_write_slot',slot,36,0,'fixed namespace write')
    call('wdsv_io_read_slot',slot,64,36,'fixed namespace read')
    assert bytes(u.mem_read(buf,36))==payload
assert len(files)==6
logical=0
call('wdsv_io_read_slot',0,36,36,'exact EOF')
call('wdsv_io_read_slot',0,35,-2,'overlong file rejected')
for logical in [3,0xffffffff]:
 call('wdsv_io_write_slot',0,36,-1,'invalid namespace');assert tests[-1]['opens']==0
 call('wdsv_io_read_slot',0,64,-2,'invalid namespace read');assert tests[-1]['opens']==0
logical=0
for slot in [2,0xffffffff]:
 call('wdsv_io_write_slot',slot,36,-1,'invalid slot');assert tests[-1]['opens']==0
call('wdsv_io_write_slot',0,36,-1,'null context',True);assert tests[-1]['opens']==0
call('wdsv_io_read_slot',0,64,-2,'null context read',True);assert tests[-1]['opens']==0
for n in [0,35,163877]:
 call('wdsv_io_write_slot',0,n,-1,'invalid record size');assert tests[-1]['opens']==0
mode='read_error';call('wdsv_io_read_slot',0,64,-2,'read failure closes')
for mode in ['write_error','zero_write','oversize','close_error']:
 u.mem_write(buf,b'X'*36);call('wdsv_io_write_slot',1,36,-1,mode)
mode='close_error';call('wdsv_io_read_slot',0,64,-2,'read close error')
mode='oversize';call('wdsv_io_read_slot',0,64,-2,'read over-report rejected')
mode='open_error';call('wdsv_io_read_slot',0,64,-2,'open denied')
report={'scope':'Own fixed-path C adapter; mocked sceIo APIs only, no disk or VitaOS','passed':len(tests),'tests':tests,'allowed_paths':paths,'elf_sha256':hashlib.sha256(elf).hexdigest()}
(HERE/'private-io-arm-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(tests),'scope':report['scope']}))