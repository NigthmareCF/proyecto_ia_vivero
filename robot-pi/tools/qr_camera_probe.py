from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None


def ensure_output_dir() -> Path:
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def decode_with_pyzbar(frame: np.ndarray) -> list[dict[str, Any]]:
    if pyzbar_decode is None:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = []
    for item in pyzbar_decode(gray):
        payload = item.data.decode("utf-8", errors="replace").strip()
        polygon = []
        if getattr(item, "polygon", None):
            for point in item.polygon:
                polygon.append([int(point.x), int(point.y)])
        rect = getattr(item, "rect", None)
        results.append(
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
    return results


def decode_with_opencv(frame: np.ndarray) -> list[dict[str, Any]]:
    detector = cv2.QRCodeDetector()
    ok, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
    if not ok or points is None:
        single_payload, single_points, _ = detector.detectAndDecode(frame)
        if not single_payload or single_points is None:
            return []
        decoded_info = [single_payload]
        points = np.array([single_points], dtype=np.float32)

    results: list[dict[str, Any]] = []
    for payload, point_set in zip(decoded_info, points):
        normalized_payload = str(payload or "").strip()
        if not normalized_payload:
            continue
        polygon = [[int(point[0]), int(point[1])] for point in point_set]
        results.append(
            {
                "method": "opencv",
                "payload": normalized_payload,
                "polygon": polygon,
                "rect": None,
            }
        )
    return results


def annotate_frame(frame: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
    annotated = frame.copy()
    for detection in detections:
        polygon = detection.get("polygon") or []
        if len(polygon) >= 4:
            points = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [points], isClosed=True, color=(0, 220, 0), thickness=3)
            label_anchor = tuple(points[0][0])
        else:
            rect = detection.get("rect") or {}
            left = int(rect.get("left", 20))
            top = int(rect.get("top", 40))
            width = int(rect.get("width", 160))
            height = int(rect.get("height", 160))
            cv2.rectangle(annotated, (left, top), (left + width, top + height), (0, 220, 0), 3)
            label_anchor = (left, max(top - 12, 24))
        cv2.putText(
            annotated,
            detection.get("payload", "QR"),
            label_anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 20, 20),
            5,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            detection.get("payload", "QR"),
            label_anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return annotated


def capture_qr(camera_index: int = 0, seconds: float = 15.0) -> dict[str, Any]:
    cap = cv2.VideoCapture(camera_index)
    started_at = time.time()
    output_dir = ensure_output_dir()
    last_frame_path = output_dir / "qr_last_frame.png"
    visualized_path = output_dir / "qr_detection_visualized.png"
    result_path = output_dir / "qr_detection_result.json"

    if not cap or not cap.isOpened():
        result = {
            "ok": False,
            "error": f"No se pudo abrir la camara {camera_index}",
            "cameraIndex": camera_index,
            "visualizedImage": None,
            "lastFrame": None,
            "detections": [],
        }
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    best_result: dict[str, Any] | None = None
    try:
        while (time.time() - started_at) <= seconds:
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.1)
                continue

            cv2.imwrite(str(last_frame_path), frame)
            detections = decode_with_pyzbar(frame) or decode_with_opencv(frame)
            if not detections:
                time.sleep(0.05)
                continue

            annotated = annotate_frame(frame, detections)
            cv2.imwrite(str(visualized_path), annotated)
            best_result = {
                "ok": True,
                "cameraIndex": camera_index,
                "visualizedImage": str(visualized_path),
                "lastFrame": str(last_frame_path),
                "detections": detections,
                "detectedPayloads": [item["payload"] for item in detections],
            }
            break
    finally:
        cap.release()

    if best_result is None:
        best_result = {
            "ok": False,
            "error": f"No se detecto ningun QR en {seconds:.1f}s",
            "cameraIndex": camera_index,
            "visualizedImage": None,
            "lastFrame": str(last_frame_path) if last_frame_path.exists() else None,
            "detections": [],
        }

    result_path.write_text(json.dumps(best_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return best_result


if __name__ == "__main__":
    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    duration_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
    result = capture_qr(camera_index=camera_index, seconds=duration_seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)
