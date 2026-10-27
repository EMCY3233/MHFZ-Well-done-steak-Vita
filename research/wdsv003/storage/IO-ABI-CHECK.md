# Contrato de E/S nativa comprobado al compilar

27-10-2026. io_abi_check.c compila para ARM/Thumb con el GCC15.2 del SDK local: siete aserciones verifican tipos de cuatro funciones y tamaños/signos de descriptor, longitud y retorno. No contiene llamadas ni punto de entrada. No valida la implementación de VitaOS.

Read/Write reciben longitudes unsigned32 y devuelven signed32; el backend debe comprobar negativos antes de convertir a longitud, rechazar resultados superiores a lo solicitado y evitar bucles sin progreso. Close devuelve int: un error de cierre debe impedir afirmar éxito. Las capacidades actuales (hasta163876 bytes por registro) quedan dentro del rango positivo signed32.

Se consultó además la implementación primaria de [Vita3K io.cpp, commit17a8b340](https://github.com/Vita3K/Vita3K/blob/17a8b34017a94f4a5914cc0700ae061a3c506a06/vita3k/io/src/io.cpp), blob69d37b91301d3e880ec02618c8f6cd867413691a. La rama de apertura con archivo inexistente devuelve el símbolo SCE_ERROR_ERRNO_ENOENT. Es evidencia del emulador, no medición física ni garantía sobre todos los fallos. No se copió su implementación al proyecto.

La búsqueda web aportó logs e información comunitaria, pero no se usan como sustituto de una definición primaria del valor numérico. En esta entrega aún no se fija ese valor en código: queda localizar su definición versionada y conservar contexto de apertura antes de traducirlo a ranura ausente. No confundir ausencia del archivo con error de montaje, permisos o directorio padre inexistente.

Próximo paso: definición primaria del error y callbacks nativos separados de stdio, con pruebas dirigidas a conversiones signed/unsigned, lecturas cortas, sobrelongitudes y cierres fallidos. No hay backend integrado, ejecución del cliente ni prueba de durabilidad física.