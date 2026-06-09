# Robot Pi: Guia de merge, respaldo y operacion desde laptop

Este documento explica como manejar desde una laptop los cambios del runtime de la Raspberry Pi sin perder la configuracion local que ya quedo funcionando en la Pi.

La idea principal es separar dos tipos de configuracion:

- configuracion versionable: archivos que pueden vivir en Git y viajar entre laptop y Raspberry Pi
- configuracion local de la Pi: cambios instalados en el sistema operativo de la Raspberry Pi, fuera del repositorio

## 1. Estado actual de referencia

Repositorio remoto:

```text
https://github.com/NigthmareCF/proyecto_ia_vivero.git
```

Rama usada en la Raspberry Pi:

```text
funcionalidad/robot-pi-runtime
```

Ruta local del proyecto en la Raspberry Pi:

```text
/home/fer-dev/ROBOT-PI-EJECUTION
```

Servicio/contenedor principal:

```text
docker compose up -d --build
container_name=agrotech-robot
```

Backend local esperado:

```text
BACKEND_BASE_URL=http://192.168.1.27:8080/api
BACKEND_WS_URL=ws://192.168.1.27:8080/api/ws/robot-stream
```

## 2. Regla importante antes de hacer merge

Nunca reemplazar la carpeta completa de la Raspberry Pi sin antes respaldar los archivos locales.

Seguro:

```bash
git fetch origin
git status --short --branch
git log --oneline --left-right --cherry-pick HEAD...origin/funcionalidad/robot-pi-runtime
```

Riesgoso:

```bash
rm -rf /home/fer-dev/ROBOT-PI-EJECUTION
git clone ...
```

El riesgo existe porque hay archivos no versionados o configuraciones del sistema que no siempre vienen desde Git.

## 3. Que vive dentro del repositorio

Estos archivos pertenecen al proyecto y conviene mantenerlos versionados si son parte de la operacion del robot:

```text
README.md
ROBOT_PI_AUTOSTART_WIFI.md
ROBOT_PI_INSTALACION_DOCKER.md
ROBOT_PI_MERGE_Y_OPERACION_REMOTA.md
SAGA_FLOW.md
docker-compose.yml
robot-pi/Dockerfile
robot-pi/main.py
robot-pi/requirements.txt
robot-pi/src/config.py
robot-pi/src/**
robot-pi/models/labels.txt
vivero-backend/**
```

Archivos locales utiles que deberian subirse si se quieren manejar desde la laptop:

```text
agrotech-robot.service
open-robot-terminal.desktop
robot-pi-autostart.cron
start-robot-at-boot.sh
robot-pi/scripts/tail_qr_backend.sh
robot-pi/scripts/tail_qr_metrics.sh
robot-pi/scripts/tail_qr_results.sh
robot-pi/scripts/tcrt5000_realtime.py
robot-pi/scripts/tcrt5000_terminal.sh
robot-pi/qr_test_mode.py
robot-pi/qr_visual_test.py
```

Estos archivos son plantillas o scripts que ayudan a recrear el arranque automatico, abrir terminales de monitoreo y ejecutar pruebas locales.

## 4. Que vive fuera del repositorio en la Raspberry Pi

Aunque existan copias o documentacion en Git, estas configuraciones reales viven fuera del repo:

### 4.1 Conexion WiFi de NetworkManager

La conexion WiFi forzada se configura en el sistema con `nmcli`.

Vive en NetworkManager, no en el contenedor ni en Git.

Comandos de verificacion:

```bash
nmcli connection show
nmcli connection show --active
```

Si se necesita recrear:

```bash
sudo nmcli connection add type wifi ifname "*" con-name "NOMBRE_WIFI" ssid "NOMBRE_WIFI"
sudo nmcli connection modify "NOMBRE_WIFI" \
  802-11-wireless.hidden yes \
  802-11-wireless-security.key-mgmt wpa-psk \
  802-11-wireless-security.psk "PASSWORD_WIFI" \
  connection.autoconnect yes \
  connection.autoconnect-priority 100 \
  connection.autoconnect-retries 0
sudo nmcli connection up "NOMBRE_WIFI"
```

No es recomendable subir passwords reales a un repositorio publico. Si el repo es privado, aun asi conviene revisar antes de compartirlo.

### 4.2 Autostart grafico de terminal

La terminal que se abre al iniciar sesion grafica vive en:

```text
/home/fer-dev/.config/autostart/open-robot-terminal.desktop
```

La copia versionable puede vivir en:

