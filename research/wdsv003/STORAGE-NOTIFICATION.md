# Ruta de notificación asociada al almacenamiento

27-10-2026. Análisis estático del ELF derivado inventariado; instrucciones originales contrastadas con objdump y Ghidra directo. No hay ejecución ni modificación del cliente.

El acceso antes pendiente en8211d230 pertenece a un bloque interno de la función8211d218..8211d254, delimitada por prólogo y retorno. No es una entrada de callback demostrada. La función tiene dos rutas según su segundo argumento: con cero carga el objeto global82cb1d1c, lee su campo+a8 y prepara una llamada a8212f272 con constantes9/1; con valor distinto usa una tabla y llama a8212f1d6. No se han localizado referencias definidas a la entrada8211d218: queda pendiente su registro/llamante indirecto.

El helper8212f272 prepara estructuras y alcanza sceSaveDataDialogInit;8212f1d6 alcanza sceMsgDialogInit. Esto respalda que la ruta forma parte de presentación de diálogos. No permite atribuir por intuición el significado de cada código o concluir que+a8 sea el resultado final+9c. Tampoco muestra por sí sola una escritura de partida. Una adaptación necesita separar confirmación del almacenamiento de la inicialización correcta de un diálogo.

Durante el análisis se creó temporalmente una función artificial en8211d230, lo que cortaba el bloque real. Se retiró y se redefinió desde8211d218; el cuerpo resultante de62bytes incluye ambos helpers. Un primer script de limpieza falló al compilar por un argumento de API incorrecto; el log posterior confirma la retirada efectiva. No se conservan sus límites anteriores como evidencia válida ni se publica pseudocódigo.

La preparación del cuarto registro en la llamada a8212f272 debe contrastarse con la estructura y firma efectiva: su pseudocódigo actual muestra solo tres parámetros. No descartar el valor+a8 por esa salida automática ni convertirlo a un código propio sin estudiar instrucciones del callee.

Próximo análisis: rastrear el cuarto registro dentro de8212f272 y el contrato de SaveDataDialog; después buscar el vínculo de la entrada8211d218 con el estado asíncrono. El consumidor+9c sigue sin identificar. Sin pruebas físicas, paquete o cambios en firmware/plugins/originales.