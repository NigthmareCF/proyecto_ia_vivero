from __future__ import annotations

import base64
import logging
import threading
import time
from typing import Any

import cv2
import numpy as np

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class CameraHandler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._captures: dict[str, Any] = {}
        self._lock = threading.Lock()

    def _open_camera(self, index: int) -> Any:
        if self.settings.camera_type == "csi":
            capture = cv2.VideoCapture(index, cv2.CAP_V4L2)
        else:
            capture = cv2.VideoCapture(index)
        if not capture or not capture.isOpened():
            LOGGER.warning("No se pudo abrir la camara con indice %s; se usara frame simulado", index)
            return None
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        return capture

    def setup(self) -> None:
        self._captures = {
            "front": self._open_camera(self.settings.camera_front_index),
            "left": self._open_camera(self.settings.camera_left_index),
            "right": self._open_camera(self.settings.camera_right_index),
        }

    def _simulated_frame(self) -> np.ndarray:
        return np.zeros((self.settings.camera_height, self.settings.camera_width, 3), dtype=np.uint8)

    def capture_frame(self, position: str = "front") -> np.ndarray | None:
        with self._lock:
            capture = self._captures.get(position)
            if capture is None:
                return self._simulated_frame()
            ok, frame = capture.read()
            return frame if ok else self._simulated_frame()

    def capture_triplet(self) -> dict[str, np.ndarray]:
        return {
            "left": self.capture_frame("left"),
            "front": self.capture_frame("front"),
            "right": self.capture_frame("right"),
        }

    def capture_burst(self, n: int) -> list[np.ndarray]:
        if n <= 1:
            frame = self.capture_frame("left")
            return [frame] if frame is not None else []
        triplet = self.capture_triplet()
        ordered = [triplet["left"], triplet["right"], triplet["front"]]
        return [frame for frame in ordered if frame is not None][:n]

    def capture_side_burst(self, n: int, interval_seconds: float) -> list[np.ndarray]:
        frames: list[np.ndarray] = []
        if n <= 0:
            return frames
        positions = ["left", "right"]
        for index in range(n):
            frame = self.capture_frame(positions[index % 2])
            if frame is not None:
                frames.append(frame)
            if index < n - 1:
                time.sleep(max(interval_seconds, 0.01))
        return frames

    def capture_position_burst(self, position: str, n: int, interval_seconds: float) -> list[np.ndarray]:
        frames: list[np.ndarray] = []
        if n <= 0:
            return frames
        for index in range(n):
            frame = self.capture_frame(position)
            if frame is not None:
                frames.append(frame)
            if index < n - 1:
                time.sleep(max(interval_seconds, 0.01))
        return frames

    def frame_to_base64(self, frame: np.ndarray) -> str:
        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.stream_quality],
        )
        if not ok:
            return ""
        return base64.b64encode(encoded.tobytes()).decode("utf-8")

    def release(self) -> None:
        for capture in self._captures.values():
            if capture is not None:
                capture.release()
