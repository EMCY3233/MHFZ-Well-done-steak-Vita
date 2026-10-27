"""Read-only ELF address mapping and independent disassembly; no target execution."""
import hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent
src=ROOT/'evidence/vita/derived/rePatch-eboot.elf'
data=src.read_bytes()
expected='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d'
assert hashlib.sha256(data).hexdigest()==expected
phoff=struct.unpack_from('<I',data,28)[0]
ents,count=struct.unpack_from('<HH',data,42)
segs=[struct.unpack_from('<8I',data,phoff+i*ents) for i in range(count)]
def read(va,size):
 for typ,off,addr,_,filesz,_,_,_ in segs:
  if typ==1 and addr<=va and va+size<=addr+filesz:
   return data[off+va-addr:off+va-addr+size]
 raise ValueError(hex(va))
windows=[('delete-control',0x8213c3ec,0x60),('save-api-call',0x8213ca60,0x40),('relaunch',0x821290b6,0x50)]
rows=[]
obj=ROOT/'analysis-tools/vitasdk-win-20260825/bin/arm-vita-eabi-objdump.exe'
for name,va,size in windows:
 raw=read(va,size); target=OUT/(name+'.bin');target.write_bytes(raw)
 asm=subprocess.check_output([str(obj),'-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma='+hex(va),str(target)],text=True)
 (OUT/(name+'.asm.txt')).write_text(asm,encoding='utf-8')
 rows.append(dict(name=name,va=hex(va),bytes=size,sha256=hashlib.sha256(raw).hexdigest()))
strings={hex(a):read(a,64).split(b'\0')[0].decode('ascii','backslashreplace') for a in [0x827f35b8,0x827f35c8]}
vt=struct.unpack('<16I',read(0x82b29960,64))
result=dict(source_sha256=expected,scope='Original derived ELF bytes, not relocated Ghidra memory; bounded windows only',windows=rows,relaunch_strings=strings,vtable_candidate=[hex(x) for x in vt])
(OUT/'control-sites.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
