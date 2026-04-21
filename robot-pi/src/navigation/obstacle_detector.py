from __future__ import annotations

import logging
import time

from src.config import IR_LEFT, IR_RIGHT, Settings, ULTRASONIC_ECHO, ULTRASONIC_TRIG


LOGGER = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_settings: Settings | None = None


def setup(settings: Settings) -> None:
    global _settings
    _settings = settings
    if GPIO is None:
        LOGGER.warning("RPi.GPIO no disponible; obstacle_detector en simulacion")
        return
    GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
    GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)
    GPIO.setup(IR_LEFT, GPIO.IN)
    GPIO.setup(IR_RIGHT, GPIO.IN)
    GPIO.output(ULTRASONIC_TRIG, False)


def get_distance_cm() -> float:
    if GPIO is None:
        return 100.0
    timeout = 0.1
    GPIO.output(ULTRASONIC_TRIG, True)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIG, False)

    start = time.monotonic()
    pulse_start = start
    while GPIO.input(ULTRASONIC_ECHO) == 0:
        pulse_start = time.monotonic()
        if pulse_start - start > timeout:
            return 999.0

    pulse_end = pulse_start
    while GPIO.input(ULTRASONIC_ECHO) == 1:
        pulse_end = time.monotonic()
        if pulse_end - pulse_start > timeout:
            return 999.0

    return round((pulse_end - pulse_start) * 17150, 2)


def is_obstacle_detected() -> bool:
    threshold = _settings.obstacle_distance_cm if _settings else 20
    distance = get_distance_cm()
    return distance < threshold
