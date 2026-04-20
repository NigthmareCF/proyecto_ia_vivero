# Robot Pi: Instalacion y Ejecucion con Docker

Guia actualizada para levantar el runtime del `robot-pi` en Raspberry Pi 5.

## 1. Requisitos previos

- Raspberry Pi OS 64-bit.
- Docker y Docker Compose instalados.
- I2C habilitado si usas LCD.
- Camaras detectadas por Linux.
- Sensores y GPIO conectados segun la documentacion de circuito.

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

## 4. Verificar dispositivos

```bash
ls /dev/video*
ls /dev/i2c-1
```

## 5. Preparar variables de entorno

Si existe `.env.example`, copialo:

```bash
cp .env.example .env
nano .env
```

Valores importantes:

- `BACKEND_BASE_URL=http://IP_DEL_BACKEND:8080/api`
- `BACKEND_WS_URL=ws://IP_DEL_BACKEND:8080/api/ws`
- `HEARTBEAT_PATH=/robot/heartbeat`
- `OBSERVATION_PATH=/robot/observations`
- `CAMERA_FRONT_INDEX=0`
- `CAMERA_LEFT_INDEX=1`
- `CAMERA_RIGHT_INDEX=2`
- `ROBOT_ID=ROBOT-001`

Compatibilidad:

- si ya existia `BRIDGE_URL`, el runtime la sigue aceptando como fallback
- para configuraciones nuevas, usar `BACKEND_BASE_URL`

## 6. Modelos opcionales

Si usaras IA local, coloca en `robot-pi/models/`:

- `modelo_vivero.tflite`
- `labels.txt`

Si no usaras IA local, el runtime puede levantarse igual.

## 7. Levantar el contenedor

```bash
docker compose up --build -d
```

## 8. Logs

```bash
docker compose logs -f robot
```

## 9. Detener o reiniciar

```bash
docker compose restart robot
docker compose down
```

## 10. Comportamiento esperado al iniciar

Al arrancar correctamente:

- inicializa GPIO
- inicializa camaras
- inicializa LCD/LED/buzzer si estan habilitados
- entra en `IDLE`
- comienza a enviar `heartbeat`
- queda listo para recibir comandos

## 11. Limitaciones actuales

El runtime actual:

- no hace todavia captura en movimiento sin detenerse
- no ofrece aun streaming real completo de tres camaras
- no debe considerarse la implementacion final de concurrencia

## 12. Problemas comunes

### No detecta camaras

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

Ajusta luego:

- `CAMERA_FRONT_INDEX`
- `CAMERA_LEFT_INDEX`
- `CAMERA_RIGHT_INDEX`

### No conecta al backend

Revisa:

- `BACKEND_BASE_URL`
- `BACKEND_WS_URL`
- rutas `HEARTBEAT_PATH` y `OBSERVATION_PATH`
- puerto `8080`
- firewall

### Falla por permisos de hardware

Revisa que `docker-compose.yml` incluya:

- `privileged: true`
- `network_mode: host`
- acceso a `/dev`
- dispositivos de video
- `/dev/i2c-1` si usas LCD
