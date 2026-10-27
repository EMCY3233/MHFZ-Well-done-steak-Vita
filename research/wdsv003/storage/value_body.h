#ifndef WDSV_VALUE_BODY_H
#define WDSV_VALUE_BODY_H
#include <stdint.h>
typedef struct { uint32_t deleted,length; const uint8_t *payload; } wdsv_value;
/* Private envelope to place INSIDE the existing CRC/sequence journal record.
 * No disk I/O. Separate non-overlapping inputs/outputs. Error leaves output intact.
 * A tombstone must have zero payload. Empty live data is distinct from deletion. */
int wdsv_pack_value(uint8_t *out,uint32_t capacity,const wdsv_value *value);
int wdsv_read_value(const uint8_t *in,uint32_t size,wdsv_value *value);
#endif
