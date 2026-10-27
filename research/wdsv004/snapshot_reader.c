#include "snapshot_reader.h"
int wdsv004_recover(const wdsv004_buffer manifests[2],const wdsv004_buffer records[3][2],
                   wdsv004_digest_fn digest,wdsv004_snapshot *out){
 wdsv004_manifest m[2];wdsv004_snapshot candidate[2];
 uint32_t parsed[2]={0,0},valid[2]={0,0},i,j,chosen;
 if(!manifests||!records||!digest||!out)return -1;
 for(i=0;i<2;i++)if(manifests[i].data&&
   wdsv004_read_manifest(manifests[i].data,manifests[i].size,&m[i])==0)parsed[i]=1;
 if(parsed[0]&&parsed[1]&&m[0].generation==m[1].generation){
  for(j=0;j<188;j++)if(manifests[0].data[j]!=manifests[1].data[j])return -1;
 }
 for(i=0;i<2;i++){
  if(!parsed[i])continue;
  valid[i]=1;candidate[i].generation=m[i].generation;candidate[i].manifest_slot=i;
  for(j=0;j<3;j++){
   const wdsv004_ref *ref=&m[i].members[j];wdsv004_view *v=&candidate[i].members[j];
   if(!ref->state){v->state=0;v->length=0;v->payload=0;continue;}
   /* Parsed references constrain slot to 0/1 and logical to this index. */
   const wdsv004_buffer *b=&records[j][ref->slot];
   if(wdsv004_resolve_record(ref,b->data,b->size,digest,v)!=0){valid[i]=0;break;}
  }
 }
 if(!valid[0]&&!valid[1]){
  if(!manifests[0].data&&!manifests[0].size&&!manifests[1].data&&!manifests[1].size)return 0;
  return -1;
 }
 chosen=valid[0]&&(!valid[1]||candidate[0].generation>=candidate[1].generation)?0:1;
 for(i=0;i<sizeof(*out);i++)((uint8_t *)out)[i]=((const uint8_t *)&candidate[chosen])[i];
 return 1;
}