# Rangos de escritura y celdas de importación

reloc_intervals.py construye un índice conservador de cuatro bytes por operación observada. Los 475219 destinos no presentan pares solapados bajo ese modelo. No equivale a validar toda instrucción, orden de carga o memoria dinámica.

**Las ocho celdas de importación seleccionadas están cubiertas por relocaciones ABS32.** Por tanto, cambiar únicamente el valor almacenado de una celda dejando su relocación intacta produciría un archivo incoherente: al aplicar la fórmula existente se recuperaría el destino calculado por símbolo+addend, no necesariamente el valor parcheado. No se ha ejecutado el cargador para observarlo; es la consecuencia de los registros originales y de la comparación zero-delta ya contrastada.

El informe identifica para cada celda la relocación correspondiente. Antes de una adaptación hay que actualizar coherentemente código, metadatos y relocaciones, o demostrar una mediación posterior al enlace pero anterior a efectos sensibles. Ninguna de esas opciones está implementada ni validada todavía.

Entre el final de memoria declarado del LOAD 0 y el inicio virtual del LOAD 1 hay solo 292 bytes. No se trata como espacio libre garantizado ni como ubicación para el backend. Ampliar segmentos o añadir otro requiere estudiar disposición, permisos, índice y referencias; no se introduce código en huecos por intuición.

Cuatro pruebas nuevas verifican rangos adyacentes, anidados y separados por segmento y límites de consulta. El conjunto de lectores suma 34 pruebas satisfactorias. No se cambió el ELF/SELF ni se generó un paquete.
