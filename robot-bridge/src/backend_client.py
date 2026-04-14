from __future__ import annotations

from collections import deque

import httpx

from .config import Settings
from .models import HeartbeatPayload, ObservationPayload, RelayEvent


class BackendRelay:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.retry_queue: deque[RelayEvent] = deque(maxlen=settings.retry_queue_limit)

    async def relay_heartbeat(self, payload: HeartbeatPayload) -> None:
        await self._post("/robot/bridge/heartbeat", payload.model_dump(mode="json"))

    async def relay_observation(self, payload: ObservationPayload) -> None:
        await self._post("/patrols/bridge/observation", payload.model_dump(mode="json"))

    async def _post(self, path: str, payload: dict) -> None:
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(base_url=self.settings.backend_base_url, timeout=timeout) as client:
            try:
                response = await client.post(path, json=payload)
                response.raise_for_status()
            except Exception:
                self.retry_queue.append(RelayEvent(event_type=path, payload=payload))
                raise
