#include "text_handoff.h"
uint8_t test_arena[WDSV004_TEXT_MAX+2];
uint32_t test_mode,test_allocations,test_releases,test_requested,test_reentry;
uintptr_t test_alias,test_freed;
wdsv004_text_owner *test_owner;
static wdsv004_text_block allocate(void *context,uint32_t n){
 wdsv004_text_block b={test_arena,n};
 test_allocations++;test_requested=n;
 if(context!=(void *)0x1234)b.extent=0;
 if(test_mode==1){b.data=0;b.extent=0;}
 if(test_mode==2)b.extent=n-1;
 if(test_mode==3)b.extent=n+1;
 if(test_mode==4)b.data=(uint8_t *)test_alias;
 if(test_mode==5){b.data=0;b.extent=1;}
 if(test_mode==7){b.data=(uint8_t *)test_alias;b.extent=n-1;}
 if(test_mode==8){b.data=(uint8_t *)test_alias;b.extent=0;}
 if(test_mode==6)test_reentry=(uint32_t)wdsv004_text_dispose(test_owner);
 return b;
}
static void release(void *context,uint8_t *p){
 test_releases++;test_freed=(uintptr_t)p;
 test_reentry=context==(void *)0x1234?(uint32_t)wdsv004_text_dispose(test_owner):99;
}
wdsv004_text_allocator test_allocator={(void *)0x1234,allocate,release};
