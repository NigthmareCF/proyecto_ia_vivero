from __future__ import annotations

import base64
import logging
import re
import subprocess
import threading
import time
from typing import Any

import cv2
import numpy as np

from src.config import Settings


LOGGER = logging.getLogger(__name__)
AUTO_FPS_FALLBACK = 30


class CameraHandler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._captures: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._auto_stream_fps = settings.stream_fps <= 0
        self._effective_stream_fps = max(settings.stream_fps, 0)
        self._base_camera_width = settings.camera_width
        self._base_camera_height = settings.camera_height
        self._profile_name = "BALANCED"
        self._stream_quality = settings.stream_quality
        self._stream_max_width = min(settings.camera_width, 960)
        self._stream_max_height = min(settings.camera_height, 540)

    def _profile_dimensions(self, profile: str) -> tuple[int, int, int, int, int]:
        normalized = str(profile or "BALANCED").strip().upper()
        base_w = max(self._base_camera_width, 1)
        base_h = max(self._base_camera_height, 1)
        if normalized == "SPEED" or normalized == "VELOCIDAD":
            return (
                max(320, int(round(base_w * 0.5))),
                max(180, int(round(base_h * 0.5))),
                30,
                30,
                55,
            )
        if normalized == "HD":
            return (
                base_w,
                base_h,
                max(5, min(10, self._resolve_requested_fps(0))),
                max(5, min(10, self._resolve_requested_fps(0))),
                75,
            )
        return (
            max(480, int(round(base_w * 0.75))),
            max(270, int(round(base_h * 0.75))),
            15,
            15,
            65,
        )

    def apply_stream_profile(self, profile: str) -> None:
        width, height, stream_fps, send_fps, quality = self._profile_dimensions(profile)
        self._profile_name = str(profile or "BALANCED").strip().upper()
        self.settings.camera_width = width
        self.settings.camera_height = height
        self.settings.stream_fps = stream_fps
        self.settings.stream_send_fps = send_fps
        self.settings.stream_quality = quality
        self._stream_quality = quality
        self._stream_max_width = width
        self._stream_max_height = height
        self.setup()

    def current_stream_profile(self) -> str:
        return self._profile_name

    def base_dimensions(self) -> tuple[int, int]:
        return self._base_camera_width, self._base_camera_height

    def _max_supported_fps(self, index: int) -> int | None:
        device_path = f"/dev/video{index}"
        try:
            result = subprocess.run(
                ["v4l2-ctl", "--list-formats-ext", "-d", device_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None

        fps_values: list[float] = []
        in_mjpg_format = False
        in_target_size = False
        size_pattern = re.compile(r"Size:\s+Discrete\s+(\d+)x(\d+)")
        fps_pattern = re.compile(r"\(([\d.]+)\s+fps\)")
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if line.startswith("["):
                in_mjpg_format = "'MJPG'" in line or '"MJPG"' in line
                in_target_size = False
                continue
            size_match = size_pattern.search(line)
            if size_match:
                in_target_size = (
                    in_mjpg_format
                    and int(size_match.group(1)) == self.settings.camera_width
                    and int(size_match.group(2)) == self.settings.camera_height
                )
                continue
            if not in_target_size:
                continue
            fps_match = fps_pattern.search(line)
            if fps_match:
                fps_values.append(float(fps_match.group(1)))

        if not fps_values:
            return None
        return max(1, int(round(max(fps_values))))

    def _resolve_requested_fps(self, index: int) -> int:
        if not self._auto_stream_fps and self.settings.stream_fps > 0:
            return self.settings.stream_fps
        max_supported_fps = self._max_supported_fps(index)
        if max_supported_fps is None:
            LOGGER.warning(
                "No se pudo detectar FPS maximo para /dev/video%s a %sx%s; se usara %s FPS",
                index,
                self.settings.camera_width,
                self.settings.camera_height,
                AUTO_FPS_FALLBACK,
            )
            return AUTO_FPS_FALLBACK
        LOGGER.info(
            "Camara /dev/video%s configurada al maximo detectado: %s FPS en %sx%s",
            index,
            max_supported_fps,
            self.settings.camera_width,
            self.settings.camera_height,
        )
        return max_supported_fps

    def _open_camera(self, index: int) -> Any:
        if self.settings.camera_type == "csi":
            capture = cv2.VideoCapture(index, cv2.CAP_V4L2)
        else:
            capture = cv2.VideoCapture(index)
        if not capture or not capture.isOpened():
            LOGGER.warning("No se pudo abrir la camara con indice %s; se usara frame simulado", index)
            return None
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        requested_fps = self._resolve_requested_fps(index)
        capture.set(cv2.CAP_PROP_FPS, requested_fps)
        self._effective_stream_fps = max(self._effective_stream_fps, requested_fps)
        self.settings.stream_fps = max(self.settings.stream_fps, self._effective_stream_fps)
        return capture

    def setup(self) -> None:
        with self._lock:
            for capture in self._captures.values():
                if capture is not None:
                    try:
                        capture.release()
                    except Exception:
                        pass
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
            [int(cv2.IMWRITE_JPEG_QUALITY), self._stream_quality],
        )
        if not ok:
            return ""
        return base64.b64encode(encoded.tobytes()).decode("utf-8")

    def release(self) -> None:
        for capture in self._captures.values():
            if capture is not None:
                capture.release()
