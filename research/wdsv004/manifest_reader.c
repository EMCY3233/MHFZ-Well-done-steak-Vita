#include "manifest_reader.h"
static uint32_t get(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint32_t crc(const uint8_t *p,uint32_t n){
 uint32_t v=0xffffffffU,i,j;
 for(i=0;i<n;i++){v^=p[i];for(j=0;j<8;j++)v=(v>>1)^((0U-(v&1U))&0xedb88320U);}
 return ~v;
}
int wdsv004_read_manifest(const uint8_t *p,uint32_t size,wdsv004_manifest *out){
 static const uint8_t magic[8]={'M','Z','B','A','T','0','0','1'};
 wdsv004_manifest m;uint32_t i,j;
 if(!p||!out||size!=188)return -1;
 for(i=0;i<8;i++)if(p[i]!=magic[i])return -1;
 m.generation=get(p+8);
 if(!m.generation||get(p+12)!=3||crc(p,184)!=get(p+184))return -1;
 for(i=0;i<3;i++){
  const uint8_t *e=p+16+i*56;wdsv004_ref *r=&m.members[i];
  r->logical=get(e);r->state=get(e+4);r->slot=get(e+8);r->sequence=get(e+12);r->record_bytes=get(e+16);
  if(r->logical!=i||r->state>2||get(e+20))return -1;
  for(j=0;j<32;j++)r->digest[j]=e[24+j];
  if(!r->state){
   if(r->slot!=0xffffffffU||r->sequence||r->record_bytes)return -1;
   for(j=0;j<32;j++)if(r->digest[j])return -1;
  }else{
   if(r->slot>1||!r->sequence||r->record_bytes<36||r->record_bytes>512036)return -1;
   if(r->state==2&&r->record_bytes!=36)return -1;
  }
 }
 for(i=0;i<sizeof(m);i++)((uint8_t *)out)[i]=((const uint8_t *)&m)[i];
 return 0;
}