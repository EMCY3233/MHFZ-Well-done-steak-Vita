# Publicación del resultado del trabajador de borrado

27-10-2026. Instrucciones originales de8213c3ec..8213c4b0 contrastadas con objdump. No se ejecutó SlotDelete ni se borró ningún archivo.

El trabajador exige estado+90=6. Si no coincide y resultado+9c era cero, publica4; si ya había otro resultado, lo conserva. Después restablece+90 a cero mediante secuencia exclusiva y termina. Esto diferencia una finalización por estado incorrecto de un borrado correcto.

Con estado6 llama a SlotDelete(0,0). Después consulta el resultado interno existente. Si ya era distinto de cero, no lo sustituye por una traducción del retorno de la API. Si era cero, clasifica el retorno mediante comparaciones signed32 con cero y constantes del intervalo80100600..80100643. **Retorno API cero lleva a resultado interno cero**. Un negativo no incluido en casos especiales lleva a4. No se asignan aún nombres semánticos a todas las constantes especiales.

Antes de almacenar, el valor intermedio8 se convierte en1. El trabajador escribe el resultado en+9c y solo después restablece+90 a cero. El consumidor8211d484 espera+90=0 antes de leer+9c; sustituir el trabajador por un desbloqueo sin publicación coherente rompería esta secuencia. Este orden de instrucciones no constituye por sí solo una demostración completa de sincronización entre hilos o barreras de memoria.

El resultado interno0 acredita la rama local seleccionada tras retorno cero de SlotDelete, no una verificación independiente del borrado. Para el laboratorio, el diario propio debe confirmar la marca de borrado antes de traducirla a finalización correcta; no reutilizar sin más un retorno aceptado de solicitud ni una escritura todavía incierta.

Próximo análisis: contrastar la publicación equivalente en el trabajador de guardado8213c7c0 y mantener separados códigos de API, resultado interno y retorno del consumidor. No simplificar las comparaciones signed a rangos unsigned. No existen hooks integrados ni autorización física nueva.