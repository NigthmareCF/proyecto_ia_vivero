from __future__ import annotations

import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode
except Exception:  # pragma: no cover
    decode = None


def detect_qr(frame: np.ndarray | None) -> str | None:
    if frame is None or decode is None:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = decode(gray)
    for result in results:
        payload = result.data.decode("utf-8").strip()
        if payload:
            return payload
    return None


def detect_qr_candidates(frame: np.ndarray | None) -> list[dict[str, float | str]]:
    if frame is None or decode is None:
        return []

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = decode(gray)
    candidates: list[dict[str, float | str]] = []
    seen_payloads: set[str] = set()

    for result in results:
        payload = result.data.decode("utf-8").strip()
        if not payload or payload in seen_payloads:
            continue
        seen_payloads.add(payload)

        rect = getattr(result, "rect", None)
        if rect is not None:
            left = float(rect.left)
            top = float(rect.top)
            width = float(rect.width)
            height = float(rect.height)
            center_x = left + (width / 2.0)
            center_y = top + (height / 2.0)
        else:
            polygon = getattr(result, "polygon", None) or []
            if polygon:
                xs = [float(point.x) for point in polygon]
                ys = [float(point.y) for point in polygon]
                left = min(xs)
                top = min(ys)
                width = max(xs) - left
                height = max(ys) - top
                center_x = left + (width / 2.0)
                center_y = top + (height / 2.0)
            else:
                left = 0.0
                top = 0.0
                width = 0.0
                height = 0.0
                center_x = 0.0
                center_y = 0.0

        candidates.append({
            "payload": payload,
            "center_x": center_x,
            "center_y": center_y,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        })

    return candidates
