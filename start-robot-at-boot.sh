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
