from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Pinout alineado a la documentacion de circuito local.
MOTOR_LEFT_IN1 = 17
MOTOR_LEFT_IN2 = 27
MOTOR_RIGHT_IN3 = 22
MOTOR_RIGHT_IN4 = 23
MOTOR_LEFT_ENA = 18
MOTOR_RIGHT_ENB = 25

LINE_SENSOR_LEFT = 13
LINE_SENSOR_CENTER = 19
LINE_SENSOR_RIGHT = 16

ULTRASONIC_TRIG = 5
ULTRASONIC_ECHO = 6

IR_LEFT = 8
IR_RIGHT = 9

LCD_SDA = 2
LCD_SCL = 3

LED_GREEN = 12
LED_YELLOW = 24
LED_RED = 26
LED_BLUE = 20

BUZZER = 21

CLASSES = ["atencion", "peligro", "sano"]
PWM_FREQUENCY_HZ = 1000
MOTOR_LEFT_INVERTED = os.getenv("MOTOR_LEFT_INVERTED", "true").lower() == "true"
MOTOR_RIGHT_INVERTED = os.getenv("MOTOR_RIGHT_INVERTED", "false").lower() == "true"
N_CAPTURES = 6


@dataclass(slots=True)
class Settings:
    backend_base_url: str
    backend_ws_url: str
    heartbeat_path: str
    observation_path: str
    command_next_path: str
    command_ack_path_template: str
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
    manual_command_timeout_seconds: float
    speed_profile_low: int
    speed_profile_medium: int
    speed_profile_high: int
    speed_profile_turbo: int
    stream_fps: int
    stream_quality: int
    capture_count: int
    qr_capture_speed: int
    burst_frame_interval_seconds: float
    end_row_forward_seconds: float
    end_row_turn_seconds: float
    observation_retry_count: int
    command_poll_interval_seconds: float
    observation_flush_interval_seconds: float
    qr_detection_cooldown_seconds: float
    qr_label_cache_path: str
    qr_label_request_timeout_seconds: float
    local_ai_enabled: bool
    offline_queue_dir: str
    wifi_ssid: str
    wifi_password: str
    cpu_temp_path: str
    battery_capacity_path: str | None
    lcd_enabled: bool
    led_enabled: bool
    buzzer_enabled: bool
    line_active_low: bool
    rear_ir_active_high: bool
    heartbeat_led_blink_interval_seconds: float
    heartbeat_led_fast_blink_interval_seconds: float
    heartbeat_led_breathe_step_seconds: float
    heartbeat_led_breathe_step_duty: float
    lcd_rotation_interval_seconds: float
    search_history_tolerance_scans: int
    state_search_pause_seconds: float

    @classmethod
    def load(cls) -> "Settings":
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:3000/api")
        return cls(
            backend_base_url=backend_base_url,
            backend_ws_url=os.getenv("BACKEND_WS_URL", "ws://localhost:3000/api/ws/robot-stream"),
            heartbeat_path=os.getenv("HEARTBEAT_PATH", "/robot/heartbeat"),
            observation_path=os.getenv("OBSERVATION_PATH", "/robot/observations"),
            command_next_path=os.getenv("COMMAND_NEXT_PATH", "/robot/commands/next"),
            command_ack_path_template=os.getenv("COMMAND_ACK_PATH_TEMPLATE", "/robot/commands/{commandId}/ack"),
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
            manual_command_timeout_seconds=float(os.getenv("MANUAL_COMMAND_TIMEOUT_SECONDS", "0.3")),
            speed_profile_low=int(os.getenv("SPEED_PROFILE_LOW", "30")),
            speed_profile_medium=int(os.getenv("SPEED_PROFILE_MEDIUM", "45")),
            speed_profile_high=int(os.getenv("SPEED_PROFILE_HIGH", "65")),
            speed_profile_turbo=int(os.getenv("SPEED_PROFILE_TURBO", "85")),
            stream_fps=int(os.getenv("STREAM_FPS", "10")),
            stream_quality=int(os.getenv("STREAM_QUALITY", "60")),
            capture_count=int(os.getenv("CAPTURE_COUNT", str(N_CAPTURES))),
            qr_capture_speed=int(os.getenv("QR_CAPTURE_SPEED", "25")),
            burst_frame_interval_seconds=float(os.getenv("BURST_FRAME_INTERVAL_SECONDS", "0.08")),
            end_row_forward_seconds=float(os.getenv("END_ROW_FORWARD_SECONDS", "5.0")),
            end_row_turn_seconds=float(os.getenv("END_ROW_TURN_SECONDS", "1.0")),
            observation_retry_count=int(os.getenv("OBSERVATION_RETRY_COUNT", "3")),
            command_poll_interval_seconds=float(os.getenv("COMMAND_POLL_INTERVAL_SECONDS", "1.0")),
            observation_flush_interval_seconds=float(os.getenv("OBSERVATION_FLUSH_INTERVAL_SECONDS", "5.0")),
            qr_detection_cooldown_seconds=float(os.getenv("QR_DETECTION_COOLDOWN_SECONDS", "12.0")),
            qr_label_cache_path=os.getenv("QR_LABEL_CACHE_PATH", "/app/data/qr-label-cache.db"),
            qr_label_request_timeout_seconds=float(os.getenv("QR_LABEL_REQUEST_TIMEOUT_SECONDS", "1.8")),
            local_ai_enabled=os.getenv("LOCAL_AI_ENABLED", "false").lower() == "true",
            offline_queue_dir=os.getenv("OFFLINE_QUEUE_DIR", "/app/data/offline-queue"),
            wifi_ssid=os.getenv("WIFI_SSID", "Redmi Note 14"),
            wifi_password=os.getenv("WIFI_PASSWORD", "tashycora"),
            cpu_temp_path=os.getenv("CPU_TEMP_PATH", "/sys/class/thermal/thermal_zone0/temp"),
            battery_capacity_path=os.getenv("BATTERY_CAPACITY_PATH"),
            lcd_enabled=os.getenv("LCD_ENABLED", "true").lower() == "true",
            led_enabled=os.getenv("LED_ENABLED", "true").lower() == "true",
            buzzer_enabled=os.getenv("BUZZER_ENABLED", "true").lower() == "true",
            line_active_low=os.getenv("LINE_ACTIVE_LOW", "false").lower() == "true",
            rear_ir_active_high=os.getenv("REAR_IR_ACTIVE_HIGH", "true").lower() == "true",
            heartbeat_led_blink_interval_seconds=float(os.getenv("HEARTBEAT_LED_BLINK_INTERVAL_SECONDS", "0.5")),
            heartbeat_led_fast_blink_interval_seconds=float(os.getenv("HEARTBEAT_LED_FAST_BLINK_INTERVAL_SECONDS", "0.2")),
            heartbeat_led_breathe_step_seconds=float(os.getenv("HEARTBEAT_LED_BREATHE_STEP_SECONDS", "0.04")),
            heartbeat_led_breathe_step_duty=float(os.getenv("HEARTBEAT_LED_BREATHE_STEP_DUTY", "5")),
            lcd_rotation_interval_seconds=float(os.getenv("LCD_ROTATION_INTERVAL_SECONDS", "2.4")),
            search_history_tolerance_scans=int(os.getenv("SEARCH_HISTORY_TOLERANCE_SCANS", "2")),
            state_search_pause_seconds=float(os.getenv("STATE_SEARCH_PAUSE_SECONDS", "5.0")),
        )
