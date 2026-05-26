from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import RPi.GPIO as GPIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from RPLCD.i2c import CharLCD
except Exception:  # pragma: no cover
    CharLCD = None


TRIG = 5
ECHO = 6
IR_LEFT = 8
IR_RIGHT = 9
BUZZER = 21
LED_BLUE = 20
THRESHOLD_CM = 20.0
IR_ACTIVE_HIGH = False
_stop_blue = threading.Event()
_manual_blue = threading.Event()


def setup_lcd():
    if CharLCD is None:
        print("RPLCD no disponible", flush=True)
        return None
    for address in (0x27, 0x3F):
        try:
            lcd = CharLCD("PCF8574", address, cols=16, rows=2)
            print(f"LCD lista en I2C {hex(address)}", flush=True)
            return lcd
        except Exception as exc:
            print(f"LCD no disponible en {hex(address)}: {exc}", flush=True)
    return None


def lcd_write(lcd, last_lines, line1: str, line2: str):
    lines = (line1[:16].ljust(16), line2[:16].ljust(16))
    if lcd is None or lines == last_lines:
        return last_lines
    lcd.clear()
    lcd.write_string(lines[0])
    lcd.cursor_pos = (1, 0)
    lcd.write_string(lines[1])
    return lines


def read_cm() -> float:
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    start = time.monotonic()
    pulse_start = start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.monotonic()
        if pulse_start - start > 0.1:
            return 999.0

    pulse_end = pulse_start
    while GPIO.input(ECHO) == 1:
        pulse_end = time.monotonic()
        if pulse_end - pulse_start > 0.1:
            return 999.0

    return round((pulse_end - pulse_start) * 17150, 2)


def ir_detected(raw: int) -> bool:
    return bool(raw) if IR_ACTIVE_HIGH else not bool(raw)


def blue_heartbeat_loop() -> None:
    while not _stop_blue.is_set():
        if _manual_blue.is_set():
            time.sleep(0.02)
            continue
        GPIO.output(LED_BLUE, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(LED_BLUE, GPIO.LOW)
        time.sleep(0.75)


def alert_buzzer_with_blue() -> None:
    _manual_blue.set()
    try:
        GPIO.output(LED_BLUE, GPIO.LOW)
        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.1)
        for _ in range(3):
            GPIO.output(LED_BLUE, GPIO.HIGH)
            GPIO.output(BUZZER, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(BUZZER, GPIO.LOW)
            GPIO.output(LED_BLUE, GPIO.LOW)
            time.sleep(0.15)
    finally:
        GPIO.output(BUZZER, GPIO.LOW)
        GPIO.output(LED_BLUE, GPIO.LOW)
        _manual_blue.clear()


def main() -> None:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.setup(IR_LEFT, GPIO.IN)
    GPIO.setup(IR_RIGHT, GPIO.IN)
    GPIO.setup(BUZZER, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_BLUE, GPIO.OUT, initial=GPIO.LOW)

    lcd = setup_lcd()
    last_lcd = None
    last_print = None
    obstacle_latched = False
    blue_thread = threading.Thread(target=blue_heartbeat_loop, name="blue-heartbeat-test", daemon=True)
    blue_thread.start()

    print(
        "Prueba continua: estado normal + deteccion obstaculos + LCD + buzzer + LED azul digital sync",
        flush=True,
    )

    try:
        while True:
            distance = read_cm()
            front = distance < THRESHOLD_CM
            raw_left = GPIO.input(IR_LEFT)
            raw_right = GPIO.input(IR_RIGHT)
            rear_left = ir_detected(raw_left)
            rear_right = ir_detected(raw_right)
            rear = rear_left or rear_right
            obstacle = front or rear

            if front:
                last_lcd = lcd_write(lcd, last_lcd, "Obstaculo front", f"{distance:.1f} cm")
            elif rear:
                if rear_left and rear_right:
                    side = "Izq+Der"
                elif rear_left:
                    side = "Izq"
                else:
                    side = "Der"
                last_lcd = lcd_write(lcd, last_lcd, "Obstaculo atras", side)
            else:
                shown = "sin eco" if distance >= 999 else f"F:{distance:.0f}cm"
                last_lcd = lcd_write(lcd, last_lcd, "Sistema normal", shown + " R:Libre")

            printable_distance = "timeout" if distance >= 999 else distance
            state = (
                printable_distance,
                raw_left,
                raw_right,
                front,
                rear_left,
                rear_right,
                obstacle,
            )
            if state != last_print:
                print(
                    "dist=%s rawL=%s rawR=%s front=%s rearL=%s rearR=%s obstacle=%s"
                    % state,
                    flush=True,
                )
                last_print = state

            if obstacle and not obstacle_latched:
                print(
                    "ALERTA: pausa heartbeat; buzzer 3x + LED azul 3x sincronizados; vuelve heartbeat",
                    flush=True,
                )
                alert_buzzer_with_blue()
                obstacle_latched = True

            if not obstacle:
                obstacle_latched = False

            time.sleep(0.15)
    finally:
        _stop_blue.set()
        _manual_blue.set()
        if blue_thread.is_alive():
            blue_thread.join(timeout=1.0)
        GPIO.output(BUZZER, GPIO.LOW)
        GPIO.output(LED_BLUE, GPIO.LOW)
        GPIO.output(TRIG, GPIO.LOW)
        if lcd is not None:
            lcd.clear()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
