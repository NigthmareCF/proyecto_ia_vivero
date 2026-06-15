#!/bin/sh
set -eu

PROJECT_DIR="/home/fer-dev/ROBOT-PI-EJECUTION"
LOG_DIR="/home/fer-dev/ROBOT-PI-EJECUTION/logs"
LOG_FILE="$LOG_DIR/boot-start.log"

mkdir -p "$LOG_DIR"

enforce_max_camera_config() {
  for env_file in .env .env.local-lab; do
    [ -f "$env_file" ] || continue
    tmp_file="${env_file}.tmp"
    awk '
      BEGIN {
        seen_width=0
        seen_height=0
        seen_fps=0
        seen_quality=0
      }
      /^CAMERA_WIDTH=/ { print "CAMERA_WIDTH=1920"; seen_width=1; next }
      /^CAMERA_HEIGHT=/ { print "CAMERA_HEIGHT=1080"; seen_height=1; next }
      /^STREAM_FPS=/ { print "STREAM_FPS=30"; seen_fps=1; next }
      /^STREAM_QUALITY=/ { print "STREAM_QUALITY=100"; seen_quality=1; next }
      { print }
      END {
        if (!seen_width) print "CAMERA_WIDTH=1920"
        if (!seen_height) print "CAMERA_HEIGHT=1080"
        if (!seen_fps) print "STREAM_FPS=30"
        if (!seen_quality) print "STREAM_QUALITY=100"
      }
    ' "$env_file" > "$tmp_file"
    mv "$tmp_file" "$env_file"
  done
}

ensure_camera_mjpeg() {
  camera_handler="robot-pi/src/vision/camera_handler.py"
  [ -f "$camera_handler" ] || return 0
  grep -q "CAP_PROP_FOURCC" "$camera_handler" || python - <<'PY'
from pathlib import Path

path = Path("robot-pi/src/vision/camera_handler.py")
text = path.read_text()
old = (
    "        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)\n"
    "        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)\n"
)
new = (
    "        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*\"MJPG\"))\n"
    "        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)\n"
    "        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)\n"
    "        capture.set(cv2.CAP_PROP_FPS, self.settings.stream_fps)\n"
)
if old in text:
    path.write_text(text.replace(old, new, 1))
PY
}

update_repo() {
  branch="$(/usr/bin/git branch --show-current)"
  [ -n "$branch" ] || branch="funcionalidad/robot-pi-runtime"
  /usr/bin/git fetch origin "$branch"
  /usr/bin/git merge -X theirs --no-edit "origin/$branch"
}

{
  echo "==== $(date -Is) starting robot runtime ===="
  cd "$PROJECT_DIR"
  update_repo
  enforce_max_camera_config
  ensure_camera_mjpeg
  /usr/bin/docker compose up -d --build
  /usr/bin/docker ps --filter name=agrotech-robot --format 'status={{.Status}}'
} >> "$LOG_FILE" 2>&1
