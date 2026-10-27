# Importaciones del ejecutable real

27-10-2026. imports.py lee el ELF derivado original y recorre sus descriptores PRX sin Ghidra, sin aplicar relocaciones ni modificar bytes. Usa las estructuras de referencia de VitaLoaderRedux local; exige el hash del ELF ya inventariado. No genera un parche.

El campo e_entry codifica segmento/desplazamiento hacia SceModuleInfo versión 6, localizado en VA 823d2aa0. La tabla de importaciones cubre 823d2b1c–823d326c: **36 descriptores de biblioteca y 476 funciones**. La lista anterior de 32 bibliotecas procedía de mensajes parciales del log Ghidra; no era un inventario exhaustivo. La nueva cifra describe los descriptores realmente recorridos, no disponibilidad de todas las implementaciones en VitaOS.

El parser enlaza ocho operaciones críticas con su biblioteca, NID, stub y celda de puntero. Ejemplos: SlotDelete NID 266a7646, DataSave 607647ba, LoadExec e6774abc e IoOpen 6c60ac61. Esos cuatro nombres/NID se corroboran en la base local vita-headers db/360; el resto se conserva como contraste con la resolución Ghidra previa. Atención: IoOpen aparece en SceLibKernel, mientras IoRead/IoClose están en SceIofilemgr; no asumir una única biblioteca de E/S.

## Consecuencia para integrar sin plugins

Ahora existen ubicaciones verificables para estudiar mediación de importaciones en una copia: stubs y sus celdas están identificados mediante dos rutas de evidencia. **Cambiar una celda no está probado como mecanismo de intercepción.** El cargador puede procesar relocaciones y enlazar stubs; faltan permisos de memoria, momento de instalación, alcance de llamadas indirectas y restauración de instrucciones/relocaciones. Tampoco basta mediar estas ocho funciones: quedan FIOS, red/NP y otros accesos ya documentados.

El RVA start_entry de SceModuleInfo es 011409dc. No se trata e_entry como si fuera la dirección normal de main, ni se anuncia un arranque offline por localizar metadatos. Antes de insertar código deben analizarse la entrada de módulo, disposición del espacio añadido y relocaciones asociadas. No se ha creado SELF/VPK modificado ni llamado al cargador real.

imports.json contiene únicamente hashes, direcciones, nombres de bibliotecas, NID y cantidades autorizados. Las tablas/binarios completos siguen locales. Pendiente probar límites de entradas sintéticas del parser antes de usarlo para decisiones de transformación.
