# Primer componente nativo del selector: lector estructural

manifest_reader.c/h leen el mismo manifiesto privado188bytes que batch_manifest.py. Código propio freestanding ARM/Thumb, sin stdio, libc, heap, archivos ni llamadas a VitaOS. Conserva la salida intacta ante error, y comprueba CRC, generación, orden de miembros, estado, slot, secuencia, longitud y campos reservados.

check_manifest_arm.py compila y ejecuta este código en Unicorn. Pasan208 casos, predominantemente truncamientos: cuatro manifiestos válidos contrastados contra el lector Python,188 longitudes truncadas, otros14 malformados y dos argumentos nulos. Incluye límite estructural512036bytes por registro. Los buffers de prueba y las referencias son sintéticos; no hay lectura de partidas.

No es todavía el selector nativo completo: no verifica SHA256 de los registros referidos, sus envolturas, disponibilidad ni generación visible. La implementación Python snapshot.py sigue siendo la referencia de esa selección. No se cambió el límite del backend ni se implementó escritura del lote. No atribuir208 casos de estructura a cobertura de recuperación, servicios offline o cliente real.

Reproducción local: ejecutar check_manifest_arm.py con el runtime que disponga de Unicorn y el VitaSDK inventariado. El ELF propio generado permanece local y no se instala. manifest-reader-arm-results.json registra hash y cantidades; CI sigue ejecutando solo las pruebas Python hasta disponer de compilador/emulador en ese entorno.

Siguiente paso: resolución de registros nativa con digest/CRC/secuencia y selección de manifiesto completo, conservando rechazo de conflictos. No repetir pruebas de contadores o del mismo formato salvo cambios o fallos nuevos.