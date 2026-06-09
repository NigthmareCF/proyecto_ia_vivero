#!/usr/bin/env bash
set -euo pipefail

cd /home/fer-dev/ROBOT-PI-EJECUTION
docker compose run --rm -v /home/fer-dev/ROBOT-PI-EJECUTION/robot-pi/scripts:/app/scripts robot python -u /app/scripts/tcrt5000_realtime.py
exec bash
