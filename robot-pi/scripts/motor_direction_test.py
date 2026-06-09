from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.navigation import motor_controller  # noqa: E402


LOGGER = logging.getLogger("motor_direction_test")


def run_step(name: str, action, speed: int, duration_seconds: float, pause_seconds: float) -> None:
    LOGGER.info("%s por %.1f segundos a velocidad %d%%", name, duration_seconds, speed)
    action(speed)
    time.sleep(duration_seconds)
    motor_controller.stop()
    if pause_seconds > 0:
        time.sleep(pause_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prueba aislada de direcciones de motores.")
    parser.add_argument("--speed", type=int, default=35, help="Velocidad PWM 0-100. Default: 35")
    parser.add_argument("--duration", type=float, default=2.0, help="Duracion por instruccion en segundos. Default: 2.0")
    parser.add_argument("--pause", type=float, default=0.5, help="Pausa detenido entre instrucciones. Default: 0.5")
    parser.add_argument(
        "--skip-sides",
        action="store_true",
        help="Omite pruebas individuales por lado y ejecuta solo maniobras completas.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    speed = max(0, min(args.speed, 100))
    duration = max(0.1, args.duration)
    pause = max(0.0, args.pause)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    LOGGER.info("Iniciando prueba aislada de motores")
    motor_controller.setup()
    try:
        sequence = []
        if not args.skip_sides:
            sequence.extend(
                [
                    ("IZQUIERDA ADELANTE", motor_controller.move_left_forward),
                    ("IZQUIERDA ATRAS", motor_controller.move_left_backward),
                    ("DERECHA ADELANTE", motor_controller.move_right_forward),
                    ("DERECHA ATRAS", motor_controller.move_right_backward),
                ]
            )
        sequence.extend([
            ("ADELANTE", motor_controller.move_forward),
            ("ATRAS", motor_controller.move_backward),
            ("GIRO IZQUIERDA", motor_controller.turn_left),
            ("GIRO DERECHA", motor_controller.turn_right),
        ])
        for name, action in sequence:
            run_step(name, action, speed, duration, pause)
    except KeyboardInterrupt:
        LOGGER.warning("Prueba interrumpida por usuario")
        return 130
    finally:
        LOGGER.info("Deteniendo motores y limpiando GPIO")
        motor_controller.cleanup()
    LOGGER.info("Prueba finalizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
