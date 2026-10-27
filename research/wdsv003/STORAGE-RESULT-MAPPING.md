# Traducción observada del resultado en8211d484

27-10-2026. Se decodificaron las nueve entradas TBB de8211d4b6 y se siguieron sus destinos en instrucciones originales. save-result-switch.json contiene direcciones y hash fuente; no bytes ni pseudocódigo comercial.

Con estado+90 distinto de cero, el helper devuelve0 sin consultar resultado. Con estado cero:

| Resultado interno+9c | Callback (primer, segundo argumento) | Retorno del helper |
|---|---|---|
| 0 | No llama | 1 |
| 1,2,6,7,8 o valor fuera de0..8 | (1,3) | 6 |
| 3 | (1,4) | 6 |
| 4 | (1,5) | 6 |
| 5, opción del helper cero | (1,3) | 6 |
| 5, opción del helper distinta de cero | (0,0) | 4 |

La opción es el segundo argumento que se pasó al helper; no el primer argumento que este entrega al callback. Los sitios previos usan opciones0 y1. En este recorrido se invoca el callback y después se fija el retorno, sin comprobar el valor devuelto por el callback. Por tanto, el retorno6 no demuestra que se haya abierto un diálogo correctamente.

El notificador8211d218 usa su segundo argumento para elegir la rama: cero llega al helper SaveDataDialog; valores3/4/5 indexan una tabla de mensajes hacia MsgDialog. No se publica ni atribuye el texto de esos mensajes sin verificar codificación/procedencia. Estas rutas describen presentación y control local, no los códigos originales de VitaOS.

La tabla resuelve el mapeo mecánico del consumidor; falta atribuir significado a cada resultado en los trabajadores de lectura, guardado y borrado. No equiparar+9c=0 a persistencia física sin revisar dónde y después de qué comprobación lo publica el trabajador. Próximo análisis acotado: asignaciones+9c en8213c3ec y8213c7c0, incluida secuencia respecto al reinicio+90.