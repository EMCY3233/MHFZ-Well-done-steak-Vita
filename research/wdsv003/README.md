# WDSV-003: aislamiento previo al cliente real

Preparación iniciada el 27-10-2026. No se ha instalado ni ejecutado el cliente. El hito físico permanece BLOQUEADO hasta demostrar aislamiento en la integración real.

## Estado consolidado a las 16:08 UTC

Existe un backend nativo **propio y separado del cliente**: rutas privadas, diario con CRC/secuencia y marca de borrado. [La cadena nativa al máximo](storage/FULL-NATIVE-PIPELINE.md) pasa39 casos en emulación ARM con APIs/archivos sustituidos en RAM. Los conjuntos de34 casos del adaptador y24 de la cadena pequeña comparten cobertura; no sumarlos como pruebas independientes. No hay prueba VitaOS ni garantía de pérdida eléctrica. La alternativa stdio tiene un [bloqueo de enlace errno](storage/STDIO-LINKAGE.md); la alternativa nativa enlaza sin FILE/errno.

Los lectores Python suman46 pruebas. CI ejecuta lectores y política Python; no ejecuta los ensayos ARM locales. El backend aún no controla los accesos del cliente ni sus estados asíncronos.

El análisis más reciente sustituye alcances parciales del inventario inicial: [36 descriptores/476 importaciones](packaging/IMPORTS.md), [799 inicializadores definidos y límites transitivos](packaging/INITIALIZER-COVERAGE.md), y [475219 relocaciones coherentes en las bases originales](packaging/ZERO-DELTA.md). Las ocho celdas seleccionadas tienen relocación ABS32. No se aplicó un parche.

El [flujo de entrada](packaging/ENTRY-CONTROL-FLOW.md) requiere controlar efectos antes de inicializadores y no asumir retorno ordinario del helper. [Añadir un segmento](packaging/SELF-TABLE-CAPACITY.md) exige redisponer tablas; no cabe ampliar las existentes in situ. El digest de control4 coincide con el ELF derivado, pero el tamaño declarado y la cola de21bytes mantienen bloqueada la transformación. [El padding del generador](packaging/GENERATOR-COMPARISON.md) es una política de representación, no un formato universal ni autorización de reparar el original.

La [unión de capas](packaging/LAYER-UNION.md) y [fronteras de staging](packaging/STAGING-BOUNDARIES.md) son hipótesis de planificación. No hay staging aprobado ni VPK del cliente. Faltan identidad AppUtil/montajes, cobertura de lecturas/escrituras/borrado/relanzamiento, alojamiento/activación del adaptador y reconstrucción verificable del contenedor.

Siguiente prioridad: política explícita de representación SELF y revisión de metadatos dependientes del ELF; después resolver alojamiento/entrada. No repetir las pruebas de contadores ni nuevos backends equivalentes por el mero tamaño. La primera ejecución física sigue requiriendo autorización específica posterior y demostración previa de aislamiento.

## Cambio de alcance

00.03 aporta evidencia física de almacenamiento sintético. 00.04 no es requisito. Esta fase prepara controles para el cliente comercial copiado localmente, sin publicar sus bytes, pseudocódigo ni recursos.

## Mapa contrastado

Fuente: ELF derivado de rePatch SHA-256 `2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d`. Su relación ejecutable/relocada con un paquete nuevo sigue pendiente.

| Punto | Evidencia y límite |
|---|---|
| Inicialización 8213befc | AppUtil recibe estructuras a cero; la API local no ofrece un Title ID explícito en esos parámetros. No se demuestra la identidad efectiva del guardado. |
| Registro 8213c2ea desde 8211b924 | Define entradas de archivos cuando estado +0x90=0; no equivale a escritura. |
| Guardado 8213c7c0 | Requiere estado +0x90=3, con condiciones posteriores y gestión de errores. API en 8213ca8c. |
| Borrado 8213c3ec | Requiere estado +0x90=6; llama SlotDelete(0,0) en 8213c426. Productor inmediato identificado: 8213c222; falta cerrar qué acción solicita ese productor. |
| Relanzamiento 821290b6 | Si 82128314 devuelve 1, LoadExec recibe literal relativo `app0:eboot.bin`, argumento `argument`. No es un destino absoluto al Title ID original; tampoco prueba el montaje efectivo. |
| Recursos 8212d3a0 | Apertura FIOS con ruta de reintento; el archivo ausente puede impedir avanzar. |

