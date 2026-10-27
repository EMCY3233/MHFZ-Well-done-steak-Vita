# Alternativa nativa sin FILE ni errno

27-10-2026. private_io.c/h implementan callbacks experimentales con nombres distintos de la versión stdio. No sustituyen todavía el backend del diario ni interceptan al cliente. Solo utilizan rutas constantes de private_paths y cuatro APIs nativas.

El enlace mínimo ARM/Thumb con libSceLibKernel_stub y libSceIofilemgr_stub pasa, con -nostdlib; nm -u no muestra símbolos pendientes. No se necesitan FILE, errno ni libc para esta unidad. Es una comprobación de enlace de un ELF propio, no ejecución ni paquete Vita válido.

La definición primaria de [Vita3K io/io.h](https://github.com/Vita3K/Vita3K/blob/17a8b34017a94f4a5914cc0700ae061a3c506a06/vita3k/io/include/io/io.h) fija SCE_ERROR_ERRNO_ENOENT=0x80010002 y lo describe como archivo o directorio ausente. io.cpp del mismo commit usa ese símbolo en apertura inexistente. Se toma como hipótesis documentada del emulador; falta contraste físico. El padre privado debe existir y haber sido comprobado: ese retorno por sí solo no distingue archivo de directorio ausente.

Se comprueban retornos negativos antes de convertir longitudes, se rechazan sobrelongitudes y escritura sin progreso; la lectura detecta bytes adicionales al alcanzar capacidad. Todo descriptor abierto se cierra aun tras error y un cierre negativo impide éxito. Se conservan límites de registro y contratos de retorno del diario. No hay creación de directorios, borrado, sincronización con flags desconocidos ni acceso a montaje original.

Validación actual: compilación con avisos como errores y enlace sin referencias pendientes. **Las pruebas de comportamiento con errores inyectados aún están pendientes.** No usar este resultado para sustituir la evidencia sintética anterior ni declarar recuperación nativa integrada. Próximo paso: ejecutar únicamente este código propio en emulación ARM con APIs sustituidas para verificar ausencia, lecturas parciales, errores, sobrelongitudes y cierre; después conectar al diario si pasa.