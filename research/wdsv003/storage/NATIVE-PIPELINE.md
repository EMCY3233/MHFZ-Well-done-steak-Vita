# Diario conectado a la alternativa nativa

27-10-2026. El arnés propio permite seleccionar WDSV_NATIVE_IO al compilar; por defecto conserva el backend stdio anterior. No cambia la aplicación instalada ni integra hooks del cliente.

check_native_pipeline_arm.py compila en un único ELF propio el diario de dos registros, formato con CRC, envoltura de valor/marca de borrado, rutas privadas y callbacks sceIo. Ejecuta código ARM en Unicorn con archivos y APIs simulados en RAM. **Pasan 24 casos de la cadena completa**; también pasan los 24 casos de regresión del arnés stdio.

La integración recupera valores independientes en tres espacios, conserva una marca de borrado tras recreación parcial fallida y conserva el valor anterior tras un borrado parcial fallido. Una escritura incierta deshabilita nuevos commits hasta recargar. Apertura denegada no devuelve éxito; cierre fallido de un registro completo tampoco se confirma, aunque ese registro puede ser seleccionado al reiniciar. Esta última posibilidad es parte del contrato de incertidumbre, no pérdida de aislamiento.

La confirmación añade relectura del registro al callback nativo; no garantiza sincronización física ni resistencia a toda pérdida eléctrica. El arnés usa buffers de 4096 bytes, no demuestra todavía la ruta nativa al tamaño máximo de registro. No se repiten pruebas de contadores ni se interpreta esta simulación como una cacería o arranque del cliente.

Pendiente: contrastar máximo de registro con la nueva cadena y revisar precondición de directorio padre/errores sin acceso físico. La instalación del adaptador antes de efectos sensibles, identidad AppUtil, montajes y reconstrucción SELF siguen pendientes. No existe un paquete del cliente real listo para probar.