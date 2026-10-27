#include "value_body.h"
static void put(uint8_t *p,uint32_t x){uint32_t i;for(i=0;i<4;i++)p[i]=(uint8_t)(x>>(8*i));}
static uint32_t get(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
int wdsv_pack_value(uint8_t *p,uint32_t cap,const wdsv_value *v){
 uint32_t i;
 if(!p||!v||v->deleted>1||v->length>0x28000||(!v->payload&&v->length)||(v->deleted&&v->length))return -1;
 if(cap<12||v->length>cap-12)return -2;
 p[0]='M';p[1]='Z';p[2]='V';p[3]='1';put(p+4,v->deleted);put(p+8,v->length);
 for(i=0;i<v->length;i++)p[12+i]=v->payload[i];
 return (int)(12+v->length);
}
int wdsv_read_value(const uint8_t *p,uint32_t size,wdsv_value *v){
 wdsv_value x;
 if(!p||!v||size<12||p[0]!='M'||p[1]!='Z'||p[2]!='V'||p[3]!='1')return -1;
 x.deleted=get(p+4);x.length=get(p+8);x.payload=p+12;
 if(x.deleted>1||x.length>0x28000||x.length!=size-12||(x.deleted&&x.length))return -1;
 *v=x;return 0;
}
