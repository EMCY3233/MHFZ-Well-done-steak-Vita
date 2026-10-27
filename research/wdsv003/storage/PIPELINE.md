# Ensayo conjunto del almacenamiento propio

pipeline_harness.c conecta value_body + value_journal + save_journal/save_record + private_files/private_paths en una misma imagen ARM. El harness es exclusivamente de prueba: tres contextos, buffers de 4096 bytes y resultados accesibles para el emulador. No se instala ni integra con Frontier.

check_pipeline_arm.py intercepta únicamente stdio: las seis rutas privadas y sus contenidos se representan en RAM Python. Las decisiones de sobre, CRC/secuencia, recuperación, selección de ranura, namespace y callbacks de archivo se ejecutan como código C compilado para ARM.

24 comprobaciones pasan: escritura y recarga en los tres contextos, borrado confirmado, conservación de los otros datos, recreación truncada tras borrado, bloqueo posterior al error sin abrir más archivos, apertura denegada, incertidumbre de fflush, recuperación de un registro completo no confirmado y borrado parcial. El namespace inválido no abre archivos. Todos los descriptores simulados quedan cerrados.

Una llamada fallida puede haber dejado un registro completo: al reiniciar es correcto recuperar el anterior o el nuevo completo según lo persistido; no se promete conservar siempre el anterior. Una marca confirmada conserva la eliminación frente a una recreación parcial en estos casos, sin garantizar corrupción posterior ni pérdida eléctrica.

Pendiente: buffers dimensionados para personaje real y límites de memoria; pruebas de ABI/errores del adaptador de cliente; registro de operaciones integrado; sistema de archivos físico y montaje AppUtil; hooks que medien todas las rutas del ejecutable. Este ensayo no prueba que la instalación original quede aislada cuando se ejecute el juego ni habilita una prueba física.
