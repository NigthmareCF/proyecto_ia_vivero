from __future__ import annotations

import logging

from src.config import (
    MOTOR_LEFT_IN1,
    MOTOR_LEFT_IN2,
    MOTOR_RIGHT_IN3,
    MOTOR_RIGHT_IN4,
    PWM_FREQUENCY_HZ,
)


LOGGER = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = None


_left_forward_pwm = None
_left_reverse_pwm = None
_right_forward_pwm = None
_right_reverse_pwm = None


def _pwms_ready() -> bool:
    return all(pwm is not None for pwm in [_left_forward_pwm, _left_reverse_pwm, _right_forward_pwm, _right_reverse_pwm])


def setup() -> None:
    global _left_forward_pwm, _left_reverse_pwm, _right_forward_pwm, _right_reverse_pwm
    if GPIO is None:
        LOGGER.warning("RPi.GPIO no disponible; motor_controller en simulacion")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_RIGHT_IN3, MOTOR_RIGHT_IN4]:
        GPIO.setup(pin, GPIO.OUT)
    _left_forward_pwm = GPIO.PWM(MOTOR_LEFT_IN1, PWM_FREQUENCY_HZ)
    _left_reverse_pwm = GPIO.PWM(MOTOR_LEFT_IN2, PWM_FREQUENCY_HZ)
    _right_forward_pwm = GPIO.PWM(MOTOR_RIGHT_IN3, PWM_FREQUENCY_HZ)
    _right_reverse_pwm = GPIO.PWM(MOTOR_RIGHT_IN4, PWM_FREQUENCY_HZ)
    for pwm in [_left_forward_pwm, _left_reverse_pwm, _right_forward_pwm, _right_reverse_pwm]:
        pwm.start(0)


def _apply(left_forward: bool, right_forward: bool, speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    duty = max(0, min(speed, 100))
    _left_forward_pwm.ChangeDutyCycle(duty if left_forward else 0)
    _left_reverse_pwm.ChangeDutyCycle(0 if left_forward else duty)
    _right_forward_pwm.ChangeDutyCycle(duty if right_forward else 0)
    _right_reverse_pwm.ChangeDutyCycle(0 if right_forward else duty)


def move_forward(speed: int) -> None:
    _apply(True, True, speed)


def move_backward(speed: int) -> None:
    _apply(False, False, speed)


def turn_left(speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    left_duty = max(0, min(speed // 2, 100))
    right_duty = max(0, min(speed, 100))
    _left_forward_pwm.ChangeDutyCycle(0)
    _left_reverse_pwm.ChangeDutyCycle(left_duty)
    _right_forward_pwm.ChangeDutyCycle(right_duty)
    _right_reverse_pwm.ChangeDutyCycle(0)


def turn_right(speed: int) -> None:
    if GPIO is None or not _pwms_ready():
        return
    left_duty = max(0, min(speed, 100))
    right_duty = max(0, min(speed // 2, 100))
    _left_forward_pwm.ChangeDutyCycle(left_duty)
    _left_reverse_pwm.ChangeDutyCycle(0)
    _right_forward_pwm.ChangeDutyCycle(0)
    _right_reverse_pwm.ChangeDutyCycle(right_duty)


def stop() -> None:
    if GPIO is None or not _pwms_ready():
        return
    for pwm in [_left_forward_pwm, _left_reverse_pwm, _right_forward_pwm, _right_reverse_pwm]:
        pwm.ChangeDutyCycle(0)


def cleanup() -> None:
    if GPIO is None:
        return
    stop()
    GPIO.cleanup()
