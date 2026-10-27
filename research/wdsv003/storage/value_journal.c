#include "value_journal.h"
int wdsv_load_value(mhfz_save_journal *j,uint8_t *buf,uint32_t cap,wdsv_value *out){
 uint32_t size=0;wdsv_value v;int result;
 if(!j||!out){if(j)j->ready=0;return -2;}
 result=mhfz_journal_load_strict(j,buf,cap,&size);
 if(result<=0)return result;
 if(wdsv_read_value(buf,size,&v)!=0){j->ready=0;return -1;}
 *out=v;return v.deleted?2:1;
}
int wdsv_commit_value(mhfz_save_journal *j,uint8_t *buf,uint32_t cap,const wdsv_value *v){
 int n=wdsv_pack_value(buf,cap,v);
 if(n<0)return n;
 return mhfz_journal_commit(j,buf,(uint32_t)n);
}
