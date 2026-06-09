#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${QR_BACKEND_LOG_HOST:-/home/fer-dev/ROBOT-PI-EJECUTION/robot-pi-data/qr_backend_monitor.log}"
mkdir -p "$(dirname "$LOG_PATH")"
[ -e "$LOG_PATH" ] || touch "$LOG_PATH"
tail -F "$LOG_PATH"
exec bash
