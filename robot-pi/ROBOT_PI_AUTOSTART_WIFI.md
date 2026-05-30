# Robot Pi: Autostart, WiFi y Arranque Forzado

Esta guia deja la Raspberry Pi 5 lista para:

- conectarse al hotspot `Redmi Note 14`
- usar la clave `tashycora`
- levantar `robot-pi` automaticamente al encender

## 1. Crear la conexion WiFi

Si usas NetworkManager:

```bash
sudo nmcli dev wifi connect "Redmi Note 14" password "tashycora" name agrotech-hotspot
sudo nmcli connection modify agrotech-hotspot connection.autoconnect yes
sudo nmcli connection modify agrotech-hotspot connection.autoconnect-priority 100
```

Verifica:

```bash
nmcli connection show
nmcli connection show --active
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
WorkingDirectory=/home/pi/proyecto_ia_vivero/robot-pi
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

- se conecta automaticamente a `Redmi Note 14`
- arranca Docker
- ejecuta `docker compose up -d --build`
- levanta el runtime del robot sin intervención manual
