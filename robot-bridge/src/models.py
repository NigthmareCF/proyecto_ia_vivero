from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HeartbeatPayload(BaseModel):
    robot_id: str = Field(..., min_length=2)
    battery_level: int = Field(..., ge=0, le=100)
    mode: str = Field(..., min_length=2)
    current_plant_qr: str | None = None
    is_connected: bool = True
    timestamp: datetime = Field(default_factory=utc_now)


class ObservationPayload(BaseModel):
    robot_id: str = Field(..., min_length=2)
    patrol_id: int | None = None
    plant_qr: str = Field(..., min_length=2)
    ai_light_result: str = Field(..., min_length=2)
    ai_light_confidence: float = Field(..., ge=0.0, le=1.0)
    operator_notes: str | None = None
    image_base64: str | None = None
    mime_type: str = "image/jpeg"
    timestamp: datetime = Field(default_factory=utc_now)


class RobotCommandPayload(BaseModel):
    command: str = Field(..., min_length=2)
    value: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class RelayEvent(BaseModel):
    event_type: str
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)
