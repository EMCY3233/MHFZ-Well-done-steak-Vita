"""Cross-compiled own code under ARM emulation; no VitaOS or physical I/O."""
import pathlib,sys,subprocess,struct,json,hashlib,collections
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from arm_tools import sdk_bin
sdk=sdk_bin();target=HERE/'record-ref-test.elf'
(HERE/'record-ref-test-stub.c').write_text('#include <stdint.h>\nint wdsv_test_digest(const uint8_t *p,uint32_t n,uint8_t *o){(void)p;(void)n;(void)o;return -1;}\n')
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_resolve_record,--build-id=none',str(HERE/'record_ref.c'),str(HERE/'record-ref-test-stub.c'),'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
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
from test_snapshot import record
mode='normal';digest_calls=0
refp=inp+0x1000;payload=out

def digest_hook(cpu,address,size,user):
 global digest_calls
 a,n,d=[cpu.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]]
 digest_calls+=1
 if mode!='digest_failure':cpu.mem_write(d,hashlib.sha256(bytes(cpu.mem_read(a,n))).digest())
 cpu.reg_write(UC_ARM_REG_R0,0xffffffff if mode=='digest_failure' else 0)
 cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,digest_hook,begin=symbols['wdsv_test_digest'],end=symbols['wdsv_test_digest'])

def check(raw,state=1,sequence=1,expected=0,digest=None,ref_fields=None,label='case'):
 fields=[0,state,0,sequence,len(raw)]
 for index,value in (ref_fields or {}).items():fields[index]=value
 u.mem_write(refp,struct.pack('<5I',*fields)+(digest or hashlib.sha256(raw).digest()))
 u.mem_write(payload,raw or b'\0');u.mem_write(obj,b'\xa5'*12)
 for reg,val in [(UC_ARM_REG_R0,refp),(UC_ARM_REG_R1,payload),(UC_ARM_REG_R2,len(raw)),(UC_ARM_REG_R3,symbols['wdsv_test_digest']|1),(UC_ARM_REG_SP,stack+0x4ffe8),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.mem_write(stack+0x4ffe8,struct.pack('<I',obj))
 
 try:u.emu_start(symbols['wdsv004_resolve_record']|1,stop,timeout=10000000,count=5000000)
 except Exception:
  print('emulation fault',hex(u.reg_read(UC_ARM_REG_PC)),hex(u.reg_read(UC_ARM_REG_LR)),hex(u.reg_read(UC_ARM_REG_SP)),symbols);raise
 assert u.reg_read(UC_ARM_REG_PC)==stop
 result=struct.unpack('<i',struct.pack('<I',u.reg_read(UC_ARM_REG_R0)))[0]
 assert result==expected,(label,result)
 if result:assert bytes(u.mem_read(obj,12))==b'\xa5'*12
 else:
  actual_state,n,ptr=struct.unpack('<3I',u.mem_read(obj,12))
  assert actual_state==state and n==len(raw)-36 and ptr==payload+36
 cases.append(label)

cases=[]
check(record(b''),label='empty live')
check(record(b'',deleted=True),state=2,label='tombstone')
check(record(b'own synthetic bytes'),label='live payload')
raw=record(b'A')
for size in range(36):check(raw[:size],expected=-1,label='truncated '+str(size))
check(raw,sequence=2,expected=-1,label='wrong sequence')
check(raw,digest=bytes(32),expected=-1,label='wrong digest')
for field,value in [(0,3),(1,0),(1,3),(2,2),(3,0),(4,38)]:check(raw,ref_fields={field:value},expected=-1,label='invalid reference '+str(field))
check(raw,state=2,expected=-1,label='live cannot become deleted')
for offset in [0,8,12,16,20,24,28,32,36]:
 damaged=bytearray(raw);damaged[offset]^=1;check(bytes(damaged),expected=-1,label='corruption '+str(offset))
import zlib
for offset in [24,28,32]:
 damaged=bytearray(raw);damaged[offset]^=1
 struct.pack_into('<I',damaged,16,zlib.crc32(damaged[24:]));struct.pack_into('<I',damaged,20,zlib.crc32(damaged[:20]))
 check(bytes(damaged),expected=-1,label='bad envelope valid CRC '+str(offset))
mode='digest_failure';check(raw,expected=-1,label='digest callback failure')
report=dict(scope='Own ARM record reference verifier; SHA256 callback executed by Python mock, no native SHA/VitaOS/client',passed=len(cases),digest_calls=digest_calls,elf_sha256=hashlib.sha256(b).hexdigest(),cases=cases)
(HERE/'record-ref-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))