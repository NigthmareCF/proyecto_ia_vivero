from __future__ import annotations

import logging

import requests

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_heartbeat(self, heartbeat: dict) -> bool:
        payload = {"robotId": self.settings.robot_id, **heartbeat}
        return self._post(self.settings.heartbeat_path, payload)

    def send_observation(self, observation: dict) -> bool:
        payload = {"robotId": self.settings.robot_id, **observation}
        return self._post(self.settings.observation_path, payload)

    def _post(self, path: str, payload: dict) -> bool:
        try:
            response = requests.post(
                f"{self.settings.bridge_url.rstrip('/')}{path}",
                json=payload,
                timeout=10,
            )
            if not response.ok:
                LOGGER.warning(
                    "Bridge POST failed for %s: status=%s body=%s",
                    path,
                    response.status_code,
                    response.text[:250],
                )
            return response.ok
        except requests.RequestException as exc:
            LOGGER.warning("Bridge POST failed for %s: %s", path, exc)
            return False
