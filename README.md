# AgroTech Robot Pi

Runtime del robot fisico para Raspberry Pi 5 del proyecto AgroTech Vivero.

## Requisitos previos en la Raspberry Pi

1. Raspberry Pi OS 64-bit Lite instalado.
2. Docker y Docker Compose instalados:
   `curl -sSL https://get.docker.com | sh`
   `sudo usermod -aG docker $USER`
3. I2C habilitado:
   `sudo raspi-config -> Interface Options -> I2C -> Enable`
4. Camara habilitada si usas CSI:
   `sudo raspi-config -> Interface Options -> Camera -> Enable`
5. Si usas tres camaras USB, verifica que Linux detecte:
   `/dev/video0`, `/dev/video1` y `/dev/video2`

## Instalacion

```bash
git clone https://github.com/<usuario>/agrotech-robot.git
cd agrotech-robot
cp .env.example .env
nano .env
docker compose up --build -d
```

Coloca el modelo TFLite en `robot-pi/models/` antes de levantar el contenedor:

- `modelo_vivero.tflite`
- `labels.txt`

Configura los indices de las tres camaras en `.env`:

- `CAMERA_FRONT_INDEX`
- `CAMERA_LEFT_INDEX`
- `CAMERA_RIGHT_INDEX`

El runtime usa la frontal para QR y streaming manual, y toma una captura izquierda/frontal/derecha para clasificacion.

## Logs

```bash
docker compose logs -f robot
```

## Detener

```bash
docker compose down
```

## Nota sobre tflite-runtime en ARM64

Si la instalacion normal falla en la Raspberry Pi 5, instala el wheel ARM64 manualmente:

```bash
pip install https://github.com/google-coral/pycoral/releases/download/v2.0.0/tflite_runtime-2.5.0.post1-cp311-cp311-linux_aarch64.whl
```
