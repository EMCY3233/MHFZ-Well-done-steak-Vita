#ifndef WDSV_AUDITED_STORE_H
#define WDSV_AUDITED_STORE_H
#include "value_journal.h"
typedef struct {uint32_t logical,operation,phase;int32_t result;uint32_t length,sequence;} wdsv_audit_event;
typedef struct {
 mhfz_save_journal *journal;uint8_t *work;uint32_t capacity,logical;
 wdsv_audit_event *events;uint32_t event_capacity,event_count,sequence;
} wdsv_audited_store;
/* Append-only RAM audit. Reserves start/end before effects; returns -3 if full.
 * No payload, paths, identity or tokens logged. Caller owns valid disjoint
 * buffers and exclusive access. NOT persistent across power loss/restart. */
int wdsv_audited_commit(wdsv_audited_store *,const wdsv_value *);
#endif
