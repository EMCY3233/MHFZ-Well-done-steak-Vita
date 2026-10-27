# Ensayo conjunto del almacenamiento propio

pipeline_harness.c conecta value_body + value_journal + save_journal/save_record + private_files/private_paths en una misma imagen ARM. El harness es exclusivamente de prueba: tres contextos, buffers de 4096 bytes y resultados accesibles para el emulador. No se instala ni integra con Frontier.

check_pipeline_arm.py intercepta únicamente stdio: las seis rutas privadas y sus contenidos se representan en RAM Python. Las decisiones de sobre, CRC/secuencia, recuperación, selección de ranura, namespace y callbacks de archivo se ejecutan como código C compilado para ARM.

24 comprobaciones pasan: escritura y recarga en los tres contextos, borrado confirmado, conservación de los otros datos, recreación truncada tras borrado, bloqueo posterior al error sin abrir más archivos, apertura denegada, incertidumbre de fflush, recuperación de un registro completo no confirmado y borrado parcial. El namespace inválido no abre archivos. Todos los descriptores simulados quedan cerrados.

Una llamada fallida puede haber dejado un registro completo: al reiniciar es correcto recuperar el anterior o el nuevo completo según lo persistido; no se promete conservar siempre el anterior. Una marca confirmada conserva la eliminación frente a una recreación parcial en estos casos, sin garantizar corrupción posterior ni pérdida eléctrica.

Pendiente: buffers dimensionados para personaje real y límites de memoria; pruebas de ABI/errores del adaptador de cliente; registro de operaciones integrado; sistema de archivos físico y montaje AppUtil; hooks que medien todas las rutas del ejecutable. Este ensayo no prueba que la instalación original quede aislada cuando se ejecute el juego ni habilita una prueba física.

## Capacidad completa

check_full_pipeline_arm.py compila el harness con capacidad 163876 por buffer y verifica 150820 bytes (tamaño observado del bloque de guardado) y 163840 bytes (límite propio). Pasan 39 casos, incluidos recarga completa, borrado, sobrescritura interrumpida y rechazo de un byte sobre el límite sin abrir archivos. Todos los datos del ensayo son patrones sintéticos, no personajes reales.

Los seis buffers scratch/work ocupan 983256 bytes estáticos en esta configuración; no incluye objetos, pilas, libc, emulador ni memoria del juego. No es una medición de consumo en Vita. La versión de prueba pequeña conserva capacidad 4096 por defecto. El tamaño original no prueba interpretación de personaje ni aceptación por el cliente.

El mock usa transferencias positivas grandes para el tamaño completo y conserva cortes de dos bytes en modos de error. Se corrigió su primera configuración, que podía completar una escritura corta de prueba antes de inyectar el fallo y por tanto no representaba una escritura parcial. Ese fallo del ensayo no fue una corrupción observada en Vita.

