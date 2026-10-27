"""Conservative byte-range index of observed relocation writes; no rewriting."""
from reloc0 import decode,validate,NO_WRITE
def overlaps(rows):
    ordered=sorted(rows,key=lambda r:(r['segment'],r['offset'],r['size']))
    active=[];hits=[]
    for row in ordered:
        active=[r for r in active if r['segment']==row['segment'] and r['offset']+r['size']>row['offset']]
        for other in active:hits.append((other,row))
        active.append(row)
    return hits
def intersects(row,segment,offset,size):return row['segment']==segment and row['offset']<offset+size and offset<row['offset']+row['size']
def index_records(data,segments,source_index):
    if len(data)%12:raise ValueError('partial relocation')
    rows=[]
    for pos in range(0,len(data),12):
        r=decode(data[pos:pos+12])
        if validate(r,segments):raise ValueError('invalid relocation')
        for code,offset in [(r['code'],r['offset'])]+([(r['code2'],r['offset']+2*r['dist2'])] if r['code2'] else []):
            if code not in NO_WRITE:rows.append(dict(segment=r['patch_segment'],offset=offset,size=1 if code==8 else 4,code=code,source_segment=source_index,record_offset=pos))
    return rows
if __name__=='__main__':
    import pathlib,json,hashlib
    from inventory import elf,region
    here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
    raw=(root/'evidence/vita/derived/rePatch-eboot.elf').read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha!='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d':raise ValueError('source changed')
    eh,ph=elf(raw);segments={p['index']:p for p in ph};rows=[]
    for p in ph:
        if p['type']==0x60000000:rows+=index_records(region(raw,p['offset'],p['filesz']),segments,p['index'])
    imports=json.loads((here/'imports.json').read_text());queries=[]
    for i in imports['selected_imports']:
        va=int(i['pointer_cell'],16)
        for p in ph:
            if p['type']==1 and p['vaddr']<=va< p['vaddr']+p['filesz']:
                hits=[r for r in rows if intersects(r,p['index'],va-p['vaddr'],4)]
                queries.append(dict(name=i['name'],pointer_cell=i['pointer_cell'],relocations=hits));break
    loads=sorted([p for p in ph if p['type']==1],key=lambda p:p['vaddr'])
    gaps=[dict(after_segment=a['index'],before_segment=b['index'],virtual_gap_after_memsz=b['vaddr']-a['vaddr']-a['memsz']) for a,b in zip(loads,loads[1:])]
    report=dict(scope=__doc__,source_sha256=sha,writes=len(rows),overlapping_pairs=len(overlaps(rows)),selected_pointer_cells=queries,load_gaps=gaps,limits='Four-byte conservative intervals for MOVW/MOVT, not bit-level or instruction coverage. No patch applied; allocated runtime layout unknown.')
    (here/'reloc-intervals.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
