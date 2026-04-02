# SAGA FLOW - Module Robot

## Proposito

El modulo `robot` centraliza el estado actual del robot y los comandos que recibe desde REST o WebSocket.
Permite consultar el estado, enviar comandos de control y relanzar el stream de camara hacia el frontend.

## Flujo principal

1. El frontend consulta `/api/robot/status`
2. El backend devuelve el ultimo `RobotStatus` persistido
3. El frontend o bridge envian comandos a `/api/robot/command` o `/app/robot/control`
4. `RobotServiceImpl` actualiza el estado y registra el ultimo comando
5. `RobotWebSocketController` publica eventos a `/topic/robot/control` y `/topic/robot/stream`

## Reglas de negocio actuales

- `ADMIN` y `OPERATOR` pueden enviar comandos
- `VIEWER` solo puede consultar estado
- si no existe estado previo, se crea uno inicial en modo `IDLE`
- `GOTO_PLANT` actualiza `currentPlantQr`
- `MANUAL_MOVE` cambia el modo a `MANUAL`