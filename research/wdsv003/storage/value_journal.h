#ifndef WDSV_VALUE_JOURNAL_H
#define WDSV_VALUE_JOURNAL_H
#include "save_journal.h"
#include "value_body.h"
/* Return 0 absent, 1 live, 2 deleted; negative error. Output changes only for 1/2.
 * buf and journal scratch must not overlap. Invalid inner value disables writes. */
int wdsv_load_value(mhfz_save_journal *,uint8_t *,uint32_t,wdsv_value *);
/* Pack into private work buffer then commit through the existing journal.
 * Buffers and payload must be separate. Return 0 only after verified commit. */
int wdsv_commit_value(mhfz_save_journal *,uint8_t *,uint32_t,const wdsv_value *);
#endif
