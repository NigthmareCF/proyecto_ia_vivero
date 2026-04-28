# Robot Pi: Autostart y Arranque del Runtime

Esta guia deja la Raspberry Pi 5 lista para:

- usar la conexion WiFi ya configurada en NetworkManager
- levantar `robot-pi` automaticamente al encender
- comunicarse con el backend local en `192.168.1.27:8080`

## 1. Estado de la conexion WiFi

La conexion WiFi ya fue creada en la Raspberry Pi como red oculta:

```bash
nmcli connection show
nmcli connection show --active
```

Si se necesita recrearla desde cero, usar:

```bash
sudo nmcli connection add type wifi ifname "*" con-name "Redmi Note 14" ssid "Redmi Note 14"
sudo nmcli connection modify "Redmi Note 14" \
  802-11-wireless.hidden yes \
  802-11-wireless-security.key-mgmt wpa-psk \
  802-11-wireless-security.psk "tashycora" \
  connection.autoconnect yes \
  connection.autoconnect-priority 100 \
  connection.autoconnect-retries 0
sudo nmcli connection up "Redmi Note 14"
```

## 2. Crear el servicio systemd para Docker Compose

Archivo:

```bash
sudo nano /etc/systemd/system/agrotech-robot.service
```

Contenido:

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

## 3. Habilitar el arranque automatico

```bash
sudo systemctl daemon-reload
sudo systemctl enable agrotech-robot.service
sudo systemctl start agrotech-robot.service
sudo systemctl status agrotech-robot.service
```

## 4. Verificacion post-reinicio

```bash
sudo reboot
```

Luego revisa:

```bash
nmcli connection show --active
docker ps
docker compose logs -f robot
```

## 5. Resultado esperado

Al encenderse la Pi:

- usa la conexion WiFi ya configurada
- arranca Docker
- ejecuta `docker compose up -d --build`
- levanta el runtime del robot sin intervencion manual
- conecta por HTTP a `http://192.168.1.27:8080/api`
- conecta el stream por WebSocket a `ws://192.168.1.27:8080/api/ws/robot-stream`
