from __future__ import annotations

import time

from src.config import BUZZER, Settings


try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_enabled = False


def setup(settings: Settings) -> None:
    global _enabled
    _enabled = settings.buzzer_enabled and GPIO is not None
    if not _enabled:
        return
    GPIO.setup(BUZZER, GPIO.OUT)
    GPIO.output(BUZZER, GPIO.LOW)


def beep(duration: float = 0.2) -> None:
    if not _enabled or GPIO is None:
        return
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER, GPIO.LOW)


def alert() -> None:
    for _ in range(3):
        beep(0.2)
        time.sleep(0.15)


def cleanup() -> None:
    if _enabled and GPIO is not None:
        GPIO.output(BUZZER, GPIO.LOW)
