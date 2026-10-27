#ifndef WDSV_PRIVATE_FILES_H
#define WDSV_PRIVATE_FILES_H
#include "private_paths.h"
/* Context is a valid pointer to logical uint32 (0/1/2), not a filename.
 * Parent must exist. No directory creation/deletion, no concurrent access. */
int wdsv_read_slot(void *,uint32_t,uint8_t *,uint32_t);
int wdsv_write_slot(void *,uint32_t,const uint8_t *,uint32_t);
#endif
