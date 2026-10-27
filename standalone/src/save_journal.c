#include "save_journal.h"
#include "save_record.h"
static void copy(uint8_t *d,const uint8_t *s,uint32_t n) {
    uint32_t i;for(i=0;i<n;++i)d[i]=s[i];
}
int mhfz_journal_load(mhfz_save_journal *j,uint8_t *data,uint32_t cap,uint32_t *size) {
    uint32_t slot,seen=0,found=0;mhfz_save_record r;
    if(!size)return -2;
    *size=0;
    if(!j)return -2;
    j->ready=0;j->sequence=0;j->slot=0;
    if(!data || !j->scratch || !j->read || !j->write)return -2;
    for(slot=0;slot<2;++slot) {
        int n=j->read(j->context,slot,j->scratch,j->scratch_capacity);
        if(n==-1)continue;
        if(n<0 || (uint32_t)n>j->scratch_capacity){*size=0;return -2;}
        seen=1;
        if(mhfz_read_save_record(j->scratch,(uint32_t)n,&r)<0)continue;
        if(r.length>cap){*size=0;return -2;}
        if(!found || r.sequence>j->sequence) {
            copy(data,r.payload,r.length);*size=r.length;
            j->sequence=r.sequence;j->slot=slot;found=1;
        }
    }
    if(!found && seen)return -1;
    j->ready=1;return found ? 1 : 0;
}
int mhfz_journal_commit(void *context,const uint8_t *data,uint32_t size) {
    mhfz_save_journal *j=(mhfz_save_journal *)context;mhfz_save_record r;
    uint32_t slot,i,sequence;int n;
    if(!j || !j->ready || !j->scratch || !j->read || !j->write || j->sequence==0xffffffffU)return -1;
    sequence=j->sequence+1;slot=j->sequence ? j->slot^1U : 0;
    r.sequence=sequence;r.length=size;r.payload=data;
    n=mhfz_pack_save_record(j->scratch,j->scratch_capacity,&r);
    if(n<0)return -1;
    j->ready=0;
    if(j->write(j->context,slot,j->scratch,(uint32_t)n)!=0)return -1;
    n=j->read(j->context,slot,j->scratch,j->scratch_capacity);
    if(n<0 || (uint32_t)n>j->scratch_capacity || mhfz_read_save_record(j->scratch,(uint32_t)n,&r)<0)return -1;
    if(r.sequence!=sequence || r.length!=size)return -1;
    for(i=0;i<size;++i)if(r.payload[i]!=data[i])return -1;
    j->sequence=sequence;j->slot=slot;j->ready=1;return 0;
}
