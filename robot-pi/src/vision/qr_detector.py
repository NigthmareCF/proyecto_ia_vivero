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
