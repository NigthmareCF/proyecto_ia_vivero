from __future__ import annotations

import threading
import time

from src.config import BUZZER, Settings


try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_enabled = False
_play_lock = threading.Lock()


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


def jingle() -> None:
    if not _enabled:
        return
    with _play_lock:
        for duration, pause in [(0.08, 0.04), (0.08, 0.04), (0.16, 0.06), (0.08, 0.03), (0.2, 0.08)]:
            beep(duration)
            time.sleep(pause)


def countdown_go() -> None:
    if not _enabled:
        return
    with _play_lock:
        for _ in range(3):
            beep(0.12)
            time.sleep(0.35)
        time.sleep(0.1)
        beep(0.28)
        time.sleep(0.06)
        beep(0.28)


def cleanup() -> None:
    if _enabled and GPIO is not None:
        GPIO.output(BUZZER, GPIO.LOW)
