# Un sexto segmento no cabe ampliando las tablas in situ

27-10-2026. Aritmética de rangos sobre el inventario SELF ya contrastado, sin alterar originales. self-table-capacity.json conserva hash fuente y extremos.

La tabla de cinco program headers empieza en224, ocupa160 bytes y termina en384, exactamente donde empieza section_info. Añadir un sexto descriptor en la misma ubicación extendería la tabla hasta416 y sobrescribiría32 bytes de section_info.

La tabla de cinco section_info empieza en384, ocupa160 bytes y termina en544, exactamente donde empieza sceversion. Añadir su sexto descriptor la extendería hasta576: invade32 bytes a partir de sceversion y también alcanza controlinfo, que comienza en560. Los704 bytes declarados de controlinfo terminan en1264.

Por tanto, la alternativa de añadir un LOAD exige rediseñar la disposición y referencias de las tablas, además de los datos comprimidos, conteos, tamaños y metadatos pertinentes. No basta añadir payload al final del archivo y aumentar phnum. Las regiones posteriores a1264 y anteriores al primer segmento no se clasifican como libres: falta interpretar su función, autenticación y requisitos del cargador.

Esta consulta no acredita que mover tablas sea aceptado ni que añadir un segmento sea compatible con este tipo de módulo. Ampliar un LOAD existente evita un descriptor adicional pero conserva los problemas de límites virtuales, permisos, relocaciones, memoria y contenedor. No se elige una de esas opciones solo porque la otra tenga un solapamiento.

Los bloqueos de tamaño declarado y cola zlib siguen vigentes. No hubo reconstrucción ni paquete. Próximo análisis: identificar estructuras dentro del encabezado y sus relaciones con el número de segmentos mediante fuentes primarias; no tratar bytes desconocidos como espacio para código o tablas.