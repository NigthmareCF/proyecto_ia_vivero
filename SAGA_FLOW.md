# SAGA FLOW - Robot Pi

Flujo vigente del runtime del robot.

## 1. Flujo implementado hoy

```text
INICIO
  main.py carga config, perifericos y modelo opcional
  command_listener inicia en hilo separado
  status_sender inicia en hilo separado
  LCD muestra estado inicial
  estado: IDLE

IDLE
  espera comandos
  envia heartbeat

FOLLOW_LINE
  sigue linea
  revisa obstaculos
  captura frame frontal para QR en el flujo actual
  si detecta QR -> QR_DETECTED

QR_DETECTED
  detiene el robot
  guarda plant_qr
  muestra estado
  -> CAPTURING

CAPTURING
  toma rafaga de imagenes
  -> CLASSIFYING opcional o SENDING

CLASSIFYING
  ejecuta IA local si esta habilitada
  -> SENDING

SENDING
  envia observacion al backend
  -> FOLLOW_LINE

MANUAL
  responde a comandos de movimiento
  puede activar stream
  puede cambiar camara activa con CAMERA_SELECT o SWITCH_CAMERA
```

## 2. Flujo objetivo posterior

```text
AUTO_LINE continuo
  QR detectado por lateral
  rafaga sin detener
  backend recibe observacion
  robot continua
```

Estado:

- acordado
- documentado
- no implementado aun

## 3. Regla operativa

No implementar automaticamente el flujo objetivo hasta confirmacion del usuario.

## 4. Cambio de camara

El backend cambia la camara activa del stream enviando el comando `CAMERA_SELECT`. Por compatibilidad con integraciones que lo nombren como switch de camara, el runtime tambien acepta `SWITCH_CAMERA`.

Payloads validos:

```json
{ "camera": "front" }
{ "camera": "left" }
{ "camera": "right" }
{ "activeCamera": "front" }
```

El runtime normaliza valores invalidos a `front`.
