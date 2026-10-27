# Fronteras del staging y dependencias nativas

27-10-2026. Clasificación estática por nombres del inventario histórico, sin copiar, modificar ni ejecutar archivos. No constituye una lista de archivos autorizados para instalar.

## Separación necesaria antes de copiar

| Grupo observado | Tratamiento propuesto, todavía no ejecutado |
|---|---|
| eboot.bin en las tres capas | Mantener cada origen separado y con hash; la unión hipotética seleccionaría rePatch. No mezclar el ELF derivado con un contenedor de otra capa. |
| sce_sys/param.sfo | El inventario de metadatos indica TITLE_ID PCSG00350 tanto en app como patch. Requiere identidad experimental generada y revisada; cambiar el título visible no basta. |
| sce_sys/package/*, clearsign, keystone | Poner fuera del staging automático. No asumir reutilización válida bajo otro Title ID ni compatibilidad de guardado. La exclusión propuesta no demuestra que el paquete restante sea válido. |
| sce_sys/trophy/* | Separar de los recursos de juego: conserva un identificador de trofeos del original. No registrar trofeos originales durante una prueba de laboratorio. |
| LiveArea, manuales, iconos y changeinfo | Son recursos y metadatos comerciales; no publicarlos. Resolver referencias y generar presentación propia para el laboratorio antes de empaquetar. |
| sce_module/* y sce_sys/about/right.suprx | Tratar como ejecutables dependientes, no como recursos inertes. Revisar cargas/importaciones y efectos antes de afirmar aislamiento. |
| Resto de rutas | Contenido todavía sin clasificar exhaustivamente; su ubicación fuera de sce_sys no demuestra ausencia de configuración, scripts, endpoints o estado sensible. |

No se ha leído ni publicado el contenido de keystone, datos de cuenta o partidas en esta clasificación. Los nombres no permiten inferir identidad efectiva de AppUtil, montaje savedata0: o permisos del cargador.

## Dependencias concretas que la unión no resuelve

En app y patch aparecen tres módulos: libc.suprx (206128 bytes), libfios2.suprx (124464) y libult.suprx (51200). También aparece right.suprx (15520) bajo sce_sys/about. Igualdad de tamaño entre capas no demuestra igualdad de bytes; el análisis de colisiones conserva hashes, pero no atribuye comportamiento a esos módulos.

El backend propio usa stdio y ha sido probado con funciones sustituidas en emulación ARM. En el proceso real esas funciones deben enlazarse contra una implementación concreta. No basta que exista libc.suprx: faltan comprobar símbolos disponibles, carga efectiva, errores y compatibilidad del ABI del adaptador. Tampoco interceptar sceIoOpen en un único punto demuestra cobertura de FIOS o llamadas internas de bibliotecas.

Por ello, el siguiente análisis debe relacionar las importaciones stdio del cliente con los módulos inventariados y comprobar qué dependencias necesita el backend compilado. Es un obstáculo concreto previo a integrar código, no una nueva prueba de contadores. Mantener pendientes los efectos transitivos de inicializadores C++ externos.

## Límite de aislamiento

No existe todavía un staging aprobado ni un VPK del cliente real. Las políticas propuestas deben aplicarse a una copia nueva con manifiesto explícito, nunca borrando archivos del original. El inventario, la unión hipotética y esta clasificación no autorizan una prueba física.