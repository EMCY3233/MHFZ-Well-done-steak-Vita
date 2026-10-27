#include "audited_store.h"
int wdsv_audited_commit(wdsv_audited_store *s,const wdsv_value *v){
 wdsv_audit_event *a,*b;int result;
 if(!s||!v||!s->journal||!s->work||!s->events||s->logical>2)return -3;
 if(s->event_count>s->event_capacity||s->event_capacity-s->event_count<2||s->sequence==0xffffffffU)return -3;
 a=&s->events[s->event_count];b=a+1;s->event_count+=2;s->sequence++;
 a->logical=s->logical;a->operation=v->deleted==1?2:v->deleted==0?1:0;a->phase=1;a->result=0;
 a->length=v->length;a->sequence=s->sequence;*b=*a;b->phase=0;b->result=-3;
 result=wdsv_commit_value(s->journal,s->work,s->capacity,v);
 b->result=result;b->phase=2;return result;
}
