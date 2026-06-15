from __future__ import annotations

import os
import time

import RPi.GPIO as GPIO  # type: ignore


PINS = {"izquierda": 13, "centro": 19, "derecha": 16}


def action_for(pattern: tuple[int, int, int]) -> str:
    if pattern == (0, 1, 0):
        return "AVANZA"
    if pattern in {(1, 1, 0), (1, 0, 0)}:
        return "IZQUIERDA"
    if pattern in {(0, 1, 1), (0, 0, 1)}:
        return "DERECHA"
    if pattern == (0, 0, 0):
        return "SIN_LINEA"
    if pattern == (1, 1, 1):
        return "TODO_ACTIVO"
    return "PATRON_MIXTO"


def normalize(value: int, active_low: bool) -> int:
    if not active_low:
        return value
    return 0 if value == 1 else 1


def main() -> None:
    active_low = os.getenv("LINE_ACTIVE_LOW", "false").lower() == "true"
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS.values():
        GPIO.setup(pin, GPIO.IN)

    print("TCRT5000 tiempo real - CTRL+C para salir", flush=True)
    print(f"LINE_ACTIVE_LOW={active_low} pins={PINS}", flush=True)
    print(
        "identificacion: izquierda=GPIO13 pin33 | centro=GPIO19 pin35 | derecha=GPIO16 pin36",
        flush=True,
    )
    print(
        "patrones: (0,1,0)=avance | (1,1,0)/(1,0,0)=izq | "
        "(0,1,1)/(0,0,1)=der | (0,0,0)=sin linea | (1,1,1)=todo activo",
        flush=True,
    )

    last_pattern: tuple[int, int, int] | None = None
    counter = 0
    try:
        while True:
            raw = {name: int(GPIO.input(pin)) for name, pin in PINS.items()}
            normalized = {name: normalize(value, active_low) for name, value in raw.items()}
            pattern = (normalized["izquierda"], normalized["centro"], normalized["derecha"])
            marker = "*" if pattern != last_pattern else " "
            last_pattern = pattern
            print(
                f"{counter:05d}{marker} raw={raw} estado={normalized} "
                f"pattern={pattern} action={action_for(pattern)}",
                flush=True,
            )
            counter += 1
            time.sleep(0.15)
    except KeyboardInterrupt:
        print("detenido", flush=True)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
