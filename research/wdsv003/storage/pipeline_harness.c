/* Test-only wiring. Not a game hook, installed app or production context. */
#include "private_files.h"
#include "value_journal.h"
#ifdef WDSV_AUDIT_LOG
#include "audited_store.h"
static wdsv_audited_store audit_stores[3];
static wdsv_audit_event audit_events[3][64];
static uint32_t audit_initialized[3];
#endif
static mhfz_save_journal journals[3];
#ifndef WDSV_PIPELINE_CAPACITY
#define WDSV_PIPELINE_CAPACITY 4096
#endif
static uint8_t scratch[3][WDSV_PIPELINE_CAPACITY],work[3][WDSV_PIPELINE_CAPACITY];
static uint32_t logical_ids[3]={0,1,2};
wdsv_value pipeline_value;
static mhfz_save_journal *get(uint32_t logical){
 mhfz_save_journal *j;
 if(logical>2)return 0;
 j=&journals[logical];j->scratch=scratch[logical];j->scratch_capacity=WDSV_PIPELINE_CAPACITY;
 j->read=wdsv_read_slot;j->write=wdsv_write_slot;j->context=&logical_ids[logical];return j;
}
#ifdef WDSV_AUDIT_LOG
static wdsv_audited_store *get_audit(uint32_t logical){
 wdsv_audited_store *s;if(logical>2)return 0;
 s=&audit_stores[logical];s->journal=get(logical);s->work=work[logical];
 s->capacity=WDSV_PIPELINE_CAPACITY;s->logical=logical;s->events=audit_events[logical];
 if(!audit_initialized[logical]){s->event_capacity=64;audit_initialized[logical]=1;}
 return s;
}
int pipeline_audit_limit(uint32_t logical,uint32_t count){
 wdsv_audited_store *s=get_audit(logical);if(!s||count>64)return -1;
 s->event_capacity=count;return 0;
}
int pipeline_audit_count(uint32_t logical){
 wdsv_audited_store *s=get_audit(logical);return s?(int)s->event_count:-1;
}
const wdsv_audit_event *pipeline_audit_event(uint32_t logical,uint32_t index){
 wdsv_audited_store *s=get_audit(logical);return s&&index<s->event_count?&s->events[index]:0;
}
#endif
int pipeline_load(uint32_t logical){
 mhfz_save_journal *j=get(logical);
 if(!j)return -2;
 return wdsv_load_value(j,work[logical],WDSV_PIPELINE_CAPACITY,&pipeline_value);
}
int pipeline_commit(uint32_t logical,const uint8_t *data,uint32_t size,uint32_t deleted){
 wdsv_value v;mhfz_save_journal *j=get(logical);
 if(!j)return -1;
 v.deleted=deleted;v.length=size;v.payload=data;
#ifdef WDSV_AUDIT_LOG
 return wdsv_audited_commit(get_audit(logical),&v);
#else
 return wdsv_commit_value(j,work[logical],WDSV_PIPELINE_CAPACITY,&v);
#endif
}
