# Consistencia con las bases originales

zero_delta.py compara cada relocación principal con el valor ya almacenado en el ELF derivado, usando las bases declaradas de sus segmentos y aritmética de 32 bits. No escribe ni aplica transformaciones.

**Los 475219 registros coinciden:** 122681 valores ABS32 y 352538 instrucciones Thumb MOVW/MOVT reproducen la mitad correspondiente de símbolo+addend. Los opcodes de las instrucciones comprobadas también cumplen sus máscaras de formato. No se encontraron destinos sin respaldo de archivo, operaciones secundarias, tipos inesperados ni discrepancias en este ensayo.

Cuatro pruebas nuevas verifican vectores Thumb fijos, rechazo de opcode incorrecto, ABS32 y suma con desbordamiento de 32 bits. El conjunto de lectores suma 30 pruebas satisfactorias.

Este resultado refuerza que los metadatos de relocación y los valores originales son coherentes **en las bases originales**. No acredita reubicación a otras bases, corrección de un escritor, orden/solapamiento de destinos, conservación de todas las instrucciones al parchear, reconstrucción SELF, aceptación del cargador ni aislamiento de la aplicación.

El siguiente requisito de una transformación es comprobar destinos superpuestos y definir qué cambios de código/datos necesitan actualizar sus relocaciones. Mantener un parche que modifica un literal sin actualizar la relocación correspondiente podría ser deshecho por el cargador. No se ha generado un ejecutable modificado en esta fase.

Formato de las operaciones contrastado con las fuentes primarias fijadas en RELOCATION-FRAMING.md; implementación y pruebas propias. Las salidas públicas contienen recuentos y localizaciones de discrepancias (vacías aquí), nunca instrucciones ni payload comercial.
