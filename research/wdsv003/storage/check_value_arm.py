"""Cross-compiled own code under ARM emulation; no VitaOS or physical I/O."""
import pathlib,sys,subprocess,struct,json,hashlib
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';target=HERE/'value-test.elf'
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv_pack_value,--build-id=none',str(HERE/'value_body.c'),'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
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
def call(name,a,c,d):
 for reg,val in [(UC_ARM_REG_R0,a),(UC_ARM_REG_R1,c),(UC_ARM_REG_R2,d),(UC_ARM_REG_SP,stack+0x4fff0),(UC_ARM_REG_LR,stop|1)]:u.reg_write(reg,val)
 u.emu_start(symbols[name]|1,stop,timeout=10000000,count=5000000)
 assert u.reg_read(UC_ARM_REG_PC)==stop
 return struct.unpack('<i',struct.pack('<I',u.reg_read(UC_ARM_REG_R0)))[0]
cases=[]
for deleted,data in [(0,b''),(1,b''),(0,b'synthetic'),(0,bytes(0x28000))]:
 u.mem_write(inp,data or b'\0');u.mem_write(obj,struct.pack('<III',deleted,len(data),inp))
 size=12+len(data);assert call('wdsv_pack_value',out,size,obj)==size
 expected=b'MZV1'+struct.pack('<II',deleted,len(data))+data
 assert bytes(u.mem_read(out,size))==expected
 assert call('wdsv_read_value',out,size,obj)==0
 assert struct.unpack('<III',u.mem_read(obj,12))==(deleted,len(data),out+12)
 cases.append('roundtrip '+str((deleted,len(data))))
raw=b'MZV1'+struct.pack('<II',0,4)+b'data'
bad=[raw[:i] for i in range(len(raw))]+[raw+b'X',b'BAD!'+raw[4:],b'MZV1'+struct.pack('<II',2,0),b'MZV1'+struct.pack('<II',1,4)+b'data']
for data in bad:
 u.mem_write(inp,data or b'\0');u.mem_write(obj,b'\xa5'*12)
 assert call('wdsv_read_value',inp,len(data),obj)==-1
 assert bytes(u.mem_read(obj,12))==b'\xa5'*12
 cases.append('rejected malformed '+str(len(cases)))
for deleted,length,capacity,code in [(1,1,100,-1),(2,0,100,-1),(0,0x28001,0x30000,-1),(0,4,15,-2),(0,0,11,-2)]:
 u.mem_write(obj,struct.pack('<III',deleted,length,inp));u.mem_write(out,b'\xa5'*32)
 assert call('wdsv_pack_value',out,capacity,obj)==code
 assert bytes(u.mem_read(out,32))==b'\xa5'*32
 cases.append('rejected pack '+str(len(cases)))
report=dict(scope=__doc__,passed=len(cases),elf_sha256=hashlib.sha256(b).hexdigest(),cases=cases)
(HERE/'value-arm-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(cases),scope=__doc__)))
