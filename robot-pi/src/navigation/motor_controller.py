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


_left_pwm = None
_right_pwm = None


def setup() -> None:
    global _left_pwm, _right_pwm
    if GPIO is None:
        LOGGER.warning("RPi.GPIO no disponible; motor_controller en simulacion")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_LEFT_ENA, MOTOR_RIGHT_IN3, MOTOR_RIGHT_IN4, MOTOR_RIGHT_ENB]:
        GPIO.setup(pin, GPIO.OUT)
    _left_pwm = GPIO.PWM(MOTOR_LEFT_ENA, PWM_FREQUENCY_HZ)
    _right_pwm = GPIO.PWM(MOTOR_RIGHT_ENB, PWM_FREQUENCY_HZ)
    _left_pwm.start(0)
    _right_pwm.start(0)


def _apply(left_forward: bool, right_forward: bool, speed: int) -> None:
    if GPIO is None:
        return
    duty = max(0, min(speed, 100))
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW if right_forward else GPIO.HIGH)
    _left_pwm.ChangeDutyCycle(duty)
    _right_pwm.ChangeDutyCycle(duty)


def move_forward(speed: int) -> None:
    _apply(True, True, speed)


def move_backward(speed: int) -> None:
    _apply(False, False, speed)


def turn_left(speed: int) -> None:
    if GPIO is None:
        return
    _left_pwm.ChangeDutyCycle(max(0, min(speed // 2, 100)))
    _right_pwm.ChangeDutyCycle(max(0, min(speed, 100)))
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)


def turn_right(speed: int) -> None:
    if GPIO is None:
        return
    _left_pwm.ChangeDutyCycle(max(0, min(speed, 100)))
    _right_pwm.ChangeDutyCycle(max(0, min(speed // 2, 100)))
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)


def stop() -> None:
    if GPIO is None:
        return
    for pin in [MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_RIGHT_IN3, MOTOR_RIGHT_IN4]:
        GPIO.output(pin, GPIO.LOW)
    _left_pwm.ChangeDutyCycle(0)
    _right_pwm.ChangeDutyCycle(0)


def cleanup() -> None:
    if GPIO is None:
        return
    stop()
    GPIO.cleanup()
