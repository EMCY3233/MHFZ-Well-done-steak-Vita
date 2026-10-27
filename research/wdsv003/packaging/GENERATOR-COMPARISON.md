# Comparación con el generador primario: padding y tamaño

27-10-2026. Inspección de [vita-make-fself.c, commit008ddc2](https://github.com/vitasdk/vita-toolchain/blob/008ddc2d7fd4bd16631d1e49cacf308de6f545f1/src/vita-make-fself/vita-make-fself.c), blob4117db403748b35a703ab7d6c4cf9c1e4d84e09e. No se ejecutó el generador sobre el cliente.

En su ruta comprimida, el generador escribe cada flujo zlib y añade entre cero y tres bytes cero para redondear su longitud a múltiplo de cuatro. Incluye ese padding en section_info.length. Antes del siguiente segmento posiciona el archivo en un límite de16bytes. Finalmente obtiene el tamaño físico del archivo y lo escribe en self_filesize.

Consecuencias para nuestro lector: **tener bytes después del fin zlib no es por sí solo prueba de corrupción**. Un padding verificado de hasta tres ceros puede corresponder a esta política. El gate actual rechaza toda cola y es deliberadamente más restrictivo; no debe anunciarse como validación universal del formato. Para admitir padding futuro deberá inspeccionar sus bytes y la aritmética de alineación, no aceptar solo una cantidad declarada.

La cola observada de21bytes en el segmento0 no queda explicada por ese redondeo de hasta tres. Tampoco los848bytes de diferencia del tamaño declarado corresponden al comportamiento final del generador consultado. Son diferencias respecto a esta implementación, sin atribuir causa ni concluir que la copia instalada no funcione. El digest tipo4 sí coincide con el ELF derivado: coherencia de datos descomprimidos y anomalías de disposición pueden coexistir.

Una reconstrucción futura tendría que declarar si conserva una disposición original aún no explicada o produce una representación canónica conforme a un generador concreto. Esas salidas no serían necesariamente idénticas byte por byte aunque sus segmentos descomprimidos coincidan. No cambiar el original para hacer desaparecer las diferencias ni usar esa equivalencia como prueba de carga.

Próximo cambio acotado: distinguir padding verificado y cola no explicada en el lector, con pruebas que rechacen longitudes mayores, bytes no cero y alineación incorrecta. La copia real seguirá bloqueada por21bytes y tamaño declarado; no reconstruir hasta cerrar el resto del contrato.