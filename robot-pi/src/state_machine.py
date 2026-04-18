from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock


class RobotState(str, Enum):
    IDLE = "IDLE"
    FOLLOW_LINE = "FOLLOW_LINE"
    QR_DETECTED = "QR_DETECTED"
    CAPTURING = "CAPTURING"
    CLASSIFYING = "CLASSIFYING"
    SENDING = "SENDING"
    MANUAL = "MANUAL"


@dataclass(slots=True)
class StateSnapshot:
    state: RobotState
    patrol_id: str | None
    current_plant_qr: str | None
    manual_direction: str
    manual_speed: int


class RobotStateMachine:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state = RobotState.IDLE
        self._patrol_id: str | None = None
        self._current_plant_qr: str | None = None
        self._manual_direction = "stop"
        self._manual_speed = 0

    def snapshot(self) -> StateSnapshot:
        with self._lock:
            return StateSnapshot(
                state=self._state,
                patrol_id=self._patrol_id,
                current_plant_qr=self._current_plant_qr,
                manual_direction=self._manual_direction,
                manual_speed=self._manual_speed,
            )

    def start_patrol(self, patrol_id: str) -> None:
        with self._lock:
            self._patrol_id = patrol_id
            self._state = RobotState.FOLLOW_LINE

    def stop(self) -> None:
        with self._lock:
            self._state = RobotState.IDLE
            self._patrol_id = None
            self._current_plant_qr = None
            self._manual_direction = "stop"
            self._manual_speed = 0

    def enable_manual(self) -> None:
        with self._lock:
            self._state = RobotState.MANUAL

    def enable_auto(self) -> None:
        with self._lock:
            self._state = RobotState.FOLLOW_LINE
            self._manual_direction = "stop"

    def update_manual_move(self, direction: str, speed: int) -> None:
        with self._lock:
            self._manual_direction = direction
            self._manual_speed = max(0, min(speed, 100))

    def qr_detected(self, plant_qr: str) -> None:
        with self._lock:
            self._current_plant_qr = plant_qr
            self._state = RobotState.QR_DETECTED

    def begin_capture(self) -> None:
        with self._lock:
            self._state = RobotState.CAPTURING

    def begin_classification(self) -> None:
        with self._lock:
            self._state = RobotState.CLASSIFYING

    def begin_sending(self) -> None:
        with self._lock:
            self._state = RobotState.SENDING

    def resume_follow_line(self) -> None:
        with self._lock:
            self._state = RobotState.FOLLOW_LINE
            self._current_plant_qr = None
