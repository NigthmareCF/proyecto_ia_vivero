# Continuity v1 - Robot Pi Runtime

## Contexto actual

Repositorio local:

```text
/home/fer-dev/ROBOT-PI-EJECUTION
```

Rama activa:

```text
funcionalidad/robot-pi-runtime
```

Remoto:

```text
origin https://github.com/NigthmareCF/proyecto_ia_vivero.git
```

Usuario Git local:

```text
user.name=NigthmareCF
user.email=ferchocastfun15@gmail.com
```

## Commits locales relevantes

Cambios guardados localmente durante esta sesion:

```text
dac6c22 Document local robot runtime setup
a5525eb Fix robot Docker build dependencies
87709b7 Use Pi 5 compatible GPIO runtime
7cc2b67 Remove unavailable lgpio apt package
b1806f4 Configure verified camera device mapping
```

El repo puede estar ahead del remoto. Revisar con:

```bash
git status --short --branch
git log --oneline -8
```

## Red y backend local

La Raspberry Pi esta en la red `192.168.1.0/24`.

Backend local esperado:

```text
BACKEND_BASE_URL=http://192.168.1.27:8080/api
BACKEND_WS_URL=ws://192.168.1.27:8080/api/ws/robot-stream
```

Al final de la sesion, `192.168.1.27:8080` no respondia desde la Pi:

```bash
curl -fsS --max-time 5 http://192.168.1.27:8080/api/actuator/health
```

## WiFi

NetworkManager tiene configurado el perfil `Redmi Note 14` como red oculta, con autoconexion y prioridad alta. La clave usada fue `tashycora`.

Comandos utiles:

```bash
nmcli connection show
nmcli connection show --active
nmcli dev wifi list --rescan yes
```

## Docker

Docker y Docker Compose quedaron instalados:

```text
Docker 26.1.5
Docker Compose 2.26.1
```

El usuario `fer-dev` fue agregado al grupo `docker`, pero puede requerir cerrar sesion o reiniciar para usar Docker sin `sudo`.

El contenedor del runtime se llama:

```text
agrotech-robot
```

Al final de la sesion el contenedor quedo detenido a proposito para liberar las camaras.

Comandos utiles:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
sudo docker compose up -d robot
sudo docker compose stop robot
sudo docker compose ps
sudo docker compose logs --tail=120 robot
```

## Camaras

Mapeo verificado fisicamente por el usuario:

```text
left  -> /dev/video0
right -> /dev/video2
front -> /dev/video4
```

Variables ya ajustadas en `.env` y `.env.example`:

```text
CAMERA_TYPE=usb
CAMERA_FRONT_INDEX=4
CAMERA_LEFT_INDEX=0
CAMERA_RIGHT_INDEX=2
```

Para liberar las camaras:

```bash
sudo docker compose stop robot
sudo fuser -v /dev/video0 /dev/video2 /dev/video4
```

Para verlas desde terminal:

```bash
ffplay /dev/video0
ffplay /dev/video2
ffplay /dev/video4
```

## GPIO en Raspberry Pi 5

`RPi.GPIO==0.7.1` fallaba en Pi 5 con:

```text
RuntimeError: Cannot determine SOC peripheral base address
```

Se reemplazo por:

```text
rpi-lgpio
```

Esto mantiene compatibilidad con imports tipo:

```python
import RPi.GPIO as GPIO
```

## I2C y LCD

El runtime aviso:

```text
LCD no disponible: [Errno 2] No such file or directory: '/dev/i2c-1'
```

Se habilito I2C en `/boot/firmware/config.txt`:

```text
dtparam=i2c_arm=on
```

Backup creado:

```text
/boot/firmware/config.txt.codex-backup-20260428-i2c
```

Requiere reinicio para que aparezca `/dev/i2c-1`.

## Ventilador

Se configuro politica persistente del ventilador en `/boot/firmware/config.txt`:

```text
dtparam=fan_temp0=2000
dtparam=fan_temp0_hyst=1000
dtparam=fan_temp0_speed=255
```

Esto significa maxima potencia desde 2 C y apagado al bajar a 1 C.

Backup creado:

```text
/boot/firmware/config.txt.codex-backup-20260428-ventilador
```

Tambien se puso temporalmente el ventilador en estado 4 durante la sesion.

## Comandos de camara del runtime

El runtime acepta:

```text
CAMERA_SELECT
SWITCH_CAMERA
```

Payloads validos:

```json
{ "camera": "front" }
{ "camera": "left" }
{ "camera": "right" }
{ "activeCamera": "front" }
```

## Pendientes recomendados

1. Reiniciar la Pi para aplicar I2C y politica de ventilador desde arranque.
2. Confirmar que `/dev/i2c-1` existe tras reinicio.
3. Levantar backend local en `192.168.1.27:8080`.
4. Levantar el robot:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
sudo docker compose up -d robot
sudo docker compose logs --tail=120 robot
```

5. Confirmar que el robot envia heartbeat al backend y recibe comandos.
6. Si todo esta correcto, hacer push de los commits locales.
