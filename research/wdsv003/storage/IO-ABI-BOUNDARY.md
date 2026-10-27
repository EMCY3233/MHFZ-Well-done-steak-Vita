# Frontera ABI de apertura: wrapper y exportación

27-10-2026. Antes de sustituir stdio por E/S nativa se compararon las declaraciones locales, sin ejecutar código. El SDK instalado declara sceIoOpen con tres argumentos. La copia de fuentes vita-headers conserva esa interfaz y además declara **_sceIoOpen con cuatro argumentos**, incluido un puntero a sceIoOpenOpt. Su comentario exige el bloque de opciones para la exportación de usuario y describe su contenido como ignorado en FW 3.60. Esta descripción es evidencia documental, no una prueba en la consola del usuario.

Hashes SHA-256 de psp2/io/fcntl.h: SDK instalado `11a0e01fb3573fae04e4338760662ad3e415c83ae6cedd866ecd5e16dd51832f`; fuentes locales `82e4ef7896bf15efa11e89df5f4a78f4fc62df0098a372358c10bcb8b0126c68`. La diferencia impide tratar ambas copias como una única versión del contrato.

El inventario del cliente identifica NID 0x6c60ac61 en SceLibKernel, stub 0x823d27c0. La base local db/360 lo etiqueta sceIoOpen. **Ese nombre no demuestra que el punto de enlace tenga el ABI del wrapper de tres argumentos.** Un adaptador colocado en la celda importada debe contrastar las instrucciones del llamante y el destino real; un backend compilado contra un wrapper debe enlazar también la implementación correcta de ese wrapper.

No se corrigió la firma del cliente por suposición. Tampoco se implementó aún la traducción de archivo ausente: la búsqueda acotada en encabezados locales no aportó una constante de error de archivos atribuible con certeza a sceIoOpen. No reutilizar SCE_NET_ENOENT ni un valor recordado como si fuera evidencia del subsistema de archivos. Un negativo desconocido debe seguir siendo fallo, no ranura ausente.

sceIoSyncByFd aparece con segundo argumento documentado como desconocido en el SDK instalado. Por tanto, añadir una llamada con cero no demostraría durabilidad ante pérdida eléctrica. La lectura posterior sigue siendo una comprobación de contenido, no garantía de persistencia física.

## Contraste posterior: son exportaciones distintas

12:38 UTC. La base db/360/SceIofilemgr.yml asigna **_sceIoOpen a NID 0xcc67b6fd**, mientras db/360/SceLibKernel.yml asigna **sceIoOpen a 0x6c60ac61**. El cliente importa este último desde SceLibKernel. Esto resuelve la ambigüedad de identificación: el puntero de opciones del export de cuatro argumentos no debe trasladarse al hook del wrapper de tres argumentos solo por semejanza de nombres.

La ventana original del llamante prepara r0 con la ruta, r1=1 y r2=0 inmediatamente antes de 8213c618. No prepara r3 después de una llamada previa que puede alterarlo. Es coherente con el contrato de tres argumentos del wrapper; no demuestra por sí sola cómo funciona su implementación interna.

El miembro SceLibKernel_SceLibKernel_sceIoOpen.o de libSceLibKernel_stub.a contiene metadatos de enlace y NID 0x6c60ac61, no el cuerpo del wrapper del sistema. Inspeccionarlo no permite reconstruir manejo de errores o un cuarto argumento interno. La búsqueda en libc.a no localizó una implementación sceIoOpen; no se deduce ausencia en otras bibliotecas o en el sistema.

Próximo análisis acotado: ABI de lectura/escritura/cierre y fuente primaria para códigos de error de archivos antes de implementar callbacks. La elección de sceIoOpen con tres argumentos ya está respaldada por biblioteca, NID, declaración y llamante; queda sin demostrar su comportamiento físico. No hay backend nativo nuevo, parche ni autorización de prueba física.