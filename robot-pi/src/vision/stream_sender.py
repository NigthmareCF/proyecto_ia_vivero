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

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class StreamSender:
    def __init__(
        self,
        settings: Settings,
        frame_provider: Callable[[], object],
        camera_name_provider: Callable[[], str],
    ) -> None:
        self.settings = settings
        self.frame_provider = frame_provider
        self.camera_name_provider = camera_name_provider
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
                kwargs = {"timeout": 5}
                if self.settings.backend_ws_origin:
                    kwargs["origin"] = self.settings.backend_ws_origin
                ws = create_connection(self._resolve_stream_url(), **kwargs)
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
                "camera": self.camera_name_provider().lower(),
                "sentAt": int(time.time() * 1000),
                "frame": base64.b64encode(encoded.tobytes()).decode("utf-8"),
            }
            websocket_obj.send(json.dumps(payload))
        except WebSocketConnectionClosedException:
            LOGGER.warning("WS de stream cerrado")

    def _resolve_stream_url(self) -> str:
        split_url = urlsplit(self.settings.backend_ws_url)
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
