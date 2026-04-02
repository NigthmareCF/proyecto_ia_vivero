# SAGA FLOW - Module Patrols

## Proposito

El modulo `patrols` registra recorridos del robot y sus resultados parciales.
Permite iniciar patrullajes, guardar observaciones por planta y cerrarlos al finalizar el recorrido.

## Flujo principal

1. Un usuario autenticado inicia `/api/patrols/start`
2. `PatrolServiceImpl` crea el patrullaje en estado `IN_PROGRESS`
3. El robot o bridge reporta resultados a `/api/patrols/{id}/result`
4. Cada resultado crea una `Observation` asociada al patrullaje
5. Cuando termina el recorrido se invoca `/api/patrols/{id}/complete`
6. El patrullaje pasa a `COMPLETED` y queda listo para consultas y reportes

## Reglas de negocio actuales

- `ADMIN`, `OPERATOR` y `VIEWER` pueden consultar patrullajes
- solo `ADMIN` y `OPERATOR` pueden iniciar, registrar resultados y completar patrullajes
- solo se aceptan resultados sobre patrullajes en estado `IN_PROGRESS`
- la observacion guarda `plantQrCode` para no depender todavia del modulo `plants` en esta rama