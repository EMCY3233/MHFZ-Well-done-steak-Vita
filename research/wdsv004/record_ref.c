#include "record_ref.h"
static uint32_t get(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint32_t crc(const uint8_t *p,uint32_t n){
 uint32_t v=0xffffffffU,i,j;
 for(i=0;i<n;i++){v^=p[i];for(j=0;j<8;j++)v=(v>>1)^((0U-(v&1U))&0xedb88320U);}
 return ~v;
}
int wdsv004_resolve_record(const wdsv004_ref *r,const uint8_t *p,uint32_t size,
                          wdsv004_digest_fn digest,wdsv004_view *out){
 static const uint8_t magic[8]={'M','Z','S','A','V','0','0','1'};
 uint8_t hash[32];uint32_t i,deleted,length;
 if(!r||!p||!digest||!out||r->logical>2||r->slot>1||!r->sequence)return -1;
 if(r->state<1||r->state>2||size<36||size>512036||size!=r->record_bytes)return -1;
 for(i=0;i<8;i++)if(p[i]!=magic[i])return -1;
 if(get(p+8)!=r->sequence||get(p+12)!=size-24)return -1;
 if(crc(p,20)!=get(p+20)||crc(p+24,size-24)!=get(p+16))return -1;
 if(p[24]!='M'||p[25]!='Z'||p[26]!='V'||p[27]!='1')return -1;
 deleted=get(p+28);length=get(p+32);
 if(deleted>1||deleted+1!=r->state||length!=size-36||(deleted&&length))return -1;
 if(digest(p,size,hash)!=0)return -1;
 for(i=0;i<32;i++)if(hash[i]!=r->digest[i])return -1;
 out->state=r->state;out->length=length;out->payload=p+36;
 return 0;
}