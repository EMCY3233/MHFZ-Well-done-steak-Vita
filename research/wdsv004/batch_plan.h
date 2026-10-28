#ifndef WDSV004_BATCH_PLAN_H
#define WDSV004_BATCH_PLAN_H
#include "snapshot_reader.h"
typedef struct {uint32_t manifest_slot,changed_mask,record_slot[3];uint8_t manifest[188];} wdsv004_plan;
/* replacements[3]: (NULL,0) unchanged; otherwise encoded immutable record.
 * Requires exclusive ownership and disjoint output. No I/O or initialization.
 * 0 success, -1 failure; failure leaves output unchanged. Native capacity
 * remains 163840 payload bytes. record_slot is UINT32_MAX when unchanged. */
int wdsv004_prepare(const wdsv004_buffer[2],const wdsv004_buffer[3][2],
                    const wdsv004_buffer[3],wdsv004_digest_fn,wdsv004_plan *);
#endif