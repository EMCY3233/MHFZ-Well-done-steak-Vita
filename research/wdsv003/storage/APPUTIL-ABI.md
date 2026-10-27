# Contrato AppUtil contrastado con VitaSDK

apputil_abi_check.c compila correctamente para ARM32/Cortex-A9 con el VitaSDK local, usando C11 y warnings como errores. Son 14 aserciones de compilación, no llamadas al sistema ni pruebas del cliente.

La firma de DataSave recibe cinco argumentos: puntero al descriptor de slot, puntero a archivos, cantidad, contexto de montaje y puntero a tamaño requerido en KB. La instrucción del cliente que guarda el quinto argumento en SP+0 ya fue contrastada en la fase anterior; el cuarto argumento observado es cero. No inventar una firma de cuatro parámetros a partir del pseudocódigo.

Cada SceAppUtilSaveDataFile mide 0x40 bytes: filePath a +0, buf a +4, bufSize a +8, offset de 64 bits a +16, mode a +24 y progDelta a +28. El descriptor FileSlot mide 0x28, SlotParam 0x34c y MountPoint 16 bytes. Los punteros/SceSize son de cuatro bytes y SceOff de ocho. El alineamiento de offset incluye un hueco: empaquetar esta estructura como una concatenación sin alineamiento daría un ABI incorrecto.

Los tamaños 0x40 de entradas y 0x34c de metadatos son consistentes con las reservas observadas en el cliente; no certifican todos los campos ni el contenido dinámico. Los títulos de SlotParam son SceWChar16, no char*: copiar cadenas ASCII a ciegas no define una conversión válida.

El encabezado no explica cómo VitaOS resuelve un MountPoint nulo ni la identidad efectiva del guardado. Tampoco permite traducir automáticamente los códigos propios del backend a errores AppUtil. El resultado de compilación valida compatibilidad con esta versión de cabeceras, no aceptación del firmware real. No se ha construido ni instalado un hook.

Reproducción local: arm-vita-eabi-gcc -std=c11 -mthumb -mcpu=cortex-a9 -Wall -Wextra -Werror -c apputil_abi_check.c. El objeto generado permanece local; el repositorio solo contiene la fuente y este resultado.
