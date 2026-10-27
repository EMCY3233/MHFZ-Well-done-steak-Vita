# Generación común: contrato propuesto antes de implementar

27-10-2026. La prueba batch-gap-arm-results.json confirma generaciones mezcladas con commits independientes. Esta propuesta busca una política propia de visibilidad por lote; no atribuye atomicidad a AppUtil ni cambia el backend actual.

## Selección de lecturas

Un manifiesto confirmado debe enumerar el estado completo de los tres identificadores lógicos, incluidos los no modificados por la solicitud: slot seleccionado, identidad de registro, longitud y digest; ausencia y marca de borrado deben distinguirse. No almacenar rutas proporcionadas por el cliente. Los lectores seleccionan exactamente esos registros, nunca el registro individual con mayor secuencia.

El formato actual no tiene ese selector. wdsv_load_value usa el diario individual para elegir su registro más reciente; **no se puede reutilizar sin cambios para leer miembros preparados**, porque haría visible un registro antes de confirmar el manifiesto común. Se necesita lectura por referencia exacta y validación de identidad/contenido.

## Orden de preparación y publicación

1. Recuperar un manifiesto válido y todos sus miembros; si no hay estado inequívoco, bloquear escrituras. Distinguir primera sesión realmente vacía de manifiestos corruptos o montaje incorrecto.
2. Para cada miembro modificado, preparar en el slot que no está seleccionado por el manifiesto actual. Escribir y releer el registro completo, preservando los registros que siguen visibles.
3. Construir un manifiesto nuevo completo: hereda referencias de miembros no modificados e incluye solo candidatos verificados de la solicitud. Comprobar duplicados, límites y generación sin desbordamiento.
4. Escribir el manifiesto en su slot alternativo y releerlo. Hasta entonces las lecturas de la sesión siguen fijadas al manifiesto anterior; no exponer la secuencia individual recién escrita.
5. Solo tras confirmar el manifiesto cambiar la vista de la sesión y publicar éxito al trabajador. Un fallo incierto bloquea nuevos commits hasta recuperar, en vez de efectuar rollback destructivo.

## Recuperación e incertidumbre

Validar ambos manifiestos con CRC/estructura y todas sus referencias antes de elegir generación. Un manifiesto completo escrito cuyo reconocimiento se perdió puede seleccionarse al reiniciar; retorno de fallo no promete que el lote jamás se hizo visible. Mantener esa incertidumbre explícita, como en el diario individual.

Con solo dos slots por miembro, preparar una generación nueva puede reutilizar datos referidos por el manifiesto anterior al actual. Por ello **no se garantiza conservar dos snapshots completos históricos**. El snapshot actual debe permanecer intacto durante preparación; manifiestos antiguos cuyas referencias ya no validen no son candidatos de recuperación. Exigir dos snapshots históricos requeriría almacenamiento o protocolo adicional, no una promesa documental.

No seleccionar silenciosamente datos parciales si un manifiesto válido no tiene todos sus miembros. La política exacta de recuperación ante corrupción posterior del snapshot actual queda por definir; conservar consistencia y disponibilidad son garantías distintas. CRC y digest no son autenticación contra modificación maliciosa.

## Bloqueos de implementación

Hace falta un formato de manifiesto versionado, dos rutas privadas nuevas, lector por referencias, presupuesto total del lote (incluida INI-DATA), concurrencia exclusiva y pruebas de cada corte entre preparaciones/publicación. Los diarios existentes y sus rutas no se migran ni eliminan automáticamente. No hay código de lote integrado, nuevo paquete ni prueba física.

Próximo paso: definir y probar únicamente el lector del manifiesto y la selección de referencias con datos sintéticos, incluida referencia a slot incorrecto, digest/longitud incoherentes, miembro duplicado, ausencia frente a borrado y generaciones empatadas. Después diseñar escritura; no empezar por un booleano de commit en RAM.