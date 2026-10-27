# Entrada: transferencia, salida y retorno inesperado

27-10-2026. Contraste con objdump sobre bytes originales del ELF derivado, mapeados por PT_LOAD; no se ejecutó el cliente ni se usó memoria relocada de Ghidra. Las ventanas se conservan privadas.

El stub 821409dc llama mediante BL al helper821408a4 y contiene dos NOP posteriores. No contiene un retorno explícito dentro de sus ocho bytes. A continuación comienza otra función definida en821409e4. Por tanto, no se debe modelar este stub como una función ordinaria que llama al runtime y luego retorna limpiamente al cargador.

En el helper, después de recorrer los799 inicializadores,821409a0 llama a821290b6 y821409a4 llama al stub de importación823d2060 identificado como exit. Existen instrucciones de restauración de pila y retorno después de esa llamada. Esas instrucciones no prueban que exit retorne físicamente: describen el código almacenado. Si el helper retornase al stub, su continuación atravesaría los dos NOP hacia el código contiguo. Ninguna prueba demuestra que ese recorrido sea válido.

Una intervención futura antes del runtime deberá conservar los argumentos originales, alineación de pila y registros preservados, y transferir el control sin fabricar un camino de retorno adicional. No colocar lógica después de BL esperando recuperar control tras iniciar el juego. Tampoco se debe reemplazar exit por éxito o retorno para observar avances: alteraría este contrato y podría alcanzar código ajeno al arranque.

En el mismo tramo se observa un bucle previo con los dos límites inicialmente iguales a82cb3628: su condición salta el cuerpo. El bucle siguiente usa82cb3628..82cb42a4, las799 celdas ya inventariadas. No sumar ambos como dos series de799 callbacks. La interpretación se limita al ELF seleccionado y sus valores originales.

No se genera un bootstrap solo para satisfacer una compilación: sigue sin ubicación demostrada, imports/relocaciones propios ni política verificable anterior a efectos sensibles. Próximo paso útil: revisar capacidad y límites del contenedor para alojar código propio, manteniendo bloqueada cualquier reconstrucción por las anomalías SELF ya registradas. Un adaptador freestanding de entrada tampoco puede usar el backend de archivos antes de establecer su entorno y precondiciones.