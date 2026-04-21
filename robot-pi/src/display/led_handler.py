from __future__ import annotations

from src.config import LED_GREEN, LED_RED, LED_YELLOW, Settings


try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_enabled = False


def setup(settings: Settings) -> None:
    global _enabled
    _enabled = settings.led_enabled and GPIO is not None
    if not _enabled:
        return
    for pin in [LED_GREEN, LED_YELLOW, LED_RED]:
        GPIO.setup(pin, GPIO.OUT)
    set_idle()


def _set(green: bool, yellow: bool, red: bool) -> None:
    if not _enabled or GPIO is None:
        return
    GPIO.output(LED_GREEN, GPIO.HIGH if green else GPIO.LOW)
    GPIO.output(LED_YELLOW, GPIO.HIGH if yellow else GPIO.LOW)
    GPIO.output(LED_RED, GPIO.HIGH if red else GPIO.LOW)


def set_healthy() -> None:
    _set(True, False, False)


def set_attention() -> None:
    _set(False, True, False)


def set_danger() -> None:
    _set(False, False, True)


def set_idle() -> None:
    _set(False, False, False)


def cleanup() -> None:
    set_idle()
