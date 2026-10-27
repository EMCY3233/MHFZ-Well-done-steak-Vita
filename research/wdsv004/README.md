# WDSV-004 — primera entrega de aislamiento

Orden recibida27-10-2026. **Fase iniciada; primer hito de aceptación pendiente.** No hay una copia ejecutable del cliente con aislamiento demostrado, ni se solicita una prueba física con este resultado.

## Cliente y dependencias

El ELF de referencia está disponible y conserva SHA256 `2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d`. SELF fuente `a5dac30c97eb87c4ab0e99b272a93752501114e6b5072159c6222857e4ac3fa3`. Se verifican de nuevo con validate.py; hashes exactos acreditan identidad de la copia, no autenticidad o capacidad de arranque.

Procedencia: copia proporcionada por el usuario de app/patch/rePatch; historial de modificaciones rePatch desconocido. AppSFO1.00/FrontierG y patchSFO1.99/FrontierZ no prueban una versión oficial exacta del ELF rePatch. Arquitectura ELF32LE ARM, tipo0xfe04, dos PT_LOAD y cinco program headers. Inventarios previos identifican36 descriptores/476 importaciones y475219 relocaciones; no se repiten análisis inalterados. Sus valores coinciden en bases originales. No equivale a relocación de un ELF modificado.

Recursos: unión hipotética7596 rutas/4036150283bytes, precedencia no observada. Metadatos originales, bibliotecas, montajes y relanzamiento necesitan control propio. El SELF mantiene tamaño declarado848bytes menor que el real y cola zlib21bytes no explicada; el gate previo no permite transformarlo. No se ha emitido SELF nuevo ni VPK. El cliente PC permanece referencia secundaria: no hace falta repetir una comparación gráfica ni afirmar equivalencia con Rain para este bloqueo de almacenamiento.

## Implementación nueva

snapshot.py valida referencias **exactas** desde el manifiesto privado MZBAT001 de WDSV-003. Verifica longitud, SHA256, cabecera/CRC del registro, secuencia, envoltura y estado de cada miembro. Selecciona una generación completa; nunca completa un miembro defectuoso usando otro archivo independiente ni selecciona un registro huérfano por su secuencia mayor.

Dos manifiestos distintos con la misma generación bloquean recuperación. Dos copias idénticas eligen el primer slot. Si no hay snapshot completo válido, se rechaza; solo dos slots ausentes devuelven None. Esto último es ausencia de manifiestos, **no autorización para crear datos o asumir directorio padre correcto**. La selección puede recuperar una generación anterior completa, con la posible pérdida de cambios posteriores que eso implica; no promete dos snapshots históricos preservados.

Es una referencia Python sin E/S, hooks ni escritor. No convierte el backend nativo individual en un coordinador de lote. Su lector admite estructuralmente una referencia512000bytes; el límite del backend nativo sigue en163840. INI-DATA y el presupuesto del lote continúan pendientes. Ausencia, valor vacío y marca de borrado se conservan como estados diferentes.

## Pruebas y observación

15 pruebas nuevas cubren registros preparados invisibles, snapshot nuevo completo, fallo del segundo miembro con recuperación íntegra anterior, slots/digests/secuencias/CRC incorrectos, manifiesto truncado, empate conflictivo, ausencia frente a borrado/valor vacío y referencia grande. validate.py ejecuta estas pruebas y las suites Python existentes, registrando resultados en validation.json. Ninguna ejecuta el cliente, VitaOS ni la consola. Los ensayos ARM anteriores usan código propio y APIs sustituidas, no se presentan como validación física.

Las pruebas de identidad válida/inválida, token caducado/incorrecto, doble sesión, cierre/reconexión, respuesta Sign/Entrance malformada, recurso ausente, destino de relanzamiento incorrecto y fallo NP siguen **pendientes en integración**. Existen contratos y evidencia previos, pero esta entrega no inventa un cliente compatible ni atribuye esas pruebas al selector de almacenamiento. La observación del primer bloqueo de arranque requiere instrumentación real aún no alojada/instalada; un registro sintético de eventos no sustituiría esa evidencia.

## Secuencia siguiente y bloqueos

1. Implementar manifiesto/selector nativos y preparación de lote preservando referencias actuales, con pruebas de interrupción. Resolver capacidad INI-DATA sin cambiar límites a ciegas.
2. Resolver alojamiento/entrada e imports/relocaciones del adaptador y una política de reconstrucción SELF verificable. Mantener originales inmutables.
3. Mediar lecturas/escrituras/borrado y relanzamiento antes de efectos sensibles; comprobar identidad AppUtil y montajes privados. El consumidor+9c y su orden de publicación ya están localizados, pero los códigos y contratos deben conservarse.
4. Solo entonces integrar identidad local y transición mínima de servicios, y observación de solicitudes reales. No asumir loopback sin Wi-Fi ni equivalencia Rain/Erupe.

Preparación física bloqueada mientras falten esos controles. Antes de pedir autorización: aportar manifiestos de instalación separados, hashes, destino experimental inequívoco, plan de observación y prueba de que no se alcanzan partidas/rutas originales. La orden requiere autorización física posterior; no se deduce del permiso de investigación.

## Revisión y reversión

Rama específica `research/wdsv004-snapshot-isolation`, basada en WDSV-003 commit `a610f2864814041f0d7531f2791c0706c8fe1504`, sin fusionar PR1 ni main. Se propone PR dependiente contra la rama WDSV-003 para revisar solo este incremento. No se encontró AGENTS.md en ancestros locales ni en main/rama remotos al iniciar.

Reversión actual: descartar exclusivamente esta rama y archivos propios WDSV-004; no hay cambios de consola que revertir. No borrar manifiestos/diarios existentes ni migrarlos automáticamente. Cualquier futura retirada física quedará limitada al TitleID y directorios experimentales comprobados y autorizados; nunca limpieza por prefijos del original.

Los temporizadores de seguimiento no constituyen permisos de instalación, ejecución ni fusión. No se reactiva el antiguo temporizador de cinco minutos.

## Actualización de almacenamiento — 27-10, 22:55 UTC

Además de snapshot.py, existen lectores nativos manifest_reader, record_ref y snapshot_reader: 208, 61 y 23 casos ARM respectivamente, con digest delegado a Python en los dos últimos. No existe aún SHA nativo ni escritor nativo de lotes.

batch_plan.py y batch_commit.py son referencias Python: conservan referencias vigentes, preparan slots alternativos y verifican el lote completo antes/después de publicar el manifiesto mediante callbacks. Los datos observados deben ser bytes inmutables; contenedores de observación se copian y cualquier resultado incierto bloquea la instancia. La exclusión entre escritores sigue siendo precondición externa, no un bloqueo implementado. Readback no demuestra persistencia ante corte de energía.

La suite WDSV004 contiene ahora 25 métodos de prueba, con seis fallos de publicación y seis variantes de datos modificables entre sus subcasos. validation.json se regenera con las suites existentes y los hashes de las copias de entrada. Los detalles de cada cobertura están en NATIVE-MANIFEST.md, NATIVE-RECORD-REF.md, NATIVE-SNAPSHOT.md, BATCH-PREPARATION.md y BATCH-PUBLICATION.md.

La siguiente tarea nativa sigue siendo verificar el digest y trasladar el protocolo de lote al backend. El límite de escritura 163840 bytes no cubre INI-DATA de 512000 bytes. No se ha demostrado aislamiento del cliente, montajes, identidad AppUtil o relanzamiento; no hay ejecución física autorizada ni hito de aceptación completado.