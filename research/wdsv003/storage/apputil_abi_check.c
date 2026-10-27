/* Compile-time contract only. No exported hook, system call or game bytes. */
#include <stddef.h>
#include <psp2/apputil.h>
typedef int (*save_signature)(SceAppUtilSaveDataFileSlot *,SceAppUtilSaveDataFile *,unsigned int,SceAppUtilSaveDataMountPoint *,SceSize *);
_Static_assert(__builtin_types_compatible_p(__typeof__(&sceAppUtilSaveDataDataSave),save_signature),"five-argument save ABI");
_Static_assert(sizeof(void *)==4,"ARM32 pointers");
_Static_assert(sizeof(SceSize)==4,"size ABI");
_Static_assert(sizeof(SceOff)==8,"offset ABI");
_Static_assert(sizeof(SceAppUtilSaveDataFile)==0x40,"file stride");
_Static_assert(offsetof(SceAppUtilSaveDataFile,filePath)==0,"path offset");
_Static_assert(offsetof(SceAppUtilSaveDataFile,buf)==4,"buffer offset");
_Static_assert(offsetof(SceAppUtilSaveDataFile,bufSize)==8,"size offset");
_Static_assert(offsetof(SceAppUtilSaveDataFile,offset)==16,"64-bit offset alignment");
_Static_assert(offsetof(SceAppUtilSaveDataFile,mode)==24,"mode offset");
_Static_assert(offsetof(SceAppUtilSaveDataFile,progDelta)==28,"progress offset");
_Static_assert(sizeof(SceAppUtilSaveDataSlotParam)==0x34c,"metadata size");
_Static_assert(sizeof(SceAppUtilSaveDataFileSlot)==0x28,"slot descriptor");
_Static_assert(sizeof(SceAppUtilSaveDataMountPoint)==16,"mount context");
