#ifndef MHFZ_SAVE_JOURNAL_H
#define MHFZ_SAVE_JOURNAL_H
#include <stdint.h>
/* read: record length, -1 missing, -2 I/O failure; write: 0 success.
 * Callbacks may only access the requested private slot (0 or 1).
 */
typedef int (*mhfz_slot_read)(void *,uint32_t,uint8_t *,uint32_t);
typedef int (*mhfz_slot_write)(void *,uint32_t,const uint8_t *,uint32_t);
typedef struct {
    uint8_t *scratch;uint32_t scratch_capacity;
    mhfz_slot_read read;mhfz_slot_write write;void *context;
    uint32_t sequence,slot,ready;
} mhfz_save_journal;
/* Load once before commit: 1 recovered, 0 both absent, -1 corrupt/no valid,
 * -2 I/O/configuration. On failure size=0 and destination is unspecified.
 * Buffers must be distinct. No sequence wrapping; ties choose slot 0.
 */
int mhfz_journal_load(mhfz_save_journal *,uint8_t *,uint32_t,uint32_t *);
/* Same contract, but equal sequence with different contents is rejected and
 * leaves writes disabled. Identical equal-sequence copies remain acceptable. */
int mhfz_journal_load_strict(mhfz_save_journal *,uint8_t *,uint32_t,uint32_t *);
/* Suitable as save_service commit callback. I/O failure disables further commits
 * until reload; old slot remains untouched. A complete unacknowledged record
 * may be selected on restart after an uncertain write/verification failure.
 */
int mhfz_journal_commit(void *,const uint8_t *,uint32_t);
#endif
