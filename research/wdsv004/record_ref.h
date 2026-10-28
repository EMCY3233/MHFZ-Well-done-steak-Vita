#ifndef WDSV004_RECORD_REF_H
#define WDSV004_RECORD_REF_H
#include "manifest_reader.h"
typedef int (*wdsv004_digest_fn)(const uint8_t *,uint32_t,uint8_t[32]);
typedef struct {uint32_t state,length;const uint8_t *payload;} wdsv004_view;
/* Digest callback must compute SHA256 and return 0 only on success.
 * Input/ref/output must be valid, disjoint, immutable during verification/use.
 * Returned view borrows input memory. No file lookup or copying takes place.
 * Failure leaves view unchanged. Does not accept absent entries (no record).
 * Structural 512000 payload ceiling does not change backend capacity. */
int wdsv004_resolve_record(const wdsv004_ref *,const uint8_t *,uint32_t,
                          wdsv004_digest_fn,wdsv004_view *);
#endif