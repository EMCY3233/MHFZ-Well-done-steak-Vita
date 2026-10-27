# Registro nativo de commits

audited_store.c reserva dos eventos RAM antes de pedir un commit al diario: inicio y finalización. Registra índice lógico, operación guardar/borrar, fase, resultado propio, longitud y secuencia. No incluye contenido, rutas, identidad ni tokens. Capacidad agotada, un único hueco, contador inválido, índice fuera de rango o secuencia máxima rechazan antes del efecto; no sobrescribe eventos anteriores.

La reserva de finalización evita empezar una escritura sin espacio para registrar su resultado en RAM. No constituye un log persistente: un cierre o corte pierde estos eventos. Los punteros deben ser válidos, los buffers separados y el acceso exclusivo. El constructor del contexto debe asociar índice lógico y backend coherentes; el wrapper no comprueba un contexto arbitrario como si fuera un sandbox.

check_audited_pipeline_arm.py conecta el wrapper con toda la cadena C y stdio simulado: 30 casos satisfactorios. Verifica pares de eventos del commit real, resultados y secuencias; log lleno rechaza tanto guardar como borrar sin abrir archivos ni cambiar su imagen RAM; un solo hueco rechaza; dos huecos permiten guardar y recargar. El harness activa la auditoría mediante WDSV_AUDIT_LOG y conserva su modo anterior sin cambios por defecto.

El código de error -3 pertenece a esta interfaz propia, no es un código Vita/AppUtil. La auditoría cubre commits propios; todavía no captura lecturas, relanzamientos o llamadas del cliente. No existe integración con Frontier, registro en disco ni observación física.
