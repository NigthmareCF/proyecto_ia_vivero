from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import requests

from src.communication.backend_endpoint_manager import BackendEndpointManager
from src.config import Settings


LOGGER = logging.getLogger(__name__)


class CommandListener:
    def __init__(
        self,
        settings: Settings,
        endpoint_manager: BackendEndpointManager,
        callback: Callable[[str, dict, int], None],
        shutdown_event: threading.Event,
    ) -> None:
        self.settings = settings
        self.endpoint_manager = endpoint_manager
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
        for _ in range(max(self.endpoint_manager.candidate_count, 1)):
            endpoint = self.endpoint_manager.current()
            try:
                response = requests.get(
                    f"{endpoint.base_url.rstrip('/')}{self.settings.command_next_path}",
                    params={"robotId": self.settings.robot_id},
                    timeout=10,
                )
                if response.status_code == 204:
                    self.endpoint_manager.mark_success(endpoint.base_url)
                    return None
                if response.status_code >= 500:
                    LOGGER.warning(
                        "Command polling failed via %s: status=%s body=%s",
                        endpoint.base_url,
                        response.status_code,
                        response.text[:250],
                    )
                    self.endpoint_manager.mark_failure(endpoint.base_url)
                    continue
                response.raise_for_status()
                payload = response.json()
                self.endpoint_manager.mark_success(endpoint.base_url)
                data = payload.get("data") if isinstance(payload, dict) else None
                return data if isinstance(data, dict) else None
            except requests.RequestException as exc:
                LOGGER.warning("Command polling failed via %s: %s", endpoint.base_url, exc)
                self.endpoint_manager.mark_failure(endpoint.base_url)
        return None

    def ack_command(self, command_id: int) -> None:
        path = self.settings.command_ack_path_template.format(commandId=command_id)
        for _ in range(max(self.endpoint_manager.candidate_count, 1)):
            endpoint = self.endpoint_manager.current()
            try:
                response = requests.post(
                    f"{endpoint.base_url.rstrip('/')}{path}",
                    json={"robotId": self.settings.robot_id},
                    timeout=10,
                )
                if response.ok:
                    self.endpoint_manager.mark_success(endpoint.base_url)
                    return
                if response.status_code >= 500:
                    LOGGER.warning(
                        "Ack command failed via %s: status=%s body=%s",
                        endpoint.base_url,
                        response.status_code,
                        response.text[:250],
                    )
                    self.endpoint_manager.mark_failure(endpoint.base_url)
                    continue
                response.raise_for_status()
                return
            except requests.RequestException as exc:
                LOGGER.warning("Ack command failed via %s: %s", endpoint.base_url, exc)
                self.endpoint_manager.mark_failure(endpoint.base_url)
        raise requests.RequestException(f"Ack command {command_id} failed on all backends")
