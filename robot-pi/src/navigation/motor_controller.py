from __future__ import annotations

import logging

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
        GPIO.setup(pin, GPIO.OUT)
    _left_speed_pwm = GPIO.PWM(MOTOR_LEFT_ENA, PWM_FREQUENCY_HZ)
    _right_speed_pwm = GPIO.PWM(MOTOR_RIGHT_ENB, PWM_FREQUENCY_HZ)
    for pwm in [_left_speed_pwm, _right_speed_pwm]:
        pwm.start(0)
    stop()


def _set_direction(left_forward: bool, right_forward: bool) -> None:
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW if right_forward else GPIO.HIGH)


def _apply(left_forward: bool, right_forward: bool, left_speed: int, right_speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    _set_direction(left_forward, right_forward)
    _left_speed_pwm.ChangeDutyCycle(max(0, min(left_speed, 100)))
    _right_speed_pwm.ChangeDutyCycle(max(0, min(right_speed, 100)))


def move_forward(speed: int) -> None:
    _apply(True, True, speed, speed)


def move_backward(speed: int) -> None:
    _apply(False, False, speed, speed)


def turn_left(speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    _apply(False, True, max(0, min(speed // 2, 100)), max(0, min(speed, 100)))


def turn_right(speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    _apply(True, False, max(0, min(speed, 100)), max(0, min(speed // 2, 100)))


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
    if GPIO is None:
        return
    stop()
    GPIO.cleanup()
