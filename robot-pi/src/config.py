from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Pinout alineado a la documentacion de circuito local.
# El L298N queda controlado por IN1..IN4; ENA/ENB deben permanecer
# puenteados en el modulo si se usa este mapeo.
MOTOR_LEFT_IN1 = 17
MOTOR_LEFT_IN2 = 27
MOTOR_RIGHT_IN3 = 22
MOTOR_RIGHT_IN4 = 23

LINE_SENSOR_LEFT = 13
LINE_SENSOR_CENTER = 19
LINE_SENSOR_RIGHT = 26

ULTRASONIC_TRIG = 5
ULTRASONIC_ECHO = 6

IR_LEFT = 16
IR_RIGHT = 20

LCD_SDA = 2
LCD_SCL = 3

LED_GREEN = 12
LED_YELLOW = 24
LED_RED = 25

BUZZER = 21

CLASSES = ["atencion", "peligro", "sano"]
PWM_FREQUENCY_HZ = 1000
N_CAPTURES = 3


@dataclass(slots=True)
class Settings:
    backend_base_url: str
    backend_ws_url: str
    heartbeat_path: str
    observation_path: str
    camera_type: str
    camera_front_index: int
    camera_left_index: int
    camera_right_index: int
    camera_width: int
    camera_height: int
    model_path: str
    labels_path: str
    ai_confidence_threshold: float
    robot_id: str
    patrol_speed: int
    obstacle_distance_cm: float
    line_lost_timeout: float
    status_interval_seconds: float
    manual_default_speed: int
    stream_fps: int
    stream_quality: int
    capture_count: int
    observation_retry_count: int
    local_ai_enabled: bool
    cpu_temp_path: str
    battery_capacity_path: str | None
    lcd_enabled: bool
    led_enabled: bool
    buzzer_enabled: bool
    line_active_low: bool

    @classmethod
    def load(cls) -> "Settings":
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        backend_base_url = os.getenv("BACKEND_BASE_URL") or os.getenv("BRIDGE_URL") or "http://localhost:8080/api"
        return cls(
            backend_base_url=backend_base_url,
            backend_ws_url=os.getenv("BACKEND_WS_URL", "ws://localhost:8080/api/ws"),
            heartbeat_path=os.getenv("HEARTBEAT_PATH", "/robot/heartbeat"),
            observation_path=os.getenv("OBSERVATION_PATH", "/robot/observations"),
            camera_type=os.getenv("CAMERA_TYPE", "usb").lower(),
            camera_front_index=int(os.getenv("CAMERA_FRONT_INDEX", "0")),
            camera_left_index=int(os.getenv("CAMERA_LEFT_INDEX", "1")),
            camera_right_index=int(os.getenv("CAMERA_RIGHT_INDEX", "2")),
            camera_width=int(os.getenv("CAMERA_WIDTH", "640")),
            camera_height=int(os.getenv("CAMERA_HEIGHT", "480")),
            model_path=os.getenv("MODEL_PATH", "/app/models/modelo_vivero.tflite"),
            labels_path=os.getenv("LABELS_PATH", "/app/models/labels.txt"),
            ai_confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.65")),
            robot_id=os.getenv("ROBOT_ID", "ROBOT-001"),
            patrol_speed=int(os.getenv("PATROL_SPEED", "40")),
            obstacle_distance_cm=float(os.getenv("OBSTACLE_DISTANCE_CM", "20")),
            line_lost_timeout=float(os.getenv("LINE_LOST_TIMEOUT", "3.0")),
            status_interval_seconds=float(os.getenv("STATUS_INTERVAL_SECONDS", "10")),
            manual_default_speed=int(os.getenv("MANUAL_DEFAULT_SPEED", "35")),
            stream_fps=int(os.getenv("STREAM_FPS", "10")),
            stream_quality=int(os.getenv("STREAM_QUALITY", "60")),
            capture_count=int(os.getenv("CAPTURE_COUNT", str(N_CAPTURES))),
            observation_retry_count=int(os.getenv("OBSERVATION_RETRY_COUNT", "3")),
            local_ai_enabled=os.getenv("LOCAL_AI_ENABLED", "false").lower() == "true",
            cpu_temp_path=os.getenv("CPU_TEMP_PATH", "/sys/class/thermal/thermal_zone0/temp"),
            battery_capacity_path=os.getenv("BATTERY_CAPACITY_PATH"),
            lcd_enabled=os.getenv("LCD_ENABLED", "true").lower() == "true",
            led_enabled=os.getenv("LED_ENABLED", "true").lower() == "true",
            buzzer_enabled=os.getenv("BUZZER_ENABLED", "true").lower() == "true",
            line_active_low=os.getenv("LINE_ACTIVE_LOW", "true").lower() == "true",
        )
