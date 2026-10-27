#ifndef WDSV_PRIVATE_PATHS_H
#define WDSV_PRIVATE_PATHS_H
#include <stdint.h>
/* 0 ini, 1 pri, 2 character; each has two private slots. No caller paths. */
const char *wdsv_slot_path(uint32_t logical,uint32_t slot);
#endif
