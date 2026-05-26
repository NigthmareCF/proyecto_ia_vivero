from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None


WINDOW_NAME = "QR Live Viewer"
RESOLUTION_CANDIDATES = [
    (3840, 2160),
    (2560, 1440),
    (1920, 1080),
    (1600, 1200),
    (1280, 720),
    (1024, 768),
    (800, 600),
    (640, 480),
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)

    def joined(self) -> str:
        return " ".join(self.parts)


def current_timestamp() -> float:
    return time.time()


def output_dir() -> Path:
    path = Path(__file__).resolve().parent / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_best_camera_mode(cap: cv2.VideoCapture) -> dict[str, int | float]:
    best_width = 0
    best_height = 0
    for width, height in RESOLUTION_CANDIDATES:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if (actual_width * actual_height) > (best_width * best_height):
            best_width = actual_width
            best_height = actual_height
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    return {
        "width": best_width,
        "height": best_height,
        "fps": fps,
    }


def is_url(payload: str) -> bool:
    try:
        parsed = urlparse(payload)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def fetch_url_text(url: str) -> dict[str, Any]:
    started_at = current_timestamp()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 QR-Live-Viewer",
                },
            ),
            timeout=15,
        ) as response:
            raw_bytes = response.read()
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {
            "url": url,
            "ok": False,
            "error": str(exc),
            "contentType": None,
            "text": None,
            "fetchStartedAt": started_at,
            "fetchCompletedAt": current_timestamp(),
            "fetchLatencyMs": round((current_timestamp() - started_at) * 1000, 1),
        }

    text = raw_bytes.decode(charset, errors="replace")
    visible_text = text
    if "html" in content_type.lower():
        parser = TextExtractor()
        parser.feed(text)
        visible_text = parser.joined()
    compact_text = " ".join(visible_text.split())
    return {
        "url": url,
        "ok": True,
        "contentType": content_type,
        "text": compact_text[:4000],
        "fetchStartedAt": started_at,
        "fetchCompletedAt": current_timestamp(),
        "fetchLatencyMs": round((current_timestamp() - started_at) * 1000, 1),
    }


def decode_with_pyzbar(frame: np.ndarray) -> list[dict[str, Any]]:
    if pyzbar_decode is None:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detections: list[dict[str, Any]] = []
    for item in pyzbar_decode(gray):
        payload = item.data.decode("utf-8", errors="replace").strip()
        polygon = []
        if getattr(item, "polygon", None):
            polygon = [[int(point.x), int(point.y)] for point in item.polygon]
        rect = getattr(item, "rect", None)
        detections.append(
            {
                "method": "pyzbar",
                "payload": payload,
                "polygon": polygon,
                "rect": None
                if rect is None
                else {
                    "left": int(rect.left),
                    "top": int(rect.top),
                    "width": int(rect.width),
                    "height": int(rect.height),
                },
            }
        )
    return detections


def decode_with_opencv(frame: np.ndarray) -> list[dict[str, Any]]:
    detector = cv2.QRCodeDetector()
    ok, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
    if not ok or points is None:
        payload, single_points, _ = detector.detectAndDecode(frame)
        if not payload or single_points is None:
            return []
        decoded_info = [payload]
        points = np.array([single_points], dtype=np.float32)

    detections: list[dict[str, Any]] = []
    for payload, point_set in zip(decoded_info, points):
        normalized_payload = str(payload or "").strip()
        if not normalized_payload:
            continue
        polygon = [[int(point[0]), int(point[1])] for point in point_set]
        detections.append(
            {
                "method": "opencv",
                "payload": normalized_payload,
                "polygon": polygon,
                "rect": None,
            }
        )
    return detections


