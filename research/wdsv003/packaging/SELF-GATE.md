# Bloqueo estructural antes de transformar el SELF

self_bounds.py verifica el hash del SELF local contra el inventario y evalúa tamaños/rangos, solapamientos y resultado de descompresión ya inventariado. No cambia un solo byte. Este control conservador no es el cargador Vita ni valida firmas, autenticidad, relocaciones o aceptación por firmware.

El contenedor real queda bloqueado para transformación por dos motivos ya observados: tamaño declarado distinto al real y datos posteriores al fin zlib dentro del segmento cero. El último rango comprimido termina exactamente en el final físico del archivo: **los 848 bytes de diferencia no son una cola fuera de todos los segmentos**. Truncar el archivo al tamaño declarado cortaría el rango comprimido del segmento 3.

No se ha establecido por qué la copia rePatch tiene esos valores ni que deba repararse para ejecutarse en su instalación actual. Puede conservar particularidades de su modificación o contenedor; no se atribuye causa. La coincidencia de los cinco segmentos descomprimidos con el ELF no prueba que reconstruir el SELF sea trivial.

Siete pruebas nuevas de casos sintéticos cubren rangos inválidos, tamaño, solapamiento, ausencia de segmentos y anomalías de descompresión. El conjunto de lectores suma 17 pruebas satisfactorias. Pasarlas solo permite continuar análisis estructural; no habilita empaquetar, instalar ni ejecutar el cliente.

Siguiente requisito de reconstrucción: documentar el tratamiento exacto de metadatos y relocaciones y comparar la salida de una reconstrucción local sin cambios semánticos antes de cualquier parche. La instalación original no participa en ese experimento; un archivo reconstruido localmente tampoco se anunciará ejecutable hasta validación posterior autorizada.
