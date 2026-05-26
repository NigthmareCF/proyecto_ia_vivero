# Resumen Operativo V2

## Contexto base

- Runtime Pi activo: `C:\Proyecto_IA_Vivero\worktrees\robot-pi\robot-pi`
- Rama runtime Pi: `funcionalidad/robot-pi-runtime`
- Frontend revisado/modificado en: `C:\Proyecto_IA_Vivero\worktrees\frontend\vivero-frontend`
- Backend a cruzar con frontend/runtime: `C:\Proyecto_IA_Vivero\worktrees\frontend\vivero-backend`
- Rama frontend: `funcionalidad/frontend`

## Nota estructural clave

- Muchos cambios del proyecto estan interconectados y no deben evaluarse como piezas aisladas.
- Los cambios internos de hardware, como control de motores, PWM, sensores o cableado, viven dentro del runtime de la Pi.
- Los cambios de operacion remota del robot no terminan en el frontend: el frontend captura acciones del usuario, pero obligatoriamente deben pasar por el backend para convertirse en comandos hacia la Pi.
- En consecuencia, para dar por valido un cambio funcional hay que revisar el flujo completo `frontend -> backend -> runtime Pi`, y tambien el retorno `runtime Pi -> backend -> frontend` para estado, heartbeat, streaming y telemetria.

## Limpieza hecha

- Se elimino `vivero-backend` de la worktree `robot-pi` porque no aporta al despliegue directo dentro de la Pi.
- Se corrigio la documentacion `documentacion_local_raiz/pines_circuito_colores.md` para dejar consistente el cableado util.

## Mapeo final de pines adoptado en codigo

### Motores

- `IN1=17`
- `IN2=27`
- `IN3=22`
- `IN4=23`
- `ENA=18`
- `ENB=25`

### Linea

- `LEFT=13`
- `CENTER=19`
- `RIGHT=16`

### Obstaculos

- Ultrasonico `TRIG=5`, `ECHO=6`
- IR trasero izquierdo `8`
- IR trasero derecho `9`

### Interfaz

- LCD `SDA=2`, `SCL=3`
- LED verde `12`
- LED amarillo `24`
- LED rojo `26`
- LED azul `20`
- buzzer `21`

## Cambios importantes en runtime Pi

- Watchdog manual implementado.
- Timeout manual actual: `0.3s` mediante `MANUAL_COMMAND_TIMEOUT_SECONDS=0.3`.
- `MOVE` puede armar `MANUAL` por si solo.
- PWM real de motores por `ENA/ENB`; ya no se usa pseudo-PWM en pines de direccion.
- `speedProfile` ahora si afecta la velocidad real.

### Perfiles actuales

- `LOW=30`
- `MEDIUM=45`
- `HIGH=65`
- `TURBO=85`
- `CUSTOM_xx` soportado

### Reversa protegida por IR traseros

- Si `GPIO8/9` detectan obstaculo, bloquea retroceso manual y la reversa de `ACRO`.
- Registra razon en telemetria.

### LED azul

- `idle`: respiracion
- `heartbeat sano`: parpadeo
- `heartbeat fallido`: parpadeo rapido

### Otros ajustes

- `obstacle_count` frontal ahora se resetea cuando vuelve a estar libre.

## Nuevas configs en `.env` y `.env.example`

- `MANUAL_COMMAND_TIMEOUT_SECONDS=0.3`
- `SPEED_PROFILE_LOW=30`
- `SPEED_PROFILE_MEDIUM=45`
- `SPEED_PROFILE_HIGH=65`
- `SPEED_PROFILE_TURBO=85`
- `REAR_IR_ACTIVE_HIGH=true`
- `HEARTBEAT_LED_BLINK_INTERVAL_SECONDS=0.5`
- `HEARTBEAT_LED_FAST_BLINK_INTERVAL_SECONDS=0.2`
- `HEARTBEAT_LED_BREATHE_STEP_SECONDS=0.04`
- `HEARTBEAT_LED_BREATHE_STEP_DUTY=5`

## Telemetria / heartbeat ahora expone ademas

- `currentSpeedPercent`
- `rearObstacleLeft`
- `rearObstacleRight`
- `rearObstacleDetected`
- `lastWatchdogTriggeredAt`
- `lastWatchdogReason`
- `lastHeartbeatAt`
- `lastHeartbeatStatus`

## Frontend manual remoto

- Teclado implementado en `RobotControlPage.tsx`

### Controles

- `ArrowUp` avanzar
- `ArrowDown` retroceder
- `ArrowLeft` izquierda
- `ArrowRight` derecha
- Al soltar tecla: `STOP`

### Reenvio continuo

- Mientras mantienes tecla: cada `90ms`

### Atajos

- `A` auto
- `M` manual
- `X` acro
- `1/2/3` camaras
- `Q/W/E/R` perfiles `LOW/MEDIUM/HIGH/TURBO`
- `P` abre potencia custom para `ADMIN`

### Roles

- `ADMIN` y `CONTROLLER`: acceso a perfiles estandar
- `ADMIN`: ademas perfil custom

### UI muestra

- Perfil de potencia
- `% PWM` activo
- Obstaculo trasero
- Ultima razon de corte defensivo si existe

## Verificaciones hechas

- `python -m compileall` del runtime: OK
- `npm run build` del frontend: OK

## Pendientes relevantes

- Probar hardware real en la Pi:
  - LED azul
  - PWM ENA/ENB
  - IR traseros
  - reversa
  - watchdog manual con teclado real
- Ver si `rear_ir_active_high=true` coincide con el comportamiento fisico real.
- Validar flujo completo de comunicacion entre frontend, backend y runtime Pi para cada accion importante.
- Si luego quieres respaldo movil, la opcion recomendable no es Bluetooth con stream, sino un modo local Wi-Fi/hotspot servido por la Pi.

## Decisiones ya tomadas

- No extender por ahora el watchdog a `AUTO/ACRO`.
- Mantenerlo solo para `MANUAL`, mas bloqueo defensivo de reversa.
