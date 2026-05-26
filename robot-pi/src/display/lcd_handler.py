from __future__ import annotations

import logging
import threading
import time

from src.config import Settings


LOGGER = logging.getLogger(__name__)

try:
    from RPLCD.i2c import CharLCD  # type: ignore
except Exception:  # pragma: no cover
    CharLCD = None


_lcd = None
_enabled = False
_settings: Settings | None = None
_worker: threading.Thread | None = None
_stop_event = threading.Event()
_state_lock = threading.Lock()
_rotation_screens: list[tuple[str, str]] = []
_rotation_interval_seconds = 2.5
_rotation_started_at = 0.0
_override_message: tuple[str, str] | None = None
_override_expires_at: float | None = None
_last_rendered: tuple[str, str] | None = None


def setup(settings: Settings) -> None:
    global _lcd, _enabled, _settings, _worker
    _settings = settings
    _enabled = settings.lcd_enabled and CharLCD is not None
    if not _enabled:
        return
    try:
        _lcd = CharLCD("PCF8574", 0x27, cols=16, rows=2)
    except Exception as exc:
        LOGGER.warning("LCD no disponible: %s", exc)
        _enabled = False
        return

    _stop_event.clear()
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_run_display_loop, name="lcd-display-loop", daemon=True)
        _worker.start()


def _truncate(value: str) -> str:
    return value[:16].ljust(16)


def _render(lines: tuple[str, str]) -> None:
    global _last_rendered
    if not _enabled or _lcd is None or _last_rendered == lines:
        return
    _lcd.clear()
    _lcd.write_string(_truncate(lines[0]))
    _lcd.cursor_pos = (1, 0)
    _lcd.write_string(_truncate(lines[1]))
    _last_rendered = lines


def _select_current_message() -> tuple[str, str]:
    with _state_lock:
        now = time.monotonic()
        if _override_message is not None:
            if _override_expires_at is None or now < _override_expires_at:
                return _override_message
            _clear_override_locked()

        if not _rotation_screens:
            return ("", "")

        if len(_rotation_screens) == 1:
            return _rotation_screens[0]

        elapsed = max(now - _rotation_started_at, 0.0)
        index = int(elapsed / max(_rotation_interval_seconds, 0.5)) % len(_rotation_screens)
        return _rotation_screens[index]


def _run_display_loop() -> None:
    while not _stop_event.is_set():
        _render(_select_current_message())
        time.sleep(0.1)


def _clear_override_locked() -> None:
    global _override_message, _override_expires_at
    _override_message = None
    _override_expires_at = None


def set_rotation_screens(screens: list[tuple[str, str]], interval_seconds: float = 2.5) -> None:
    global _rotation_screens, _rotation_interval_seconds, _rotation_started_at
    normalized = [(str(line1), str(line2)) for line1, line2 in screens if line1 or line2]
    if not normalized:
        normalized = [("", "")]
    with _state_lock:
        if _rotation_screens == normalized and abs(_rotation_interval_seconds - interval_seconds) < 0.01:
            return
        _rotation_screens = normalized
        _rotation_interval_seconds = interval_seconds
        _rotation_started_at = time.monotonic()


def show_message(line1: str, line2: str = "") -> None:
    if not _enabled:
        return
    with _state_lock:
        global _override_message, _override_expires_at
        _override_message = (line1, line2)
        _override_expires_at = None


def show_temporary_message(line1: str, line2: str = "", duration_seconds: float = 3.0) -> None:
    if not _enabled:
        return
    with _state_lock:
        global _override_message, _override_expires_at
        _override_message = (line1, line2)
        _override_expires_at = time.monotonic() + max(duration_seconds, 0.5)


def clear_override() -> None:
    with _state_lock:
        _clear_override_locked()


def show_state(state: str) -> None:
    show_temporary_message("Estado", state, duration_seconds=2.5)


def show_result(ai_class: str, confidence: float) -> None:
    show_temporary_message(ai_class.upper(), f"{confidence:.0%}", duration_seconds=3.5)


def clear() -> None:
    global _last_rendered
    if _enabled and _lcd is not None:
        _lcd.clear()
        _last_rendered = None


def cleanup() -> None:
    _stop_event.set()
    clear()
