from __future__ import annotations

import logging
import os
import signal
import threading
import time
from datetime import datetime
from typing import Any

import numpy as np

from src.ai.classifier import classify_burst
from src.ai.model_loader import load_model
from src.communication.backend_client import BackendClient
from src.communication.command_listener import CommandListener
from src.config import Settings
from src.display import buzzer_handler, lcd_handler, led_handler
from src.navigation import line_follower, motor_controller, obstacle_detector
from src.state_machine import RobotState, RobotStateMachine
from src.vision.camera_handler import CameraHandler
from src.vision.qr_detector import detect_qr
from src.vision.stream_sender import StreamSender


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOGGER = logging.getLogger("agrotech.robot")


def main() -> None:
    settings = Settings.load()
    shutdown_event = threading.Event()
    state_machine = RobotStateMachine()
    backend_client = BackendClient(settings)
    camera = CameraHandler(settings)
    stream_sender = StreamSender(settings, lambda: camera.capture_frame(str(runtime_context["active_camera"])))
    interpreter = None
    input_details = None
    output_details = None
    if settings.local_ai_enabled:
        interpreter, input_details, output_details = load_model(settings)
    command_listener: CommandListener | None = None
    local_ai_available = all(item is not None for item in (interpreter, input_details, output_details))
    runtime_context: dict[str, Any] = {
        "captured_frames": [],
        "last_local_analysis": None,
        "last_observation_at": None,
        "last_observation_status": "idle",
        "last_capture_count": 0,
        "last_obstacle_distance_cm": None,
        "obstacle_detected": False,
        "obstacle_count": 0,
        "stream_active": False,
        "active_camera": "front",
        "control_profile": "AUTO_LINE",
        "speed_profile": "MEDIUM",
        "started_at": time.monotonic(),
    }

    if settings.local_ai_enabled and not local_ai_available:
        LOGGER.warning("Clasificacion local habilitada pero el modelo no esta disponible; se enviaran solo observaciones")

    def set_stream_enabled(enabled: bool) -> None:
        if enabled and not runtime_context["stream_active"]:
            stream_sender.start_stream()
            runtime_context["stream_active"] = True
        elif not enabled and runtime_context["stream_active"]:
            stream_sender.stop_stream()
            runtime_context["stream_active"] = False

    def read_optional_float(path: str | None, scale: float = 1.0) -> float | None:
        if not path:
            return None
        try:
            raw_value = open(path, "r", encoding="utf-8").read().strip()
            if not raw_value:
                return None
            return round(float(raw_value) / scale, 2)
        except (OSError, ValueError):
            return None

    def get_cpu_temperature_c() -> float | None:
        return read_optional_float(settings.cpu_temp_path, scale=1000.0)

    def get_battery_level() -> float | None:
        return read_optional_float(settings.battery_capacity_path)

    def get_cpu_usage_percent() -> float | None:
        try:
            cpu_count = os.cpu_count() or 1
            return round(min((os.getloadavg()[0] / cpu_count) * 100, 100.0), 2)
        except (AttributeError, OSError):
            return None

    def get_connection_quality() -> str:
        if runtime_context["last_observation_status"] == "failed":
            return "DEGRADED"
        if runtime_context["last_observation_status"] == "retrying":
            return "UNSTABLE"
        return "GOOD"

    def map_state_to_mode(state: RobotState) -> str:
        if state == RobotState.IDLE:
            return "IDLE"
        if state == RobotState.MANUAL:
            return "MANUAL"
        if state == RobotState.QR_DETECTED:
            return "GOTO"
        return "AUTO"

    def build_robot_health(snapshot: Any) -> dict[str, Any]:
        return {
            "batteryLevel": get_battery_level(),
            "temperatureCelsius": get_cpu_temperature_c(),
            "cpuUsagePercent": get_cpu_usage_percent(),
            "connectionQuality": get_connection_quality(),
            "uptimeSeconds": round(time.monotonic() - runtime_context["started_at"], 1),
            "streamActive": bool(runtime_context["stream_active"]),
            "manualDirection": snapshot.manual_direction,
            "manualSpeed": snapshot.manual_speed,
            "obstacleDetected": bool(runtime_context["obstacle_detected"]),
            "obstacleDistanceCm": runtime_context["last_obstacle_distance_cm"],
            "obstacleCount": int(runtime_context["obstacle_count"]),
            "lastObservationAt": runtime_context["last_observation_at"],
            "lastObservationStatus": runtime_context["last_observation_status"],
            "lastCaptureCount": int(runtime_context["last_capture_count"]),
            "localAiEnabled": settings.local_ai_enabled,
            "localAiAvailable": local_ai_available,
            "camera": {
                "type": settings.camera_type,
                "width": settings.camera_width,
                "height": settings.camera_height,
            },
            "activeCamera": str(runtime_context["active_camera"]).upper(),
            "controlProfile": str(runtime_context["control_profile"]).upper(),
            "speedProfile": str(runtime_context["speed_profile"]).upper(),
        }

    def build_heartbeat(snapshot: Any) -> dict[str, Any]:
        health = build_robot_health(snapshot)
        return {
            "mode": map_state_to_mode(snapshot.state),
            "batteryLevel": int(health["batteryLevel"]) if health["batteryLevel"] is not None else None,
            "temperatureCelsius": health["temperatureCelsius"],
            "cpuUsagePercent": health["cpuUsagePercent"],
            "connectionQuality": health["connectionQuality"],
            "currentPlantQr": snapshot.current_plant_qr,
            "currentPatrolId": snapshot.patrol_id,
            "obstacleDetected": bool(runtime_context["obstacle_detected"]),
            "blocked": bool(runtime_context["obstacle_detected"] and runtime_context["obstacle_count"] >= 3),
            "streamActive": bool(runtime_context["stream_active"]),
            "queueDepth": 0,
            "statusSummary": runtime_context["last_observation_status"],
            "activeCamera": str(runtime_context["active_camera"]).upper(),
            "controlProfile": str(runtime_context["control_profile"]).upper(),
            "speedProfile": str(runtime_context["speed_profile"]).upper(),
        }

    def encode_observation_images(frames: list[np.ndarray]) -> list[str]:
        encoded_images: list[str] = []
        for frame in frames:
            if not isinstance(frame, np.ndarray) or frame.size == 0:
                continue
            encoded = camera.frame_to_base64(frame)
            if not encoded:
                continue
            encoded_images.append(encoded)
        return encoded_images

    def build_observation_payload(snapshot: Any, frames: list[np.ndarray]) -> dict[str, Any]:
        local_analysis = runtime_context.get("last_local_analysis")
        return {
            "patrolId": snapshot.patrol_id or "manual-patrol",
            "plantQr": snapshot.current_plant_qr or "UNKNOWN",
            "captureReason": "QR_DETECTED",
            "statusHint": local_analysis["className"] if isinstance(local_analysis, dict) and local_analysis.get("className") else "PENDING_BACKEND_ANALYSIS",
            "observedAt": datetime.now().isoformat(),
            "mimeType": "image/jpeg",
            "imagesBase64": encode_observation_images(frames),
        }

    def cleanup() -> None:
        shutdown_event.set()
        set_stream_enabled(False)
        if command_listener is not None:
            command_listener.stop()
        camera.release()
        motor_controller.stop()
        motor_controller.cleanup()
        lcd_handler.cleanup()
        led_handler.cleanup()
        buzzer_handler.cleanup()

    def handle_signal(signum: int, _frame: Any) -> None:
        LOGGER.info("Signal %s received, shutting down", signum)
        cleanup()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    motor_controller.setup()
    line_follower.setup(settings)
    obstacle_detector.setup(settings)
    lcd_handler.setup(settings)
    led_handler.setup(settings)
    buzzer_handler.setup(settings)
    camera.setup()

    lcd_handler.show_message("AgroTech Robot", "Listo")
    led_handler.set_idle()

    def status_sender() -> None:
        while not shutdown_event.is_set():
            snapshot = state_machine.snapshot()
            backend_client.send_heartbeat(build_heartbeat(snapshot))
            shutdown_event.wait(settings.status_interval_seconds)

    def on_command(command: str, data: dict[str, Any]) -> None:
        LOGGER.info("Received command %s with data %s", command, data)
        if command == "START_PATROL":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            runtime_context["control_profile"] = "AUTO_LINE"
            lcd_handler.show_state("FOLLOW_LINE")
        elif command == "STOP":
            state_machine.stop()
            motor_controller.stop()
            set_stream_enabled(False)
            runtime_context["control_profile"] = "SAFE_STOP"
            lcd_handler.show_state("IDLE")
            led_handler.set_idle()
        elif command == "MANUAL_CONTROL":
            state_machine.enable_manual()
            runtime_context["control_profile"] = "MANUAL_FREE"
            lcd_handler.show_state("MANUAL")
        elif command == "AUTO":
            state_machine.enable_auto()
            set_stream_enabled(False)
            runtime_context["control_profile"] = "AUTO_LINE"
            lcd_handler.show_state("FOLLOW_LINE")
        elif command == "MOVE":
            state_machine.update_manual_move(
                direction=str(data.get("direction", "stop")),
                speed=int(data.get("speed", settings.manual_default_speed)),
            )
            if state_machine.snapshot().state == RobotState.MANUAL:
                apply_manual_move(state_machine.snapshot().manual_direction, state_machine.snapshot().manual_speed)
        elif command == "CAMERA_SELECT":
            requested_camera = str(data.get("camera", "front")).lower()
            runtime_context["active_camera"] = requested_camera if requested_camera in {"front", "left", "right"} else "front"
        elif command == "SPEED_PROFILE":
            runtime_context["speed_profile"] = str(data.get("profile", "MEDIUM")).upper()
        elif command == "ACRO":
            runtime_context["control_profile"] = "ACRO"
            run_acro(str(data.get("sequence", "SPIN")).upper())

    def apply_manual_move(direction: str, speed: int) -> None:
        if direction == "forward":
            motor_controller.move_forward(speed)
        elif direction == "backward":
            motor_controller.move_backward(speed)
        elif direction == "left":
            motor_controller.turn_left(speed)
        elif direction == "right":
            motor_controller.turn_right(speed)
        else:
            motor_controller.stop()

    def run_acro(sequence: str) -> None:
        if sequence == "SPIN":
            motor_controller.turn_left(min(settings.patrol_speed + 20, 100))
            time.sleep(0.8)
            motor_controller.stop()
            return
        motor_controller.move_forward(settings.patrol_speed)
        time.sleep(0.25)
        motor_controller.turn_right(settings.patrol_speed)
        time.sleep(0.35)
        motor_controller.move_backward(settings.patrol_speed)
        time.sleep(0.25)
        motor_controller.stop()

    command_listener = CommandListener(settings, on_command, shutdown_event)

    status_thread = threading.Thread(target=status_sender, name="status-sender", daemon=True)
    status_thread.start()
    command_listener.start()

    try:
        while not shutdown_event.is_set():
            snapshot = state_machine.snapshot()

            if snapshot.state == RobotState.IDLE:
                motor_controller.stop()
                set_stream_enabled(False)
                led_handler.set_idle()

            elif snapshot.state == RobotState.MANUAL:
                set_stream_enabled(True)

            elif snapshot.state == RobotState.FOLLOW_LINE:
                set_stream_enabled(False)
                obstacle_distance = obstacle_detector.get_distance_cm()
                runtime_context["last_obstacle_distance_cm"] = obstacle_distance
                runtime_context["obstacle_detected"] = obstacle_distance < settings.obstacle_distance_cm
                if runtime_context["obstacle_detected"]:
                    runtime_context["obstacle_count"] += 1
                    motor_controller.stop()
                    lcd_handler.show_message("Obstaculo", "Detectado")
                    buzzer_handler.alert()
                    time.sleep(2)
                    motor_controller.turn_right(settings.patrol_speed)
                    time.sleep(0.5)
                    motor_controller.stop()
                else:
                    line_follower.follow_line(settings.patrol_speed)
                    if line_follower.is_line_lost():
                        motor_controller.stop()
                        lcd_handler.show_message("Linea perdida", "Detenido")
                        time.sleep(0.5)
                    frame = camera.capture_frame("front")
                    plant_qr = detect_qr(frame)
                    if plant_qr:
                        state_machine.qr_detected(plant_qr)

            elif snapshot.state == RobotState.QR_DETECTED:
                motor_controller.stop()
                lcd_handler.show_message("QR detectado", snapshot.current_plant_qr or "")
                led_handler.set_attention()
                state_machine.begin_capture()

            elif snapshot.state == RobotState.CAPTURING:
                runtime_context["captured_frames"] = camera.capture_burst(settings.capture_count)
                runtime_context["last_capture_count"] = len(runtime_context["captured_frames"])
                runtime_context["last_local_analysis"] = None
                lcd_handler.show_message("Capturando", "F L R")
                if settings.local_ai_enabled and local_ai_available:
                    state_machine.begin_classification()
                else:
                    state_machine.begin_sending()

            elif snapshot.state == RobotState.CLASSIFYING:
                result = classify_burst(
                    runtime_context.get("captured_frames", []),
                    interpreter,
                    input_details,
                    output_details,
                    settings,
                )
                runtime_context["last_local_analysis"] = {
                    "source": "robot-pi",
                    "modelPath": settings.model_path,
                    "className": result["class"],
                    "confidence": float(result["confidence"]),
                    "rawScores": result["raw_scores"],
                }
                lcd_handler.show_result(result["class"], float(result["confidence"]))
                if result["class"] == "sano":
                    led_handler.set_healthy()
                elif result["class"] == "peligro":
                    led_handler.set_danger()
                    buzzer_handler.alert()
                else:
                    led_handler.set_attention()
                state_machine.begin_sending()

            elif snapshot.state == RobotState.SENDING:
                frames = runtime_context.get("captured_frames", [])
                payload = build_observation_payload(snapshot, frames)
                runtime_context["last_observation_status"] = "sending"
                for _ in range(settings.observation_retry_count):
                    if backend_client.send_observation(payload):
                        runtime_context["last_observation_status"] = "sent"
                        runtime_context["last_observation_at"] = payload["observedAt"]
                        break
                    runtime_context["last_observation_status"] = "retrying"
                    time.sleep(1)
                else:
                    runtime_context["last_observation_status"] = "failed"
                state_machine.resume_follow_line()

            time.sleep(0.05)
    except KeyboardInterrupt:
        LOGGER.info("KeyboardInterrupt received")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
