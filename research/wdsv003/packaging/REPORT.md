# WDSV-003: ejecutable, recursos y empaquetado

27-10-2026. Inventario estático reproducible; no paquete instalable ni lanzamiento. `inventory.py` solo lee los dos ejecutables indicados, manifiesto histórico y log Ghidra; emite metadatos y hashes, nunca bytes comerciales.

## Comprobación del contenedor real

- SELF rePatch: 15.176.628 bytes, SHA-256 `a5dac30c97eb87c4ab0e99b272a93752501114e6b5072159c6222857e4ac3fa3`.
- ELF derivado: 35.814.152 bytes, SHA-256 `2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d`.
- ELF32 little endian, ARM (40), tipo 0xfe04; sin tabla de secciones declarada. Cinco program headers. La cabecera ELF y tabla de program headers coinciden con sus equivalentes embebidos en SELF.
- Los cinco segmentos zlib descomprimidos vuelven a coincidir byte a byte con sus regiones del derivado. Se trabaja en memoria: no se reescribe el derivado.
- Dos PT_LOAD: archivos de 28.483.284 y 1.614.524 bytes; tamaños de memoria 28.483.292 y 25.829.404. Esto no es una medida del consumo total del proceso: faltan heap, recursos, servicios, pilas y GPU.
- Dos PT_SCE_RELA de 5.107.260 y 595.368 bytes y un PT_SCE_VERSION de 13.468 bytes. Los segmentos de relocaciones existen y coinciden; no se han validado/aplicado individualmente sus registros en esta herramienta.
- Persisten dos anomalías previas: SELF declara 15.175.780 bytes frente a 15.176.628 reales; el rango comprimido del segmento cero incluye 21 bytes posteriores al fin del flujo zlib. Que el contenido descomprimido coincida no explica esas discrepancias ni certifica que reempaquetar funcione.

La entrada ELF (`20785824`, no una dirección convencional asumida) no se convierte en punto de entrada por intuición. La base Ghidra aplica interpretaciones/relocaciones de análisis; sus bytes no deben copiarse como un ejecutable reconstruido. El derivado no está certificado como equivalente ejecutable.

## Dependencias y recursos

`inventory.json` enumera 32 nombres de bibliotecas que el log de importación Ghidra reportó, entre ellas AppUtil, FIOS2, red/HTTP/SSL, NP Manager/Common/Trophy/Activity/Utility, GXM/display, audio, libc y kernel. Son dependencias candidatas identificadas por el cargador: el mensaje «not found in project» significa que Ghidra no enlazó archivos adicionales, no que falten en la Vita. No es una resolución exhaustiva NID a implementación ni una lista de todo lo inicializado en cada arranque.

El manifiesto conservado contabiliza app: 4492 archivos/2.166.676.271 bytes; patch: 3666/2.934.729.913; rePatch: 103/111.084.243. Estos son inventarios históricos, no precedencia de montajes observada. App 01.00 Frontier G y patch 01.99 Frontier Z tienen el mismo TITLE_ID PCSG00350. No se fusionan automáticamente ni se asume que app+patch+rePatch sean una distribución independiente lista para instalar.

Las aperturas FIOS y rutas `app0:` necesitan resolverse dentro de una copia privada: los archivos ausentes pueden activar reintentos. La lista de recursos obligatorios de arranque sigue pendiente de resolución dinámica o de un trazado estático más completo. Las coincidencias de recursos PC no sustituyen esta verificación.

## Relanzamiento y operaciones críticas

La cadena `app0:eboot.bin` está en offset de archivo `0x17f3698`, VA `0x827f35b8` según PT_LOAD. Coincide con el argumento de `sceAppMgrLoadExec` del pseudocódigo conservado de `821290b6`, condicionado a `82128314() == 1`. La ruta es relativa al montaje app0; no contiene aquí el ID original. Eso **no demuestra aislamiento**: falta garantizar qué app0 quedó montado y auditar rutas construidas/cargadas fuera de estos literales. La herramienta enumera también `savedata0:`, PRI-DATA/INI-DATA y el identificador NP original.

Antes de parchear esta llamada se deben validar las instrucciones originales del punto concreto, preservar relocaciones asociadas y definir qué resultado registra el adaptador cuando rechaza un destino. No se emite éxito artificial ni se publica un parche sin validación.

## Propuesta de empaquetado y condiciones previas

Propuesta condicionada, todavía sin VPK del cliente:

1. Crear staging privado, fuera del árbol original, con manifiesto de procedencia/elección de cada recurso. El ensamblado de capas debe ser una decisión explícita documentada; no activar plugins ni apoyarse implícitamente en rePatch del título original.
2. Usar identidad propia coherente en metadatos y contexto de ejecución. No basta cambiar TITLE_ID visible: los accesos AppUtil/savedata y todo camino de escritura/borrado han de quedar resueltos hacia almacenamiento exclusivo o rechazados con resultados coherentes.
3. Seleccionar entre conservar el SELF original en la copia o reconstruir uno modificado solo después de verificar formato, metadatos, importaciones y relocaciones. El resultado de `vita-make-fself` sobre homebrew no certifica compatibilidad con este PRX comercial. No se ha ejecutado el empaquetador sobre él.
4. Integrar observación de guardado/borrado/apertura/relanzamiento antes del lanzamiento. Registrar operación, identificador sintético, resultado y transición; nunca credenciales ni contenido original.
5. Rechazar el artefacto si existen rutas críticas no mediadas, recursos incompletos, metadatos/relocaciones sin resolver, destino LoadExec fuera de la copia o dependencias de red no controladas. No producir un VPK anunciado como seguro por superar solo estas cuatro pruebas del lector.
6. Emitir hash/manifiesto de paquete y revisión final. Solicitar autorización específica únicamente cuando exista un artefacto revisable y se haya demostrado aislamiento suficiente. Instalación/ejecución física permanecen fuera de esta orden.

Reversión prevista: hasta empaquetar, basta conservar o descartar exclusivamente el staging y herramientas propias; no hay cambios de consola que revertir. La reversión física futura tendrá que identificar y desinstalar solo el ID experimental y retirar solo su carpeta de datos, con rutas verificadas. No se prescribe borrar PCSG00350.

## Verificación y límites

`test_inventory.py`: cuatro pruebas propias de rangos, ELF truncado/ELF64 y conversión offset→VA que excluye BSS/no LOAD; todas pasan. El inventario real pasa cinco comparaciones de segmentos. No son pruebas de ejecución, seguridad efectiva del cliente ni aceptación por el cargador Vita.

Fuentes locales: `research/COMPARACION-REAL-VITA-PC.md`, `vita-static-inventory.json`, `vita-existing-copy-manifest.csv`, `vita-sfo-metadata.json`, `ghidra-vita-import.log`, `client-isolation-storage-entrypoints.json`; estructuras/constantes de `sources/VitaLoaderRedux/src/main/java/vitaloaderredux/elf/ElfPhdr.java`. Conserva metadatos, no ejecutables comerciales, en una eventual PR.
