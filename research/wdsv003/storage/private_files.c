#include "private_files.h"
#include <stdio.h>
#include <errno.h>
int wdsv_read_slot(void *context,uint32_t slot,uint8_t *dst,uint32_t cap) {
    FILE *f;size_t total=0;int ok=1;unsigned char extra;
    const char *path=context?wdsv_slot_path(*(const uint32_t *)context,slot):0;
    if(!path || !dst || !cap || cap>163876)return -2;
    errno=0;f=fopen(path,"rb");
    if(!f)return errno==ENOENT ? -1 : -2;
    while(total<cap) {
        size_t n=fread(dst+total,1,cap-total,f);total+=n;
        if(!n)break;
    }
    if((ferror)(f))ok=0;
    if(total==cap && fread(&extra,1,1,f)!=0)ok=0;
    if((ferror)(f))ok=0;
    if(fclose(f)!=0)ok=0;
    return ok ? (int)total : -2;
}
int wdsv_write_slot(void *context,uint32_t slot,const uint8_t *src,uint32_t size) {
    FILE *f;size_t total=0;int ok=1;
    const char *path=context?wdsv_slot_path(*(const uint32_t *)context,slot):0;
    if(!path || !src || size<36 || size>163876)return -1;
    f=fopen(path,"wb");if(!f)return -1;
    while(total<size) {
        size_t n=fwrite(src+total,1,size-total,f);total+=n;
        if(!n){ok=0;break;}
    }
    if(fflush(f)!=0)ok=0;
    if(fclose(f)!=0)ok=0;
    return ok ? 0 : -1;
}
