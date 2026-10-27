# MHFZ — Well Done Steak Vita

Preparación parcial de una política experimental de almacenamiento. No incluye cliente, recursos, informes ni metadatos de los archivos privados del usuario.

El código de research/wdsv003/storage es propio y funciona únicamente como modelo Python con almacenamiento simulado en RAM. No intercepta llamadas de un juego, no accede a la consola y no certifica aislamiento ni durabilidad física.

Pruebas: `python -m unittest discover -s research/wdsv003/storage -p 'test_*.py' -v` (20 casos locales satisfactorios).

Se rechazan nombres arbitrarios y estados inválidos, se verifica antes de confirmar una operación, se bloquea tras efectos inciertos y se usa una marca persistente simulada de borrado para recuperación. No simula pérdida de energía ni corrupción posterior de la marca de borrado.

La integración con un cliente real, traducción de códigos de error, montajes y empaquetado quedan pendientes. La instalación y ejecución física requieren autorización específica. No se modifica firmware, plugins ni originales.