```text
open-robot-terminal.desktop
```

Contenido esperado:

```ini
[Desktop Entry]
Type=Application
Name=Robot Pi Terminal
Comment=Open a terminal in the Robot Pi project folder
Exec=lxterminal --working-directory=/home/fer-dev/ROBOT-PI-EJECUTION
Terminal=false
X-GNOME-Autostart-enabled=true
```

Para instalar desde el repo hacia la Pi:

```bash
mkdir -p /home/fer-dev/.config/autostart
cp /home/fer-dev/ROBOT-PI-EJECUTION/open-robot-terminal.desktop /home/fer-dev/.config/autostart/open-robot-terminal.desktop
chmod +x /home/fer-dev/.config/autostart/open-robot-terminal.desktop
```

### 4.3 Servicio systemd

Si se usa systemd, el archivo real debe estar en:

```text
/etc/systemd/system/agrotech-robot.service
```

La copia versionable puede vivir en:

```text
agrotech-robot.service
```

Contenido esperado:

```ini
[Unit]
Description=AgroTech Robot Pi Runtime
After=network-online.target docker.service
Wants=network-online.target docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/fer-dev/ROBOT-PI-EJECUTION
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Para instalar:

```bash
sudo cp /home/fer-dev/ROBOT-PI-EJECUTION/agrotech-robot.service /etc/systemd/system/agrotech-robot.service
sudo systemctl daemon-reload
sudo systemctl enable agrotech-robot.service
sudo systemctl start agrotech-robot.service
sudo systemctl status agrotech-robot.service
```

Para revisar:

```bash
systemctl is-enabled agrotech-robot.service
systemctl is-active agrotech-robot.service
journalctl -u agrotech-robot.service -n 100 --no-pager
```

### 4.4 Cron de arranque

Si se usa cron en vez de systemd, la linea real vive en el crontab del usuario:

```bash
crontab -l
```

Plantilla versionable:

```text
robot-pi-autostart.cron
```

Contenido esperado:

```cron
@reboot /bin/sleep 25 && /home/fer-dev/ROBOT-PI-EJECUTION/start-robot-at-boot.sh
```

Instalar:

```bash
crontab /home/fer-dev/ROBOT-PI-EJECUTION/robot-pi-autostart.cron
```

Nota: usar systemd o cron, no ambos al mismo tiempo, para evitar levantar Docker Compose dos veces.

## 5. Archivos que no se deben pisar sin revisar

Antes de traer cambios desde la laptop, revisar especialmente:

```text
.env
.env.example
docker-compose.yml
robot-pi/Dockerfile
robot-pi/src/config.py
ROBOT_PI_AUTOSTART_WIFI.md
ROBOT_PI_INSTALACION_DOCKER.md
agrotech-robot.service
open-robot-terminal.desktop
robot-pi-autostart.cron
start-robot-at-boot.sh
robot-pi/scripts/
robot-pi/qr_test_mode.py
robot-pi/qr_visual_test.py
```

Directorios locales que normalmente no deben subirse:

```text
logs/
robot-pi-data/
.codex/
```

`logs/` contiene salidas de ejecucion.

`robot-pi-data/` contiene datos de runtime, por ejemplo cola offline o logs internos.

`.codex/` es metadata local del asistente.

## 6. Flujo recomendado desde la laptop

### 6.1 Antes de trabajar

En la laptop:

```bash
git clone https://github.com/NigthmareCF/proyecto_ia_vivero.git
cd proyecto_ia_vivero
git checkout funcionalidad/robot-pi-runtime
git pull origin funcionalidad/robot-pi-runtime
```

Crear una rama de trabajo:

```bash
git checkout -b trabajo/laptop-robot-pi
```

### 6.2 Antes de subir cambios

Ver cambios:

```bash
git status --short
git diff --stat
git diff
```

Evitar subir archivos locales sensibles o generados:

```bash
git status --short
```

No subir:

```text
logs/
robot-pi-data/
.codex/
```

Revisar con cuidado:

```text
.env
```

Si se sube `.env`, confirmar que el repositorio es privado y que los valores corresponden al entorno esperado.

### 6.3 Commit y push

```bash
git add ARCHIVOS_CAMBIADOS
git commit -m "descripcion clara del cambio"
git push origin trabajo/laptop-robot-pi
```

Luego crear Pull Request hacia:

```text
funcionalidad/robot-pi-runtime
```

## 7. Flujo recomendado en la Raspberry Pi antes de traer cambios

Entrar al proyecto:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
```

