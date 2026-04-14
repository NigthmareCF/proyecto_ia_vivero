from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    bridge_host: str = os.getenv("ROBOT_BRIDGE_HOST", "0.0.0.0")
    bridge_port: int = int(os.getenv("ROBOT_BRIDGE_PORT", "5000"))
    backend_base_url: str = os.getenv("BACKEND_BASE_URL", "http://backend:8080/api")
    shared_secret: str = os.getenv("ROBOT_SHARED_SECRET", "")
    retry_queue_limit: int = int(os.getenv("BRIDGE_RETRY_QUEUE_LIMIT", "200"))
    request_timeout_seconds: float = float(os.getenv("BRIDGE_REQUEST_TIMEOUT_SECONDS", "8"))
