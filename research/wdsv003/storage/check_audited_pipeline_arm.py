"""Vita file adapter with stdio calls simulated; no real device filesystem."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';output=HERE/'audited-pipeline-test.elf'
stub=HERE/'audited-pipeline-stdio-stubs.c'
stub.write_text('#include <stdio.h>\nFILE *fopen(const char *a,const char *b){(void)a;(void)b;return 0;}\nsize_t fread(void *a,size_t b,size_t c,FILE *d){(void)a;(void)b;(void)c;(void)d;return 0;}\nsize_t fwrite(const void *a,size_t b,size_t c,FILE *d){(void)a;(void)b;(void)c;(void)d;return 0;}\nint ferror(FILE *a){(void)a;return 0;}\nint fflush(FILE *a){(void)a;return 0;}\nint fclose(FILE *a){(void)a;return 0;}\nint *__errno(void){return 0;}\n')
command=[str(sdk/'arm-vita-eabi-gcc.exe'),'-DWDSV_AUDIT_LOG','-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-ipa-icf','-fno-stack-protector','-nostdlib','-Wl,-Ttext=0x10000,--entry=pipeline_load,--build-id=none',str(HERE/'private_files.c'),str(HERE/'private_paths.c'),str(stub),str(HERE/'audited_store.c'),str(HERE/'value_body.c'),str(HERE/'value_journal.c'),str(HERE/'pipeline_harness.c'),str(ROOT/'standalone/src/save_journal.c'),str(ROOT/'standalone/src/save_record.c'),'-I'+str(ROOT/'standalone/src'),'-o',str(output)]
stub.write_text(stub.read_text().replace('#include <stdio.h>','#include <stdio.h>\n#undef ferror'))
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
reverse={symbols[n]&~1:n for n in ['fopen','fread','fwrite','ferror','fflush','fclose','__errno']}
assert len(reverse)==7
def hook(cpu,address,size,user):
    global closed
    name=reverse[address];a,b,c,d=[cpu.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]];result=0
    if name=='__errno':result=errp
    elif name=='fopen':
        path,access=text_at(a),text_at(b);assert path in paths and access in ['rb','wb'];opens.append((path,access))
        error=13 if mode=='open_error' else 2 if access=='rb' and path not in files else 0
        u.mem_write(errp,struct.pack('<I',error))
        if not error:
            if access=='wb':files[path]=b''
            result=0x9000+len(opens)*4;handles[result]={'path':path,'pos':0,'error':False}
    elif name in ['fread','fwrite']:
        h=handles[d];path=h['path'];assert b==1;n=min(c,2)
        if mode in ['read_error','write_error'] and h['pos']>=2:
            h['error']=True;result=0
        elif name=='fread':
            chunk=files[path][h['pos']:h['pos']+n];result=len(chunk)
            if result:u.mem_write(a,chunk)
        else:
            chunk=bytes(u.mem_read(a,n));files[path]+=chunk;result=n
        h['pos']+=result
    elif name=='ferror':result=int(handles[a]['error'])
    elif name=='fflush':result=-1 if mode=='flush_error' else 0
    elif name=='fclose':closed+=1;handles.pop(a);result=-1 if mode=='close_error' else 0
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
mode='flush_error';commit('flush uncertainty not acknowledged',2,b'UNACK',0,-1)
mode='normal';load('complete unacknowledged data can recover',2,1,b'UNACK')
mode='write_error';commit('partial deletion fails',0,b'',1,-1)
mode='normal';load('partial deletion preserves old',0,1,b'A'*100)
before=len(opens);load('bad namespace load',3,-2);commit('bad namespace commit',3,b'X',0,-1);assert len(opens)==before
assert all(p in paths for p,access in opens)

count=call('pipeline_audit_count',[0]);assert count>0 and count%2==0
for i in range(0,count,2):
 a=call('pipeline_audit_event',[0,i]);b=call('pipeline_audit_event',[0,i+1])
 start=struct.unpack('<IIIiII',u.mem_read(a,24));end=struct.unpack('<IIIiII',u.mem_read(b,24))
 assert start[0]==end[0]==0 and start[2]==1 and end[2]==2
 assert start[1]==end[1] and start[4:]==end[4:]
 assert start[5]==i//2+1
tests.append('paired metadata-only audit records follow real C commits')
before_files=dict(files);before_opens=len(opens)
assert call('pipeline_audit_limit',[0,count])==0
commit('full log rejects save before fopen',0,b'NEW',0,-3)
commit('full log rejects delete before fopen',0,b'',1,-3)
assert files==before_files and len(opens)==before_opens
assert call('pipeline_audit_limit',[0,count+1])==0
commit('single log slot is insufficient',0,b'NEW',0,-3)
assert files==before_files and len(opens)==before_opens
assert call('pipeline_audit_limit',[0,count+2])==0
commit('two reserved slots permit verified save',0,b'AUDITED',0,0)
load('audited saved value recovers',0,1,b'AUDITED')
assert call('pipeline_audit_count',[0])==count+2

report={'scope':'Entire own C audit/value/journal/fixed-path stdio chain under ARM emulation; files and failures simulated in Python RAM, no VitaOS','passed':len(tests),'tests':tests,'opened_paths':sorted({p for p,a in opens}),'elf_sha256':hashlib.sha256(elf).hexdigest()}
(HERE/'audited-pipeline-arm-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(tests),'scope':report['scope']}))
