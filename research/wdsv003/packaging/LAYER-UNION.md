# Unión hipotética de recursos

27-10-2026. layer_union.py lee únicamente el inventario histórico CSV, SHA-256 `8b47aa9a185431ca69183e602446c63d3576d9ce03084d141e013375f349ea85`. No abre los archivos comerciales indicados en Source ni vuelve a verificar sus hashes.

Bajo la hipótesis explícita app < patch < rePatch, las 8261 entradas se reducen a **7596 rutas y 4036150283 bytes** (unos 4,04 GB decimales). Patch aporta 3102 rutas nuevas, sustituye 508 con contenido distinto y repite 56 con tamaño/hash iguales. RePatch aporta dos rutas nuevas y sustituye 101 distintas. Son transiciones por capa; no 665 archivos sobrantes que deban borrarse.

La unión conserva 37 archivos bajo sce_sys. Por tanto, **no es un árbol preparado para instalar**: falta resolver identidad, metadatos y montajes efectivos. Las capas ganadoras son patch 3596, app 3897 y rePatch 103. El tamaño no incluye espacio adicional de empaquetado, diarios, temporales ni margen del sistema.

Se rechazan raíces ajenas, duplicados dentro de una capa, rutas con traversal o componentes vacíos, hashes mal formados y tamaños negativos. Tres pruebas nuevas comprueban precedencia, colisiones y rechazo de datos malformados; 37 pruebas del conjunto de lectores pasan. Esto valida el cálculo, no la precedencia real ni la integridad actual de recursos.

No se copiaron recursos, generó paquete ni contactó la consola. Siguiente paso: separar en un plan de staging los metadatos y rutas sensibles de los recursos, sin escribir contenido comercial; no autorizar instalación por el mero cierre del inventario.