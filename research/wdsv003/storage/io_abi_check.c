/* Compile-only SDK contract checks; no target calls or entry point. */
#include <psp2/io/fcntl.h>
#define SAME(expr, type) _Static_assert(__builtin_types_compatible_p(__typeof__(expr), type), #expr)
SAME(&sceIoOpen, SceUID (*)(const char *, int, SceMode));
SAME(&sceIoRead, SceSSize (*)(SceUID, void *, SceSize));
SAME(&sceIoWrite, SceSSize (*)(SceUID, const void *, SceSize));
SAME(&sceIoClose, int (*)(SceUID));
_Static_assert(sizeof(SceUID)==4, "descriptor width");
_Static_assert(sizeof(SceSize)==4 && (SceSize)-1>0, "unsigned size32");
_Static_assert(sizeof(SceSSize)==4 && (SceSSize)-1<0, "signed result32");