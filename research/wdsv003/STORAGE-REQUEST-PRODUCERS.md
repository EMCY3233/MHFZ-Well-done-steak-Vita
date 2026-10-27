# Productores de solicitudes locales de guardado y borrado

27-10-2026. Análisis estático del ELF derivado ya identificado en el inventario. Sin ejecución ni parche.

Se cierra una parte pendiente del mapa: las funciones que asignan los estados 3 y 6 no son las que realizan directamente las llamadas AppUtil. Preparan trabajos asíncronos.

| Solicitud | Productor | Estado +0x90 | Callback Thumb | Trabajo |
|---|---|---|---|---|
| Guardar | 8213c092 | 3 | 8213c7c1 | Cuerpo conocido 8213c7c0, que llega a DataSave |
| Borrar | 8213c222 | 6 | 8213c3ed | Cuerpo conocido 8213c3ec, que llega a SlotDelete |
| Otra operación, todavía sin clasificar | 8213c15a | 4 | 8213c4b3 | No atribuirle semántica sin estudiar el callback |

Los productores solo aceptan inicialmente estado cero. Reinician resultado +0x9c y dato +0xa8; gestionan trabajo previo mediante +0x94/+0x98. Pasan callback y objeto a 8212e6e0, que crea/inicia un hilo mediante APIs del kernel y entrega ambos valores como argumentos. 8212e924 alcanza ChangeThreadPriority. Si el identificador almacenado resulta negativo, restauran estado cero, ponen resultado 1 y devuelven rechazo; en otro caso marcan +0x94=1 y devuelven aceptación del trabajo. Esa aceptación **no es confirmación de escritura o borrado**.

Contraste independiente: las ventanas originales exportadas por audit_control_sites.py muestran en el productor de guardado la constante Thumb 8213c7c1, carga del valor 3 y escritura a +0x90, seguida de llamada a 8212e6e0. La ventana equivalente de borrado contiene 8213c3ed y el valor 6. Los hashes y rangos están en control-sites.json; bytes/desensamblados permanecen locales.

## Llamantes y consecuencias para la adaptación

Referencias definidas a 8213c092: 8211c2c2 dentro de 8211c234 y 8211d45a dentro de 8211d3dc. Ambas preparan datos y habilitan entradas mediante 8213c336; una selecciona argumentos (2,1), (3,0), (4,0), y la otra (2,1), (3,1), (4,1). El significado completo de las entradas aún no está cerrado.

El primer llamante comprueba si se aceptó el trabajo antes de cambiar su estado +0x28. El segundo no comprueba ese resultado antes de marcarlo. Por tanto, sustituir el productor por un retorno de éxito o rechazo sin reproducir el ciclo de finalización podría dejar estados incoherentes. Un adaptador necesita distinguir solicitud aceptada, trabajo pendiente, resultado final y persistencia verificada.

No aparecen referencias definidas al productor 8213c222 en la base parcial. Esto no prueba que sea inalcanzable: quedan posibles registros indirectos y funciones no analizadas. Se identificó quién pone estado 6, pero todavía no qué acción de usuario o error solicita ese productor. No se afirma borrado al arrancar.

## Próximo punto acotado

Estudiar 8213c336 y los consumidores del resultado +0x9c para definir el contrato de terminación. Después clasificar callback 8213c4b2 y buscar registro indirecto del productor de borrado con una pista concreta. No parchear ni llamar a AppUtil hasta cerrar firmas, montajes y resultados. Ninguna prueba física autorizada o ejecutada en esta fase.

Evidencia local: save-entry-refs.json, save-producer-refs.json y save-producer-callers.json (pseudocódigo conservado localmente), ventanas y logs. Solo se publica este resumen técnico y metadatos, no pseudocódigo ni bytes comerciales.