Corrección importante del análisis previo: la declaración VitaSDK de SaveDataDataSave tiene cinco parámetros. Las instrucciones originales preparan el quinto en SP+0 antes de la llamada. El pseudocódigo anterior que muestra cuatro no debe usarse como prototipo de un hook. No se ha demostrado todavía el valor del puntero durante ejecución.

El candidato de tabla 82b29960 contiene entradas Thumb 8213c001/8213c049. El análisis dirigido de 8213c048 muestra un destructor que espera estado cero, libera memoria y destruye el objeto; no es un despachador de guardado. No se interpreta el resto de datos contiguos como más entradas sin límites de tabla probados.

## Arquitectura propuesta y bloqueo

Preferir un adaptador dentro del proceso que controle las operaciones de almacenamiento, apertura y relanzamiento antes de alcanzar APIs del sistema. Cada operación debe fallar de forma explícita si no hay ruta autorizada, sin devolver éxito por defecto. El modelo sintético de esta entrega no intercepta el cliente.

La primera integración deberá demostrar cobertura de todas las salidas relevantes, incluidas llamadas indirectas, y rutas de carga/lectura además de escritura/borrado. Mientras esa cobertura, el contenedor ejecutable y los montajes no estén resueltos, no se preparará una prueba física ni se calificará un VPK como seguro.

## Observación prevista

Registro limitado a generación de proceso, secuencia, operación, fase, longitud, código de resultado propio y estado de confirmación. No registrar datos de partida, identidades PSN, tokens, nombres reales ni contraseñas. Los códigos propios deben traducirse a códigos Vita únicamente tras validar firma y semántica de cada llamada. Un rechazo de política nunca cuenta como guardado confirmado.

Eventos mínimos: init, resource_open_failed, save_requested, save_committed, delete_requested, delete_rejected, relaunch_requested, relaunch_rejected y recovery. Persistencia del registro también debe quedar bajo la raíz experimental; si falla, detener la operación que requiera auditoría antes de afirmar éxito.

## Criterios de aceptación y reversión

1. Herramientas propias y pruebas sintéticas revisables: ver subdirectorios storage y packaging.
2. Inventario ELF/SELF e hipótesis de empaquetado: análisis estático, pendiente de validación física.
3. Identidad AppUtil y montajes efectivos: PENDIENTE.
4. Hooks integrados con firma correcta y cobertura de lectura/escritura/borrado/relanzamiento: PENDIENTE.
5. Prototipo ejecutable del cliente real: NO PRODUCIDO.
6. Primera barrera offline observada en Vita: NO EJECUTADA, requiere autorización específica posterior.

Reversión actual: descartar exclusivamente la rama de investigación y las salidas propias generadas. No se ha cambiado ningún archivo de consola. Para una futura prueba, la retirada se limitará al Title ID experimental y su directorio propio después de verificar esas identidades; no ejecutar limpiezas por prefijos ni borrar ranuras del original. Se conservarán manifiestos antes/después.

## Reproducción

`audit_control_sites.py` lee el ELF local seleccionado, exige su hash y exporta ventanas para objdump. Las ventanas binarias, desensamblados y resultados Ghidra se mantienen locales y no se publican. Ninguna herramienta arranca el juego, conecta a Rain ni contacta la consola. Las pruebas de almacenamiento trabajan únicamente con datos sintéticos en directorios temporales.

Riesgo abierto principal: las garantías del modelo no se transfieren automáticamente al cliente. La preparación de WDSV-003 es parcial mientras falten los puntos 3–5.

Continuación 27-10-2026: [productores de solicitudes](STORAGE-REQUEST-PRODUCERS.md) distingue aceptación del trabajo asíncrono y confirmación persistente; identifica 8213c092 para estado 3 y 8213c222 para estado 6.