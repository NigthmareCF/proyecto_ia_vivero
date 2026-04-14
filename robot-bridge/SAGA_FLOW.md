# Robot Bridge

1. El robot envia heartbeats, observaciones y estado al bridge.
2. El bridge reenvia al backend Spring Boot cuando esta disponible.
3. El bridge publica actualizaciones en WebSocket para monitoreo local.
4. Si el backend falla, el bridge conserva eventos en memoria para reintento.
