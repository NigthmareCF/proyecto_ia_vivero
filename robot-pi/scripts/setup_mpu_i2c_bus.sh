#!/bin/sh
set -eu

CONFIG_FILE="/boot/firmware/config.txt"
OVERLAY_LINE="dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=7,i2c_gpio_scl=11"

echo "Configurando bus I2C del MPU"
echo "SDA: GPIO7  (pin fisico 26)"
echo "SCL: GPIO11 (pin fisico 23)"
echo

if ! command -v dtoverlay >/dev/null 2>&1; then
  echo "ERROR: dtoverlay no esta disponible"
  exit 1
fi

echo "Cargando overlay en caliente..."
sudo dtoverlay i2c-gpio bus=3 i2c_gpio_sda=7 i2c_gpio_scl=11 || true

echo "Dejando overlay persistente en $CONFIG_FILE..."
if ! sudo grep -q "i2c_gpio_sda=7,i2c_gpio_scl=11" "$CONFIG_FILE"; then
  sudo sh -c "printf '\n# MPU I2C bus: SDA GPIO7 pin26, SCL GPIO11 pin23\n%s\n' '$OVERLAY_LINE' >> '$CONFIG_FILE'"
else
  echo "La configuracion persistente ya existe."
fi

echo
echo "Buses I2C detectados:"
i2cdetect -l || true

if [ -e /dev/i2c-3 ]; then
  echo
  echo "Escaneo de /dev/i2c-3:"
  sudo i2cdetect -y 3 || true
else
  echo
  echo "No aparece /dev/i2c-3 todavia. Si el overlay no cargo en caliente, reinicia la Raspberry."
fi

echo
echo "Listo. Presiona ENTER para cerrar."
read _unused
