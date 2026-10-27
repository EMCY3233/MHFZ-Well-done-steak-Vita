# WDSV-003: política de almacenamiento previa a integración

Fecha: 2026-10-27. Esto es código propio de referencia para el host, con backend de memoria e inyección de fallos. No contiene ejecutables ni recursos comerciales, no abre sockets, no utiliza credenciales y no ejecuta AppUtil ni el cliente Vita.

## Implementado y comprobado

`storage_policy.py` restringe las operaciones a tres nombres lógicos exactos (`INI-DATA`, `PRI-DATA`, `character`), traducidos a destinos fijos bajo `ux0:data/MHFZL0001/wdsv003/`. No admite rutas de entrada, normalización, nombres alternativos ni borrado recursivo. El backend recibe exclusivamente destinos generados por la política; debe ser de confianza y cumplir su contrato. `memory_journal.py` implementa ese contrato en memoria; no existe backend físico aquí.

Los estados de solicitud de esta referencia son 3 para guardar y 6 para borrar, tomados de las ramas estáticas conocidas; no son un puente ABI al objeto real. Solo se comunica éxito tras resultado correcto del backend y lectura de verificación. Un fallo tras comenzar un efecto deja el modelo bloqueado hasta recuperación explícita: no se sustituye por éxito. El borrado de un dato ausente devuelve un resultado propio `MISSING`, sin asignarle todavía un código Vita. Los eventos registran número, operación, nombre lógico permitido, longitud y resultado, sin contenido ni entrada hostil.

`test_storage_policy.py`: **9 pruebas satisfactorias**, incluyendo 16 variantes hostiles para guardar/borrar sin alcanzar el backend, estados no permitidos, tamaño/tipo inválidos, truncamiento, fallo anterior/posterior a escritura, fallo de lectura, borrado fallido y borrado que devuelve éxito sin eliminar. Un dato centinela con ruta del original permanece intacto en todos los ensayos. `test-results.json` registra alcance, resultado y hashes del código.

Ejecutar con Python desde esta carpeta o mediante ruta absoluta. La salida es solo `test-results.json` y caché Python local.

## AppUtil: lo que el encabezado demuestra

Fuente local: `analysis-tools/vitasdk-win-20260825/arm-vita-eabi/include/psp2/apputil.h`. `SceAppUtilInitParam` tiene `workBufSize` y 60 bytes reservados (0x40); `SceAppUtilBootParam` tiene `attr`, `appVersion` y 32 bytes reservados (0x28). Ninguno declara un campo Title ID. Las APIs de slot reciben `slotId` y un puntero a mountPoint; las de datos también describen archivos y slot. Estos encabezados **no explican por sí solos cómo VitaOS resuelve la identidad efectiva o un mountPoint nulo**. No concluyen aislamiento por cambiar SFO ni justifican llamar a AppUtil bajo la identidad original.

La evidencia Ghidra local `client-isolation-save-effects.json` muestra la llamada a `sceAppUtilSaveDataSlotDelete(0,0)` bajo estado 6 y guardado bajo estado 3. **La firma de `sceAppUtilSaveDataDataSave` en el encabezado tiene cinco argumentos**, incluido `requiredSizeKB`; el pseudocódigo actual presenta cuatro. La comprobación del coordinador de bytes originales identifica `str r4,[sp,#0]` en 8213ca88 antes del BLX en 8213ca8c: sí se prepara un quinto argumento. Véase su `control-sites.json` y desensamblado local para la evidencia de instrucciones. Falta interpretar completamente la estructura y el resultado antes de adaptar; no inventar ABI a partir de ese pseudocódigo.

## Diario existente: reutilizar, no duplicar

