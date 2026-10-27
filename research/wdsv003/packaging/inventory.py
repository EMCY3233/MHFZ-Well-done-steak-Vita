"""Read-only structural inventory; never emits executable/resource bytes."""
import argparse, collections, csv, hashlib, json, pathlib, re, struct, zlib

def sha(data): return hashlib.sha256(data).hexdigest()
def region(data, off, size):
    if off < 0 or size < 0 or off + size > len(data): raise ValueError('range outside input')
    return data[off:off+size]
def elf(data):
    h=region(data,0,52)
    if h[:7] != b'\x7fELF\x01\x01\x01': raise ValueError('requires ELF32 little endian v1')
    names=('type','machine','version','entry','phoff','shoff','flags','ehsize','phentsize','phnum','shentsize','shnum','shstrndx')
    hdr=dict(zip(names,struct.unpack_from('<HHIIIIIHHHHHH',h,16)))
    if hdr['phentsize'] != 32 or hdr['phnum']>128: raise ValueError('unsupported program-header layout')
    segments=[]
    for i in range(hdr['phnum']):
        p=dict(zip(('type','offset','vaddr','paddr','filesz','memsz','flags','align'),struct.unpack('<8I',region(data,hdr['phoff']+i*32,32))))
        body=region(data,p['offset'],p['filesz'])
        if p['type']==1 and p['filesz']>p['memsz']: raise ValueError('LOAD file size exceeds memory size')
        p.update(index=i,sha256=sha(body),type_name={1:'PT_LOAD',0x60000000:'PT_SCE_RELA',0x6fffff01:'PT_SCE_VERSION',0x700000a4:'PT_SCE_ARMRELA'}.get(p['type'],'other'))
        segments.append(p)
    return hdr,segments
def va_for_offset(segments, off):
    return [p['vaddr']+off-p['offset'] for p in segments if p['type']==1 and p['offset']<=off<p['offset']+p['filesz']]
def inventory(root):
    sp=root/'evidence/vita/current-ftp/rePatch-eboot.bin';ep=root/'evidence/vita/derived/rePatch-eboot.elf'
    s=sp.read_bytes();e=ep.read_bytes();eh,ph=elf(e)
    if s[:4]!=b'SCE\0': raise ValueError('expected SCE container')
    names=('header_len','elf_filesize','self_filesize','unknown','self_offset','appinfo_offset','elf_offset','phdr_offset','shdr_offset','section_info_offset','sceversion_offset','controlinfo_offset','controlinfo_size','padding')
    sh=dict(zip(names,struct.unpack('<14Q',region(s,16,112))))
    comparison=[]
    for i,p in enumerate(ph):
        offset,length,compression,encryption=struct.unpack('<4Q',region(s,sh['section_info_offset']+i*32,32))
        raw=region(s,offset,length)
        if compression!=2 or encryption!=2: raise ValueError('unsupported compressed/plain segment flags')
        dec=zlib.decompressobj();plain=dec.decompress(raw,p['filesz']+1)
        if not dec.eof or dec.unconsumed_tail or len(plain)!=p['filesz']: raise ValueError('segment decompression mismatch')
        comparison.append(dict(index=i,container_offset=offset,container_length=length,compression=compression,encryption=encryption,decoded_bytes=len(plain),unused_trailing_bytes=len(dec.unused_data),matches_derived=plain==region(e,p['offset'],p['filesz']),sha256=sha(plain)))
    literals=[]
    for m in re.finditer(rb'[\x20-\x7e]{4,}',e):
        if re.search(rb'PCSG00350|app0:|savedata0:|PRI-DATA|INI-DATA',m.group(),re.I):
            literals.append(dict(file_offset=hex(m.start()),load_virtual_addresses=[hex(x) for x in va_for_offset(ph,m.start())],text=m.group().decode()))
    manifest=root/'research/vita-existing-copy-manifest.csv'
    layers=collections.defaultdict(lambda:dict(files=0,bytes=0))
    with manifest.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            match=re.search(r'/((?:app|patch|rePatch))/PCSG00350/',row['RemotePath'])
            if match:
                d=layers[match.group(1)];d['files']+=1;d['bytes']+=int(row['Bytes'])
    log=root/'research/ghidra-vita-import.log'
    libs=re.findall(r'^\s*\[([^\]]+)\] -> not found in project',log.read_text(encoding='utf-8'),re.M)
    return dict(scope='Structural read-only inventory; no launch, relocation application, runtime mount discovery, or packaging',source=dict(path=sp.relative_to(root).as_posix(),bytes=len(s),sha256=sha(s)),derived=dict(path=ep.relative_to(root).as_posix(),bytes=len(e),sha256=sha(e)),self_header=sh,self_declared_size_matches=len(s)==sh['self_filesize'],embedded_header_matches=region(s,sh['elf_offset'],52)==region(e,0,52),embedded_phdrs_match=region(s,sh['phdr_offset'],32*eh['phnum'])==region(e,eh['phoff'],32*eh['phnum']),elf_header=eh,segments=ph,compressed_segment_comparison=comparison,literals=literals,layers_from_prior_manifest=dict(layers),ghidra_imported_library_candidates=libs,import_scope='Library names reported by previous Ghidra import log; not runtime availability or exhaustive NID resolution',limits=['Derived ELF is not certified launchable or executable-equivalent.','Relocation segments retained as bytes; relocation records are not applied or individually validated here.','Manifest layer counts are historical inventory, not observed mount precedence.','No commercial bytes emitted in this report.'])
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path(__file__).with_name('inventory.json'));a=parser.parse_args()
    report=inventory(a.root);a.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'segments':len(report['segments']),'all_segment_bytes_match':all(x['matches_derived'] for x in report['compressed_segment_comparison']),'output':str(a.output)}))
