"""Run original SHA code under ARM; Python hashlib is an oracle, not a hook."""
import pathlib,sys,subprocess,struct,json,hashlib
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from arm_tools import sdk_bin
sdk=sdk_bin();target=HERE/'sha256-test.elf'
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_sha256,--build-id=none',str(HERE/'sha256.c'),'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
undefined=subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'-u',str(target)],text=True)
assert not undefined.strip(),undefined
symbols={}
for line in subprocess.check_output([str(sdk/'arm-vita-eabi-nm.exe'),'--defined-only',str(target)],text=True).splitlines():
 p=line.split()
 if len(p)==3:symbols[p[2]]=int(p[0],16)
b=target.read_bytes();off=struct.unpack_from('<I',b,28)[0];ent,n=struct.unpack_from('<HH',b,42)
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x10000,0x40000);u.mem_map(0x400000,0x200000)
for i in range(n):
 typ,o,v,_,fs,ms,_,_=struct.unpack_from('<8I',b,off+i*ent)
 if typ==1:u.mem_write(v,b[o:o+fs])
source=0x400001;output=0x500003;stack=0x5ff000;stop=0x5fe000
cases=[]
def check(payload,null=False,declared=None,no_output=False):
 u.mem_write(source,payload or b'\0');u.mem_write(output,b'\xa5'*32)
 size=len(payload) if declared is None else declared
 for reg,val in [(UC_ARM_REG_R0,0 if null else source),(UC_ARM_REG_R1,size),(UC_ARM_REG_R2,0 if no_output else output),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.emu_start(symbols['wdsv004_sha256']|1,stop,timeout=30000000,count=150000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop,'execution did not finish'
 result=u.reg_read(UC_ARM_REG_R0)
 invalid=no_output or (null and size!=0) or size>512036
 assert result==(0xffffffff if invalid else 0)
 digest=bytes(u.mem_read(output,32))
 assert digest==(b'\xa5'*32 if invalid else hashlib.sha256(payload).digest())
 cases.append(dict(size=size,null_input=null,null_output=no_output,result=-1 if invalid else 0,digest=None if invalid else digest.hex()))
check(b'');check(b'',null=True);check(b'abc')
for size in [1,55,56,63,64,65,119,120,127,128,129,163876,512036]:
 check(bytes((i*17+3)%256 for i in range(size)))
check(b'X',null=True);check(b'',no_output=True);check(b'',declared=512037)
report=dict(scope='Original freestanding SHA256 executed under ARM; hashlib comparison only, no digest hook/OS/client/Vita',passed=len(cases),elf_sha256=hashlib.sha256(b).hexdigest(),undefined_symbols=[],cases=cases)
(HERE/'sha256-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))