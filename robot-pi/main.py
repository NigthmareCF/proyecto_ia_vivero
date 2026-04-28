from __future__ import annotations

import logging
import os
import queue
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
from src.communication.offline_queue import OfflineObservationQueue
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
    os.makedirs(settings.offline_queue_dir, exist_ok=True)

    shutdown_event = threading.Event()
    state_machine = RobotStateMachine()
    backend_client = BackendClient(settings)
    camera = CameraHandler(settings)
    offline_queue = OfflineObservationQueue(settings.offline_queue_dir)
    observation_events: queue.Queue[dict[str, Any]] = queue.Queue()
    interpreter = None
    input_details = None
    output_details = None
    if settings.local_ai_enabled:
        interpreter, input_details, output_details = load_model(settings)

    command_listener: CommandListener | None = None
    local_ai_available = all(item is not None for item in (interpreter, input_details, output_details))
    runtime_context: dict[str, Any] = {
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
        "recent_qr_detected_at": {},
        "last_stream_frame_at": None,
        "target_plant_qr": None,
        "awaiting_patrol_approval": False,
    }
    stream_sender = StreamSender(
        settings,
        lambda: camera.capture_frame(str(runtime_context["active_camera"])),
        lambda: str(runtime_context["active_camera"]),
    )

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

    def current_queue_depth() -> int:
        return offline_queue.size() + observation_events.qsize()

    def get_connection_quality() -> str:
        if runtime_context["last_observation_status"] == "failed":
            return "DEGRADED"
        if runtime_context["last_observation_status"] in {"retrying", "queued"}:
            return "UNSTABLE"
        return "GOOD"

    def map_state_to_mode(state: RobotState) -> str:
        if state == RobotState.IDLE:
            return "IDLE"
        if state == RobotState.MANUAL:
            return "MANUAL"
        if runtime_context["target_plant_qr"]:
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
            "queueDepth": current_queue_depth(),
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
            "queueDepth": health["queueDepth"],
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
            if encoded:
                encoded_images.append(encoded)
        return encoded_images

    def build_observation_payload(snapshot: Any, plant_qr: str, frames: list[np.ndarray]) -> dict[str, Any]:
        local_analysis = runtime_context.get("last_local_analysis")
        status_hint = "PENDING_BACKEND_ANALYSIS"
        if isinstance(local_analysis, dict) and local_analysis.get("className"):
            status_hint = str(local_analysis["className"])
        return {
            "patrolId": snapshot.patrol_id or "manual-patrol",
            "plantQr": plant_qr or "UNKNOWN",
            "captureReason": "QR_IN_MOTION",
            "statusHint": status_hint,
            "observedAt": datetime.now().isoformat(),
            "mimeType": "image/jpeg",
            "imagesBase64": encode_observation_images(frames),
        }

    def persist_observation(payload: dict) -> bool:
        runtime_context["last_observation_status"] = "sending"
        for _ in range(settings.observation_retry_count):
            if backend_client.send_observation(payload):
                runtime_context["last_observation_status"] = "sent"
                runtime_context["last_observation_at"] = payload["observedAt"]
                return True
            runtime_context["last_observation_status"] = "retrying"
            time.sleep(1)
        runtime_context["last_observation_status"] = "queued"
        offline_queue.enqueue(payload)
        return False

    def process_observation_event(event: dict[str, Any]) -> None:
        snapshot = state_machine.snapshot()
        frames = event["frames"]
        if settings.local_ai_enabled and local_ai_available:
            result = classify_burst(
                frames,
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
            if result["class"] == "sano":
                led_handler.set_healthy()
            elif result["class"] == "peligro":
                led_handler.set_danger()
            else:
                led_handler.set_attention()
        else:
            runtime_context["last_local_analysis"] = None
            led_handler.set_attention()

        payload = build_observation_payload(snapshot, event["plant_qr"], frames)
        runtime_context["last_capture_count"] = len(frames)
        persist_observation(payload)

    def observation_worker() -> None:
        while not shutdown_event.is_set():
            try:
                event = observation_events.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                process_observation_event(event)
            except Exception as exc:
                LOGGER.warning("Observation worker failed: %s", exc)
                payload = {
                    "patrolId": state_machine.snapshot().patrol_id or "manual-patrol",
                    "plantQr": event.get("plant_qr", "UNKNOWN"),
                    "captureReason": "QR_IN_MOTION",
                    "statusHint": "PROCESSING_ERROR",
                    "observedAt": datetime.now().isoformat(),
                    "mimeType": "image/jpeg",
                    "imagesBase64": encode_observation_images(event.get("frames", [])),
                }
                offline_queue.enqueue(payload)
                runtime_context["last_observation_status"] = "queued"
            finally:
                observation_events.task_done()

    def offline_flush_worker() -> None:
        while not shutdown_event.is_set():
            pending = offline_queue.peek_oldest()
            if pending is None:
                shutdown_event.wait(settings.observation_flush_interval_seconds)
                continue
            entry_id, payload = pending
            try:
                if backend_client.send_observation(payload):
                    offline_queue.remove(entry_id)
                    runtime_context["last_observation_status"] = "sent"
                    runtime_context["last_observation_at"] = payload.get("observedAt")
                else:
                    runtime_context["last_observation_status"] = "retrying"
            except Exception as exc:
                LOGGER.warning("Offline flush failed: %s", exc)
                runtime_context["last_observation_status"] = "retrying"
            shutdown_event.wait(settings.observation_flush_interval_seconds)

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
    buzzer_handler.jingle()

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
            runtime_context["target_plant_qr"] = None
            runtime_context["awaiting_patrol_approval"] = False
            buzzer_handler.countdown_go()
            lcd_handler.show_state("FOLLOW_LINE")
        elif command == "STOP":
            state_machine.stop()
            motor_controller.stop()
            set_stream_enabled(False)
            runtime_context["control_profile"] = "SAFE_STOP"
            runtime_context["target_plant_qr"] = None
            lcd_handler.show_state("IDLE")
            led_handler.set_idle()
        elif command == "GOTO_PLANT":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            runtime_context["control_profile"] = "GOTO"
            runtime_context["target_plant_qr"] = str(data.get("plantQr") or data.get("targetPlantQr") or "").strip().upper() or None
            runtime_context["awaiting_patrol_approval"] = False
            buzzer_handler.countdown_go()
            lcd_handler.show_message("Buscando", runtime_context["target_plant_qr"] or "QR")
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
        elif command in {"CAMERA_SELECT", "SWITCH_CAMERA"}:
            requested_camera = str(data.get("camera") or data.get("activeCamera") or "front").lower()
            runtime_context["active_camera"] = requested_camera if requested_camera in {"front", "left", "right"} else "front"
        elif command == "SPEED_PROFILE":
            runtime_context["speed_profile"] = str(data.get("profile", "MEDIUM")).upper()
        elif command == "ACRO":
            runtime_context["control_profile"] = "ACRO"
            run_acro(str(data.get("sequence", "SPIN")).upper())
        elif command == "PLANT_STATE_UPDATE":
            state = str(data.get("state", "ATENCION")).upper()
            if state == "SANO":
                led_handler.set_healthy()
            elif state == "PELIGRO":
                led_handler.set_danger()
            else:
                led_handler.set_attention()

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
            buzzer_handler.jingle()
            return
        motor_controller.move_forward(settings.patrol_speed)
        time.sleep(0.25)
        motor_controller.turn_right(settings.patrol_speed)
        time.sleep(0.35)
        motor_controller.move_backward(settings.patrol_speed)
        time.sleep(0.25)
        motor_controller.stop()

    def finish_row_and_wait_for_patrol() -> None:
        runtime_context["awaiting_patrol_approval"] = True
        runtime_context["last_observation_status"] = "awaiting_patrol_approval"
        lcd_handler.show_message("Fin de linea", "Esperando")
        motor_controller.move_forward(settings.patrol_speed)
        time.sleep(settings.end_row_forward_seconds)
        motor_controller.turn_left(settings.patrol_speed)
        time.sleep(settings.end_row_turn_seconds)
        motor_controller.move_forward(settings.patrol_speed)
        max_seek_seconds = 8.0
        started_at = time.monotonic()
        while (time.monotonic() - started_at) < max_seek_seconds and not shutdown_event.is_set():
            if line_follower.has_black_detected():
                break
            motor_controller.move_forward(settings.patrol_speed)
            time.sleep(0.05)
        motor_controller.stop()
        led_handler.set_attention()
        buzzer_handler.countdown_go()
        state_machine.stop()

    def has_reached_target_qr(plant_qr: str) -> bool:
        target = runtime_context["target_plant_qr"]
        return bool(target and plant_qr.strip().upper() == str(target).upper())

    def should_capture_plant(plant_qr: str) -> bool:
        now = time.monotonic()
        last_seen = runtime_context["recent_qr_detected_at"].get(plant_qr)
        if last_seen is not None and (now - last_seen) < settings.qr_detection_cooldown_seconds:
            return False
        runtime_context["recent_qr_detected_at"][plant_qr] = now
        return True

    def enqueue_observation_capture(plant_qr: str) -> None:
        motor_controller.move_forward(settings.qr_capture_speed)
        selected_frames = camera.capture_side_burst(
            max(settings.capture_count, 4),
            settings.burst_frame_interval_seconds,
        )
        observation_events.put({
            "plant_qr": plant_qr,
            "frames": selected_frames,
        })
        runtime_context["last_capture_count"] = len(selected_frames)
        lcd_handler.show_message("QR detectado", plant_qr)

    command_listener = CommandListener(settings, on_command, shutdown_event)

    status_thread = threading.Thread(target=status_sender, name="status-sender", daemon=True)
    observation_thread = threading.Thread(target=observation_worker, name="observation-worker", daemon=True)
    offline_thread = threading.Thread(target=offline_flush_worker, name="offline-flush-worker", daemon=True)
    status_thread.start()
    observation_thread.start()
    offline_thread.start()
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
                if runtime_context["awaiting_patrol_approval"]:
                    motor_controller.stop()
                    time.sleep(0.1)
                    continue
                obstacle_distance = obstacle_detector.get_distance_cm()
                runtime_context["last_obstacle_distance_cm"] = obstacle_distance
                runtime_context["obstacle_detected"] = obstacle_distance < settings.obstacle_distance_cm
                if runtime_context["obstacle_detected"]:
                    runtime_context["obstacle_count"] += 1
                    motor_controller.stop()
                    lcd_handler.show_message("Obstaculo", "Detectado")
                    buzzer_handler.alert()
                    time.sleep(1.5)
                    motor_controller.turn_right(settings.patrol_speed)
                    time.sleep(0.5)
                    motor_controller.stop()
                else:
                    line_follower.follow_line(settings.patrol_speed)
                    if line_follower.is_all_white():
                        finish_row_and_wait_for_patrol()
                        time.sleep(0.1)
                        continue
                    left_frame = camera.capture_frame("left")
                    right_frame = camera.capture_frame("right")
                    plant_qr = detect_qr(left_frame) or detect_qr(right_frame)
                    if plant_qr and should_capture_plant(plant_qr):
                        state_machine.qr_detected(plant_qr)
                        enqueue_observation_capture(plant_qr)
                        if has_reached_target_qr(plant_qr):
                            motor_controller.stop()
                            lcd_handler.show_message("Planta objetivo", plant_qr)
                            led_handler.set_attention()
                            buzzer_handler.alert()
                            runtime_context["last_observation_status"] = "target_found"
                            runtime_context["target_plant_qr"] = None
                            state_machine.stop()
                            time.sleep(0.1)
                            continue
                        state_machine.resume_follow_line()
                    elif line_follower.is_line_lost():
                        motor_controller.stop()
                        lcd_handler.show_message("Linea perdida", "Detenido")
                        time.sleep(0.25)

            time.sleep(0.05)
    except KeyboardInterrupt:
        LOGGER.info("KeyboardInterrupt received")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
