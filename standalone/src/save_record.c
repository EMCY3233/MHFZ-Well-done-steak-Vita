#include "save_record.h"
static const uint8_t magic[8]={'M','Z','S','A','V','0','0','1'};
static uint32_t crc(const uint8_t *p,uint32_t n) {
    uint32_t v=0xffffffffU,i,j;
    for(i=0;i<n;++i) {
        v^=p[i];
        for(j=0;j<8;++j)v=(v>>1)^((0U-(v&1U))&0xedb88320U);
    }
    return ~v;
}
static void put32(uint8_t *p,uint32_t v) {
    uint32_t i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8));
}
static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
int mhfz_pack_save_record(uint8_t *d,uint32_t cap,const mhfz_save_record *r) {
    uint32_t i,checksum;
    if(!d || !r || !r->sequence || !r->length || !r->payload || r->length>1048576)return -1;
    if(r->length+24>cap)return -2;
    checksum=crc(r->payload,r->length);
    for(i=0;i<8;++i)d[i]=magic[i];
    put32(d+8,r->sequence);put32(d+12,r->length);put32(d+16,checksum);
    put32(d+20,crc(d,20));
    for(i=0;i<r->length;++i)d[24+i]=r->payload[i];
    return (int)(r->length+24);
}
int mhfz_read_save_record(const uint8_t *s,uint32_t size,mhfz_save_record *r) {
    mhfz_save_record value;uint32_t i;
    if(!s || !r || size<24)return -1;
    for(i=0;i<8;++i)if(s[i]!=magic[i])return -1;
    if(crc(s,20)!=get32(s+20))return -1;
    value.sequence=get32(s+8);value.length=get32(s+12);value.payload=s+24;
    if(!value.sequence || !value.length || value.length>1048576 || value.length!=size-24)return -1;
    if(crc(value.payload,value.length)!=get32(s+16))return -1;
    *r=value;return 0;
}
