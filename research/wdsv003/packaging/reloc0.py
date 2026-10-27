"""Decode main form-0 fields and check target ranges, without applying fixups."""
import struct,collections
KNOWN={0,2,3,8,10,28,29,38,40,41,42,43,44,47,48,255}
NO_WRITE={0,40,255}
def decode(raw):
    if len(raw)!=12:raise ValueError('form-0 size')
    first,addend,offset=struct.unpack('<III',raw)
    if first&15:raise ValueError('not form 0')
    return dict(symbol_segment=(first>>4)&15,code=(first>>8)&255,patch_segment=(first>>16)&15,code2=(first>>20)&255,dist2=(first>>28)&15,addend=addend,offset=offset)
def validate(r,segments):
    problems=[];patch=r['patch_segment'];symbol=r['symbol_segment']
    if symbol!=15 and (symbol not in segments or segments[symbol]['type']!=1):problems.append('symbol_segment')
    if patch not in segments or segments[patch]['type']!=1:return problems+['patch_segment']
    for code,offset in [(r['code'],r['offset'])]+([(r['code2'],r['offset']+2*r['dist2'])] if r['code2'] else []):
        if code not in KNOWN:problems.append('unknown_code');continue
        if code in NO_WRITE:continue
        width=1 if code==8 else 4
        if offset+width>segments[patch]['memsz']:problems.append('target_range')
    return problems
def summarize(data,segments):
    if len(data)%12:raise ValueError('trailing incomplete record')
    codes=collections.Counter();symbols=collections.Counter();patches=collections.Counter();issues=collections.Counter();examples=[];secondary=0;bss=0
    for pos in range(0,len(data),12):
        r=decode(data[pos:pos+12]);codes[r['code']]+=1;symbols[r['symbol_segment']]+=1;patches[r['patch_segment']]+=1
        if r['code2']:secondary+=1
        problems=validate(r,segments)
        for p in problems:issues[p]+=1
        if problems and len(examples)<8:examples.append(dict(record_offset=pos,problems=problems))
        p=segments.get(r['patch_segment'])
        if p and p['type']==1 and r['code'] not in NO_WRITE and r['offset']>=p['filesz']:bss+=1
    return dict(records=len(data)//12,codes=dict(codes),symbol_segments=dict(symbols),patch_segments=dict(patches),secondary_operations=secondary,primary_targets_in_bss=bss,issues=dict(issues),issue_examples=examples)
if __name__=='__main__':
    import pathlib,json,hashlib
    from inventory import elf,region
    here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
    raw=(root/'evidence/vita/derived/rePatch-eboot.elf').read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d':raise ValueError('source changed')
    eh,ps=elf(raw);segments={p['index']:p for p in ps};reports=[]
    for p in ps:
        if p['type']==0x60000000:reports.append(dict(segment=p['index'],summary=summarize(region(raw,p['offset'],p['filesz']),segments)))
    report=dict(scope=__doc__,source_sha256=digest,segments=reports,limits='Range/type checks only. No instruction validation, symbol resolution, overlap/order analysis, relocation application or launch proof.')
    (here/'reloc0.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
