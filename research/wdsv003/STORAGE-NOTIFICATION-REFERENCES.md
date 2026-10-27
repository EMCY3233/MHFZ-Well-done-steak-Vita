# Referencias al notificador recuperadas desde relocaciones

27-10-2026. Un barrido de punteros literales8211d218/8211d219 en PT_LOAD no encontró coincidencias. Esto no era ausencia de referencias: al recorrer los475219 registros de relocación se localizaron dos pares MOVW/MOVT que materializan el puntero Thumb8211d219.

| Sitios de instrucciones | Destino materializado | Uso contrastado en bytes originales |
|---|---|---|
| 8211d5aa /8211d5ae | 8211d219 | Se prepara r2, r1=0 y se llama a8211d484 en8211d5b4 |
| 823cd526 /823cd52a | 8211d219 | Se prepara r2, r1=1 y se llama al mismo helper en823cd530 |

save-notification-pointer-candidates.json conserva offsets de registros, tipos y hash fuente, sin bytes comerciales. La consulta calcula base del segmento símbolo+addend y compara el resultado completo; no aplica fixups ni interpreta solo la mitad baja de una dirección.

Ambos sitios pasan la dirección como argumento: no son llamadas directas al notificador. Esto aporta un vínculo concreto para estudiar callback y estados; falta comprobar si8211d484 lo almacena o invoca y con qué argumentos. El segundo sitio evalúa su retorno y cambia estados locales; no se asigna aún significado de éxito de guardado a esos números.

Próximo análisis:8211d484 y su consumidor del tercer argumento, seguido de8211d5dc si conecta la misma secuencia. No repetir escaneos de literales vacíos ni afirmar ausencia a partir de referencias Ghidra parciales. El resultado+9c del trabajador sigue pendiente de relacionar con esta ruta.