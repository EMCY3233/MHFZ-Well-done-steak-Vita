"""Cross-compiled own code under ARM emulation; no VitaOS or physical I/O."""
import pathlib,sys,subprocess,struct,json,hashlib,collections
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis-tools/test-python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';target=HERE/'manifest-reader-test.elf'
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),'-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-Ttext=0x10000,--entry=wdsv004_read_manifest,--build-id=none',str(HERE/'manifest_reader.c'),'-o',str(target)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
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

sys.path.insert(0,str(HERE))
from test_snapshot import manifest,record
from batch_manifest import read_manifest
cases=[]
valid=[manifest(members={0:(1,0,1,record(b'X'*512000))}),manifest(),manifest(0xffffffff),manifest(members={0:(1,0,1,record(b'')),1:(2,1,2,record(b'',2,True))})]
for raw in valid:
 u.mem_write(inp,raw);u.mem_write(obj,b'\xa5'*160)
 assert call('wdsv004_read_manifest',inp,len(raw),obj)==0
 expected=read_manifest(raw)
 values=struct.unpack('<40I',u.mem_read(obj,160))
 assert values[0]==expected['generation']
 for i,entry in enumerate(expected['entries']):
  actual=bytes(u.mem_read(obj+4+i*52,52))
  assert struct.unpack('<5I',actual[:20])==tuple(entry[k] for k in ['logical','state','slot','sequence','record_bytes'])
  assert actual[20:].hex()==entry['sha256']
 cases.append('valid manifest parity')
raw=manifest()
bad=[raw[:i] for i in range(188)]+[raw+b'X',b'BADMAGIC'+raw[8:]]
import zlib
for offset,value in [(8,0),(12,2),(16,1),(20,3),(24,0),(36,1)]:
 altered=bytearray(raw);struct.pack_into('<I',altered,offset,value);struct.pack_into('<I',altered,184,zlib.crc32(altered[:184]));bad.append(bytes(altered))
live=manifest(members={0:(1,0,1,record(b'X'))})
for offset,value in [(24,2),(28,0),(32,35),(32,512037),(36,1),(20,2)]:
 altered=bytearray(live);struct.pack_into('<I',altered,offset,value);struct.pack_into('<I',altered,184,zlib.crc32(altered[:184]));bad.append(bytes(altered))
for raw in bad:
 u.mem_write(inp,raw or b'\0');u.mem_write(obj,b'\xa5'*160)
 assert call('wdsv004_read_manifest',inp,len(raw),obj)==-1
 assert bytes(u.mem_read(obj,160))==b'\xa5'*160
 cases.append('malformed output preserved')
u.mem_write(inp,valid[0]);u.mem_write(obj,b'\xa5'*160)
assert call('wdsv004_read_manifest',0,188,obj)==-1
assert bytes(u.mem_read(obj,160))==b'\xa5'*160
assert call('wdsv004_read_manifest',inp,188,0)==-1
cases+=['null input rejected','null output rejected']
report=dict(scope='Own freestanding C manifest parser under ARM emulation; no records/SHA/selector/client/VitaOS',passed=len(cases),elf_sha256=hashlib.sha256(b).hexdigest(),case_counts=dict(collections.Counter(cases)))
(HERE/'manifest-reader-arm-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(cases),scope=report['scope'])))