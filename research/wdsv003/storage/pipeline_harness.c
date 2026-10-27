/* Test-only wiring. Not a game hook, installed app or production context. */
#include "private_files.h"
#include "value_journal.h"
static mhfz_save_journal journals[3];
static uint8_t scratch[3][4096],work[3][4096];
static uint32_t logical_ids[3]={0,1,2};
wdsv_value pipeline_value;
static mhfz_save_journal *get(uint32_t logical){
 mhfz_save_journal *j;
 if(logical>2)return 0;
 j=&journals[logical];j->scratch=scratch[logical];j->scratch_capacity=4096;
 j->read=wdsv_read_slot;j->write=wdsv_write_slot;j->context=&logical_ids[logical];return j;
}
int pipeline_load(uint32_t logical){
 mhfz_save_journal *j=get(logical);
 if(!j)return -2;
 return wdsv_load_value(j,work[logical],4096,&pipeline_value);
}
int pipeline_commit(uint32_t logical,const uint8_t *data,uint32_t size,uint32_t deleted){
 wdsv_value v;mhfz_save_journal *j=get(logical);
 if(!j)return -1;
 v.deleted=deleted;v.length=size;v.payload=data;
 return wdsv_commit_value(j,work[logical],4096,&v);
}
