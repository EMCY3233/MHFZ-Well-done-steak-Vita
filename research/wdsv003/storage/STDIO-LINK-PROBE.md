# Enlace mínimo: fallo reproducido sin ejecución

27-10-2026. El enlace del objeto private_files junto a private_paths contra libSceLibc_stub, sin bibliotecas por defecto, falla con dos referencias no resueltas a __errno dentro de wdsv_read_slot. Las seis dependencias stdio y wdsv_slot_path ya no figuran entre las referencias pendientes de este enlace. No se produjo un ejecutable válido.

Reproducción desde la raíz, con el GCC del SDK local:

```
arm-vita-eabi-gcc -mthumb -mcpu=cortex-a9 -mfloat-abi=soft -Os -ffreestanding -fno-builtin -c research/wdsv003/storage/private_paths.c -o research/wdsv003/storage/private_paths-dependency.o
arm-vita-eabi-gcc -nostdlib -Wl,-e,wdsv_read_slot research/wdsv003/storage/private_files-dependency.o research/wdsv003/storage/private_paths-dependency.o -lSceLibc_stub -o research/wdsv003/storage/stdio-link-probe.elf
```

El objeto private_files se compila según STDIO-LINKAGE.md. En PowerShell se debe entrecomillar el argumento `-Wl,-e,wdsv_read_slot`; el primer intento sin comillas fue rechazado por el intérprete y no constituye un resultado del enlazador. El intento corregido devuelve código 1 del enlazador con las dos referencias indicadas.

Fuente private_files.c SHA-256 `5017b401c1e39e649821d9bcedec2af31ef954b459a8e2cbf8d9c6ab480487bb`; encabezado SDK sys/errno.h SHA-256 `29855b0cb77ec38fd7c2e5a6ec947b2d01cd8c8991af01f76bf080ec22e2dd5e`. No es necesario publicar objetos ni bibliotecas para verificar el resultado.

El encabezado stdio local declara FILE mediante __FILE y expone interfaces de newlib con struct _reent. Resolver nombres de símbolos SceLibc no prueba que todos los contratos sean compatibles. El backend no accede a campos FILE, pero eso tampoco valida códigos de error o manejo interno de la biblioteca.

Se descarta como arreglo automático introducir un alias entre localizadores errno o enlazar ambas familias C sin revisar. El próximo cambio debe definir una frontera explícita de E/S: callbacks nativos con resultados propios ausente/error/longitud, manteniendo los contratos de recuperación existentes. Esto permite revisar traducción de errores sin afirmar compatibilidad de FILE ni cargar bibliotecas comerciales. Sigue pendiente su implementación y contraste con las declaraciones VitaSDK.

No se ejecutó código ARM, cliente ni consola. El punto de entrada de esta orden solo permite al enlazador construir la prueba; no se propone como entrada de una aplicación.