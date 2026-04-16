from __future__ import annotations

import logging

import requests

from src.config import Settings


LOGGER = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_patrol_result(
        self,
        patrol_id: str,
        plant_qr: str,
        ai_result: str,
        ai_confidence: float,
        images_base64: list[str],
    ) -> bool:
        payload = {
            "robotId": self.settings.robot_id,
            "patrolId": patrol_id,
            "plantQr": plant_qr,
            "aiResult": ai_result,
            "aiConfidence": ai_confidence,
            "imagesBase64": images_base64,
        }
        return self._post("/api/robot/result", payload)

    def send_status(self, status: dict) -> bool:
        payload = {
            "robotId": self.settings.robot_id,
            **status,
        }
        return self._post("/api/robot/status", payload)

    def _post(self, path: str, payload: dict) -> bool:
        try:
            response = requests.post(
                f"{self.settings.bridge_url.rstrip('/')}{path}",
                json=payload,
                timeout=10,
            )
            return response.ok
        except requests.RequestException as exc:
            LOGGER.warning("Bridge POST failed for %s: %s", path, exc)
            return False
