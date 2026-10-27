# Ruta de notificación asociada al almacenamiento

27-10-2026. Análisis estático del ELF derivado inventariado; instrucciones originales contrastadas con objdump y Ghidra directo. No hay ejecución ni modificación del cliente.

El acceso antes pendiente en8211d230 pertenece a un bloque interno de la función8211d218..8211d254, delimitada por prólogo y retorno. No es una entrada de callback demostrada. La función tiene dos rutas según su segundo argumento: con cero carga el objeto global82cb1d1c, lee su campo+a8 y prepara una llamada a8212f272 con constantes9/1; con valor distinto usa una tabla y llama a8212f1d6. No se han localizado referencias definidas a la entrada8211d218: queda pendiente su registro/llamante indirecto.

El helper8212f272 prepara estructuras y alcanza sceSaveDataDialogInit;8212f1d6 alcanza sceMsgDialogInit. Esto respalda que la ruta forma parte de presentación de diálogos. No permite atribuir por intuición el significado de cada código o concluir que+a8 sea el resultado final+9c. Tampoco muestra por sí sola una escritura de partida. Una adaptación necesita separar confirmación del almacenamiento de la inicialización correcta de un diálogo.

Durante el análisis se creó temporalmente una función artificial en8211d230, lo que cortaba el bloque real. Se retiró y se redefinió desde8211d218; el cuerpo resultante de62bytes incluye ambos helpers. Un primer script de limpieza falló al compilar por un argumento de API incorrecto; el log posterior confirma la retirada efectiva. No se conservan sus límites anteriores como evidencia válida ni se publica pseudocódigo.

La preparación del cuarto registro en la llamada a8212f272 debe contrastarse con la estructura y firma efectiva: su pseudocódigo actual muestra solo tres parámetros. No descartar el valor+a8 por esa salida automática ni convertirlo a un código propio sin estudiar instrucciones del callee.

## Seguimiento del cuarto registro en instrucciones originales

16:53 UTC. El helper8212f272 sobrescribe r3 en8212f276 con una constante antes de usar su valor entrante. Conserva únicamente r0/r1/r2 en registros locales. En este cuerpo el valor+a8 preparado por el llamante no se consume; el pseudocódigo de tres argumentos coincide con ese detalle de instrucciones. Esto no elimina otros posibles usos de+a8 ni demuestra que el llamante fuera escrito originalmente con tres parámetros.

La ruta conserva r1=9 y r2=1 en estructuras antes de SaveDataDialogInit. No se atribuye nombre semántico a esos campos sin contrastar la estructura. Tras la inicialización, retorno cero de la API permite marcar mediante operación exclusiva el objeto de diálogo; retorno distinto de cero devuelve rechazo. Es estado de presentación, no confirmación de persistencia del diario ni lectura de+9c.

Próximo análisis: registro o referencias indirectas a8211d218 y relación de sus argumentos con el estado asíncrono. No seguir interpretando el r3 descartado como traducción de error del guardado. El consumidor+9c sigue sin identificar. Sin pruebas físicas, paquete o cambios en firmware/plugins/originales.