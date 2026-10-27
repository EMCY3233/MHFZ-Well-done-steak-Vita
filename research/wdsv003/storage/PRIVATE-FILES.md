# Adaptador nativo de archivos privados

private_files.c usa un contexto con índice lógico (0 ini, 1 pri, 2 personaje) y ranura 0/1. private_paths.c devuelve una de seis rutas constantes bajo ux0:data/MHFZL0001/wdsv003. No recibe nombres de archivo, no crea directorios, no borra archivos ni modifica los datos del laboratorio 00.03/00.04. Un contexto nulo, índice inválido o ranura inválida se rechaza antes de abrir un archivo. El llamante debe proporcionar un contexto válido en memoria; no es un sandbox para punteros arbitrarios.

La lectura comunica tamaño real, distingue ENOENT de error y detecta bytes que excedan la capacidad. Lecturas/escrituras parciales positivas se acumulan; errores de apertura, transferencia, fflush y fclose se propagan. La escritura acepta registros de 36 a 163876 bytes (sobre + cuerpo + registro externo). El directorio debe existir de antemano; ninguna prueba lo crea en consola.

32 casos de código ARM propio con stdio simulado pasan: seis destinos separados, entradas inválidas sin apertura, contexto nulo, límites de tamaño, EOF y errores de E/S/cierre. Los callbacks simulados verifican cada ruta abierta y que no queden descriptores activos. No se ejecutó el filesystem VitaOS ni disco real.

fflush/fclose no constituyen prueba de durabilidad frente a pérdida eléctrica. El diario debe verificar el registro tras escribir y conservar el otro slot. Los accesos deben ser exclusivos para evitar carreras. Todavía falta ensayar conjuntamente value_journal + private_files y conectar el cliente real; no existe mediación de sus APIs AppUtil o savedata0. Estas rutas fijas solo limitan este componente propio.
