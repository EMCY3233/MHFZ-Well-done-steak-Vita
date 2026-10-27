"""Read-only PRX module/import metadata; does not relocate or patch the image."""
import hashlib,json,pathlib,struct
from inventory import elf,region
from prx_tables import read_va,read_name,descriptor
ROOT=pathlib.Path(__file__).resolve().parents[3]
path=ROOT/'evidence/vita/derived/rePatch-eboot.elf';data=path.read_bytes()
digest=hashlib.sha256(data).hexdigest()
assert digest=='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d'
eh,segments=elf(data)
def at(va,size):
 return read_va(data,segments,va,size)
index=eh['entry']>>30;offset=eh['entry']&0x3fffffff
if index>=len(segments):raise ValueError('bad module segment')
p=segments[index]
assert p['type']==1 and offset+0x5c<=p['filesz']
base=p['vaddr'];module_va=base+offset;m=at(module_va,0x5c)
assert m[31]==6,'Only observed module info version 6 supported'
top,end=struct.unpack_from('<II',m,0x2c)
cursor=base+top;limit=base+end
if end<top or base+end>0x100000000:raise ValueError('bad stub bounds')
rows=[];selected=[]
wanted={0x823d1230:'sceAppUtilSaveDataSlotDelete',0x823d1240:'sceAppUtilSaveDataDataSave',0x823d1250:'sceAppUtilSaveDataSlotGetParam',0x823d1260:'sceAppUtilInit',0x823d27c0:'sceIoOpen',0x823d2930:'sceIoRead',0x823d2920:'sceIoClose',0x823d1c00:'sceAppMgrLoadExec'}
while cursor<limit:
 size=at(cursor,1)[0]
 if size not in (0x24,0x34,0x2c) or cursor+size>limit:raise ValueError('bad descriptor size')
 d=descriptor(at(cursor,size));nfunc=d['functions'];nvar=d['variables'];ntls=d['tls_variables'];libnid=d['nid'];name=d['name_va'];nids=d['nids_va'];funcs=d['functions_va']
 library=read_name(at,name)
 row=dict(descriptor_va=hex(cursor),size=size,name=library,nid=None if libnid is None else hex(libnid),functions=nfunc,variables=nvar,tls_variables=ntls)
 for i in range(nfunc):
  nid=struct.unpack('<I',at(nids+i*4,4))[0];entry=struct.unpack('<I',at(funcs+i*4,4))[0]
  if (entry&~1) in wanted:selected.append(dict(name=wanted[entry&~1],library=library,nid=hex(nid),stub_va=hex(entry),nid_cell=hex(nids+i*4),pointer_cell=hex(funcs+i*4)))
 rows.append(row);cursor+=size
assert cursor==limit
init_raw=at(0x82cb3628,0x82cb42a4-0x82cb3628)
init_entries=struct.unpack('<'+'I'*(len(init_raw)//4),init_raw)
report=dict(scope=__doc__,source_sha256=digest,module_info_va=hex(module_va),info_version=m[31],start_entry_rva=hex(struct.unpack_from('<I',m,0x44)[0]),stub_top_va=hex(base+top),stub_end_va=hex(base+end),libraries=rows,selected_imports=selected,initializer_candidate=dict(start_va='0x82cb3628',end_va='0x82cb42a4',entries=len(init_entries),nonzero=sum(bool(x) for x in init_entries),sha256=hashlib.sha256(init_raw).hexdigest(),scope='Range referenced by static startup helper; entries not executed or individually traced'),limits=['Raw stored pointers mapped only; no runtime binding/relocation or hook coverage proved.','Selected names are cross-checks against prior Ghidra NID resolution, not private server code.'])
(pathlib.Path(__file__).with_name('imports.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(libraries=len(rows),functions=sum(x['functions'] for x in rows),selected=selected,module_info_va=hex(module_va))))
