from __future__ import annotations

import logging

from src.config import Settings


LOGGER = logging.getLogger(__name__)

try:
    from RPLCD.i2c import CharLCD  # type: ignore
except Exception:  # pragma: no cover
    CharLCD = None


_lcd = None
_enabled = False


def setup(settings: Settings) -> None:
    global _lcd, _enabled
    _enabled = settings.lcd_enabled and CharLCD is not None
    if not _enabled:
        return
    try:
        _lcd = CharLCD("PCF8574", 0x27, cols=16, rows=2)
    except Exception as exc:
        LOGGER.warning("LCD no disponible: %s", exc)
        _enabled = False


def _truncate(value: str) -> str:
    return value[:16].ljust(16)


def show_message(line1: str, line2: str = "") -> None:
    if not _enabled or _lcd is None:
        return
    _lcd.clear()
    _lcd.write_string(_truncate(line1))
    _lcd.cursor_pos = (1, 0)
    _lcd.write_string(_truncate(line2))


def show_state(state: str) -> None:
    show_message("Estado", state)


def show_result(ai_class: str, confidence: float) -> None:
    show_message(ai_class.upper(), f"{confidence:.0%}")


def clear() -> None:
    if _enabled and _lcd is not None:
        _lcd.clear()


def cleanup() -> None:
    clear()
