#ifndef WDSV004_SHA256_H
#define WDSV004_SHA256_H
#include <stdint.h>
/* One-shot private-record digest, maximum 512036 bytes. Returns 0/-1.
 * NULL input allowed only with size zero. Output 32 bytes, unchanged on error.
 * Valid disjoint buffers and immutable input are caller preconditions. */
int wdsv004_sha256(const uint8_t *,uint32_t,uint8_t *);
#endif