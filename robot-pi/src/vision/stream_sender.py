from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable

import base64
import cv2
import numpy as np
from websocket import WebSocketConnectionClosedException, create_connection

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class StreamSender:
    def __init__(self, settings: Settings, frame_provider: Callable[[], object]) -> None:
        self.settings = settings
        self.frame_provider = frame_provider
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start_stream(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="stream-sender", daemon=True)
        self._thread.start()

    def stop_stream(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            ws = None
            try:
                ws = create_connection(self.settings.backend_ws_url, timeout=5)
                while not self._stop_event.is_set():
                    frame = self.frame_provider()
                    self.send_frame(frame, ws)
                    time.sleep(max(1 / max(self.settings.stream_fps, 1), 0.05))
            except Exception as exc:
                LOGGER.warning("Stream sender disconnected: %s", exc)
                time.sleep(2)
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass

    def send_frame(self, frame: object, websocket_obj: object) -> None:
        if not isinstance(frame, np.ndarray) or frame.size == 0:
            return
        try:
            ok, encoded = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.stream_quality],
            )
            if not ok:
                return
            payload = {
                "type": "robot.stream",
                "robotId": self.settings.robot_id,
                "frame": base64.b64encode(encoded.tobytes()).decode("utf-8"),
            }
            websocket_obj.send(json.dumps(payload))
        except WebSocketConnectionClosedException:
            LOGGER.warning("WS de stream cerrado")
