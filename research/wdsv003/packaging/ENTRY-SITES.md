# Sitios de entrada frente a relocaciones originales

27-10-2026. Consulta de solo lectura contra el índice completo de475219 relocaciones del ELF derivado, hash fijado en entry-sites.json. Se mapeó cada rango mediante su PT_LOAD y se buscó intersección con intervalos conservadores de cuatro bytes. Los hashes identifican ventanas privadas; no se publican sus bytes.

| Rango candidato | Intersecciones observadas |
|---|---|
| module_start 821409dc, ocho bytes | Ninguna |
| Campo start_entry de module info, 823d2ae4, cuatro bytes | Ninguna |
| Prefijo helper 821408a4, ocho bytes | Una MOVW tipo47; su destino comienza seis bytes después del inicio del prefijo |

La intersección del helper se extiende fuera del rango consultado: cortar un prefijo de ocho bytes podría además cortar una instrucción de cuatro bytes. No se ha elegido ese rango para trampolín ni se copiará como bloque arbitrario. Un cambio del helper necesita límites de instrucciones y adaptación coherente de la relocación; no basta reproducir los primeros ocho bytes.

El pequeño module_start contiene transferencia al helper y dos NOP según el análisis previo. Ausencia de relocaciones en ese rango facilita estudiar una intervención local, pero no demuestra espacio para código, alcance de un salto, contrato de retorno o seguridad antes de TLS/libc. Alterar el campo start_entry también requiere respetar su representación como RVA y el segmento base, además del contenedor. Ninguna alternativa está implementada.

Reproducción del cálculo: inventory.elf/region obtienen segmentos; reloc_intervals.index_records procesa cada PT_SCE_RELA; intersects compara los tres rangos anteriores. No se consultó memoria Ghidra modificada ni se aplicaron relocaciones.

Próximo trabajo: verificar instrucciones y contrato de entrada/retorno del stub y requisitos mínimos de un bootstrap propio sin stdio, antes de diseñar una intervención. El alojamiento sigue sin resolver; no se crea un SELF ni un VPK por este resultado.