#include "private_paths.h"
static const char *paths[3][2]={
 {"ux0:data/MHFZL0001/wdsv003/ini-a.bin","ux0:data/MHFZL0001/wdsv003/ini-b.bin"},
 {"ux0:data/MHFZL0001/wdsv003/pri-a.bin","ux0:data/MHFZL0001/wdsv003/pri-b.bin"},
 {"ux0:data/MHFZL0001/wdsv003/character-a.bin","ux0:data/MHFZL0001/wdsv003/character-b.bin"}
};
const char *wdsv_slot_path(uint32_t logical,uint32_t slot){
 if(logical>2||slot>1)return 0;
 return paths[logical][slot];
}
