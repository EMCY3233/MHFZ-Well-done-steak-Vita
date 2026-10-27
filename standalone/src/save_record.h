#ifndef MHFZ_SAVE_RECORD_H
#define MHFZ_SAVE_RECORD_H
#include <stdint.h>
typedef struct {
    uint32_t sequence,length;const uint8_t *payload;
} mhfz_save_record;
/* Private lab container, not an original Frontier format. CRC is for accidental
 * corruption only. Sequence starts at 1. Nonempty payload <=1 MiB.
 * Separate inputs/outputs required. Failures leave outputs unchanged.
 */
int mhfz_pack_save_record(uint8_t *dst,uint32_t capacity,const mhfz_save_record *record);
int mhfz_read_save_record(const uint8_t *src,uint32_t size,mhfz_save_record *record);
#endif
