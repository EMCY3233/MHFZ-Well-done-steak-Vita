# Consumidores del resultado asíncrono +9c identificados

27-10-2026. Se cierra una búsqueda pendiente:8211d484 y8211d5dc consumen el campo+9c del objeto global82cb1d1c después de consultar su estado+90. Evidencia Ghidra directa y, para el primero, contraste con instrucciones originales mediante objdump. Pseudocódigo y ventanas permanecen privados.

En8211d484, la consulta exclusiva de+90 mantiene el valor; si no es cero, devuelve0 sin interpretar+9c. Con estado cero carga+9c en8211d4aa y despacha por tabla de saltos. El resultado interno0 devuelve1. Para varios resultados no cero llama indirectamente al tercer argumento recibido, el puntero al notificador8211d219 ya contrastado en dos sitios. La opción del segundo argumento modifica una rama, por lo que no hay traducción única resultado→diálogo sin conservar ese contexto.

Esto conecta el trabajador con la presentación: el helper no se limita a comprobar que terminó el hilo. A diferencia de8213bfdc, distingue estado ocupado y resultado final. **No sustituirlo por estado cero o retorno1 incondicional:** eso saltaría la interpretación del error y podría presentar como terminado correctamente un trabajo fallido.

8211d5dc también espera estado cero antes de leer+9c; su análisis dirigido muestra rutas hacia sceMsgDialogInit y resultados locales diferentes. El mapeo completo de cada número a significado del juego sigue pendiente. Los códigos internos del trabajador, los retornos de estos consumidores y los de VitaOS son espacios distintos; no copiar números entre ellos por coincidencia.

El retorno1 ante resultado interno0 es el comportamiento observado del consumidor, no una garantía física de escritura. Para un backend integrado aún se necesita establecer exactamente cuándo el trabajador publica+9c, preservar el ciclo asíncrono y confirmar la operación propia antes de publicar éxito.

Próximo paso: decodificar la tabla de saltos desde bytes originales y contrastar productores concretos de+9c por guardado/lectura/borrado. No usar el pseudocódigo de funciones parciales como definición de todas las ramas. No hubo ejecución del cliente, parche ni transferencia.