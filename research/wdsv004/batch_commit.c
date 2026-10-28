#include "batch_commit.h"
#include "sha256.h"
static int equal(const uint8_t *a,const uint8_t *b,uint32_t n){uint32_t i;if(!a||!b)return 0;for(i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;}
static int same(const wdsv004_buffer *b,const uint8_t *saved,uint32_t present){
 if(!present)return !b->data&&!b->size;
 return b->size==188&&equal(b->data,saved,188);
}
int wdsv004_commit(wdsv004_epoch *epoch,const wdsv004_store *store,
 const wdsv004_buffer changes[3],wdsv004_snapshot *out){
 wdsv004_buffer m[2],r[3][2],candidate[2],mb;
 wdsv004_plan plan;wdsv004_snapshot selected,final;
 uint8_t saved[2][188];uint32_t present[2],i,j;
 if(!epoch||epoch->blocked)return -1;
 /* Fail closed immediately; cleared only after final full confirmation. */
 epoch->blocked=1;
 if(!store||!out||!changes||!store->read_all||!store->write_record||!store->write_manifest)return -1;
 if(store->read_all(store->context,m,r))return -1;
 for(i=0;i<2;i++){
  present[i]=m[i].data!=0;
  if(!present[i]){if(m[i].size)return -1;continue;}
  /* Narrower than pure recovery: publication requires fixed-size slots. */
  if(m[i].size!=188)return -1;
  for(j=0;j<188;j++)saved[i][j]=m[i].data[j];
 }
 if(wdsv004_prepare(m,r,changes,wdsv004_sha256,&plan))return -1;
 for(i=0;i<3;i++)if(plan.changed_mask&(1u<<i))
  if(store->write_record(store->context,i,plan.record_slot[i],&changes[i]))return -1;
 if(store->read_all(store->context,m,r))return -1;
 for(i=0;i<2;i++)if(!same(&m[i],saved[i],present[i]))return -1;
 for(i=0;i<3;i++)if(plan.changed_mask&(1u<<i)){
  const wdsv004_buffer *b=&r[i][plan.record_slot[i]];
  if(b->size!=changes[i].size||!equal(b->data,changes[i].data,b->size))return -1;
 }
 candidate[0]=m[0];candidate[1]=m[1];
 mb.data=plan.manifest;mb.size=188;candidate[plan.manifest_slot]=mb;
 if(wdsv004_recover(candidate,r,wdsv004_sha256,&selected)!=1||selected.manifest_slot!=plan.manifest_slot)return -1;
 if(store->write_manifest(store->context,plan.manifest_slot,&mb))return -1;
 if(store->read_all(store->context,m,r))return -1;
 for(i=0;i<2;i++)if(i==plan.manifest_slot){if(m[i].size!=188||!equal(m[i].data,plan.manifest,188))return -1;}
 else if(!same(&m[i],saved[i],present[i]))return -1;
 if(wdsv004_recover(m,r,wdsv004_sha256,&final)!=1||final.generation!=selected.generation||final.manifest_slot!=plan.manifest_slot)return -1;
 for(i=0;i<sizeof(final);i++)((uint8_t *)out)[i]=((const uint8_t *)&final)[i];
 epoch->blocked=0;return 0;
}