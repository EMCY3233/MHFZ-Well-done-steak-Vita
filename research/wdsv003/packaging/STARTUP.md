# Orden de inicio: runtime, inicializadores y entrada del juego

27-10-2026. El RVA start_entry del módulo apunta a 821409dc. Sus primeras instrucciones transfieren al helper 821408a4. El análisis dirigido de este helper muestra registro del DSO y TLS, preparación de argumentos, un bucle de callbacks no nulos, llamada a 821290b6 y salida mediante exit.

La tabla recorrida va de 82cb3628 a 82cb42a4 (límite excluido): 799 celdas de cuatro bytes, todas no nulas en el ELF derivado. imports.json conserva su hash y cantidades, sin publicar sus bytes. No se han trazado individualmente los 799 callbacks ni observado sus efectos. Su denominación como inicializadores describe el uso visto en el helper, no una atribución semántica de cada entrada.

## Consecuencia para el aislamiento

El control colocado únicamente al entrar en 821290b6 llegaría **después** de ese recorrido. No se puede anunciar protección desde el arranque sin estudiar efectos anteriores: inicializadores pueden llamar a código del cliente y a servicios. Aún no se afirma que alguno escriba o conecte; precisamente falta verificarlo.

Una adaptación debe establecer controles antes del primer efecto sensible y respetar lo que necesite el runtime (TLS, libc y constructores). Intervenir antes de su inicialización tampoco es automáticamente válido. Falta definir cómo alojar código propio y sus relocaciones/importaciones en una copia reconstruida y cómo evitar que el enlazador del sistema deshaga una mediación de stubs.

El pseudocódigo automático de module_start, cuyo cuerpo definido mide ocho bytes, no se toma como una función de aplicación completa: puede seguir el flujo del helper y mostrar estructuras ajenas al pequeño stub. La cadena aquí descrita se basa en el helper analizado y la transferencia inicial, no en atribuir todo ese pseudocódigo al stub.

No se insertó ningún salto, no se creó un SELF modificado y no se ejecutó el cliente. Siguiente experimento estático: delimitar callbacks iniciales y referencias a APIs sensibles con trazado acotado, sin concluir que ausencia en un grafo parcial implique seguridad. El backend nativo propio continúa separado de este flujo.

Evidencia local: module-start-facts.json y module-start-helper-facts.json; metadatos reproducibles en imports.py/json. No se publica pseudocódigo del cliente.
