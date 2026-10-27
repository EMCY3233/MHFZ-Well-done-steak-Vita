#ifndef WDSV_PRIVATE_IO_H
#define WDSV_PRIVATE_IO_H
#include "private_paths.h"
/* Experimental alternative to private_files, not installed or integrated.
 * Same context/slot contract. Parent directory must already exist and be
 * verified by integration. Missing-file mapping is emulator-source evidence.
 * read: length/-1 absent/-2 error. write: 0 complete/-1 error.
 * Close/readback do not establish power-loss durability. */
int wdsv_io_read_slot(void *,uint32_t,uint8_t *,uint32_t);
int wdsv_io_write_slot(void *,uint32_t,const uint8_t *,uint32_t);
#endif