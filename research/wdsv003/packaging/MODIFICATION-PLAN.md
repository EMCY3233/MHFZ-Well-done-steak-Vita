# Plan de transformación reversible: todavía sin escritor

27-10-2026. Plan derivado de los lectores locales; no se ha producido un ELF modificado, SELF nuevo ni VPK. Fuente ELF SHA-256: `2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d`.

## Decisión actual

No usar los 292 bytes entre LOAD 0 y LOAD 1 como alojamiento. No sustituir solamente las ocho celdas de importación: todas tienen una relocación ABS32 que también debe participar en el cambio. No tratar el resultado de Ghidra como imagen original para generar un parche.

La primera transformación eventual debe ser una salida local nueva y descartable, nunca una modificación in situ. El bloqueo del contenedor descrito en SELF-GATE.md sigue vigente: no reconstruir hasta explicar o gestionar explícitamente el tamaño declarado y los bytes posteriores al flujo zlib. Cambiar el campo de tamaño por sí solo no demuestra validez.

## Contrato requerido del escritor futuro

Cada operación del manifiesto debe declarar: hash del archivo padre, segmento y desplazamiento, longitud, hash de bytes anteriores, clase de cambio, bytes propios de sustitución y razón. Registrar también las relocaciones que intersectan ese intervalo, permisos y referencias afectadas. Los manifiestos que incluyan bytes comerciales permanecen privados; solo los resúmenes técnicos son publicables.

Antes de escribir: verificar hash y límites; rechazar cambios solapados, destinos BSS sin política explícita, cambios parciales de una instrucción Thumb y toda modificación de una celda relocada sin una operación coherente sobre su registro. Validar el conjunto completo antes de crear la salida. Un fallo de validación debe dejarla ausente, sin cambios en el padre.

Después de escribir: volver a analizar la salida desde bytes; comprobar que solo cambiaron los rangos declarados, que todos los segmentos y tablas quedan dentro del archivo y que las fórmulas de relocación coinciden con los destinos nuevos esperados. Conservar hash de salida y manifiesto. Invertir los rangos con los bytes previos debe recuperar exactamente el hash padre; esto verifica reversibilidad de archivo, no reversión de efectos de ejecución.

## Alojamiento y entrada: alternativas pendientes

| Alternativa | Evidencia necesaria antes de implementarla |
|---|---|
| Ampliar un LOAD existente | Límites virtuales y de archivo, permisos, referencias a límites, alineación, memoria y metadatos SELF coherentes. El hueco actual no aporta esa demostración. |
| Añadir LOAD propio | Aceptación del tipo de módulo y cargador, límites de índices de segmento, tablas y relocaciones nuevas. No asumir que un ELF genérico basta para Vita. |
| Adaptador posterior al enlace | Punto de instalación anterior a los 799 inicializadores y a efectos sensibles; impedir ejecución con instalación parcial. No existe aún ese punto probado. |

El adaptador debe preservar registros, pila y modo ARM/Thumb; DataSave tiene cinco argumentos, incluido el de pila. Tampoco puede traducir un rechazo propio a un código del cliente sin cerrar su semántica. El backend nativo probado aparte no resuelve este contrato automáticamente.

## Preparación de recursos sin tocar originales

Un directorio de staging futuro debe estar vacío y separado del árbol fuente. Antes de copiar, crear un manifiesto por capa app/patch/rePatch con rutas relativas, tamaños y hashes; resolver colisiones con una política declarada. La precedencia propuesta es una hipótesis hasta demostrar los montajes efectivos. No mezclar automáticamente metadatos de instalación original con la identidad experimental MHFZL0001, ni trasladar partidas, cuenta o credenciales.

Una copia completa de recursos tampoco demuestra independencia: quedan aperturas FIOS, savedata0:, identidad AppUtil y relanzamiento relativo app0:eboot.bin. La comprobación debe cubrir lecturas y descriptores abiertos, además de escrituras y borrados. Un hash idéntico acredita copia, no selección en tiempo de ejecución.

## Próximo experimento autorizado

Construir únicamente el manifiesto comparativo de capas desde el inventario existente, con conteo de colisiones iguales/distintas y tamaño de la unión bajo precedencia explícita. No copiar recursos ni emitir un paquete. Ese resultado permitirá dimensionar staging y detectar decisiones pendientes sin confundir una unión de archivos con el montaje observado.

La prueba física sigue bloqueada por aislamiento, alojamiento, contenedor e integración. Requiere autorización específica posterior; este plan no la concede.