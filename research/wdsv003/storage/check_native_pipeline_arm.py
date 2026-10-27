"""Native IO and value journal chain with OS calls simulated; no real device filesystem."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';output=HERE/'native-pipeline-test.elf'
stub=HERE/'native-pipeline-stubs.c'
stub.write_text('#include <psp2/io/fcntl.h>\nSceUID sceIoOpen(const char *p,int f,SceMode m){(void)p;(void)f;(void)m;return 0;}\nSceSSize sceIoRead(SceUID f,void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nSceSSize sceIoWrite(SceUID f,const void *p,SceSize n){(void)f;(void)p;(void)n;return 0;}\nint sceIoClose(SceUID f){(void)f;return 0;}\n')
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-DWDSV_NATIVE_IO','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-ipa-icf','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=pipeline_load,--build-id=none',str(HERE/'private_io.c'),str(HERE/'private_paths.c'),str(stub),str(HERE/'value_body.c'),str(HERE/'value_journal.c'),str(HERE/'pipeline_harness.c'),str(ROOT/'standalone/src/save_journal.c'),str(ROOT/'standalone/src/save_record.c'),'-I'+str(ROOT/'standalone/src'),'-o',str(output)]
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
tests=[]
def call(name,args):
 for reg,val in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(reg,val)
 u.reg_write(UC_ARM_REG_SP,stack+0x1fff0);u.reg_write(UC_ARM_REG_LR,stop|1)
 u.emu_start(symbols[name]|1,stop,timeout=10000000,count=5000000);assert u.reg_read(UC_ARM_REG_PC)==stop
 x=u.reg_read(UC_ARM_REG_R0);assert not handles
 return x-(1<<32) if x&0x80000000 else x
def load(label,logical,code,payload=None):
 assert call('pipeline_load',[logical])==code,label
 if code in [1,2]:
  flag,n,p=struct.unpack('<III',u.mem_read(symbols['pipeline_value'],12))
  assert flag==(code==2) and bytes(u.mem_read(p,n))==(payload or b''),label
 tests.append(label)
def commit(label,logical,payload,deleted,code):
 u.mem_write(buf,payload or b'\0')
 assert call('pipeline_commit',[logical,buf,len(payload),deleted])==code,label
 tests.append(label)
for logical in range(3):
 load('initial absent',logical,0)
 commit('independent live',logical,bytes([65+logical])*100,0,0)
for logical in range(3):load('independent recover',logical,1,bytes([65+logical])*100)
commit('confirmed deletion',1,b'',1,0);load('deletion restart',1,2)
load('other namespace preserved',0,1,b'A'*100)
load('other namespace preserved',2,1,b'C'*100)
mode='write_error';commit('partial recreate fails',1,b'RECREATE',0,-1)
before=len(opens);commit('uncertain state cannot write',1,b'NEXT',0,-1);assert len(opens)==before
mode='normal';load('partial recreate keeps tombstone',1,2)
mode='open_error';commit('denied open not acknowledged',2,b'NEW',0,-1)
mode='normal';load('old data after open failure',2,1,b'C'*100)
mode='close_error';commit('close uncertainty not acknowledged',2,b'UNACK',0,-1)
mode='normal';load('complete unacknowledged data can recover',2,1,b'UNACK')
mode='write_error';commit('partial deletion fails',0,b'',1,-1)
mode='normal';load('partial deletion preserves old',0,1,b'A'*100)
before=len(opens);load('bad namespace load',3,-2);commit('bad namespace commit',3,b'X',0,-1);assert len(opens)==before
assert all(p in paths for p,access in opens)
report={'scope':'Entire own C value/journal/fixed-path native IO chain under ARM emulation; files and failures simulated in Python RAM, no VitaOS','passed':len(tests),'tests':tests,'opened_paths':sorted({p for p,a in opens}),'elf_sha256':hashlib.sha256(elf).hexdigest()}
(HERE/'native-pipeline-arm-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(tests),'scope':report['scope']}))