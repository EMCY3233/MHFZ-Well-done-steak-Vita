#include "batch_plan.h"
static void put(uint8_t *p,uint32_t n){uint32_t i;for(i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i));}
static uint32_t get(const uint8_t *p){return p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint32_t crc(const uint8_t *p,uint32_t n){uint32_t c=0xffffffff,i,j;for(i=0;i<n;i++){c^=p[i];for(j=0;j<8;j++)c=(c>>1)^(0xedb88320u& (0u-(c&1u)));}return ~c;}
int wdsv004_prepare(const wdsv004_buffer m[2],const wdsv004_buffer records[3][2],
 const wdsv004_buffer replacement[3],wdsv004_digest_fn digest,wdsv004_plan *out){
 wdsv004_snapshot current;wdsv004_manifest baseline,other;wdsv004_plan plan;
 wdsv004_ref ref;wdsv004_view view;uint32_t generation,i,j;uint8_t *row;
 if(!replacement||!out||!digest)return -1;
 if(wdsv004_recover(m,records,digest,&current)!=1)return -1;
 if(wdsv004_read_manifest(m[current.manifest_slot].data,m[current.manifest_slot].size,&baseline))return -1;
 generation=baseline.generation;
 for(i=0;i<2;i++)if(wdsv004_read_manifest(m[i].data,m[i].size,&other)==0&&other.generation>generation)generation=other.generation;
 if(generation==0xffffffff)return -1;
 plan.manifest_slot=1-current.manifest_slot;plan.changed_mask=0;
 for(i=0;i<188;i++)plan.manifest[i]=m[current.manifest_slot].data[i];
 put(plan.manifest+8,generation+1);
 for(i=0;i<3;i++){
  const wdsv004_buffer *b=&replacement[i];plan.record_slot[i]=0xffffffff;
  if(!b->data&&!b->size)continue;
  if(!b->data||b->size<36||b->size>163876)return -1;
  ref=baseline.members[i];
  if(ref.sequence==0xffffffff||get(b->data+8)!=ref.sequence+1)return -1;
  ref.state=get(b->data+28)+1;
  if(ref.state!=1&&ref.state!=2)return -1;
  ref.slot=baseline.members[i].state?1-ref.slot:0;
  ref.sequence++;ref.record_bytes=b->size;
  if(digest(b->data,b->size,ref.digest))return -1;
  if(wdsv004_resolve_record(&ref,b->data,b->size,digest,&view))return -1;
  row=plan.manifest+16+56*i;
  put(row,i);put(row+4,ref.state);put(row+8,ref.slot);put(row+12,ref.sequence);put(row+16,ref.record_bytes);put(row+20,0);
  for(j=0;j<32;j++)row[24+j]=ref.digest[j];
  plan.changed_mask|=1u<<i;plan.record_slot[i]=ref.slot;
 }
 if(!plan.changed_mask)return -1;
 put(plan.manifest+184,crc(plan.manifest,184));
 for(i=0;i<sizeof(plan);i++)((uint8_t *)out)[i]=((const uint8_t *)&plan)[i];
 return 0;
}