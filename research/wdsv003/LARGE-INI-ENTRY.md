# La entrada temporal mayor corresponde a INI-DATA

27-10-2026. El análisis dirigido del registro8213c2ea y su llamante de inicialización8211b924 relaciona índice4 con INI-DATA. La cadena original en827ef5e0 se verificó leyendo el ELF;827ef5d4 contiene PRI-DATA.

El registro usa entradas de0x1c bytes: nombre en objeto+índice*0x1c+4, tamaño en+0x14, puntero en+0x18 y opción en+0x1c. La inicialización registra índice2 como PRI-DATA con buffer y tamaño0x2000; índice4 como INI-DATA con puntero/tamaño iniciales cero y opción1. Este tamaño cero inicial no implica que INI-DATA siempre sea un archivo vacío.

En el trabajador de guardado, la entrada4 seleccionada recibe temporalmente tamaño0x7d000 y buffer propio. Invoca una operación virtual de otro objeto para prepararlo y finalmente limpia la entrada temporal. La asociación proviene de la combinación de índices y registros; no atribuye por intuición el formato interno ni el tamaño útil efectivamente serializado.

Esto concreta el límite del backend: **INI-DATA puede requerir una capacidad de512000 bytes en esa ruta**, mayor que163840 del laboratorio. No derivar el límite de la prueba de cuerpo de red150820 ni asumir que el nombre INI indica un archivo de configuración pequeño. PRI-DATA y la entrada mayor tienen tamaños y preparación distintos.

## Contraste posterior con instrucciones originales

18:38 UTC. En8211bcb4 se llama al registrador con índice2, buffer objeto+0xb8 y tamaño8192; la dirección del nombre PRI-DATA se prepara como argumento de pila. En8211bccc se llama con índice4, puntero y tamaño cero y el nombre INI-DATA también en pila. Esto corrobora los índices y tamaños sin depender solo del pseudocódigo de seis argumentos.

El trabajador almacena512000 en el tamaño de la entrada en8213ca52, reserva el buffer y lo limpia. En8213ca76 carga de la tabla virtual el método en desplazamiento0x20 y lo llama en8213ca78. El destino concreto sigue pendiente: no es una función directa identificada únicamente por ese desplazamiento.

18:53 UTC. Se corrige la pista del objeto auxiliar del campo5: **no es el receptor demostrado de esta llamada**. El getter8211b918 devuelve el contenedor global839e16d4; en8213ca6a el trabajador carga el puntero del campo0 de ese contenedor, comprueba que no sea nulo y solo después obtiene su tabla virtual. El constructor8211b5bc crea otro objeto almacenado en el campo5; su tabla82b285b0 no permite resolver el método del campo0. No usarla para atribuir el serializador.

La inicialización deja el campo0 a cero. Falta identificar dónde se asigna posteriormente y qué objeto recibe la llamada. Si permanece nulo, el tramo salta la llamada virtual tras haber reservado y limpiado el buffer; esto tampoco demuestra que una partida utilizable sea serializada. La corrección deriva del seguimiento de cargas originales, no de ejecutar el juego.

Falta rastrear ese método, incluida longitud real y validación al leer. Antes de aumentar límites debe revisarse el presupuesto de buffers y el formato de registro propio. No se modifica todavía el límite ni se fabrica un INI-DATA del juego.

No hubo ejecución, lectura de partidas personales ni transferencia. La interpretación de configuración/partida asociada a cada nombre sigue siendo parcial; solo se publica la relación técnica índice/nombre/capacidad.