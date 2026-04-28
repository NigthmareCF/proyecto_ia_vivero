# Robot Pi: Instalacion y Ejecucion con Docker

Guia actualizada para levantar el runtime de `robot-pi` en Raspberry Pi 5 usando CLI y Docker.

## 1. Requisitos previos

- Raspberry Pi OS 64-bit.
- Docker Engine y Docker Compose Plugin.
- I2C habilitado si usas LCD.
- Camaras visibles en `/dev/video*`.
- Sensores y GPIO cableados segun la documentacion del circuito.

## 2. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 3. Habilitar interfaces necesarias

```bash
sudo raspi-config
```

Activar:

- `Interface Options -> I2C -> Enable`
- `Interface Options -> Camera -> Enable` si usas CSI

## 4. Preparar variables de entorno

```bash
cp .env.example .env
nano .env
```

Variables clave para trabajo local en la red actual:

- `BACKEND_BASE_URL=http://192.168.1.27:8080/api`
- `BACKEND_WS_URL=ws://192.168.1.27:8080/api/ws/robot-stream`
- `ROBOT_ID=ROBOT-001`
- `WIFI_SSID=Redmi Note 14`
- `WIFI_PASSWORD=tashycora`

La configuracion WiFi de la Raspberry Pi ya fue creada con NetworkManager para priorizar el hotspot `Redmi Note 14` como red oculta. No hace falta recrearla para levantar el runtime; estas variables quedan como referencia operativa del robot.

## 5. Verificar hardware

```bash
ls /dev/video*
ls /dev/i2c-1
```

## 6. Levantar el runtime

```bash
docker compose up --build -d
```

## 7. Ver logs

```bash
docker compose logs -f robot
```

## 8. Reinicio o apagado

```bash
docker compose restart robot
docker compose down
```

## 9. Comportamiento esperado

Al iniciar correctamente, el runtime:

- inicializa GPIO, LCD, LED y buzzer
- abre las camaras
- entra en `IDLE`
- comienza a enviar `heartbeat`
- queda listo para recibir comandos REST del backend
- envia el stream por WebSocket raw al endpoint `/api/ws/robot-stream`

## 10. Notas de operacion

- La camara frontal queda dedicada al stream.
- Las camaras laterales se usan para QR y rafaga de fotos.
- El backend puede cambiar la camara activa de stream enviando el comando `CAMERA_SELECT`.
- Por compatibilidad, el runtime tambien acepta `SWITCH_CAMERA`.
- El payload esperado es `{ "camera": "front" }`, `{ "camera": "left" }` o `{ "camera": "right" }`.
- Si el backend cae, las observaciones se quedan en cola local y se reintentan despues.
