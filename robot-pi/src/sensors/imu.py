from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from smbus2 import SMBus

from src.config import Settings


LOGGER = logging.getLogger(__name__)

MPU6050_DEFAULT_POWER_MGMT = 0x6B
MPU6050_ACCEL_XOUT_H = 0x3B
MPU6050_GYRO_XOUT_H = 0x43
MPU6050_TEMP_OUT_H = 0x41
IMU_REFERENCE_AXIS = "Z"


@dataclass(slots=True)
class ImuSample:
    accel_x_g: float
    accel_y_g: float
    accel_z_g: float
    gyro_x_dps: float
    gyro_y_dps: float
    gyro_z_dps: float
    temperature_c: float | None
    bus: int
    address: int
    timestamp: float
    heading_deg: float
    estimated_speed_mps: float


_settings: Settings | None = None
_bus: SMBus | None = None
_last_sample_at = 0.0
_last_sample: ImuSample | None = None
_available = False
_heading_deg = 259.0
_last_heading_update_at = 0.0


def setup(settings: Settings) -> None:
    global _settings, _bus, _available, _heading_deg, _last_heading_update_at
    _settings = settings
    _available = False
    _heading_deg = 259.0
    _last_heading_update_at = time.monotonic()
    if not settings.imu_enabled:
        LOGGER.info("IMU deshabilitada por configuracion")
        return
    try:
        _bus = SMBus(settings.imu_i2c_bus)
        _bus.write_byte_data(settings.imu_i2c_address, MPU6050_DEFAULT_POWER_MGMT, 0)
        _available = True
        LOGGER.info(
            "IMU inicializada en bus I2C %s direccion 0x%02X",
            settings.imu_i2c_bus,
            settings.imu_i2c_address,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("IMU no disponible: %s", exc)
        cleanup()


def _read_word_signed(register: int) -> int:
    if _bus is None or _settings is None:
        raise RuntimeError("IMU no inicializada")
    raw = _bus.read_word_data(_settings.imu_i2c_address, register)
    swapped = ((raw << 8) & 0xFF00) + (raw >> 8)
    return swapped - 65536 if swapped >= 32768 else swapped


def sample() -> ImuSample | None:
    global _last_sample_at, _last_sample, _heading_deg, _last_heading_update_at
    if not _available or _settings is None or _bus is None:
        return None
    now = time.monotonic()
    if _last_sample is not None and (now - _last_sample_at) < _settings.imu_sample_cooldown_seconds:
        return _last_sample
    try:
        accel_x = _read_word_signed(MPU6050_ACCEL_XOUT_H) / _settings.imu_accel_scale
        accel_y = _read_word_signed(MPU6050_ACCEL_XOUT_H + 2) / _settings.imu_accel_scale
        accel_z = _read_word_signed(MPU6050_ACCEL_XOUT_H + 4) / _settings.imu_accel_scale
        temp_raw = _read_word_signed(MPU6050_TEMP_OUT_H)
        temperature_c = round((temp_raw / 340.0) + 36.53, 2)
        gyro_x = _read_word_signed(MPU6050_GYRO_XOUT_H) / _settings.imu_gyro_scale
        gyro_y = _read_word_signed(MPU6050_GYRO_XOUT_H + 2) / _settings.imu_gyro_scale
        gyro_z = _read_word_signed(MPU6050_GYRO_XOUT_H + 4) / _settings.imu_gyro_scale
        delta_seconds = max(now - _last_heading_update_at, 0.0)
        _heading_deg = (_heading_deg + (gyro_z * delta_seconds)) % 360.0
        _last_heading_update_at = now
        estimated_speed_mps = round(max((abs(accel_x) + abs(accel_y)) * 0.25, 0.0), 4)
        _last_sample = ImuSample(
            accel_x_g=round(accel_x, 4),
            accel_y_g=round(accel_y, 4),
            accel_z_g=round(accel_z, 4),
            gyro_x_dps=round(gyro_x, 4),
            gyro_y_dps=round(gyro_y, 4),
            gyro_z_dps=round(gyro_z, 4),
            temperature_c=temperature_c,
            bus=_settings.imu_i2c_bus,
            address=_settings.imu_i2c_address,
            timestamp=time.time(),
            heading_deg=round(_heading_deg, 2),
            estimated_speed_mps=estimated_speed_mps,
        )
        _last_sample_at = now
        return _last_sample
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Fallo al leer IMU: %s", exc)
        return None


def health_snapshot() -> dict[str, object]:
    sample_value = sample()
    if sample_value is None:
        return {"enabled": bool(_settings and _settings.imu_enabled), "available": False}
    return {
        "enabled": True,
        "available": True,
        "bus": sample_value.bus,
        "address": sample_value.address,
        "accelXg": sample_value.accel_x_g,
        "accelYg": sample_value.accel_y_g,
        "accelZg": sample_value.accel_z_g,
        "gyroXdps": sample_value.gyro_x_dps,
        "gyroYdps": sample_value.gyro_y_dps,
        "gyroZdps": sample_value.gyro_z_dps,
        "temperatureCelsius": sample_value.temperature_c,
        "headingDeg": sample_value.heading_deg,
        "referenceAxis": IMU_REFERENCE_AXIS,
        "estimatedSpeedMps": sample_value.estimated_speed_mps,
        "timestamp": sample_value.timestamp,
    }


def cleanup() -> None:
    global _bus, _available, _last_sample
    _available = False
    _last_sample = None
    if _bus is not None:
        try:
            _bus.close()
        except Exception:
            pass
    _bus = None
