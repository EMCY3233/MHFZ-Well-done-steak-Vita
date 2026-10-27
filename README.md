# MHFZ — Well Done Steak Vita

Investigación de ejecución autónoma de Monster Hunter Frontier Z en PS Vita.

Preparación parcial: [informe WDSV-003](research/wdsv003/README.md), [almacenamiento](research/wdsv003/storage/README.md) e [inventario y empaquetado](research/wdsv003/packaging/REPORT.md).

Incluye herramientas propias, informes técnicos y metadatos cuya publicación autorizó el usuario. No incluye ejecutables comerciales, recursos protegidos, credenciales ni partidas.

24 pruebas locales satisfactorias: 20 de almacenamiento y recuperación simulados y 4 del lector ELF. No hay hooks integrados, cliente autónomo ni paquete seguro validado. Instalación y ejecución física requieren autorización específica.

Pruebas: `python -m unittest discover -s research/wdsv003/storage -p 'test_*.py' -v` y la misma orden con `packaging`.
