# Continuity v2 - Cambios locales Robot Pi

Fecha local de reconstruccion: 2026-04-28

Repositorio:

```text
/home/fer-dev/ROBOT-PI-EJECUTION
```

Rama:

```text
funcionalidad/robot-pi-runtime
```

Estado observado:

```text
La rama local esta ahead 6 respecto a origin/funcionalidad/robot-pi-runtime.
Hay archivos nuevos sin commit relacionados con autostart y arranque local.
```

## Commits locales ya guardados

Estos commits existen localmente y aun no estan en el remoto segun `git log origin/funcionalidad/robot-pi-runtime..HEAD`:

```text
c4dc8a7 Add session continuity notes
b1806f4 Configure verified camera device mapping
7cc2b67 Remove unavailable lgpio apt package
87709b7 Use Pi 5 compatible GPIO runtime
a5525eb Fix robot Docker build dependencies
dac6c22 Document local robot runtime setup
```

Resumen funcional de esos commits:

- Se documento la instalacion y operacion local del runtime de Robot Pi.
- Se ajusto el build Docker del runtime para Raspberry Pi 5.
- Se reemplazo `RPi.GPIO` por `rpi-lgpio`, manteniendo compatibilidad con imports `RPi.GPIO`.
- Se quito el paquete apt `lgpio` porque no estaba disponible en la imagen usada.
- Se dejo mapeo verificado de camaras:
  - `left -> /dev/video0`
  - `right -> /dev/video2`
  - `front -> /dev/video4`
- Se agrego documentacion de continuidad en `continuityv1.md`.

## Archivos nuevos sin commit

`git status --short` muestra:

```text
?? agrotech-robot.service
?? logs/
?? open-robot-terminal.desktop
?? robot-pi-autostart.cron
?? start-robot-at-boot.sh
```

### agrotech-robot.service

Servicio systemd propuesto para levantar el runtime al iniciar el sistema:

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

Uso previsto:

```bash
sudo cp agrotech-robot.service /etc/systemd/system/agrotech-robot.service
sudo systemctl daemon-reload
sudo systemctl enable agrotech-robot.service
sudo systemctl start agrotech-robot.service
sudo systemctl status agrotech-robot.service
```

Estado observado durante esta reconstruccion:

```text
systemctl is-enabled agrotech-robot.service no devolvio "enabled".
systemctl is-active agrotech-robot.service no devolvio "active".
```

Interpretacion: el archivo existe en el repo, pero no queda confirmado que el servicio este instalado o habilitado en systemd.

### start-robot-at-boot.sh

Script local de arranque:

```sh
#!/bin/sh
set -eu

PROJECT_DIR="/home/fer-dev/ROBOT-PI-EJECUTION"
LOG_DIR="/home/fer-dev/ROBOT-PI-EJECUTION/logs"
LOG_FILE="$LOG_DIR/boot-start.log"

mkdir -p "$LOG_DIR"

{
  echo "==== $(date -Is) starting robot runtime ===="
  cd "$PROJECT_DIR"
  /usr/bin/docker compose up -d --build
  /usr/bin/docker ps --filter name=agrotech-robot --format 'status={{.Status}}'
} >> "$LOG_FILE" 2>&1
```

Funcion:

- Crea `logs/`.
- Entra al repo.
- Ejecuta `docker compose up -d --build`.
- Registra estado del contenedor `agrotech-robot`.

### robot-pi-autostart.cron

Entrada cron propuesta:

```cron
@reboot /bin/sleep 25 && /home/fer-dev/ROBOT-PI-EJECUTION/start-robot-at-boot.sh
```

Funcion:

- Espera 25 segundos despues del boot.
- Ejecuta el script de arranque.

Estado observado:

```text
crontab -l fallo con "Permission denied" en el entorno actual.
```

Interpretacion: la entrada existe como archivo local, pero no queda confirmado que este instalada en el crontab del usuario.

### open-robot-terminal.desktop

Acceso directo local:

