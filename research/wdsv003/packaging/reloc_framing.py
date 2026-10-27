"""Read-only framing of main relocation records; no decoding of fixup semantics."""
import collections,struct
SIZES={0:12,1:8,2:8,3:8,4:4,5:4,6:4,7:4,8:4,9:4}
def scan(data):
    cursor=0;counts=collections.Counter()
    while cursor<len(data):
        if len(data)-cursor<4:return dict(complete=False,offset=cursor,reason='truncated_header',forms=dict(counts))
        form=struct.unpack_from('<I',data,cursor)[0]&15
        if form not in SIZES:return dict(complete=False,offset=cursor,reason='unsupported_form',form=form,forms=dict(counts))
        size=SIZES[form]
        if len(data)-cursor<size:return dict(complete=False,offset=cursor,reason='truncated_record',form=form,forms=dict(counts))
        counts[form]+=1;cursor+=size
    return dict(complete=True,bytes=cursor,records=sum(counts.values()),forms=dict(counts))

if __name__=='__main__':
    import pathlib,json,hashlib
    from inventory import elf,region
    here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
    data=(root/'evidence/vita/derived/rePatch-eboot.elf').read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if digest!='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d':raise ValueError('source changed')
    eh,ph=elf(data);rows=[]
    for p in ph:
        if p['type']==0x60000000:rows.append(dict(segment=p['index'],sha256=p['sha256'],framing=scan(region(data,p['offset'],p['filesz']))))
    report=dict(scope=__doc__,source_sha256=digest,segments=rows,limits=['Lengths/forms only; offsets, stateful relative forms, segment indexes and relocation effects not decoded or validated.','Not variable-import reftables. No executable bytes changed.'])
    (here/'reloc-framing.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