Actualizar referencias sin hacer merge:

```bash
git fetch origin
```

Ver estado:

```bash
git status --short --branch
```

Comparar commits locales vs remotos:

```bash
git log --oneline --decorate --left-right --cherry-pick HEAD...origin/funcionalidad/robot-pi-runtime
```

Interpretacion:

```text
< commit
```

Existe localmente en la Pi, pero no esta en remoto.

```text
> commit
```

Existe en remoto, pero no esta en la Pi.

Ver archivos que cambiaron en remoto respecto a la Pi:

```bash
git diff --name-status HEAD..origin/funcionalidad/robot-pi-runtime
```

Ver archivos que tiene la Pi y no estan en remoto:

```bash
git diff --name-status origin/funcionalidad/robot-pi-runtime..HEAD
```

Ver cambios sin commit:

```bash
git diff --name-status
git ls-files --others --exclude-standard
```

## 8. Backup recomendado antes de merge en la Pi

Crear carpeta temporal:

```bash
mkdir -p /tmp/robot-pi-backup
```

Copiar archivos criticos:

```bash
cp .env /tmp/robot-pi-backup/.env 2>/dev/null || true
cp .env.example /tmp/robot-pi-backup/.env.example 2>/dev/null || true
cp docker-compose.yml /tmp/robot-pi-backup/docker-compose.yml 2>/dev/null || true
cp robot-pi/Dockerfile /tmp/robot-pi-backup/robot-pi.Dockerfile 2>/dev/null || true
cp robot-pi/src/config.py /tmp/robot-pi-backup/config.py 2>/dev/null || true
cp agrotech-robot.service /tmp/robot-pi-backup/agrotech-robot.service 2>/dev/null || true
cp open-robot-terminal.desktop /tmp/robot-pi-backup/open-robot-terminal.desktop 2>/dev/null || true
cp robot-pi-autostart.cron /tmp/robot-pi-backup/robot-pi-autostart.cron 2>/dev/null || true
cp start-robot-at-boot.sh /tmp/robot-pi-backup/start-robot-at-boot.sh 2>/dev/null || true
```

Copiar scripts:

```bash
mkdir -p /tmp/robot-pi-backup/scripts
cp robot-pi/scripts/* /tmp/robot-pi-backup/scripts/ 2>/dev/null || true
```

Verificar backup:

```bash
find /tmp/robot-pi-backup -maxdepth 2 -type f | sort
```

## 9. Como hacer merge en la Pi de forma controlada

Despues de revisar y respaldar:

```bash
git merge origin/funcionalidad/robot-pi-runtime
```

Si hay conflictos, no resolver a ciegas.

Ver conflictos:

```bash
git status
```

Archivos mas probables de conflicto:

```text
.env
.env.example
docker-compose.yml
robot-pi/Dockerfile
robot-pi/src/config.py
README.md
ROBOT_PI_AUTOSTART_WIFI.md
ROBOT_PI_INSTALACION_DOCKER.md
SAGA_FLOW.md
```

Despues de resolver:

```bash
git add ARCHIVOS_RESUELTOS
git commit
```

## 10. Como probar despues de merge

Reconstruir y levantar:

```bash
docker compose up -d --build
```

Ver contenedor:

```bash
docker ps --filter name=agrotech-robot
```

Ver logs:

```bash
docker compose logs -f robot
```

Ver camaras:

```bash
ls -l /dev/video*
```

Ver conexion de red:

```bash
nmcli connection show --active
ip route
```

Ver endpoints configurados:

```bash
grep -E 'BACKEND_BASE_URL|BACKEND_WS_URL|CAMERA_|LINE_ACTIVE_LOW' .env
```

## 11. Configuracion sensible actual

Valores que afectan directamente la operacion:

```text
BACKEND_BASE_URL
BACKEND_WS_URL
CAMERA_FRONT_INDEX
CAMERA_LEFT_INDEX
CAMERA_RIGHT_INDEX
LINE_ACTIVE_LOW
LOCAL_AI_ENABLED
OFFLINE_QUEUE_DIR
WIFI_SSID
WIFI_PASSWORD
```

Mapeo de camaras verificado en esta Pi:

```text
left  -> /dev/video0
right -> /dev/video2
front -> /dev/video4
```

Entradas usadas por el runtime:

```text
CAMERA_LEFT_INDEX=0   -> camara lateral izquierda, usada para QR lateral y evidencia de planta
CAMERA_RIGHT_INDEX=2  -> camara lateral derecha, usada para QR lateral y evidencia de planta
CAMERA_FRONT_INDEX=4  -> camara frontal, usada para stream operativo, supervision manual y evidencia ante obstaculos
```

