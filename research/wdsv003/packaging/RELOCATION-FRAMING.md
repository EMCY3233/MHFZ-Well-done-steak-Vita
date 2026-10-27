# Encuadre de las relocaciones principales

27-10-2026. Se contrastaron dos fuentes primarias fijadas: [VitaSDK vita-toolchain](https://github.com/vitasdk/vita-toolchain/blob/008ddc2d7fd4bd16631d1e49cacf308de6f545f1/src/vita-elf-create/sce-elf.h) y [Vita3K](https://github.com/Vita3K/Vita3K/blob/17a8b34017a94f4a5914cc0700ae061a3c506a06/vita3k/kernel/src/relocation.cpp). La implementación propia reloc_framing.py solo reconoce tamaños y formas; no copia su código ni aplica operaciones al ejecutable.

Ambos segmentos PT_SCE_RELA del ELF real se recorren exactamente hasta su final, sin bytes sobrantes: segmento 2, 425605 registros/5107260 bytes; segmento 3, 49614 registros/595368 bytes. **Los 475219 registros observados son forma 0, de 12 bytes.** Esto reduce el siguiente trabajo a esa forma real; no es necesario implementar por intuición todas las formas compactas antes de estudiar este cliente.

Las fuentes consultadas difieren en la partición de ciertos campos de la forma 1 principal; no se eligió una interpretación silenciosamente. Esa discrepancia no afecta al encuadre observado, que no contiene forma 1, y permanece fuera de cualquier transformación propuesta.

Cuatro pruebas nuevas verifican el encuadre, truncamientos y parada en forma desconocida; el conjunto de lectores suma 21 pruebas satisfactorias. Las entradas de prueba son fabricadas, no capturas ni datos del juego.

## Alcance pendiente

Recorrer todos los registros por longitud no valida el segmento de destino, offset, addend, tipo ARM, segunda operación ni instrucción afectada. Tampoco prueba que se pueda añadir código o reconstruir el contenedor. El siguiente paso es decodificar los campos de forma 0 y validar sus rangos contra PT_LOAD, manteniendo bytes originales intactos.

Las reftables de imports procesadas por VitaLoaderRedux son un formato distinto: su aplicación en la base de análisis no sustituye estas relocaciones principales. No se usará la memoria modificada de Ghidra como si fuera el ELF original reconstruido.
