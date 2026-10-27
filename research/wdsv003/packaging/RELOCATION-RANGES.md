# Campos y destinos de las relocaciones reales

27-10-2026. reloc0.py decodifica únicamente forma 0, la observada en todos los registros. Valida índices de segmentos de símbolo/destino y que la escritura primaria/secundaria quepa en memoria. No modifica ni aplica registros.

Resultado de los 475219 registros:

| Tipo ARM | Cantidad | Destino observado |
|---|---:|---|
| 47, Thumb MOVW absoluto | 176269 | Segmento LOAD 0 |
| 48, Thumb MOVT absoluto | 176269 | Segmento LOAD 0 |
| 2, ABS32 | 122681 | 73067 en LOAD 0; 49614 en LOAD 1 |

No hay operaciones secundarias. Todos los índices observados son LOAD 0/1; los destinos comprobados caben en sus segmentos y ninguno empieza en BSS. No se detectan tipos desconocidos ni errores de rango bajo estas reglas. Cinco pruebas nuevas del decoder pasan; el conjunto de lectores suma 26.

Esto reduce el trabajo de reconstrucción a tres tipos realmente presentes, pero no valida todavía los opcodes MOVW/MOVT ni comprueba que el valor codificado corresponda a símbolo+addend. No basta contar una cantidad igual de MOVW/MOVT para emparejarlas correctamente. Tampoco se ha estudiado orden/solapamiento de escrituras ni referencia a nuevas áreas añadidas.

Siguiente comprobación: comparar, sin escribir, el resultado esperado en las bases declaradas con los valores/instrucciones originales. Ese ensayo de desplazamiento cero puede detectar incoherencias de metadatos; no demuestra arranque ni aislamiento. No se genera SELF nuevo en esta fase.

Fuentes de formato y tipos: referencias primarias fijadas en RELOCATION-FRAMING.md. Implementación Python propia; ningún código del cliente se publica.
