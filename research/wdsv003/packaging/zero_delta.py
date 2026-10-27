"""Compare relocation expectations at declared bases with original stored values."""
import struct,collections
from reloc0 import decode,validate
from inventory import region,elf

def thumb_immediate(raw,code):
    if len(raw)!=4 or code not in (47,48):raise ValueError('unsupported instruction')
    a,b=struct.unpack('<HH',raw)
    opcode=0xf240 if code==47 else 0xf2c0
    if a&0xfbf0!=opcode or b&0x8000:raise ValueError('opcode mismatch')
    return ((a&15)<<12)|(((a>>10)&1)<<11)|(((b>>12)&7)<<8)|(b&255)

def compare(data,segments,relocations):
    counts=collections.Counter();issues=collections.Counter();examples=[]
    if len(relocations)%12:raise ValueError('record boundary')
    for position in range(0,len(relocations),12):
        r=decode(relocations[position:position+12]);code=r['code'];counts[code]+=1
        problems=validate(r,segments)
        if problems:issues['invalid_range_or_type']+=1;continue
        if code not in (2,47,48) or r['code2']:issues['unsupported_operation']+=1;continue
        p=segments[r['patch_segment']]
        if r['offset']+4>p['filesz']:issues['not_file_backed']+=1;continue
        raw=region(data,p['offset']+r['offset'],4)
        base=0 if r['symbol_segment']==15 else segments[r['symbol_segment']]['vaddr']
        expected=(base+r['addend'])&0xffffffff
        try:stored=struct.unpack('<I',raw)[0] if code==2 else thumb_immediate(raw,code)
        except ValueError:
            issues['opcode_mismatch']+=1;continue
        if code==47:expected&=0xffff
        elif code==48:expected>>=16
        if stored!=expected:
            issues['stored_value_mismatch']+=1
            if len(examples)<8:examples.append(dict(record_offset=position,patch_va=hex(p['vaddr']+r['offset']),code=code))
    return dict(records=sum(counts.values()),counts=dict(counts),issues=dict(issues),mismatch_locations=examples)

if __name__=='__main__':
    import pathlib,json,hashlib
    here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
    data=(root/'evidence/vita/derived/rePatch-eboot.elf').read_bytes();sha=hashlib.sha256(data).hexdigest()
    if sha!='2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d':raise ValueError('source changed')
    eh,ph=elf(data);segs={p['index']:p for p in ph};results=[]
    for p in ph:
        if p['type']==0x60000000:results.append(dict(segment=p['index'],comparison=compare(data,segs,region(data,p['offset'],p['filesz']))))
    report=dict(scope=__doc__,source_sha256=sha,segments=results,limits='Read-only zero-delta consistency; no changed bases, writing, relocation ordering/overlap proof, SELF reconstruction or runtime validation.')
    (here/'zero-delta.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
