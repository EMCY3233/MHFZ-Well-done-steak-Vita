"""Bounded readers for supported PRX import layouts; no target I/O."""
import struct

def read_va(data,segments,va,size):
    if va<0 or size<0 or va+size>0x100000000:
        raise ValueError('invalid virtual range')
    for p in segments:
        if p['type']==1 and p['vaddr']<=va and va+size<=p['vaddr']+p['filesz']:
            off=p['offset']+va-p['vaddr']
            if off<0 or off+size>len(data):raise ValueError('truncated LOAD')
            return data[off:off+size]
    raise ValueError('virtual range not backed by one LOAD')

def read_name(reader,va,limit=96):
    if not va or limit<1 or limit>256:raise ValueError('invalid library name')
    out=bytearray()
    for i in range(limit):
        c=reader(va+i,1)[0]
        if c==0:
            if not out:raise ValueError('empty library name')
            return out.decode('ascii')
        if not 0x20<=c<=0x7e:raise ValueError('non ASCII library name')
        out.append(c)
    raise ValueError('unterminated library name')

def descriptor(raw):
    if not raw:raise ValueError('empty descriptor')
    size=raw[0]
    if size not in (0x24,0x34,0x2c) or len(raw)!=size:raise ValueError('bad descriptor range')
    if size!=0x24 and struct.unpack_from('<H',raw)[0]!=size:raise ValueError('bad descriptor size word')
    version,attr,nfunc,nvar,ntls=struct.unpack_from('<5H',raw,2)
    if size==0x24:libnid,name,nids,funcs=struct.unpack_from('<4I',raw,12)
    elif size==0x34:
        libnid,name=struct.unpack_from('<2I',raw,16);nids,funcs=struct.unpack_from('<2I',raw,28)
    else:
        libnid=None;name,nids,funcs=struct.unpack_from('<3I',raw,16)
    if not name or (nfunc and (not nids or not funcs)):raise ValueError('null required table')
    return dict(size=size,version=version,attribute=attr,functions=nfunc,variables=nvar,tls_variables=ntls,nid=libnid,name_va=name,nids_va=nids,functions_va=funcs)