```ini
[Desktop Entry]
Type=Application
Name=Robot Pi Terminal
Comment=Open a terminal in the Robot Pi project folder
Exec=lxterminal --working-directory=/home/fer-dev/ROBOT-PI-EJECUTION
Terminal=false
X-GNOME-Autostart-enabled=true
```

Funcion:

- Abre `lxterminal` directamente en el directorio del proyecto.
- Puede usarse como acceso rapido de escritorio/autostart grafico.

### logs/boot-start.log

Evidencia observada en el log:

```text
==== 2026-04-28T06:06:38-06:00 starting robot runtime ====
...
Container agrotech-robot  Running
status=Up 9 minutes
```

Interpretacion:

- El script de arranque se ejecuto al menos una vez.
- Docker Compose encontro la imagen cacheada y dejo `agrotech-robot` corriendo en ese momento.
- Esto es evidencia de arranque exitoso por el script, pero no confirma si fue lanzado por cron, systemd o ejecucion manual.

## Configuracion operativa esperada

Backend local:

```text
BACKEND_BASE_URL=http://192.168.1.27:8080/api
BACKEND_WS_URL=ws://192.168.1.27:8080/api/ws/robot-stream
```

Robot:

```text
ROBOT_ID=ROBOT-001
Contenedor Docker: agrotech-robot
```

Camaras verificadas:

```text
left  -> /dev/video0
right -> /dev/video2
front -> /dev/video4
```

GPIO Raspberry Pi 5:

```text
Usar rpi-lgpio, no RPi.GPIO==0.7.1 directo.
```

I2C/LCD:

```text
Se documento en continuityv1.md que se agrego dtparam=i2c_arm=on a /boot/firmware/config.txt.
Requiere reinicio para confirmar /dev/i2c-1.
```

Ventilador:

```text
Se documento en continuityv1.md que se agregaron parametros fan_temp0 a /boot/firmware/config.txt.
Requiere reinicio para confirmar comportamiento persistente.
```

## Comandos utiles para retomar

Ver estado Git:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
git status --short --branch
git log --oneline origin/funcionalidad/robot-pi-runtime..HEAD
```

Ver archivos nuevos:

```bash
git status --short
sed -n '1,220p' agrotech-robot.service
sed -n '1,220p' start-robot-at-boot.sh
sed -n '1,220p' robot-pi-autostart.cron
sed -n '1,220p' open-robot-terminal.desktop
sed -n '1,220p' logs/boot-start.log
```

Levantar runtime:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail=120 robot
```

Detener runtime:

```bash
cd /home/fer-dev/ROBOT-PI-EJECUTION
sudo docker compose stop robot
```

Verificar servicio systemd:

```bash
systemctl is-enabled agrotech-robot.service
systemctl is-active agrotech-robot.service
systemctl status agrotech-robot.service
```

Verificar cron:

```bash
crontab -l
```

Verificar hardware:

```bash
ls -l /dev/video0 /dev/video2 /dev/video4
ls -l /dev/i2c-1
```

## Pendientes recomendados

1. Decidir si el arranque automatico final sera por systemd o cron. No conviene dejar ambos activos al mismo tiempo porque ambos pueden ejecutar `docker compose up -d --build`.
2. Confirmar si `agrotech-robot.service` esta instalado en `/etc/systemd/system/`.
3. Confirmar si la entrada `@reboot` esta instalada en el crontab.
4. Verificar despues de reiniciar:
   - WiFi conectado.
   - Docker activo.
   - Contenedor `agrotech-robot` corriendo.
   - `/dev/i2c-1` disponible.
   - Camaras `/dev/video0`, `/dev/video2`, `/dev/video4` disponibles.
5. Si todo queda correcto, hacer commit de los archivos nuevos:

```bash
git add agrotech-robot.service start-robot-at-boot.sh robot-pi-autostart.cron open-robot-terminal.desktop continuityv2.md
git add logs/boot-start.log
git commit -m "Document and add local robot autostart"
```

Nota: evaluar si `logs/boot-start.log` debe versionarse. Si solo es evidencia local, puede dejarse fuera del commit y agregar `logs/` a `.gitignore`.

