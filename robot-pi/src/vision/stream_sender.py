from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import base64
import cv2
import numpy as np
from websocket import WebSocketConnectionClosedException, create_connection

from src.communication.backend_endpoint_manager import BackendEndpointManager
from src.config import Settings


LOGGER = logging.getLogger(__name__)


class StreamSender:
    def __init__(
        self,
        settings: Settings,
        endpoint_manager: BackendEndpointManager,
        frame_provider: Callable[[], object],
        camera_name_provider: Callable[[], str],
    ) -> None:
        self.settings = settings
        self.endpoint_manager = endpoint_manager
        self.frame_provider = frame_provider
        self.camera_name_provider = camera_name_provider
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._stream_max_width = settings.camera_width
        self._stream_max_height = settings.camera_height

    def apply_stream_profile(self, profile: str, width: int, height: int) -> None:
        self._stream_max_width = max(1, int(width))
        self._stream_max_height = max(1, int(height))

    def start_stream(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="stream-sender", daemon=True)
        self._thread.start()

    def stop_stream(self) -> None:
        self._stop_event.set()

    def _resize_frame_for_stream(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        max_width = self._stream_max_width
        max_height = self._stream_max_height
        scale = min(max_width / max(width, 1), max_height / max(height, 1), 1.0)
        if scale >= 1.0:
            return frame
        target_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
        return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            ws = None
            endpoint = self.endpoint_manager.current()
            try:
                kwargs = {"timeout": 5}
                if self.settings.backend_ws_origin:
                    kwargs["origin"] = self.settings.backend_ws_origin
                stream_url = self._resolve_stream_url()
                ws = create_connection(stream_url, **kwargs)
                self.endpoint_manager.mark_success(endpoint.base_url)
                send_fps = max(1, min(self.settings.stream_fps, self.settings.stream_send_fps))
                send_interval = max(1 / send_fps, 0.1)
                while not self._stop_event.is_set():
                    frame = self.frame_provider()
                    self.send_frame(frame, ws)
                    time.sleep(send_interval)
            except Exception as exc:
                LOGGER.warning("Stream sender disconnected: %s", exc)
                self.endpoint_manager.mark_failure(endpoint.base_url)
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
            stream_frame = self._resize_frame_for_stream(frame)
            ok, encoded = cv2.imencode(
                ".jpg",
                stream_frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.stream_quality],
            )
            if not ok:
                return
            payload = {
                "type": "robot.stream",
                "robotId": self.settings.robot_id,
                "camera": self.camera_name_provider().lower(),
                "sentAt": int(time.time() * 1000),
                "frame": base64.b64encode(encoded.tobytes()).decode("utf-8"),
            }
            websocket_obj.send(json.dumps(payload))
        except WebSocketConnectionClosedException:
            LOGGER.warning("WS de stream cerrado")

    def _resolve_stream_url(self) -> str:
        split_url = urlsplit(self.endpoint_manager.current().ws_url)
        query = dict(parse_qsl(split_url.query, keep_blank_values=True))
        query.setdefault("role", "robot")
        query.setdefault("robotId", self.settings.robot_id)
        return urlunsplit((
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(query),
            split_url.fragment,
        ))
