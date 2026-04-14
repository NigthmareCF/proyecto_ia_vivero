from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    robot_id: str = os.getenv("ROBOT_ID", "robot-pi-01")
    bridge_base_url: str = os.getenv("ROBOT_BRIDGE_BASE_URL", "http://localhost:5000")
    patrol_id: int | None = int(os.getenv("ROBOT_PATROL_ID", "0")) or None
    use_simulation: bool = os.getenv("ROBOT_SIMULATION", "true").lower() == "true"
    model_path: str = os.getenv("TFLITE_MODEL_PATH", "./modelos/modelo_vivero.tflite")
    labels_path: str = os.getenv("TFLITE_LABELS_PATH", "./labels.txt")
    heartbeat_interval_seconds: float = float(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "5"))
