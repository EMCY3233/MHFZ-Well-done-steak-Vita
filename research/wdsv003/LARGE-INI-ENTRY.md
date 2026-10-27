# La entrada temporal mayor corresponde a INI-DATA

27-10-2026. El análisis dirigido del registro8213c2ea y su llamante de inicialización8211b924 relaciona índice4 con INI-DATA. La cadena original en827ef5e0 se verificó leyendo el ELF;827ef5d4 contiene PRI-DATA.

El registro usa entradas de0x1c bytes: nombre en objeto+índice*0x1c+4, tamaño en+0x14, puntero en+0x18 y opción en+0x1c. La inicialización registra índice2 como PRI-DATA con buffer y tamaño0x2000; índice4 como INI-DATA con puntero/tamaño iniciales cero y opción1. Este tamaño cero inicial no implica que INI-DATA siempre sea un archivo vacío.

En el trabajador de guardado, la entrada4 seleccionada recibe temporalmente tamaño0x7d000 y buffer propio. Invoca una operación virtual de otro objeto para prepararlo y finalmente limpia la entrada temporal. La asociación proviene de la combinación de índices y registros; no atribuye por intuición el formato interno ni el tamaño útil efectivamente serializado.

Esto concreta el límite del backend: **INI-DATA puede requerir una capacidad de512000 bytes en esa ruta**, mayor que163840 del laboratorio. No derivar el límite de la prueba de cuerpo de red150820 ni asumir que el nombre INI indica un archivo de configuración pequeño. PRI-DATA y la entrada mayor tienen tamaños y preparación distintos.

Falta contrastar las instrucciones de los argumentos del registro y rastrear el método virtual que llena INI-DATA, incluida longitud real y validación al leer. Antes de aumentar límites debe revisarse el presupuesto de buffers y el formato de registro propio. No se modifica todavía el límite ni se fabrica un INI-DATA del juego.

No hubo ejecución, lectura de partidas personales ni transferencia. La interpretación de configuración/partida asociada a cada nombre sigue siendo parcial; solo se publica la relación técnica índice/nombre/capacidad.