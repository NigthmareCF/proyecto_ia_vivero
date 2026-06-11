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

Variables clave:

- `BACKEND_BASE_URL=http://IP_O_DOMINIO_BACKEND:3000/api`
- `BACKEND_WS_URL=ws://IP_O_DOMINIO_BACKEND:3000/api/ws/robot-stream?role=robot&robotId=ROBOT-001`
- `ROBOT_ID=ROBOT-001`
- `WIFI_SSID=Redmi Note 14`
- `WIFI_PASSWORD=tashycora`

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
- El backend puede cambiar la camara activa de stream con el comando `SWITCH_CAMERA`.
- Si el backend cae, las observaciones se quedan en cola local y se reintentan despues.
