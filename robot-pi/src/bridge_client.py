from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from urllib import request

from .models import ObservationEvent, RobotHeartbeat


class BridgeClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def send_heartbeat(self, heartbeat: RobotHeartbeat) -> None:
        self._post("/api/v1/heartbeat", asdict(heartbeat))

    def send_observation(self, observation: ObservationEvent) -> None:
        self._post("/api/v1/observation", asdict(observation))

    def _post(self, path: str, payload: dict) -> None:
        body = json.dumps(payload, default=self._json_default).encode("utf-8")
        req = request.Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=8) as response:
            if response.status >= 400:
                raise RuntimeError(f"Bridge returned status {response.status}")

    def _json_default(self, value: object) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"Unsupported type: {type(value)!r}")