`standalone/src/save_journal.c` y `.h` ya implementan dos ranuras, carga de la secuencia válida más reciente, CRC mediante save_record, escritura de ranura alterna, relectura y comparación del contenido. No se reescribieron ni se repitieron sus pruebas en esta entrega. Sus callbacks solo deben recibir ranura 0/1 y el adaptador debe convertirlas en dos rutas privadas fijas. Ante error, se bloquean nuevos commits hasta recarga; un registro completo no confirmado puede recuperarse tras reinicio. Esto no equivale a garantía frente a pérdida eléctrica.

Para integrar este esquema con los tres datos lógicos: cada uno necesitará su par de ranuras o un snapshot agregado con catálogo validado. **Un borrado requiere una marca persistente de eliminación, con secuencia y validación**, o un protocolo equivalente; borrar únicamente la ranura más reciente permitiría resucitar la anterior. No reutilizar el diario C como borrador por el mero hecho de tener dos ranuras.

## Recuperación sintética concreta

`memory_journal.py` implementa dos registros por nombre lógico, secuencia sin wrap, CRC32 de cabecera y contenido y tombstone de borrado. Formato privado propio `WDSV3M01`: 24 bytes de cabecera y hasta 0x28000 bytes de contenido. No es formato Frontier ni el formato del diario C. La imagen de bytes en memoria representa hipotéticamente lo persistido; `snapshot` y nueva instancia representan un reinicio. Nunca hace E/S en Vita ni simula su sistema operativo.

La escritura siempre usa el registro alternativo. La recuperación valida tamaño, secuencia, flags y CRC antes de escoger la secuencia mayor. Dos registros corruptos o secuencias iguales conflictivas provocan error; no se reinicializa silenciosamente. El borrado escribe un registro nuevo con flag de tombstone y contenido vacío, conserva el anterior y se verifica por lectura antes de comunicar éxito. Una lectura de la tombstone devuelve ausencia, sin recurrir al dato anterior. Solo una recreación explícita y completa puede reemplazarla.

`test_memory_journal.py`: **11 pruebas satisfactorias**, con cuatro puntos de interrupción (`before`, `partial`, `afterwrite`, `beforeACK`) tanto al guardar como al borrar. Tras reiniciar se recupera el dato anterior o el nuevo completo; después de borrar y confirmar no reaparece el anterior en reinicios sin corrupción adicional. Se comprueban recreación truncada tras borrado, CRC de cabecera/contenido, ambas ranuras corruptas, secuencia ambigua, wrap, aislamiento entre tres nombres y tamaños 0, 150820 y 163840 bytes. Resultados y hashes: `recovery-test-results.json`.

El fallo `beforeACK` escribe el registro completo pero provoca un error en la lectura de verificación. La operación no devuelve éxito y la política se bloquea, aunque tras reiniciar puede aparecer el nuevo estado completo. Esa ambigüedad está documentada; no promete un commit imposible de observar.

Límite: pérdida o corrupción arbitraria posterior de una tombstone válida puede permitir seleccionar un registro antiguo que aún sea válido. Este ensayo no demuestra tolerancia a destrucción del medio ni durabilidad eléctrica; para ello harían falta garantías y pruebas del backend físico. Tampoco reproduce códigos AppUtil, autenticación ni semántica de personajes.

## Bloqueos de aceptación física

- Ninguna llamada del cliente real pasa todavía por esta política. No existen hooks aplicados ni prueba de cobertura total.
- No hay traducción de resultados propios a códigos y estados AppUtil verificados.
- Falta resolver la identidad de guardado y los montajes en el paquete final.
- Existe recuperación sintética de bytes y tombstone en RAM. Falta backend nativo con garantías de persistencia, tratamiento de errores y revisión de todos los accesos alternativos.
- El centinela de memoria demuestra el alcance del ensayo, no protección del original en VitaOS.
- No instalar ni ejecutar un paquete de cliente real basándose en estas pruebas.

Reversión de esta entrega: no se cambió ningún original ni paquete. La herramienta no instala nada. Puede omitirse su incorporación; solo se han creado estos archivos propios.
