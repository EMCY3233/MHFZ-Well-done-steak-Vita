#include "private_store.h"
#include <psp2/io/fcntl.h>
/* ENOENT mapping inherited from WDSV003/Vita3K evidence, not physical proof. */
#define ABSENT 0x80010002U
static const char *paths[8]={
 "ux0:data/MHFZL0001/wdsv004/manifest-a.bin","ux0:data/MHFZL0001/wdsv004/manifest-b.bin",
 "ux0:data/MHFZL0001/wdsv004/ini-a.bin","ux0:data/MHFZL0001/wdsv004/ini-b.bin",
 "ux0:data/MHFZL0001/wdsv004/pri-a.bin","ux0:data/MHFZL0001/wdsv004/pri-b.bin",
 "ux0:data/MHFZL0001/wdsv004/character-a.bin","ux0:data/MHFZL0001/wdsv004/character-b.bin"};
static int load(uint32_t index,uint8_t *p,uint32_t capacity){
 SceUID fd=sceIoOpen(paths[index],SCE_O_RDONLY,0);SceSSize n;uint32_t total=0;uint8_t extra;int ok=1;
 if(fd<0)return (uint32_t)fd==ABSENT?-1:-2;
 while(total<capacity){n=sceIoRead(fd,p+total,capacity-total);if(n<0||(uint32_t)n>capacity-total){ok=0;break;}if(!n)break;total+=(uint32_t)n;}
 if(ok&&total==capacity&&sceIoRead(fd,&extra,1)!=0)ok=0;
 if(sceIoClose(fd)<0)ok=0;
 return ok?(int)total:-2;
}
static int save(wdsv004_private_pool *pool,uint32_t index,const wdsv004_buffer *b,uint32_t minimum,uint32_t maximum){
 SceUID fd;SceSSize n;uint32_t total=0;int ok=1;uintptr_t start,end,src;
 if(!pool||pool->parent_verified!=1||!b||!b->data||b->size<minimum||b->size>maximum)return -1;
 start=(uintptr_t)pool;end=start+sizeof(*pool);src=(uintptr_t)b->data;
 /* Replacements must survive read_all buffer reuse, so cannot alias pool. */
 if(src>UINTPTR_MAX-b->size||(src<end&&src+b->size>start))return -1;
 fd=sceIoOpen(paths[index],SCE_O_WRONLY|SCE_O_CREAT|SCE_O_TRUNC,0600);if(fd<0)return -1;
 while(total<b->size){n=sceIoWrite(fd,b->data+total,b->size-total);if(n<=0||(uint32_t)n>b->size-total){ok=0;break;}total+=(uint32_t)n;}
 if(sceIoClose(fd)<0)ok=0;
 return ok?0:-1;
}
int wdsv004_private_read(void *context,wdsv004_buffer m[2],wdsv004_buffer r[3][2]){
 wdsv004_private_pool *pool=context;wdsv004_buffer tm[2],tr[3][2];uint32_t i,j;int n;
 if(!pool||pool->parent_verified!=1||!m||!r)return -1;
 for(i=0;i<2;i++){n=load(i,pool->manifests[i],188);if(n< -1)return -1;tm[i].data=n==-1?0:pool->manifests[i];tm[i].size=n==-1?0:(uint32_t)n;}
 for(i=0;i<3;i++)for(j=0;j<2;j++){n=load(2+2*i+j,pool->records[i][j],163876);if(n< -1)return -1;tr[i][j].data=n==-1?0:pool->records[i][j];tr[i][j].size=n==-1?0:(uint32_t)n;}
 for(i=0;i<sizeof(tm);i++)((uint8_t *)m)[i]=((uint8_t *)tm)[i];
 for(i=0;i<sizeof(tr);i++)((uint8_t *)r)[i]=((uint8_t *)tr)[i];
 return 0;
}
int wdsv004_private_record(void *c,uint32_t logical,uint32_t slot,const wdsv004_buffer *b){if(logical>2||slot>1)return -1;return save(c,2+2*logical+slot,b,36,163876);}
int wdsv004_private_manifest(void *c,uint32_t slot,const wdsv004_buffer *b){if(slot>1)return -1;return save(c,slot,b,188,188);}