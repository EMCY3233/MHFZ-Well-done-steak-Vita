#ifndef WDSV004_PRIVATE_STORE_H
#define WDSV004_PRIVATE_STORE_H
#include "batch_commit.h"
/* Caller-owned persistent storage; NEVER allocate this ~961 KiB on stack.
 * parent_verified must be 1 only after independent private-directory identity
 * and exclusive ownership checks. This flag is not evidence of those checks.
 * No mkdir, mount, migration, initialization or lock is implemented. */
typedef struct {uint32_t parent_verified;uint8_t manifests[2][188];uint8_t records[3][2][163876];} wdsv004_private_pool;
int wdsv004_private_read(void *,wdsv004_buffer[2],wdsv004_buffer[3][2]);
int wdsv004_private_record(void *,uint32_t,uint32_t,const wdsv004_buffer *);
int wdsv004_private_manifest(void *,uint32_t,const wdsv004_buffer *);
#endif