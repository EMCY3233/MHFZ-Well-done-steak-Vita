#ifndef WDSV004_MANIFEST_READER_H
#define WDSV004_MANIFEST_READER_H
#include <stdint.h>
typedef struct { uint32_t logical,state,slot,sequence,record_bytes; uint8_t digest[32]; } wdsv004_ref;
typedef struct { uint32_t generation; wdsv004_ref members[3]; } wdsv004_manifest;
/* Own private format only. Valid disjoint input/output memory is required.
 * 0 success, -1 malformed/null. Failure leaves output unchanged.
 * Structural bounds do not raise the native storage backend's size limit.
 * No record resolution, SHA verification, I/O, or generation selection yet. */
int wdsv004_read_manifest(const uint8_t *,uint32_t,wdsv004_manifest *);
#endif