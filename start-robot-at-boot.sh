#!/bin/sh
set -eu

PROJECT_DIR="/home/fer-dev/ROBOT-PI-EJECUTION"
LOG_DIR="/home/fer-dev/ROBOT-PI-EJECUTION/logs"
LOG_FILE="$LOG_DIR/boot-start.log"
REMOTE_NAME="origin"
REMOTE_BRANCH="funcionalidad/robot-pi-runtime"

mkdir -p "$LOG_DIR"

ensure_wifi_profiles() {
  if ! command -v nmcli >/dev/null 2>&1; then
    return 0
  fi

  # The lab 5 GHz AP is on channel 153. Some Broadcom regulatory defaults hide
  # high 5 GHz channels until the regdomain is set.
  if command -v iw >/dev/null 2>&1; then
    iw reg set US >/dev/null 2>&1 || true
  fi

  nmcli connection modify "Redmi Note 14" \
    802-11-wireless.hidden yes \
    connection.autoconnect yes \
    connection.autoconnect-priority 100 \
    connection.autoconnect-retries 0 \
    ipv4.route-metric 40 \
    ipv6.route-metric 40 >/dev/null 2>&1 || true

  if ! nmcli -t -f NAME connection show | grep -Fxq "CLARO_5GHz_FD7255"; then
    nmcli connection add type wifi ifname wlan0 con-name "CLARO_5GHz_FD7255" ssid "CLARO_5GHz_FD7255" >/dev/null 2>&1 || true
  fi
  nmcli connection modify "CLARO_5GHz_FD7255" \
    802-11-wireless.ssid "CLARO_5GHz_FD7255" \
    802-11-wireless.bssid "BA:85:7B:FD:72:60" \
    802-11-wireless.band a \
    802-11-wireless.channel 153 \
    connection.autoconnect yes \
    connection.autoconnect-priority 80 \
    connection.autoconnect-retries 0 \
    ipv4.route-metric 50 \
    ipv6.route-metric 50 >/dev/null 2>&1 || true

  if ! nmcli -t -f NAME connection show | grep -Fxq "CLARO_2.4GHz_FD7255"; then
    nmcli connection add type wifi ifname wlan0 con-name "CLARO_2.4GHz_FD7255" ssid "CLARO_2.4GHz_FD7255" >/dev/null 2>&1 || true
  fi
  nmcli connection modify "CLARO_2.4GHz_FD7255" \
    802-11-wireless.ssid "CLARO_2.4GHz_FD7255" \
    802-11-wireless.bssid "BA:85:7B:FD:72:5C" \
    802-11-wireless.band bg \
    802-11-wireless.channel 1 \
    connection.autoconnect yes \
    connection.autoconnect-priority 70 \
    connection.autoconnect-retries 0 \
    ipv4.route-metric 60 \
    ipv6.route-metric 60 >/dev/null 2>&1 || true

  nmcli connection modify "Wired connection 1" \
    connection.autoconnect yes \
    connection.autoconnect-priority -999 \
    ipv4.route-metric 700 \
    ipv6.route-metric 700 >/dev/null 2>&1 || true

  nmcli connection up "CLARO_5GHz_FD7255" >/dev/null 2>&1 || \
    nmcli connection up "CLARO_2.4GHz_FD7255" >/dev/null 2>&1 || true
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

wait_for_network() {
  i=0
  while [ "$i" -lt 24 ]; do
    if /usr/bin/git -C "$PROJECT_DIR" ls-remote --exit-code "$REMOTE_NAME" "refs/heads/$REMOTE_BRANCH" >/dev/null 2>&1; then
      return 0
    fi
    i=$((i + 1))
    /bin/sleep 5
  done
  echo "network/git remote not reachable after retries"
  return 1
}

force_remote_repo() {
  wait_for_network
  /usr/bin/git -C "$PROJECT_DIR" fetch "$REMOTE_NAME" "$REMOTE_BRANCH"
  /usr/bin/git -C "$PROJECT_DIR" checkout -B "$REMOTE_BRANCH" "$REMOTE_NAME/$REMOTE_BRANCH"
  /usr/bin/git -C "$PROJECT_DIR" reset --hard "$REMOTE_NAME/$REMOTE_BRANCH"
}

{
  echo "==== $(date -Is) starting robot runtime ===="
  cd "$PROJECT_DIR"
  ensure_wifi_profiles
  force_remote_repo
  ensure_camera_mjpeg
  /usr/bin/docker rm -f agrotech-robot >/dev/null 2>&1 || true
  /usr/bin/docker compose up -d --build --force-recreate
  /usr/bin/docker ps --filter name=agrotech-robot --format 'status={{.Status}}'
} >> "$LOG_FILE" 2>&1
