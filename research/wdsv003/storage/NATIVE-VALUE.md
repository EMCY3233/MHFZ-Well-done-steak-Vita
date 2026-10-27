# Cuerpo nativo con marca de borrado

27-10-2026. value_body.c/.h implementan un sobre privado en C para insertar como payload no vacío del diario CRC/secuencia existente, sin modificar su formato externo. No es un formato original de Frontier.

Doce bytes de cabecera distinguen dato vivo (incluso vacío) de marca de borrado: magic MZV1, tipo uint32 LE y longitud uint32 LE. El dato eliminado exige longitud cero; tipo desconocido, longitud excesiva, truncamiento y bytes sobrantes se rechazan. La función lectora conserva la salida en errores. El checksum y secuencia corresponden al registro externo existente, no a este cuerpo: no usarlo desnudo como registro recuperable.

check_value_arm.py compila el código propio con VitaSDK para Cortex-A9/Thumb y lo ejecuta mediante Unicorn: 29 casos satisfactorios, incluido límite de 0x28000 bytes, distinción vacío/borrado, entradas inválidas y salida intacta en error. No llama VitaOS ni simula disco. El ELF generado es propio y permanece local; la PR contiene solo fuentes, herramienta y resultados.

Falta integrar este cuerpo con save_journal, definir por dato las ranuras y comprobar el ciclo completo nativo de escritura/recuperación/borrado. Aún no hay backend físico ni hooks del cliente. La existencia de un tombstone válido en memoria no garantiza durabilidad eléctrica ni inmunidad a corrupción posterior. No habilita instalar o ejecutar un VPK.
