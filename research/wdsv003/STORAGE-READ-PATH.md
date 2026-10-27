# Lectura local fuera de las APIs de guardado

27-10-2026. Análisis estático de la copia ELF derivada inventariada; sin ejecución ni modificaciones de originales.

Se clasifica el trabajo de estado 4: el callback 8213c4b2 consulta parámetros del slot y lee archivos mediante sceIoOpen/sceIoRead/sceIoClose. Construye la ruta con formato `%s%s`, prefijo `savedata0:` y el nombre registrado. Esto amplía la superficie de aislamiento: controlar únicamente DataSave/SlotDelete no evita leer una partida del montaje original.

Contraste con instrucciones del ELF original derivado:

| Dirección de llamada | Destino identificado por importación |
|---|---|
| 8213c52e | sceAppUtilSaveDataSlotGetParam |
| 8213c60e | Formateador 8212e44a |
| 8213c618 | sceIoOpen |
| 8213c628 | sceIoRead |
| 8213c63a y 8213c6ca | sceIoClose |

Las cadenas están en VA 827f9ab8 (`%s%s`) y 827f9ac0 (`savedata0:`). Los bytes de cada ventana se mantienen locales; control-sites.json conserva rangos y hashes. La correspondencia de APIs usa los nombres resueltos de la importación Ghidra, no observación de VitaOS.

## Selección y finalización

8213c336 cambia el campo en objeto + índice*0x1c +0x1c únicamente con estado +0x90=0. Es el mismo campo de opción registrado por 8213c2ea. El trabajo lector consulta opciones de las entradas y puede reservar un búfer de 0x7d000 para una de ellas. No se ha completado la atribución semántica de todos esos datos.

8213bfdc espera a que estado +0x90 vuelva a cero, durmiendo 500000 microsegundos entre comprobaciones. **No devuelve por sí mismo el resultado +0x9c ni demuestra éxito de E/S.** El destructor 8211bd36 usa esta espera antes de destruir el objeto. La adaptación debe conservar la separación entre trabajo terminado y resultado correcto; no basta desbloquear la espera.

## Consecuencia y siguiente paso

La política Python publicada sigue siendo un modelo sin hooks. La integración real necesita mediar lecturas y el montaje `savedata0:`, además de escrituras, borrados y relanzamiento. No se ha observado qué identidad resuelve ese montaje en un paquete nuevo. Por tanto, este hallazgo no habilita instalar un VPK del cliente.

Siguiente trabajo: identificar consumidores del resultado +0x9c, cerrar la selección de entradas y revisar tratamiento de lecturas cortas y errores antes de diseñar el ABI nativo. No atribuir significado a códigos internos solo por su valor ni afirmar que todo acceso del cliente esté enumerado.

Evidencia local: save-completion-and-entry-selection.json, save-state4-worker.json, ventanas read-worker/entry-selector y logs. Solo el resumen, herramienta propia y metadatos son publicables; no pseudocódigo ni ventanas binarias.

## Lecturas cortas: condición contrastada

Continuación 27-10-2026: después de sceIoRead en 8213c628, las instrucciones 8213c62c/8213c62e comparan el retorno con cero y toman la rama de error solo si es negativo. En ese tramo no comparan la cantidad devuelta con la solicitada. El recorrido no negativo cierra el descriptor y continúa. Esto permite que una lectura corta alcance esa continuación local; no demuestra aceptación de los datos por validadores posteriores. No etiquetar automáticamente el resultado local cero como lectura completa.

El adaptador nativo deberá conservar cantidad solicitada/devuelta y diferenciar lectura corta, fin de archivo y error, antes de declarar datos completos. La lectura parcial no se corrige rellenando ceros ni fabricando éxito. La política sintética actual verifica identidad de bytes en guardado, pero no es todavía un adaptador de lectura del cliente.

La búsqueda acotada de instrucciones definidas con desplazamiento literal +0x9c en 8211b000–8211e000 no encontró candidatos. Es un resultado negativo de esa consulta, no ausencia de consumidores: quedan accesos indirectos, alias y zonas fuera del intervalo. No repetirla sin una pista nueva.


