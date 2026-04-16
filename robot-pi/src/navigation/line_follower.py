from __future__ import annotations

import logging
import time

from src.config import LINE_SENSOR_CENTER, LINE_SENSOR_LEFT, LINE_SENSOR_RIGHT, Settings
from src.navigation import motor_controller


LOGGER = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_settings: Settings | None = None
_last_line_seen = time.monotonic()


def setup(settings: Settings) -> None:
    global _settings
    _settings = settings
    if GPIO is None:
        LOGGER.warning("RPi.GPIO no disponible; line_follower en simulacion")
        return
    for pin in [LINE_SENSOR_LEFT, LINE_SENSOR_CENTER, LINE_SENSOR_RIGHT]:
        GPIO.setup(pin, GPIO.IN)


def _normalize(value: int) -> int:
    if _settings is None:
        return value
    return 0 if (_settings.line_active_low and value == 1) else 1 if _settings.line_active_low else value


def read_sensors() -> tuple[int, int, int]:
    global _last_line_seen
    if GPIO is None:
        return (0, 1, 0)
    left = _normalize(GPIO.input(LINE_SENSOR_LEFT))
    center = _normalize(GPIO.input(LINE_SENSOR_CENTER))
    right = _normalize(GPIO.input(LINE_SENSOR_RIGHT))
    if (left, center, right) not in {(1, 1, 1), (0, 0, 0)}:
        _last_line_seen = time.monotonic()
    return left, center, right


def follow_line(speed: int) -> str:
    left, center, right = read_sensors()
    pattern = (left, center, right)
    if pattern == (0, 1, 0):
        motor_controller.move_forward(speed)
        return "forward"
    if pattern == (1, 1, 0):
        motor_controller.turn_left(speed)
        return "left_soft"
    if pattern == (0, 1, 1):
        motor_controller.turn_right(speed)
        return "right_soft"
    if pattern == (1, 0, 0):
        motor_controller.turn_left(speed)
        return "left_hard"
    if pattern == (0, 0, 1):
        motor_controller.turn_right(speed)
        return "right_hard"
    motor_controller.stop()
    return "line_lost"


def is_line_lost() -> bool:
    if _settings is None:
        return False
    return (time.monotonic() - _last_line_seen) > _settings.line_lost_timeout
