#!/bin/sh
set -eu

PROJECT_DIR="/home/fer-dev/ROBOT-PI-EJECUTION"

cd "$PROJECT_DIR"

echo "Calibracion del seguidor de linea"
echo "Se pausara el runtime para liberar GPIO13/GPIO19/GPIO16."
echo

/usr/bin/docker compose stop robot

echo
echo "Lectura en tiempo real:"
echo "  izquierda = GPIO13 pin fisico 33"
echo "  centro    = GPIO19 pin fisico 35"
echo "  derecha   = GPIO16 pin fisico 36"
echo
echo "Ajusta los potenciometros mirando raw/estado. Usa CTRL+C cuando termines."
echo

set +e
python robot-pi/scripts/tcrt5000_realtime.py
set -e

echo
echo "Calibracion detenida."
echo "Presiona ENTER para reiniciar el runtime del robot."
read _unused

/usr/bin/docker compose up -d --build
/usr/bin/docker compose ps

echo
echo "Runtime reiniciado. Presiona ENTER para cerrar."
read _unused
