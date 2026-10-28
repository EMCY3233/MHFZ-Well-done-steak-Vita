#include "text_handoff.h"
static int range(uintptr_t p,uint32_t n){return p<=UINTPTR_MAX-n;}
static int overlap(uintptr_t a,uint32_t an,uintptr_t b,uint32_t bn){
 return an&&bn&&a<b+bn&&b<a+an;
}
static void clear(wdsv004_text_owner *o,uint32_t state){
 o->data=0;o->size=0;o->extent=0;o->context=0;o->release=0;o->state=state;
}
int wdsv004_text_prepare(wdsv004_text_owner *owner,const uint8_t *source,
 uint32_t source_extent,uint32_t expected,uint32_t completed,uint32_t capacity,
 const wdsv004_text_allocator *allocator){
 wdsv004_text_block block;wdsv004_text_allocator callbacks;uint32_t i,needed;
 uintptr_t src=(uintptr_t)source,dst;
 if(!owner||owner->state!=WDSV004_TEXT_EMPTY||!allocator||
    !allocator->allocate||!allocator->release)return WDSV004_TEXT_INVALID;
 if(expected!=completed||completed>capacity||capacity>WDSV004_TEXT_MAX||
    source_extent<completed||(!source&&source_extent)||
    !range(src,source_extent)||!range((uintptr_t)owner,sizeof(*owner)))return WDSV004_TEXT_INVALID;
 if(overlap(src,source_extent,(uintptr_t)owner,sizeof(*owner)))return WDSV004_TEXT_INVALID;
 for(i=0;i<completed;i++)if(!source[i])return WDSV004_TEXT_INVALID;
 callbacks=*allocator;needed=completed+1;owner->state=WDSV004_TEXT_BUSY;
 block=callbacks.allocate(callbacks.context,needed);
 if(!block.data){
  clear(owner,block.extent?WDSV004_TEXT_FAILED:WDSV004_TEXT_EMPTY);
  return block.extent?WDSV004_TEXT_BAD_ALLOCATOR:WDSV004_TEXT_NO_MEMORY;
 }
 dst=(uintptr_t)block.data;
 /* Do not free a borrowed source/handle returned by a broken allocator.
  * No ownership is transferred; this terminal state requires investigation. */
 if((source&&dst==src)||!range(dst,1)||!range(dst,block.extent)||overlap(dst,1,src,source_extent)||
    overlap(dst,1,(uintptr_t)owner,sizeof(*owner))||
    overlap(dst,block.extent,src,source_extent)||
    overlap(dst,block.extent,(uintptr_t)owner,sizeof(*owner))){
  clear(owner,WDSV004_TEXT_FAILED);return WDSV004_TEXT_BAD_ALLOCATOR;
 }
 if(block.extent!=needed){
  clear(owner,WDSV004_TEXT_FAILED);
  callbacks.release(callbacks.context,block.data);
  return WDSV004_TEXT_BAD_ALLOCATOR;
 }
 for(i=0;i<completed;i++)block.data[i]=source[i];
 block.data[completed]=0;
 owner->data=block.data;owner->size=completed;owner->extent=needed;
 owner->context=callbacks.context;owner->release=callbacks.release;
 owner->state=WDSV004_TEXT_OWNED;return WDSV004_TEXT_OK;
}
int wdsv004_text_move(wdsv004_text_owner *destination,wdsv004_text_owner *source){
 if(!destination||!source||destination==source||
    !range((uintptr_t)destination,sizeof(*destination))||
    !range((uintptr_t)source,sizeof(*source))||
    overlap((uintptr_t)destination,sizeof(*destination),(uintptr_t)source,sizeof(*source))||
    destination->state!=WDSV004_TEXT_EMPTY||source->state!=WDSV004_TEXT_OWNED)
  return WDSV004_TEXT_INVALID;
 if(!source->data||!source->release||!range((uintptr_t)source->data,source->extent)||
    overlap((uintptr_t)destination,sizeof(*destination),(uintptr_t)source->data,source->extent))
  return WDSV004_TEXT_INVALID;
 *destination=*source;clear(source,WDSV004_TEXT_MOVED);return WDSV004_TEXT_OK;
}
int wdsv004_text_dispose(wdsv004_text_owner *owner){
 wdsv004_text_release release;void *context;uint8_t *data;
 if(!owner||owner->state!=WDSV004_TEXT_OWNED||!owner->data||!owner->release)
  return WDSV004_TEXT_INVALID;
 release=owner->release;context=owner->context;data=owner->data;
 /* Publish terminal state before invoking external cleanup (reentrant safe). */
 clear(owner,WDSV004_TEXT_RELEASED);release(context,data);return WDSV004_TEXT_OK;
}
