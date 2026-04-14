from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RobotHeartbeat:
    robot_id: str
    battery_level: int
    mode: str
    current_plant_qr: str | None
    is_connected: bool
    timestamp: datetime


@dataclass(slots=True)
class ObservationEvent:
    robot_id: str
    patrol_id: int | None
    plant_qr: str
    ai_light_result: str
    ai_light_confidence: float
    operator_notes: str | None
    image_base64: str | None
    mime_type: str
    timestamp: datetime