En codigo, estas entradas se cargan desde `robot-pi/src/config.py` y se abren en `robot-pi/src/vision/camera_handler.py` con las llaves:

```text
"left"
"front"
"right"
```

El orden operativo usado para captura multiple es:

```text
capture_triplet() -> left, front, right
capture_burst()   -> left, right, front
```

Configuracion esperada:

```env
CAMERA_TYPE=usb
CAMERA_FRONT_INDEX=4
CAMERA_LEFT_INDEX=0
CAMERA_RIGHT_INDEX=2
LINE_ACTIVE_LOW=false
LOCAL_AI_ENABLED=false
OFFLINE_QUEUE_DIR=/app/data/offline-queue
```

## 12. Luz integrada de las camaras

Las camaras tienen un panel tactil fisico para alternar modos de luz:

```text
1. apagado
2. luz blanca
3. luz calida
4. luz amarilla
```

La posibilidad de controlarlo por codigo depende de si el firmware USB de la camara expone esa luz como control UVC/V4L2.

Estado verificado en esta Pi: las camaras no exponen controles UVC/V4L2 para cambiar la luz integrada. No aparece ningun control `led`, `light`, `torch`, `illuminator` ni equivalente en `/dev/video0`, `/dev/video2` o `/dev/video4`.

Conclusion practica: con la interfaz USB visible actualmente, el codigo puede ajustar parametros de imagen, pero no puede alternar directamente los 4 modos fisicos de luz del panel tactil.

### 12.1 Lo que se debe verificar

En Linux, una camara USB normalmente expone controles estandar como:

```text
brightness
contrast
saturation
gain
exposure
white_balance_temperature
```

Pero la luz integrada solo se puede controlar por software si aparece algun control relacionado, por ejemplo:

```text
led
light
torch
illuminator
illumination
privacy
vendor
```

Si no aparece ningun control de ese tipo, probablemente el panel tactil controla la luz internamente en el hardware y no por USB. En ese caso, Python/OpenCV no puede cambiar los 4 modos directamente con una propiedad estandar.

### 12.2 Comandos para comprobar controles UVC/V4L2

Ejecutar en la Raspberry Pi:

```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-ctrls-menus
v4l2-ctl -d /dev/video2 --list-ctrls-menus
v4l2-ctl -d /dev/video4 --list-ctrls-menus
```

Si el usuario no tiene permisos para abrir `/dev/video*`, agregarlo al grupo `video` y reiniciar sesion:

```bash
sudo usermod -aG video fer-dev
sudo reboot
```

Despues del reinicio:

```bash
id
ls -l /dev/video0 /dev/video2 /dev/video4
v4l2-ctl -d /dev/video0 --list-ctrls-menus
```

### 12.3 Interpretacion del resultado

Caso A: aparece un control de luz.

Ejemplo hipotetico:

```text
led_mode 0x009a0901 (menu) min=0 max=3 default=0 value=0
```

En ese caso se puede probar:

```bash
v4l2-ctl -d /dev/video0 --set-ctrl=led_mode=0
v4l2-ctl -d /dev/video0 --set-ctrl=led_mode=1
v4l2-ctl -d /dev/video0 --set-ctrl=led_mode=2
v4l2-ctl -d /dev/video0 --set-ctrl=led_mode=3
```

Luego se podria envolver en Python con llamadas a `v4l2-ctl` o usando una libreria V4L2.

Caso B: no aparece ningun control de luz.

Este fue el caso observado en esta Pi. No hay una API estandar visible para cambiar los 4 modos. Las opciones serian:

```text
1. mantener el modo seleccionado manualmente desde el panel tactil
2. buscar si el fabricante publica comandos USB propietarios
3. capturar trafico USB mientras se toca el panel para investigar si envia eventos al host
4. controlar una luz externa desde GPIO, que si seria totalmente programable
```

### 12.4 Estado observado en esta Pi

En la revision actual se confirmo que el contenedor ve nodos de video, incluyendo:

```text
/dev/video0
/dev/video2
/dev/video4
```

Tambien se observo en `dmesg` que Linux detecta camaras UVC USB:

```text
USB Camera (058f:3863)
USB 2.0 Camera (0c45:6366)
uvcvideo
```

Con `sudo v4l2-ctl --list-devices` se verifico el mapeo fisico:

