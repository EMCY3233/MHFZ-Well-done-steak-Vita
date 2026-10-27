#include "private_io.h"
#include <psp2/io/fcntl.h>
/* Vita3K 17a8b340, io/include/io/io.h; not a physical measurement. */
#define WDSV_IO_ENOENT 0x80010002U
int wdsv_io_read_slot(void *context,uint32_t slot,uint8_t *dst,uint32_t cap) {
    const char *path=context?wdsv_slot_path(*(const uint32_t *)context,slot):0;
    SceUID fd;SceSSize n;uint32_t total=0;int ok=1;uint8_t extra;
    if(!path || !dst || !cap || cap>163876)return -2;
    fd=sceIoOpen(path,SCE_O_RDONLY,0);
    if(fd<0)return (uint32_t)fd==WDSV_IO_ENOENT ? -1 : -2;
    while(total<cap) {
        n=sceIoRead(fd,dst+total,cap-total);
        if(n<0 || (uint32_t)n>cap-total){ok=0;break;}
        if(!n)break;
        total+=(uint32_t)n;
    }
    if(ok && total==cap) {
        n=sceIoRead(fd,&extra,1);
        if(n!=0)ok=0;
    }
    if(sceIoClose(fd)<0)ok=0;
    return ok ? (int)total : -2;
}
int wdsv_io_write_slot(void *context,uint32_t slot,const uint8_t *src,uint32_t size) {
    const char *path=context?wdsv_slot_path(*(const uint32_t *)context,slot):0;
    SceUID fd;SceSSize n;uint32_t total=0;int ok=1;
    if(!path || !src || size<36 || size>163876)return -1;
    fd=sceIoOpen(path,SCE_O_WRONLY|SCE_O_CREAT|SCE_O_TRUNC,0600);
    if(fd<0)return -1;
    while(total<size) {
        n=sceIoWrite(fd,src+total,size-total);
        if(n<=0 || (uint32_t)n>size-total){ok=0;break;}
        total+=(uint32_t)n;
    }
    if(sceIoClose(fd)<0)ok=0;
    return ok ? 0 : -1;
}