# SAGA FLOW - Robot Pi

INICIO
  main.py carga config, GPIO, modelo TFLite
  command_listener inicia en hilo separado
  status_sender inicia en hilo separado
  LCD muestra "AgroTech Ready"
  LED verde ON
  estado: IDLE

IDLE
  espera comando START_PATROL del backend
  envia status cada 10s

FOLLOW_LINE
  lee sensores de linea y ajusta motores
  verifica sensor ultrasonico en cada ciclo
  si hay obstaculo: stop, espera, intenta correccion
  captura frame y busca QR valido
  si detecta QR -> QR_DETECTED

QR_DETECTED
  detiene motores
  guarda el plant_qr actual
  LCD muestra el QR
  LED amarillo ON
  -> CAPTURING

CAPTURING
  captura 3 fotos simultaneas: izquierda, frontal y derecha
  LCD muestra "Analizando..."
  -> CLASSIFYING

CLASSIFYING
  ejecuta inferencia local TFLite
  consolida clase final y confianza
  -> SENDING

SENDING
  codifica imagenes a base64
  POST al bridge con patrol_id, plant_qr y resultado
  si el resultado es peligro: LED rojo + buzzer
  -> FOLLOW_LINE

MANUAL
  activa stream de camara
  responde a comandos MOVE en tiempo real
  espera AUTO o STOP