```text
USB Camera: USB Camera (usb-xhci-hcd.0-1)
  /dev/video0
  /dev/video1
  /dev/media3

USB Camera: USB Camera (usb-xhci-hcd.1-1)
  /dev/video2
  /dev/video3
  /dev/media4

USB 2.0 Camera: USB 2.0 Camera (usb-xhci-hcd.1-2)
  /dev/video4
  /dev/video5
  /dev/media5
```

Controles encontrados en `/dev/video0` y `/dev/video2`:

```text
brightness
contrast
saturation
hue
white_balance_automatic
gamma
power_line_frequency
white_balance_temperature
sharpness
backlight_compensation
auto_exposure
exposure_time_absolute
focus_absolute
focus_automatic_continuous
```

Controles encontrados en `/dev/video4`:

```text
brightness
contrast
saturation
hue
white_balance_automatic
gamma
gain
power_line_frequency
white_balance_temperature
sharpness
backlight_compensation
auto_exposure
exposure_time_absolute
exposure_dynamic_framerate
focus_absolute
focus_automatic_continuous
```

Los nodos auxiliares `/dev/video1`, `/dev/video3` y `/dev/video5` no mostraron controles adicionales.

Nota importante: `white_balance_temperature`, `brightness`, `gain` y `exposure` modifican la imagen capturada, pero no cambian fisicamente el modo de luz de la camara. Pueden ayudar a compensar color o luminosidad en software, pero no equivalen a seleccionar apagado/blanca/calida/amarilla en el panel tactil.

### 12.5 Alternativa programable: perfiles de imagen

Aunque no se pueda cambiar la luz fisica integrada, si se pueden aplicar perfiles de imagen para compensar la escena segun el modo de luz seleccionado manualmente.

Estos perfiles no controlan la lampara. Solo ajustan como la camara interpreta la imagen.

Ejemplo de perfil para luz blanca:

```bash
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_automatic=0
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature=5200
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=0
v4l2-ctl -d /dev/video0 --set-ctrl=contrast=34
```

Ejemplo de perfil para luz calida:

```bash
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_automatic=0
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature=3600
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=0
v4l2-ctl -d /dev/video0 --set-ctrl=contrast=34
```

Ejemplo de perfil para poca luz:

```bash
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=10
v4l2-ctl -d /dev/video0 --set-ctrl=gamma=130
v4l2-ctl -d /dev/video0 --set-ctrl=backlight_compensation=3
```

Para aplicar el mismo perfil a las tres camaras principales:

```bash
for dev in /dev/video0 /dev/video2 /dev/video4; do
  v4l2-ctl -d "$dev" --set-ctrl=white_balance_automatic=0
  v4l2-ctl -d "$dev" --set-ctrl=white_balance_temperature=4600
done
```

Antes de automatizar estos perfiles en el runtime, hay que probarlos visualmente con cada camara porque `/dev/video0` y `/dev/video2` no tienen exactamente los mismos rangos que `/dev/video4`.

## 13. Decision sobre `.env`

Hay dos opciones:

### Opcion A: versionar `.env`

Ventaja:

- la Pi queda reproducible desde Git
- la laptop ve exactamente los valores usados en campo

Riesgo:

- puede subir passwords o IPs privadas
- si otra persona cambia `.env`, puede romper la Pi

### Opcion B: no versionar `.env`

Ventaja:

- protege secretos y configuracion local
- reduce riesgo de pisar valores de la Pi

Riesgo:

- hay que mantener `.env.example` muy actualizado
- despues de clonar, hay que recrear `.env` manualmente

Recomendacion practica:

- mantener `.env.example` como plantilla limpia
- mantener `.env` solo si el repositorio es privado y todo el equipo entiende que contiene configuracion real de la Pi
- antes de cada merge, revisar cualquier cambio en `.env`

## 14. Restaurar desde cero una Pi nueva

Clonar:

```bash
cd /home/fer-dev
git clone https://github.com/NigthmareCF/proyecto_ia_vivero.git ROBOT-PI-EJECUTION
cd /home/fer-dev/ROBOT-PI-EJECUTION
git checkout funcionalidad/robot-pi-runtime
```

Crear `.env`:

```bash
cp .env.example .env
nano .env
```

Instalar autostart de terminal:

```bash
mkdir -p /home/fer-dev/.config/autostart
cp open-robot-terminal.desktop /home/fer-dev/.config/autostart/open-robot-terminal.desktop
chmod +x /home/fer-dev/.config/autostart/open-robot-terminal.desktop
```

