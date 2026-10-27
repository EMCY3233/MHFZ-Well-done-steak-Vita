# Cobertura de los inicializadores antes de entrar al juego

27-10-2026. Se definieron las 799 entradas concretas de la tabla de inicio en Ghidra, en lotes de máximo 64 y decodificación acotada. Se conservaron instrucciones ya definidas sin cambiar su contexto Thumb. Son modificaciones de la base de análisis, no del ejecutable original.

Los cuerpos definidos suman 37570 bytes. Se detectan 15 llamadas directas cuyo destino todavía no tiene función definida y ninguna instrucción de llamada calculada dentro de esos cuerpos. Estas cifras no acreditan límites completos de funciones ni ausencia de llamadas indirectas más abajo en la cadena.

Una búsqueda inversa de hasta tres aristas hacia 113 funciones sensibles conocidas sigue sin rutas desde estas entradas. La consulta anterior tenía 791 entradas sin definir; ahora ninguna entrada queda sin definir. **El resultado negativo sigue sin ser prueba de seguridad:** faltan esos 15 destinos, posibles saltos de cola, otros imports y referencias transitivas/indirectas. No basta ampliar profundidad indiscriminadamente.

Los primeros callbacks incluyen retornos sin trabajo aparente, inicialización de objetos con guards y registro de destructores, e inicialización de iostream. No se han ejecutado. No se afirma que todos los demás sean equivalentes ni que sea seguro omitir constructores.

initializer-coverage.json conserva cantidades, destinos pendientes y alcance de la búsqueda. Las herramientas propias se publican en tools/ghidra; no incluyen pseudocódigo ni bytes del cliente. Siguiente paso: resolver únicamente los destinos pendientes y sus efectos antes de definir el punto de mediación. No existe todavía hook ni SELF reconstruido.
