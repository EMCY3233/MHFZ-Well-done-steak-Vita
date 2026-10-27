# Callbacks nativos: 34 casos en emulación ARM

27-10-2026. check_private_io_arm.py compila private_io.c y private_paths.c para Thumb/Cortex-A9 y ejecuta únicamente ese código propio en Unicorn. Sustituye las cuatro APIs sceIo por funciones de prueba en RAM. No ejecuta un cliente comercial ni VitaOS, no abre archivos de juego ni contacta la consola.

Pasan 34 casos: los seis destinos privados con escritura/lectura parcial, archivo ausente, final exacto, archivo que excede capacidad, namespace/slot/contexto inválidos rechazados antes de abrir, tamaños inválidos, error de lectura/escritura, escritura sin progreso, retornos de longitud superiores a la petición, fallo de cierre y apertura denegada. Los descriptores abiertos quedan cerrados incluso al fallar. Los resultados incluyen hash del ELF de prueba para reproducibilidad; no se publica el ELF.

La sobrelongitud se simula sin escribir más allá del búfer: comprueba la reacción del adaptador a un retorno inválido, no que un sistema operativo malicioso pueda escribir sin límites. El código ya acepta retornos signed32 y comprueba negativos antes de convertirlos a longitudes. El test de ausencia inyecta el valor documentado del emulador; no acredita el código devuelto por la Vita física ni la existencia del padre.

No hay flush simulado: esta alternativa no usa stdio ni añade una sincronización de semántica desconocida. Éxito del callback de escritura significa que terminó el bucle y cerró; la confirmación por relectura corresponde al diario, todavía sin conectar en esta prueba. No se afirma durabilidad ante pérdida eléctrica.

Próximo paso: conectar estos callbacks al diario propio y ejecutar fallos parciales con recuperación y marca de borrado. Conservar nombres separados de la implementación stdio, para que una prueba no cambie silenciosamente el backend de otra. Aún faltan hooks, contenedor, montajes e identidad del cliente real.