Configurar WiFi:

```bash
nmcli connection show
sudo nmcli connection up "NOMBRE_WIFI"
```

Instalar systemd:

```bash
sudo cp agrotech-robot.service /etc/systemd/system/agrotech-robot.service
sudo systemctl daemon-reload
sudo systemctl enable agrotech-robot.service
sudo systemctl start agrotech-robot.service
```

Levantar manualmente si se quiere probar antes:

```bash
docker compose up -d --build
docker compose logs -f robot
```

## 15. Checklist antes de subir desde laptop

Antes de hacer push:

```text
[ ] Revise git status --short
[ ] Revise git diff --stat
[ ] No estoy subiendo logs/
[ ] No estoy subiendo robot-pi-data/
[ ] No estoy subiendo .codex/
[ ] Revise si .env contiene secretos reales
[ ] Revise si cambie CAMERA_* o LINE_ACTIVE_LOW
[ ] Si cambie mapeo de camaras, actualice la seccion de entradas de camara
[ ] Si se comprobo control de luz por V4L2, documente el nombre exacto del control
[ ] Revise si cambie docker-compose.yml
[ ] Revise si cambie robot-pi/Dockerfile
[ ] Si toque arranque, actualice agrotech-robot.service/open-robot-terminal.desktop/start-robot-at-boot.sh
[ ] Si toque WiFi/autostart, actualice este documento o ROBOT_PI_AUTOSTART_WIFI.md
```

## 16. Checklist antes de aplicar cambios en la Pi

Antes de hacer merge/pull:

```text
[ ] git fetch origin
[ ] git status --short --branch
[ ] git log --oneline --left-right --cherry-pick HEAD...origin/funcionalidad/robot-pi-runtime
[ ] git diff --name-status HEAD..origin/funcionalidad/robot-pi-runtime
[ ] git diff --name-status
[ ] git ls-files --others --exclude-standard
[ ] Backup de .env y archivos de arranque en /tmp/robot-pi-backup
[ ] Confirmar que no se reemplazara robot-pi-data/
[ ] Confirmar si se usara systemd o cron, no ambos
[ ] Confirmar acceso a /dev/video0, /dev/video2 y /dev/video4
[ ] Si se depende de luz integrada, confirmar controles con v4l2-ctl
```

## 17. Estado observado en la ultima comparacion

La ultima comparacion realizada en la Pi mostro:

```text
funcionalidad/robot-pi-runtime...origin/funcionalidad/robot-pi-runtime [ahead 6, behind 1]
```

Remoto tenia un commit nuevo:

```text
e62bbda docs(robot-pi): add resumen operativo v1
```

Ese commit agregaba:

```text
RESUMEN_OPERATIVO_V1.md
```

La Pi tenia commits locales no subidos:

```text
c4dc8a7 Add session continuity notes
b1806f4 Configure verified camera device mapping
7cc2b67 Remove unavailable lgpio apt package
87709b7 Use Pi 5 compatible GPIO runtime
a5525eb Fix robot Docker build dependencies
dac6c22 Document local robot runtime setup
```

La Pi tambien tenia cambios locales sin commit en:

```text
.env
.env.example
robot-pi/Dockerfile
robot-pi/src/config.py
```

Y archivos nuevos no versionados relacionados con arranque, pruebas y monitoreo:

```text
agrotech-robot.service
continuityv2.md
open-robot-terminal.desktop
robot-pi-autostart.cron
robot-pi/qr_test_mode.py
robot-pi/qr_visual_test.py
robot-pi/scripts/
start-robot-at-boot.sh
```

Tambien existian directorios locales que no deberian subirse normalmente:

```text
logs/
robot-pi-data/
.codex/
```

## 18. Resumen operativo

Para trabajar desde laptop:

1. Trabajar en una rama nueva desde `funcionalidad/robot-pi-runtime`.
2. No modificar `.env` sin intencion clara.
3. No subir `logs/`, `robot-pi-data/` ni `.codex/`.
4. Subir scripts de arranque solo si se quieren manejar desde Git.
5. En la Pi, hacer siempre `git fetch origin` y comparar antes de merge.
6. Respaldar `.env` y archivos de arranque antes de aplicar cambios.
7. Despues del merge, probar `docker compose up -d --build`.
8. Confirmar que la WiFi sigue activa con `nmcli connection show --active`.
9. Confirmar que el contenedor esta arriba con `docker ps --filter name=agrotech-robot`.
10. Confirmar logs con `docker compose logs -f robot`.
