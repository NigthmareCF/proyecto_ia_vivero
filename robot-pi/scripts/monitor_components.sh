#!/usr/bin/env bash
set -u

cd /home/fer-dev/ROBOT-PI-EJECUTION || exit 1

line_values() {
  gpioget --numeric -c gpiochip0 GPIO13 GPIO19 GPIO16 GPIO6 GPIO8 GPIO9 2>&1
}

while true; do
  clear
  date '+%Y-%m-%d %H:%M:%S %Z'
  echo
  echo "== Robot container =="
  docker compose ps 2>&1
  echo

  echo "== Cameras =="
  v4l2-ctl --list-devices 2>&1 | sed -n '1,70p'
  echo

  echo "== GPIO chips =="
  gpiodetect 2>&1
  echo

  echo "== GPIO lines used by robot =="
  gpioinfo -c gpiochip0 2>&1 | grep -E 'GPIO(2|3|5|6|8|9|12|13|16|17|18|19|20|21|22|23|24|25|26|27)' || true
  echo

  echo "== Sensor read attempt =="
  echo "line sensors L/C/R: GPIO13 GPIO19 GPIO16 | ultrasonic echo GPIO6 | rear IR GPIO8 GPIO9"
  line_values
  echo "Nota: 'Device or resource busy'/'GPIO busy' significa que el proceso del robot ya tomo esos pines."
  echo

  echo "== Recent robot logs =="
  docker logs --tail 35 agrotech-robot 2>&1
  echo
  echo "Actualizando cada 2s. Ctrl+C para salir."
  sleep 2
done
