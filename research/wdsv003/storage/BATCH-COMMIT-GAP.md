# Límite de integración: una solicitud puede incluir varios archivos

27-10-2026. El trabajador comercial construye un array de entradas seleccionadas y pasa su cantidad a DataSave. La firma VitaSDK también recibe una colección y un recuento. Por tanto, el adaptador debe manejar una solicitud con varios archivos, no solo una operación aislada por nombre.

El backend propio actual tiene tres diarios independientes. pipeline_commit recibe un único identificador lógico y llama a wdsv_commit_value para ese diario. No hay coordinador de lote ni generación compartida. Las pruebas de independencia entre namespaces no demuestran consistencia de una solicitud que actualiza más de uno.

Si una adaptación ingenua confirma el primer archivo y falla al guardar el segundo, devolver fallo global no deshace el primer commit. Después de recargar podría observarse una mezcla de generaciones. No se afirma aquí que AppUtil garantice atomicidad entre archivos: su semántica completa sigue pendiente. Sí se identifica que nuestra propuesta todavía no define cómo expone esa situación al único resultado final del trabajador.

Antes de conectar DataSave debe fijarse una política explícita: manifestar todos los miembros y longitudes de la solicitud, preparar/verificar los registros candidatos, y decidir qué marca común selecciona la generación visible y cómo se recupera una preparación incompleta. Una marca de generación requeriría a su vez recuperación y aislamiento propios; no basta añadir un booleano de éxito en RAM. Tampoco sirve borrar o sobrescribir el slot anterior para simular rollback.

El tamaño mayor de INI-DATA hace importante separar presupuesto total del lote y límite individual. El formato exterior actual permite hasta1MiB de payload, pero la envoltura y callbacks aplican límites menores; esa capacidad exterior no autoriza aumentar todos los buffers ni garantiza cabida del conjunto.

Próximo experimento autorizado: demostrar con el arnés propio existente qué se conserva tras primer commit correcto y segundo fallido, sin cambiar el backend ni usar partidas comerciales. Después diseñar el contrato del lote con esa evidencia y contrastar la semántica primaria de AppUtil. No presentarlo como garantía de atomicidad del juego o prueba física.