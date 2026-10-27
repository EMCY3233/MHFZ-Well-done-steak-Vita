"""Conservative structural gate only, not a Vita loader or signature validator."""
def check_layout(file_size,declared_size,segments):
    issues=[];ranges=[]
    if not segments:issues.append('NO_SEGMENTS')
    if file_size<0 or declared_size<0:raise ValueError('negative file size')
    if file_size!=declared_size:issues.append('DECLARED_SIZE_MISMATCH')
    for s in segments:
        off,n=s['container_offset'],s['container_length']
        if off<0 or n<0 or off+n>file_size:issues.append('SEGMENT_OUTSIDE_FILE')
        else:ranges.append((off,off+n,s['index']))
        if s.get('unused_trailing_bytes',0):issues.append('COMPRESSED_TRAILING_DATA')
        if not s.get('matches_derived',False):issues.append('DECODED_SEGMENT_MISMATCH')
    ranges.sort()
    for a,b in zip(ranges,ranges[1:]):
        if b[0]<a[1]:issues.append('OVERLAPPING_SEGMENTS')
    return sorted(set(issues))

if __name__=='__main__':
    import pathlib,json,hashlib
    here=pathlib.Path(__file__).resolve().parent;root=here.parents[2]
    inventory=json.loads((here/'inventory.json').read_text(encoding='utf-8-sig'))
    source=root/inventory['source']['path'];data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=inventory['source']['sha256']:raise ValueError('source changed; rerun inventory')
    segments=inventory['compressed_segment_comparison']
    issues=check_layout(len(data),inventory['self_header']['self_filesize'],segments)
    compressed_end=max(s['container_offset']+s['container_length'] for s in segments)
    report=dict(scope=__doc__,source_sha256=inventory['source']['sha256'],blocking_issues=issues,transformation_allowed=not issues,actual_file_size=len(data),declared_file_size=inventory['self_header']['self_filesize'],last_compressed_end=compressed_end,uncovered_tail_bytes=len(data)-compressed_end,limits='Passing layout checks does not prove authenticity, metadata/relocation correctness, hook coverage, isolation or launchability. No bytes rewritten.')
    (here/'self-gate.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
