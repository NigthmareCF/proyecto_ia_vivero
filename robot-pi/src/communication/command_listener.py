from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import requests

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class CommandListener:
    def __init__(
        self,
        settings: Settings,
        callback: Callable[[str, dict, int], None],
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
        while not self.shutdown_event.is_set():
            try:
                command = self._fetch_next_command()
                if command is not None:
                    self.callback(command["command"], command.get("data") or {}, int(command["id"]))
                else:
                    self.shutdown_event.wait(self.settings.command_poll_interval_seconds)
            except Exception as exc:
                LOGGER.warning("Command polling failed: %s", exc)
                self.shutdown_event.wait(self.settings.command_poll_interval_seconds)

    def _fetch_next_command(self) -> dict | None:
        response = requests.get(
            f"{self.settings.backend_base_url.rstrip('/')}{self.settings.command_next_path}",
            params={"robotId": self.settings.robot_id},
            timeout=10,
        )
        if response.status_code == 204:
            return None
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        return data if isinstance(data, dict) else None

    def ack_command(self, command_id: int) -> None:
        path = self.settings.command_ack_path_template.format(commandId=command_id)
        response = requests.post(
            f"{self.settings.backend_base_url.rstrip('/')}{path}",
            json={"robotId": self.settings.robot_id},
            timeout=10,
        )
        response.raise_for_status()