def annotate_frame(
    frame: np.ndarray,
    detections: list[dict[str, Any]],
    fps: float,
    camera_mode: dict[str, int | float],
    url_text_cache: dict[str, dict[str, Any]],
) -> np.ndarray:
    annotated = frame.copy()
    header = f"Detections: {len(detections)} | FPS: {fps:.1f}"
    cv2.putText(annotated, header, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 255, 30), 2, cv2.LINE_AA)
    camera_header = f"Camera: {camera_mode['width']}x{camera_mode['height']}"
    cv2.putText(annotated, camera_header, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(
        annotated,
        "Q/ESC: salir",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    for index, detection in enumerate(detections):
        polygon = detection.get("polygon") or []
        if len(polygon) >= 4:
            points = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [points], True, (0, 220, 0), 3)
            anchor = tuple(points[0][0])
        else:
            rect = detection.get("rect") or {}
            left = int(rect.get("left", 20))
            top = int(rect.get("top", 100 + (index * 40)))
            width = int(rect.get("width", 160))
            height = int(rect.get("height", 160))
            cv2.rectangle(annotated, (left, top), (left + width, top + height), (0, 220, 0), 3)
            anchor = (left, max(top - 12, 24))

        payload = detection.get("payload", "")
        line_1 = f"QR {index + 1}: {payload}"
        line_2 = f"Metodo: {detection.get('method', 'unknown')}"
        cv2.putText(annotated, line_1, anchor, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 5, cv2.LINE_AA)
        cv2.putText(annotated, line_1, anchor, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(
            annotated,
            line_2,
            (anchor[0], anchor[1] + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
            cv2.LINE_AA,
        )
        payload = detection.get("payload", "")
        timing_anchor_y = anchor[1] + 54
        if is_url(payload):
            url_result = url_text_cache.get(payload)
            if url_result and url_result.get("ok") and url_result.get("text"):
                preview = str(url_result["text"])[:120]
                cv2.putText(
                    annotated,
                    f"Texto: {preview}",
                    (anchor[0], timing_anchor_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                timing_anchor_y += 24
            if url_result and detection.get("latencyToResolvedTextMs") is not None:
                latency_line = (
                    f"Det->texto: {detection['latencyToResolvedTextMs']} ms | "
                    f"Fetch: {url_result.get('fetchLatencyMs', '--')} ms"
                )
                cv2.putText(
                    annotated,
                    latency_line,
                    (anchor[0], timing_anchor_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 200, 255),
                    1,
                    cv2.LINE_AA,
                )
    return annotated


def persist_state(
    detections: list[dict[str, Any]],
    frame: np.ndarray | None,
    camera_mode: dict[str, int | float],
    url_text_cache: dict[str, dict[str, Any]],
) -> None:
    out = output_dir()
    state = {
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cameraMode": camera_mode,
        "detections": detections,
        "detectedPayloads": [item["payload"] for item in detections],
        "resolvedUrls": [url_text_cache[payload] for payload in url_text_cache],
    }
    (out / "qr_live_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    if frame is not None:
        cv2.imwrite(str(out / "qr_live_last_frame.png"), frame)


def main() -> int:
    cap = cv2.VideoCapture(0)
    if not cap or not cap.isOpened():
        print(json.dumps({"ok": False, "error": "No se pudo abrir la camara 0"}, ensure_ascii=False))
        return 1

    camera_mode = configure_best_camera_mode(cap)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 720)

    previous_time = time.time()
    url_text_cache: dict[str, dict[str, Any]] = {}
    first_seen_at: dict[str, float] = {}
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                black = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(black, "Sin frame de camara", (40, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                cv2.imshow(WINDOW_NAME, black)
                if cv2.waitKey(30) & 0xFF in {27, ord("q"), ord("Q")}:
                    break
                continue

            current_time = time.time()
            fps = 1.0 / max(current_time - previous_time, 1e-6)
            previous_time = current_time

            detections = decode_with_pyzbar(frame) or decode_with_opencv(frame)
            for detection in detections:
                payload = str(detection.get("payload", "")).strip()
                if payload and payload not in first_seen_at:
                    first_seen_at[payload] = current_time
                detection["detectedAt"] = first_seen_at.get(payload)
                if payload and is_url(payload) and payload not in url_text_cache:
                    url_text_cache[payload] = fetch_url_text(payload)
                if payload and payload in url_text_cache:
                    resolved = url_text_cache[payload]
                    fetch_completed_at = resolved.get("fetchCompletedAt")
                    detected_at = detection.get("detectedAt")
                    if isinstance(fetch_completed_at, (int, float)) and isinstance(detected_at, (int, float)):
                        detection["latencyToResolvedTextMs"] = round((fetch_completed_at - detected_at) * 1000, 1)
                    if resolved.get("ok") and resolved.get("text"):
                        detection["resolvedTextPreview"] = str(resolved["text"])[:240]
            persist_state(detections, frame, camera_mode, url_text_cache)
            annotated = annotate_frame(frame, detections, fps, camera_mode, url_text_cache)
            cv2.imshow(WINDOW_NAME, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key in {27, ord("q"), ord("Q")}:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
