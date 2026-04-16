from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable

from websocket import WebSocketApp

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class CommandListener:
    def __init__(
        self,
        settings: Settings,
        callback: Callable[[str, dict], None],
        shutdown_event: threading.Event,
    ) -> None:
        self.settings = settings
        self.callback = callback
        self.shutdown_event = shutdown_event
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="command-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.shutdown_event.set()

    def _run(self) -> None:
        backoff = 2
        while not self.shutdown_event.is_set():
            ws = WebSocketApp(
                self.settings.backend_ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
            )
            try:
                ws.run_forever()
            except Exception as exc:
                LOGGER.warning("Command listener error: %s", exc)
            if self.shutdown_event.is_set():
                return
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)

    def _on_message(self, _ws: WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            LOGGER.warning("Ignoring non-JSON command: %s", message)
            return
        command = str(payload.get("command", "")).upper()
        data = payload.get("data") or {}
        self.callback(command, data)

    def _on_error(self, _ws: WebSocketApp, error: object) -> None:
        LOGGER.warning("WS command listener error: %s", error)
