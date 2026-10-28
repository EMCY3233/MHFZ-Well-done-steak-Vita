#ifndef WDSV004_BATCH_COMMIT_H
#define WDSV004_BATCH_COMMIT_H
#include "batch_plan.h"
typedef struct {uint32_t blocked;} wdsv004_epoch;
typedef struct {
 void *context;
 int (*read_all)(void *,wdsv004_buffer[2],wdsv004_buffer[3][2]);
 int (*write_record)(void *,uint32_t,uint32_t,const wdsv004_buffer *);
 int (*write_manifest)(void *,uint32_t,const wdsv004_buffer *);
} wdsv004_store;
/* Epoch initially {0}, owned exclusively by caller; nonzero blocks all calls.
 * Callbacks return 0 only for acknowledged completion. All supplied buffers
 * immutable, valid and owned until next read_all; replacements immutable for
 * entire call. Final snapshot borrows last-read buffers. No locks or I/O here.
 * 0 confirmed visible snapshot, -1 failed/uncertain; output unchanged on error.
 * Error blocks epoch. Reinitializing requires independent recovery/ownership.
 * Readback does not establish power-loss durability or rollback on failure. */
int wdsv004_commit(wdsv004_epoch *,const wdsv004_store *,const wdsv004_buffer[3],wdsv004_snapshot *);
#endif