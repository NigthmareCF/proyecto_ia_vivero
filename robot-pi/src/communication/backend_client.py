from __future__ import annotations

import logging

import requests

from src.communication.backend_endpoint_manager import BackendEndpointManager
from src.config import Settings


LOGGER = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, settings: Settings, endpoint_manager: BackendEndpointManager) -> None:
        self.settings = settings
        self.endpoint_manager = endpoint_manager

    def send_heartbeat(self, heartbeat: dict) -> bool:
        payload = {"robotId": self.settings.robot_id, **heartbeat}
        return self._post(self.settings.heartbeat_path, payload)

    def send_observation(self, observation: dict) -> bool:
        payload = {"robotId": self.settings.robot_id, **observation}
        return self._post(self.settings.observation_path, payload)

    def _post(self, path: str, payload: dict) -> bool:
        for _ in range(max(self.endpoint_manager.candidate_count, 1)):
            endpoint = self.endpoint_manager.current()
            try:
                response = requests.post(
                    f"{endpoint.base_url.rstrip('/')}{path}",
                    json=payload,
                    timeout=10,
                )
                if response.ok:
                    self.endpoint_manager.mark_success(endpoint.base_url)
                    return True
                if response.status_code >= 500:
                    LOGGER.warning(
                        "Backend POST failed for %s via %s: status=%s body=%s",
                        path,
                        endpoint.base_url,
                        response.status_code,
                        response.text[:250],
                    )
                    self.endpoint_manager.mark_failure(endpoint.base_url)
                    continue
                LOGGER.warning(
                    "Backend POST rejected for %s via %s: status=%s body=%s",
                    path,
                    endpoint.base_url,
                    response.status_code,
                    response.text[:250],
                )
                return False
            except requests.RequestException as exc:
                LOGGER.warning("Backend POST failed for %s via %s: %s", path, endpoint.base_url, exc)
                self.endpoint_manager.mark_failure(endpoint.base_url)
        return False
