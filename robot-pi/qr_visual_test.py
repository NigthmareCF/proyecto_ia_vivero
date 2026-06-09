from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import sys
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np
import requests

try:
    from pyzbar.pyzbar import decode
except Exception:  # pragma: no cover
    decode = None

from src.config import LINE_SENSOR_CENTER, LINE_SENSOR_LEFT, LINE_SENSOR_RIGHT, Settings
from src.vision.camera_handler import CameraHandler


BACKEND_LOG = Path(os.getenv("QR_BACKEND_LOG", "/tmp/qr_backend_monitor.log"))

HTML = b"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QR visual test</title>
  <style>
    body { margin: 0; background: #101010; color: #eee; font-family: sans-serif; }
    header { padding: 10px 14px; background: #1e1e1e; font-size: 15px; }
    img { display: block; width: 100vw; height: calc(100vh - 42px); object-fit: contain; background: #050505; }
  </style>
</head>
<body>
  <header>Modo test QR visual: texto, distancia estimada, fotos de rafaga y etiqueta plantQr por rafaga.</header>
  <img src="/stream" alt="QR stream">
</body>
</html>
"""


def polygon_points(result: Any) -> list[tuple[int, int]]:
    points = getattr(result, "polygon", None) or []
    return [(int(point.x), int(point.y)) for point in points]


def qr_pixel_width(result: Any) -> float:
    points = polygon_points(result)
    if len(points) >= 4:
        distances = []
        for index, point in enumerate(points):
            next_point = points[(index + 1) % len(points)]
            distances.append(math.dist(point, next_point))
        return float(max(distances))
    rect = result.rect
    return float(max(rect.width, rect.height))


def draw_label(frame: np.ndarray, lines: list[str]) -> None:
    y = 28
    for line in lines:
        cv2.putText(frame, line[:95], (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, line[:95], (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
        y += 26


def draw_badge(frame: np.ndarray, text: str, y: int = 26) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 38), (0, 0, 0), -1)
    cv2.putText(frame, text[:95], (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)


def log_backend(message: str, data: dict[str, Any] | None = None) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}"
    if data is not None:
        line += " | " + json.dumps(data, ensure_ascii=True, sort_keys=True)
    with BACKEND_LOG.open("a", encoding="utf-8") as file:
        file.write(line + "\n")
        file.flush()


def encode_images(camera: CameraHandler, frames: list[np.ndarray]) -> list[str]:
    encoded: list[str] = []
    for frame in frames:
        if isinstance(frame, np.ndarray) and frame.size:
            image = camera.frame_to_base64(frame)
            if image:
                encoded.append(image)
    return encoded


def backend_target(settings: Settings, path: str) -> tuple[str, str, int | None, str]:
    url = f"{settings.backend_base_url.rstrip('/')}{path}"
    parsed = urlparse(url)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80 if parsed.scheme == "http" else None
    return url, parsed.hostname or "", port, parsed.scheme


def read_line_sensors(settings: Settings) -> dict[str, Any]:
    try:
        import RPi.GPIO as GPIO  # type: ignore
    except Exception as exc:
        return {"available": False, "reason": f"RPi.GPIO no disponible: {exc}"}
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (LINE_SENSOR_LEFT, LINE_SENSOR_CENTER, LINE_SENSOR_RIGHT):
            GPIO.setup(pin, GPIO.IN)
        raw = {
            "left": int(GPIO.input(LINE_SENSOR_LEFT)),
            "center": int(GPIO.input(LINE_SENSOR_CENTER)),
            "right": int(GPIO.input(LINE_SENSOR_RIGHT)),
        }
        if settings.line_active_low:
            normalized = {name: 0 if value == 1 else 1 for name, value in raw.items()}
        else:
            normalized = raw.copy()
        pattern = (normalized["left"], normalized["center"], normalized["right"])
        return {
            "available": True,
            "activeLow": settings.line_active_low,
            "raw": raw,
            "normalized": normalized,
            "pattern": pattern,
            "lineDetected": pattern not in {(0, 0, 0), (1, 1, 1)},
        }
    except Exception as exc:
        return {"available": False, "reason": str(exc)}


def probe_backend_startup(settings: Settings) -> None:
    command_url, command_host, command_port, command_scheme = backend_target(settings, settings.command_next_path)
    log_backend(
        "PROBANDO_BACKEND_COMANDOS",
        {
            "method": "GET",
            "url": command_url,
            "scheme": command_scheme,
            "backendHost": command_host,
            "backendPort": command_port,
            "params": {"robotId": settings.robot_id},
            "expectedResponse": "204 sin comando o 200 JSON con data",
        },
    )
    try:
        response = requests.get(command_url, params={"robotId": settings.robot_id}, timeout=5)
        body_preview = response.text[:500] if response.status_code != 204 else ""
        log_backend(
            "RESPUESTA_BACKEND_COMANDOS",
            {"ok": response.ok, "statusCode": response.status_code, "bodyPreview": body_preview},
        )
    except requests.RequestException as exc:
        log_backend("ERROR_COMUNICACION_BACKEND_COMANDOS", {"error": str(exc)})

    heartbeat_url, heartbeat_host, heartbeat_port, heartbeat_scheme = backend_target(settings, settings.heartbeat_path)
    payload = {
        "robotId": settings.robot_id,
        "mode": "QR_TEST_STARTUP",
        "connectionQuality": "TESTING",
        "currentPlantQr": None,
        "streamActive": True,
        "statusSummary": "qr_visual_test_startup_probe",
        "activeCamera": "LEFT_RIGHT",
        "controlProfile": "TEST_ONLY",
        "speedProfile": "STOPPED",
        "queueDepth": 0,
    }
    log_backend(
        "PROBANDO_BACKEND_HEARTBEAT",
        {
            "method": "POST",
            "url": heartbeat_url,
            "scheme": heartbeat_scheme,
            "backendHost": heartbeat_host,
            "backendPort": heartbeat_port,
            "expectedResponse": "HTTP 2xx",
            "payload": payload,
        },
    )
    try:
        response = requests.post(heartbeat_url, json=payload, timeout=5)
        log_backend(
            "RESPUESTA_BACKEND_HEARTBEAT_STARTUP",
            {"ok": response.ok, "statusCode": response.status_code, "bodyPreview": response.text[:500]},
        )
    except requests.RequestException as exc:
        log_backend("ERROR_COMUNICACION_BACKEND_HEARTBEAT_STARTUP", {"error": str(exc)})


class VisualQrState:
    def __init__(
        self,
        camera: CameraHandler,
        settings: Settings,
        qr_size_cm: float,
        focal_length_px: float | None,
        camera_fov_degrees: float,
        reference_distance_cm: float | None,
    ) -> None:
        self.camera = camera
        self.settings = settings
        self.qr_size_cm = qr_size_cm
        self.focal_length_px = focal_length_px
        self.camera_fov_degrees = camera_fov_degrees
        self.reference_distance_cm = reference_distance_cm
        self.calibration_samples: list[float] = []
        self.lock = threading.Lock()
        self.latest_frame: bytes = b""
        self.latest_burst: list[np.ndarray] = []
        self.latest_burst_qr = ""
        self.latest_burst_started_at = 0.0
        self.latest_burst_duration = 0.0
        self.latest_qr_text = ""
        self.latest_qr_camera = ""
        self.latest_qr_seen_at = 0.0
        self.burst_status = "esperando QR"
        self.backend_status = "sin envio todavia"
        self.backend_target_summary = self.build_backend_target_summary()
        self.recent_qr: dict[str, float] = {}
        self.capture_running = False
        self.running = True
        self.telemetry_threads: list[threading.Thread] = []

    def build_backend_target_summary(self) -> str:
        url, host, port, scheme = backend_target(self.settings, self.settings.observation_path)
        port_text = str(port) if port is not None else "desconocido"
        return f"{scheme}://{host}:{port_text} -> {url}"

    def update_loop(self) -> None:
        while self.running:
            frame = self.build_frame()
            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                with self.lock:
                    self.latest_frame = encoded.tobytes()
            time.sleep(0.03)

    def build_frame(self) -> np.ndarray:
        frames = [("left", self.camera.capture_frame("left")), ("right", self.camera.capture_frame("right"))]
        rendered: list[np.ndarray] = []
        for name, frame in frames:
            if frame is None:
                continue
            rendered.append(self.annotate(name, frame.copy()))
        if not rendered:
            live = np.zeros((480, 640, 3), dtype=np.uint8)
        elif len(rendered) == 1:
            live = rendered[0]
        else:
            height = min(frame.shape[0] for frame in rendered)
            resized = [
                cv2.resize(frame, (int(frame.shape[1] * height / frame.shape[0]), height))
                for frame in rendered
            ]
            live = cv2.hconcat(resized)
        burst = self.build_burst_panel(live.shape[1])
        status = self.build_status_panel(live.shape[1])
        return cv2.vconcat([status, live, burst])

    def build_status_panel(self, target_width: int) -> np.ndarray:
        panel = np.zeros((96, target_width, 3), dtype=np.uint8)
        with self.lock:
            latest_qr_text = self.latest_qr_text
            latest_qr_camera = self.latest_qr_camera
            latest_qr_seen_at = self.latest_qr_seen_at
            burst_status = self.burst_status
            backend_status = self.backend_status
            backend_target_summary = self.backend_target_summary
        age = time.monotonic() - latest_qr_seen_at if latest_qr_seen_at else 0.0
        qr_line = "QR leido: ninguno todavia"
        if latest_qr_text:
            qr_line = f"QR leido: {latest_qr_text} | camara={latest_qr_camera} | hace={age:.1f}s"
        lines = [
            f"FOV inicial automatico: {self.camera_fov_degrees:.0f} deg | QR real={self.qr_size_cm:.1f}cm",
            qr_line,
            f"rafaga: {burst_status}",
            f"envio/backend puerto: {backend_target_summary} | ultimo estado: {backend_status}",
        ]
        draw_label(panel, lines)
        return panel

    def annotate(self, camera_name: str, frame: np.ndarray) -> np.ndarray:
        lines = [f"camara: {camera_name}"]
        if decode is None:
            draw_label(frame, lines + ["pyzbar/libzbar no disponible"])
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = decode(gray)
        if not results:
            draw_label(frame, lines + ["QR: no detectado"])
            return frame
        for result in results:
            text = result.data.decode("utf-8", errors="replace").strip()
            with self.lock:
                self.latest_qr_text = text
                self.latest_qr_camera = camera_name
                self.latest_qr_seen_at = time.monotonic()
            points = polygon_points(result)
            if points:
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 3)
            width_px = qr_pixel_width(result)
            self.auto_calibrate(width_px)
            distance_line = self.distance_line(frame.shape[1], width_px)
            self.maybe_capture_burst(text)
            lines.extend([
                f"QR: {text}",
                f"ancho_qr: {width_px:.1f} px",
                distance_line,
                f"etiqueta interna: plantQr={text}",
            ])
            break
        draw_label(frame, lines)
        return frame

    def auto_calibrate(self, qr_width_px: float) -> None:
        if self.focal_length_px is not None or self.reference_distance_cm is None or qr_width_px <= 0:
            return
        focal_px = (qr_width_px * self.reference_distance_cm) / self.qr_size_cm
        self.calibration_samples.append(focal_px)
        if len(self.calibration_samples) > 20:
            self.calibration_samples.pop(0)
        if len(self.calibration_samples) >= 8:
            ordered = sorted(self.calibration_samples)
            middle = ordered[len(ordered) // 4 : len(ordered) * 3 // 4]
            self.focal_length_px = sum(middle) / len(middle)

    def distance_line(self, frame_width_px: int, qr_width_px: float) -> str:
        if qr_width_px <= 0:
            return "distancia_estimada: no disponible"
        focal_px = self.focal_length_px
        source = "focal calibrada"
        if focal_px is None:
            fov_radians = math.radians(self.camera_fov_degrees)
            focal_px = frame_width_px / (2.0 * math.tan(fov_radians / 2.0))
            source = f"FOV {self.camera_fov_degrees:.0f}deg estimado"
        distance_cm = (self.qr_size_cm * focal_px) / qr_width_px
        return f"distancia_estimada: {distance_cm:.1f} cm ({source}, QR {self.qr_size_cm:.1f}cm)"

    def maybe_capture_burst(self, qr_text: str) -> None:
        now = time.monotonic()
        last_seen = self.recent_qr.get(qr_text)
        if self.capture_running:
            return
        if last_seen is not None and now - last_seen < self.settings.qr_detection_cooldown_seconds:
            with self.lock:
                remaining = self.settings.qr_detection_cooldown_seconds - (now - last_seen)
                self.burst_status = f"cooldown activo para plantQr={qr_text} ({remaining:.1f}s)"
            return
        self.recent_qr[qr_text] = now
        self.capture_running = True
        try:
            started_at = time.monotonic()
            with self.lock:
                self.burst_status = f"inicializada para plantQr={qr_text}"
            frames = self.camera.capture_side_burst(
                max(self.settings.capture_count, 4),
                self.settings.burst_frame_interval_seconds,
            )
            finished_at = time.monotonic()
            with self.lock:
                self.latest_burst = [frame.copy() for frame in frames]
                self.latest_burst_qr = qr_text
                self.latest_burst_started_at = started_at
                self.latest_burst_duration = finished_at - started_at
                self.burst_status = (
                    f"completada plantQr={qr_text}; fotos={len(frames)}; "
                    f"duracion={finished_at - started_at:.3f}s"
                )
            self.start_backend_report(qr_text, frames, finished_at - started_at)
        finally:
            self.capture_running = False

    def start_backend_report(self, qr_text: str, frames: list[np.ndarray], burst_duration: float) -> None:
        thread = threading.Thread(
            target=self.send_backend_report,
            args=(qr_text, [frame.copy() for frame in frames], burst_duration),
            daemon=True,
        )
        thread.start()
        self.telemetry_threads.append(thread)

    def send_backend_report(self, qr_text: str, frames: list[np.ndarray], burst_duration: float) -> None:
        line_state = read_line_sensors(self.settings)
        payload = {
            "robotId": self.settings.robot_id,
            "patrolId": "qr-test-mode",
            "plantQr": qr_text or "UNKNOWN",
            "captureReason": "QR_TEST_VISUAL",
            "statusHint": "PENDING_BACKEND_ANALYSIS",
            "observedAt": datetime.now().isoformat(),
            "mimeType": "image/jpeg",
            "imagesBase64": encode_images(self.camera, frames),
            "testMetadata": {
                "source": "qr_visual_test",
                "cameraFovDegrees": self.camera_fov_degrees,
                "burstFrameCount": len(frames),
                "burstDurationSeconds": round(burst_duration, 3),
                "lineFollower": line_state,
            },
        }
        url, host, port, scheme = backend_target(self.settings, self.settings.observation_path)
        with self.lock:
            self.backend_status = f"enviando observacion por puerto {port} ({scheme})"
        log_backend(
            "ENVIANDO_OBSERVACION_QR",
            {
                "method": "POST",
                "url": url,
                "scheme": scheme,
                "backendHost": host,
                "backendPort": port,
                "expectedResponse": "HTTP 2xx; si falla se registra status/body o excepcion",
                "payloadSummary": {
                    "robotId": payload["robotId"],
                    "patrolId": payload["patrolId"],
                    "plantQr": payload["plantQr"],
                    "captureReason": payload["captureReason"],
                    "mimeType": payload["mimeType"],
                    "imageCount": len(payload["imagesBase64"]),
                    "lineFollower": line_state,
                },
            },
        )
        try:
            response = requests.post(url, json=payload, timeout=10)
            with self.lock:
                self.backend_status = f"observacion HTTP {response.status_code} por puerto {port}"
            log_backend(
                "RESPUESTA_BACKEND_OBSERVACION",
                {"ok": response.ok, "statusCode": response.status_code, "bodyPreview": response.text[:500]},
            )
        except requests.RequestException as exc:
            with self.lock:
                self.backend_status = f"error observacion por puerto {port}: {exc}"
            log_backend("ERROR_COMUNICACION_BACKEND_OBSERVACION", {"error": str(exc)})

        heartbeat_url, heartbeat_host, heartbeat_port, heartbeat_scheme = backend_target(self.settings, self.settings.heartbeat_path)
        heartbeat = {
            "robotId": self.settings.robot_id,
            "mode": "QR_TEST",
            "connectionQuality": "TESTING",
            "currentPlantQr": qr_text,
            "streamActive": True,
            "statusSummary": "qr_visual_test",
            "activeCamera": "LEFT_RIGHT",
            "controlProfile": "TEST_ONLY",
            "speedProfile": "STOPPED",
            "queueDepth": 0,
        }
        log_backend(
            "ENVIANDO_HEARTBEAT_TEST",
            {
                "method": "POST",
                "url": heartbeat_url,
                "scheme": heartbeat_scheme,
                "backendHost": heartbeat_host,
                "backendPort": heartbeat_port,
                "expectedResponse": "HTTP 2xx",
                "payload": heartbeat,
            },
        )
        try:
            response = requests.post(heartbeat_url, json=heartbeat, timeout=10)
            with self.lock:
                self.backend_status = f"heartbeat HTTP {response.status_code} por puerto {heartbeat_port}"
            log_backend(
                "RESPUESTA_BACKEND_HEARTBEAT",
                {"ok": response.ok, "statusCode": response.status_code, "bodyPreview": response.text[:500]},
            )
        except requests.RequestException as exc:
            with self.lock:
                self.backend_status = f"error heartbeat por puerto {heartbeat_port}: {exc}"
            log_backend("ERROR_COMUNICACION_BACKEND_HEARTBEAT", {"error": str(exc)})

    def build_burst_panel(self, target_width: int) -> np.ndarray:
        with self.lock:
            frames = [frame.copy() for frame in self.latest_burst]
            qr_text = self.latest_burst_qr
            started_at = self.latest_burst_started_at
            duration = self.latest_burst_duration
        panel_height = max(190, int(target_width * 0.18))
        if not frames:
            panel = np.zeros((panel_height, target_width, 3), dtype=np.uint8)
            draw_label(panel, ["rafaga: esperando primer QR", "cada foto tomada se mostrara aqui con etiqueta plantQr"])
            return panel
        cell_count = len(frames)
        cell_width = max(1, target_width // cell_count)
        cells: list[np.ndarray] = []
        for index, frame in enumerate(frames):
            thumb = cv2.resize(frame, (cell_width, panel_height))
            draw_badge(thumb, f"foto {index + 1}/{cell_count} | plantQr={qr_text}")
            cells.append(thumb)
        panel = cv2.hconcat(cells)
        if panel.shape[1] < target_width:
            pad = np.zeros((panel_height, target_width - panel.shape[1], 3), dtype=np.uint8)
            panel = cv2.hconcat([panel, pad])
        elif panel.shape[1] > target_width:
            panel = panel[:, :target_width]
        age = time.monotonic() - started_at if started_at else 0.0
        summary = f"ultima rafaga: fotos={len(frames)} duracion={duration:.3f}s hace={age:.1f}s etiqueta=plantQr={qr_text}"
        cv2.rectangle(panel, (0, panel_height - 34), (target_width, panel_height), (0, 0, 0), -1)
        cv2.putText(panel, summary[:120], (10, panel_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
        return panel

    def get_frame(self) -> bytes:
        with self.lock:
            return self.latest_frame


class Handler(BaseHTTPRequestHandler):
    state: VisualQrState

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML)))
            self.end_headers()
            self.wfile.write(HTML)
            return
        if self.path != "/stream":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        while self.state.running:
            frame = self.state.get_frame()
            if not frame:
                time.sleep(0.05)
                continue
            try:
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            except BrokenPipeError:
                break
            time.sleep(0.05)


def optional_float(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    return float(raw) if raw else None


def float_from_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    return float(raw) if raw else default


def main() -> int:
    parser = argparse.ArgumentParser(description="Visor web para test visual de QR.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()

    settings = Settings.load()
    BACKEND_LOG.write_text("", encoding="utf-8")
    observation_url, observation_host, observation_port, observation_scheme = backend_target(settings, settings.observation_path)
    command_url, command_host, command_port, command_scheme = backend_target(settings, settings.command_next_path)
    log_backend(
        "QR_VISUAL_TEST_INICIADO",
        {
            "robotId": settings.robot_id,
            "backendBaseUrl": settings.backend_base_url,
            "observation": {
                "url": observation_url,
                "host": observation_host,
                "port": observation_port,
                "scheme": observation_scheme,
                "expects": "POST JSON de observacion; respuesta HTTP 2xx",
            },
            "commands": {
                "url": command_url,
                "host": command_host,
                "port": command_port,
                "scheme": command_scheme,
                "expects": "GET puede devolver 204 sin comandos o 200 JSON con data",
            },
            "camera": {
                "type": settings.camera_type,
                "frontIndex": settings.camera_front_index,
                "leftIndex": settings.camera_left_index,
                "rightIndex": settings.camera_right_index,
                "width": settings.camera_width,
                "height": settings.camera_height,
                "fovDefaultDegrees": float_from_env("QR_TEST_CAMERA_FOV_DEGREES", 60.0),
            },
            "lineFollowerInitial": read_line_sensors(settings),
        },
    )
    threading.Thread(target=probe_backend_startup, args=(settings,), daemon=True).start()
    camera = CameraHandler(settings)
    camera.setup()
    state = VisualQrState(
        camera,
        settings=settings,
        qr_size_cm=float_from_env("QR_TEST_QR_SIZE_CM", 5.0),
        focal_length_px=optional_float("QR_TEST_FOCAL_LENGTH_PX"),
        camera_fov_degrees=float_from_env("QR_TEST_CAMERA_FOV_DEGREES", 60.0),
        reference_distance_cm=optional_float("QR_TEST_REFERENCE_DISTANCE_CM"),
    )
    Handler.state = state

    def stop(_signum: int, _frame: object) -> None:
        state.running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    worker = threading.Thread(target=state.update_loop, daemon=True)
    worker.start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"QR visual test listo en http://{args.host}:{args.port}", flush=True)
    try:
        while state.running:
            server.handle_request()
    finally:
        server.server_close()
        camera.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
