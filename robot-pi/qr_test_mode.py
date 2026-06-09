from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from src.config import Settings
from src.vision.camera_handler import CameraHandler
from src.vision.qr_detector import detect_qr


QR_LOG = Path("/tmp/qr_test_results.log")
METRICS_LOG = Path("/tmp/qr_test_burst_metrics.log")


def write_line(path: Path, message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} | {message}\n")
        file.flush()


def detect_from_sides(camera: CameraHandler) -> tuple[str | None, str | None]:
    for position in ("left", "right"):
        frame = camera.capture_frame(position)
        payload = detect_qr(frame)
        if payload:
            return position, payload
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Modo test: solo reconocimiento QR y metricas de rafaga.")
    parser.add_argument("--poll-interval", type=float, default=0.05, help="Segundos entre lecturas de QR.")
    parser.add_argument("--cooldown", type=float, default=None, help="Segundos para ignorar el mismo QR repetido.")
    parser.add_argument("--once", action="store_true", help="Salir despues de la primera rafaga.")
    args = parser.parse_args()

    settings = Settings.load()
    cooldown = settings.qr_detection_cooldown_seconds if args.cooldown is None else max(args.cooldown, 0.0)
    camera = CameraHandler(settings)
    running = True
    recent_qr: dict[str, float] = {}
    test_started_at = time.monotonic()

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    QR_LOG.write_text("", encoding="utf-8")
    METRICS_LOG.write_text("", encoding="utf-8")
    write_line(QR_LOG, "TEST_QR_ONLY iniciado; esperando QR de texto en camaras left/right")
    write_line(
        METRICS_LOG,
        (
            "TEST_QR_ONLY iniciado; "
            f"capture_count={max(settings.capture_count, 4)} "
            f"interval_seconds={settings.burst_frame_interval_seconds:.3f}"
        ),
    )

    try:
        camera.setup()
        while running:
            detected_at = time.monotonic()
            position, payload = detect_from_sides(camera)
            if not payload:
                time.sleep(max(args.poll_interval, 0.01))
                continue

            last_seen = recent_qr.get(payload)
            if last_seen is not None and detected_at - last_seen < cooldown:
                time.sleep(max(args.poll_interval, 0.01))
                continue
            recent_qr[payload] = detected_at

            write_line(
                QR_LOG,
                (
                    f"QR detectado | camera={position} | texto={payload} | "
                    f"desde_inicio={detected_at - test_started_at:.3f}s"
                ),
            )

            burst_started_at = time.monotonic()
            frames = camera.capture_side_burst(
                max(settings.capture_count, 4),
                settings.burst_frame_interval_seconds,
            )
            burst_finished_at = time.monotonic()

            write_line(
                METRICS_LOG,
                (
                    f"QR={payload} | rafaga_inicio_desde_deteccion={burst_started_at - detected_at:.3f}s | "
                    f"rafaga_inicio_desde_test={burst_started_at - test_started_at:.3f}s | "
                    f"duracion={burst_finished_at - burst_started_at:.3f}s | "
                    f"fotos={len(frames)}"
                ),
            )

            if args.once:
                break
    finally:
        camera.release()
        write_line(QR_LOG, "TEST_QR_ONLY detenido")
        write_line(METRICS_LOG, "TEST_QR_ONLY detenido")

    return 0


if __name__ == "__main__":
    sys.exit(main())
