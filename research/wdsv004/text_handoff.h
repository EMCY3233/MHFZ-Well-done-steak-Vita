#ifndef WDSV004_TEXT_HANDOFF_H
#define WDSV004_TEXT_HANDOFF_H
#include <stdint.h>
#define WDSV004_TEXT_MAX 512000U
/* Own interface, NOT a declaration of the commercial client's ABI. */
typedef struct { uint8_t *data; uint32_t extent; } wdsv004_text_block;
typedef wdsv004_text_block (*wdsv004_text_allocate)(void *,uint32_t);
typedef void (*wdsv004_text_release)(void *,uint8_t *);
typedef struct {
 void *context;
 wdsv004_text_allocate allocate;
 wdsv004_text_release release;
} wdsv004_text_allocator;
enum { WDSV004_TEXT_EMPTY=0, WDSV004_TEXT_BUSY=1, WDSV004_TEXT_OWNED=2,
       WDSV004_TEXT_MOVED=3, WDSV004_TEXT_RELEASED=4, WDSV004_TEXT_FAILED=5 };
enum { WDSV004_TEXT_OK=0, WDSV004_TEXT_INVALID=-1,
       WDSV004_TEXT_NO_MEMORY=-2, WDSV004_TEXT_BAD_ALLOCATOR=-3 };
/* Zero initialize once. Never copy an owning handle or modify its fields.
 * Single-threaded/exclusive use; callback context outlives the owning handle.
 * Valid object extents, fresh independent allocations and immutable source
 * throughout prepare are caller obligations. This is not a pointer validator. */
typedef struct {
 uint32_t state;
 uint8_t *data;
 uint32_t size,extent;
 void *context;
 wdsv004_text_release release;
} wdsv004_text_owner;
int wdsv004_text_prepare(wdsv004_text_owner *,const uint8_t *,uint32_t,
                        uint32_t,uint32_t,uint32_t,const wdsv004_text_allocator *);
int wdsv004_text_move(wdsv004_text_owner *,wdsv004_text_owner *);
int wdsv004_text_dispose(wdsv004_text_owner *);
#endif
