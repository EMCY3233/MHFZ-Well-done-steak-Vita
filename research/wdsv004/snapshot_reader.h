#ifndef WDSV004_SNAPSHOT_READER_H
#define WDSV004_SNAPSHOT_READER_H
#include "record_ref.h"
typedef struct {const uint8_t *data;uint32_t size;} wdsv004_buffer;
typedef struct {uint32_t generation,manifest_slot;wdsv004_view members[3];} wdsv004_snapshot;
/* All input memory must remain immutable/exclusively owned during validation
 * and use of borrowed views. Arrays have exactly 2 manifests and 3x2 records.
 * 1 complete snapshot, 0 only when both manifests absent (NULL,0), -1 failure.
 * Failure/absence leave output unchanged. Absence is not permission to write.
 * No disk access, batch publication, locks, or native SHA implementation. */
int wdsv004_recover(const wdsv004_buffer[2],const wdsv004_buffer[3][2],
                   wdsv004_digest_fn,wdsv004_snapshot *);
#endif