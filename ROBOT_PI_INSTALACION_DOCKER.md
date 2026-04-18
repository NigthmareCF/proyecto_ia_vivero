# Robot Pi: Instalacion y Ejecucion con Docker

Guia rapida para levantar el runtime del `robot-pi` en una Raspberry Pi 5 usando Docker.

## 1. Requisitos previos

- Raspberry Pi OS 64-bit instalado.
- Docker y Docker Compose disponibles.
- I2C habilitado si usas LCD.
- Camaras detectadas por Linux.
- Sensores y GPIO conectados fisicamente.

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

Activa:

- `Interface Options -> I2C -> Enable`
- `Interface Options -> Camera -> Enable` si usas CSI

## 4. Verificar dispositivos

Comprueba que las camaras existan:

```bash
ls /dev/video*
```

Si usas LCD por I2C:

```bash
ls /dev/i2c-1
```

## 5. Ubicarse en la carpeta del robot

```bash
cd /ruta/a/C:\Proyecto_IA_Vivero/worktrees/robot-pi
```

Si estas ya en la Raspberry con el repo clonado:

```bash
cd worktrees/robot-pi
```

## 6. Crear el archivo de entorno

Copia la plantilla:

```bash
cp .env.example .env
```

Edita:

```bash
nano .env
```

Valores importantes:

- `BRIDGE_URL=http://IP_DEL_BACKEND:8080`
- `BACKEND_WS_URL=ws://IP_DEL_BACKEND:8080/ws`
- `CAMERA_FRONT_INDEX=0`
- `CAMERA_LEFT_INDEX=1`
- `CAMERA_RIGHT_INDEX=2`
- `ROBOT_ID=ROBOT-001`

Nota:

- Aunque la variable se llama `BRIDGE_URL`, en el codigo actual apunta al backend HTTP que recibe `heartbeat` y `observations`.

## 7. Modelos opcionales

Si vas a usar IA local opcional, coloca estos archivos en:

```bash
robot-pi/models/
```

Archivos:

- `modelo_vivero.tflite`
- `labels.txt`

Si no usaras IA local, el robot puede levantarse igual y solo capturar/enviar observaciones al backend.

## 8. Levantar el contenedor

Desde `worktrees/robot-pi`:

```bash
docker compose up --build -d
```

## 9. Ver logs

```bash
docker compose logs -f robot
```

## 10. Verificar estado del contenedor

```bash
docker ps
docker compose ps
```

## 11. Reiniciar

```bash
docker compose restart robot
```

## 12. Detener

```bash
docker compose down
```

## 13. Flujo esperado al iniciar

Al arrancar correctamente:

- inicializa GPIO
- inicializa camaras
- inicializa LCD/LED/buzzer si estan habilitados
- entra en estado `IDLE`
- empieza a enviar `heartbeat` al backend
- queda listo para recibir comandos

## 14. Problemas comunes

### No detecta camaras

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

Luego ajusta en `.env`:

- `CAMERA_FRONT_INDEX`
- `CAMERA_LEFT_INDEX`
- `CAMERA_RIGHT_INDEX`

### No conecta al backend

Revisa:

- IP correcta en `BRIDGE_URL`
- IP correcta en `BACKEND_WS_URL`
- puerto `8080`
- firewall
- backend encendido

### Falla por permisos de hardware

Revisa que el `docker-compose.yml` tenga:

- `privileged: true`
- `network_mode: host`
- montaje de `/dev`
- dispositivos `video*`
- `/dev/i2c-1`

## 15. Comando rapido de uso diario

```bash
cd worktrees/robot-pi
cp .env.example .env
nano .env
docker compose up --build -d
docker compose logs -f robot
```
