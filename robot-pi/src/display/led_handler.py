from __future__ import annotations

import threading
import time
from collections.abc import Callable

from src.config import LED_BLUE, LED_GREEN, LED_RED, LED_YELLOW, Settings


try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_enabled = False
_blue_pwm = None
_blue_mode = "off"
_blue_worker: threading.Thread | None = None
_blue_lock = threading.Lock()
_blue_stop_event = threading.Event()
_blue_manual_event = threading.Event()
_settings: Settings | None = None


def setup(settings: Settings) -> None:
    global _enabled, _blue_pwm, _blue_worker, _settings
    _settings = settings
    _enabled = settings.led_enabled and GPIO is not None
    if not _enabled:
        return
    for pin in [LED_GREEN, LED_YELLOW, LED_RED, LED_BLUE]:
        GPIO.setup(pin, GPIO.OUT)
    _blue_pwm = GPIO.PWM(LED_BLUE, 100)
    _blue_pwm.start(0)
    _blue_stop_event.clear()
    if _blue_worker is None or not _blue_worker.is_alive():
        _blue_worker = threading.Thread(target=_run_blue_effect, name="blue-led-effect", daemon=True)
        _blue_worker.start()
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


def _set_blue_duty(duty_cycle: float) -> None:
    if not _enabled or GPIO is None or _blue_pwm is None:
        return
    _blue_pwm.ChangeDutyCycle(max(0.0, min(duty_cycle, 100.0)))


def _stop_blue_pwm_for_manual_control() -> bool:
    if not _enabled or GPIO is None or _blue_pwm is None:
        return False
    _set_blue_duty(0.0)
    _blue_pwm.stop()
    GPIO.output(LED_BLUE, GPIO.LOW)
    return True


def _restart_blue_pwm_after_manual_control(was_running: bool) -> None:
    global _blue_pwm
    if not was_running or not _enabled or GPIO is None:
        return
    _blue_pwm = GPIO.PWM(LED_BLUE, 100)
    _blue_pwm.start(0)


def pulse_blue_with(
    action: Callable[[float], None],
    repeats: int = 3,
    on_duration: float = 0.2,
    off_duration: float = 0.15,
) -> None:
    _blue_manual_event.set()
    pwm_was_running = False
    try:
        pwm_was_running = _stop_blue_pwm_for_manual_control()
        time.sleep(0.08)
        for _ in range(max(repeats, 0)):
            if _enabled and GPIO is not None:
                GPIO.output(LED_BLUE, GPIO.HIGH)
            started_at = time.monotonic()
            action(on_duration)
            remaining = on_duration - (time.monotonic() - started_at)
            if remaining > 0:
                time.sleep(remaining)
            if _enabled and GPIO is not None:
                GPIO.output(LED_BLUE, GPIO.LOW)
            time.sleep(max(off_duration, 0.0))
    finally:
        if _enabled and GPIO is not None:
            GPIO.output(LED_BLUE, GPIO.LOW)
        _restart_blue_pwm_after_manual_control(pwm_was_running)
        _blue_manual_event.clear()


def set_heartbeat_off() -> None:
    global _blue_mode
    with _blue_lock:
        _blue_mode = "off"


def set_heartbeat_blink() -> None:
    global _blue_mode
    with _blue_lock:
        _blue_mode = "blink"


def set_heartbeat_fast_blink() -> None:
    global _blue_mode
    with _blue_lock:
        _blue_mode = "fast_blink"


def set_heartbeat_breathe() -> None:
    global _blue_mode
    with _blue_lock:
        _blue_mode = "breathe"


def _current_blue_mode() -> str:
    with _blue_lock:
        return _blue_mode


def _run_blue_effect() -> None:
    brightness = 0.0
    direction = 1.0
    while not _blue_stop_event.is_set():
        mode = _current_blue_mode()
        if _settings is None:
            time.sleep(0.1)
            continue
        if _blue_manual_event.is_set():
            time.sleep(0.02)
            continue
        if mode == "off":
            _set_blue_duty(0.0)
            time.sleep(0.1)
            continue
        if mode == "blink":
            _set_blue_duty(100.0)
            time.sleep(_settings.heartbeat_led_blink_interval_seconds)
            _set_blue_duty(0.0)
            time.sleep(_settings.heartbeat_led_blink_interval_seconds)
            continue
        if mode == "fast_blink":
            _set_blue_duty(100.0)
            time.sleep(_settings.heartbeat_led_fast_blink_interval_seconds)
            _set_blue_duty(0.0)
            time.sleep(_settings.heartbeat_led_fast_blink_interval_seconds)
            continue

        # Respiracion: subida/bajada gradual de brillo.
        step = max(_settings.heartbeat_led_breathe_step_duty, 1.0)
        brightness += direction * step
        if brightness >= 100.0:
            brightness = 100.0
            direction = -1.0
        elif brightness <= 0.0:
            brightness = 0.0
            direction = 1.0
        _set_blue_duty(brightness)
        time.sleep(max(_settings.heartbeat_led_breathe_step_seconds, 0.01))


def cleanup() -> None:
    _blue_stop_event.set()
    set_heartbeat_off()
    _set_blue_duty(0.0)
    if _blue_pwm is not None:
        _blue_pwm.stop()
    set_idle()
