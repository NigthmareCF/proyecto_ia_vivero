from __future__ import annotations

import logging
import time

from src.config import (
    MOTOR_LEFT_ENA,
    MOTOR_LEFT_IN1,
    MOTOR_LEFT_IN2,
    MOTOR_RIGHT_ENB,
    MOTOR_RIGHT_IN3,
    MOTOR_RIGHT_IN4,
    PWM_FREQUENCY_HZ,
)


LOGGER = logging.getLogger(__name__)
LOW_POWER_THRESHOLD = 20
LOW_POWER_START_DUTY = 25
LOW_POWER_START_SECONDS = 0.12
FULL_SPEED_MULTIPLIER = 3.5
TURN_INNER_SPEED_MULTIPLIER = 0.25

MOTION_PATTERNS = {
    "backward": (0, 1, 1, 0),
    "turn_left": (1, 0, 1, 0),
    "forward": (1, 0, 0, 1),
    "turn_right": (0, 1, 0, 1),
    "forward_right": (0, 0, 0, 1),
    "forward_left": (1, 0, 0, 0),
    "backward_left": (0, 1, 0, 0),
    "backward_right": (0, 0, 1, 0),
}

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_left_speed_pwm = None
_right_speed_pwm = None


def _pwms_ready() -> bool:
    return all(pwm is not None for pwm in [_left_speed_pwm, _right_speed_pwm])


def setup() -> None:
    global _left_speed_pwm, _right_speed_pwm
    if GPIO is None:
        LOGGER.warning("RPi.GPIO no disponible; motor_controller en simulacion")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_RIGHT_IN3, MOTOR_RIGHT_IN4, MOTOR_LEFT_ENA, MOTOR_RIGHT_ENB]:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    _left_speed_pwm = GPIO.PWM(MOTOR_LEFT_ENA, PWM_FREQUENCY_HZ)
    _right_speed_pwm = GPIO.PWM(MOTOR_RIGHT_ENB, PWM_FREQUENCY_HZ)
    for pwm in [_left_speed_pwm, _right_speed_pwm]:
        pwm.start(0)
    stop()


def _clamp_speed(speed: int) -> int:
    return max(0, min(speed, 100))


def _relative_speed(speed: int, multiplier: float) -> int:
    return _clamp_speed(int(round(speed * multiplier)))


def _apply_pwm(left_speed: int, right_speed: int) -> None:
    left_speed = _clamp_speed(left_speed)
    right_speed = _clamp_speed(right_speed)
    needs_start_boost = (
        0 < left_speed < LOW_POWER_THRESHOLD
        or 0 < right_speed < LOW_POWER_THRESHOLD
    )
    if needs_start_boost:
        _left_speed_pwm.ChangeDutyCycle(LOW_POWER_START_DUTY if left_speed > 0 else 0)
        _right_speed_pwm.ChangeDutyCycle(LOW_POWER_START_DUTY if right_speed > 0 else 0)
        time.sleep(LOW_POWER_START_SECONDS)
    _left_speed_pwm.ChangeDutyCycle(left_speed)
    _right_speed_pwm.ChangeDutyCycle(right_speed)


def _apply_pattern(pattern: tuple[int, int, int, int], speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    in1, in2, in3, in4 = pattern
    left_speed = speed if in1 or in2 else 0
    right_speed = speed if in3 or in4 else 0
    apply_raw(in1, in2, in3, in4, left_speed, right_speed)


def _apply_relative_drive(
    pattern: tuple[int, int, int, int],
    speed: int,
    ena_multiplier: float,
    enb_multiplier: float,
) -> None:
    if GPIO is None or not _pwms_ready():
        return
    in1, in2, in3, in4 = pattern
    apply_raw(
        in1,
        in2,
        in3,
        in4,
        _relative_speed(speed, ena_multiplier),
        _relative_speed(speed, enb_multiplier),
    )


def pin_map() -> dict[str, int]:
    return {
        "IN1": MOTOR_LEFT_IN1,
        "IN2": MOTOR_LEFT_IN2,
        "IN3": MOTOR_RIGHT_IN3,
        "IN4": MOTOR_RIGHT_IN4,
        "ENA": MOTOR_LEFT_ENA,
        "ENB": MOTOR_RIGHT_ENB,
    }


def apply_raw(in1: int, in2: int, in3: int, in4: int, ena_speed: int, enb_speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH if in1 else GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH if in2 else GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH if in3 else GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH if in4 else GPIO.LOW)
    _apply_pwm(ena_speed, enb_speed)


def move_forward(speed: int) -> None:
    _apply_pattern(MOTION_PATTERNS["forward"], speed)


def move_backward(speed: int) -> None:
    _apply_pattern(MOTION_PATTERNS["backward"], speed)


def turn_left(speed: int) -> None:
    _apply_pattern(MOTION_PATTERNS["turn_left"], speed)


def turn_right(speed: int) -> None:
    _apply_pattern(MOTION_PATTERNS["turn_right"], speed)


def move_left_forward(speed: int) -> None:
    _apply_relative_drive(MOTION_PATTERNS["forward"], speed, TURN_INNER_SPEED_MULTIPLIER, FULL_SPEED_MULTIPLIER)


def move_left_backward(speed: int) -> None:
    _apply_relative_drive(MOTION_PATTERNS["backward"], speed, TURN_INNER_SPEED_MULTIPLIER, FULL_SPEED_MULTIPLIER)


def move_right_forward(speed: int) -> None:
    _apply_relative_drive(MOTION_PATTERNS["forward"], speed, FULL_SPEED_MULTIPLIER, TURN_INNER_SPEED_MULTIPLIER)


def move_right_backward(speed: int) -> None:
    _apply_relative_drive(MOTION_PATTERNS["backward"], speed, FULL_SPEED_MULTIPLIER, TURN_INNER_SPEED_MULTIPLIER)


def move_forward_left(speed: int) -> None:
    move_left_forward(speed)


def move_forward_right(speed: int) -> None:
    move_right_forward(speed)


def move_backward_left(speed: int) -> None:
    move_left_backward(speed)


def move_backward_right(speed: int) -> None:
    move_right_backward(speed)


def stop() -> None:
    if GPIO is None or not _pwms_ready():
        return
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    for pwm in [_left_speed_pwm, _right_speed_pwm]:
        pwm.ChangeDutyCycle(0)


def cleanup() -> None:
    global _left_speed_pwm, _right_speed_pwm
    if GPIO is None:
        return
    stop()
    pwms = [_left_speed_pwm, _right_speed_pwm]
    for pwm in pwms:
        if pwm is not None:
            pwm.stop()
    _left_speed_pwm = None
    _right_speed_pwm = None
    del pwms
    GPIO.cleanup()
