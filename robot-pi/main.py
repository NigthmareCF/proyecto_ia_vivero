from __future__ import annotations

import logging
import signal
import threading
import time
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
    stream_sender = StreamSender(settings, lambda: camera.capture_frame("front"))
    interpreter, input_details, output_details = load_model(settings)
    command_listener: CommandListener | None = None
    runtime_context: dict[str, Any] = {
        "captured_frames": [],
        "last_result": None,
    }

    def cleanup() -> None:
        shutdown_event.set()
        stream_sender.stop_stream()
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
            payload = {
                "robot_id": settings.robot_id,
                "state": snapshot.state.value,
                "battery_level": 100,
                "current_plant_qr": snapshot.current_plant_qr,
                "timestamp": time.time(),
            }
            backend_client.send_status(payload)
            shutdown_event.wait(settings.status_interval_seconds)

    def on_command(command: str, data: dict[str, Any]) -> None:
        LOGGER.info("Received command %s with data %s", command, data)
        if command == "START_PATROL":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            lcd_handler.show_state("FOLLOW_LINE")
        elif command == "STOP":
            state_machine.stop()
            motor_controller.stop()
            stream_sender.stop_stream()
            lcd_handler.show_state("IDLE")
            led_handler.set_idle()
        elif command == "MANUAL_CONTROL":
            state_machine.enable_manual()
            lcd_handler.show_state("MANUAL")
        elif command == "AUTO":
            state_machine.enable_auto()
            stream_sender.stop_stream()
            lcd_handler.show_state("FOLLOW_LINE")
        elif command == "MOVE":
            state_machine.update_manual_move(
                direction=str(data.get("direction", "stop")),
                speed=int(data.get("speed", settings.manual_default_speed)),
            )
            if state_machine.snapshot().state == RobotState.MANUAL:
                apply_manual_move(state_machine.snapshot().manual_direction, state_machine.snapshot().manual_speed)

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

    command_listener = CommandListener(settings, on_command, shutdown_event)

    status_thread = threading.Thread(target=status_sender, name="status-sender", daemon=True)
    status_thread.start()
    command_listener.start()

    try:
        while not shutdown_event.is_set():
            snapshot = state_machine.snapshot()

            if snapshot.state == RobotState.IDLE:
                motor_controller.stop()
                stream_sender.stop_stream()
                led_handler.set_idle()

            elif snapshot.state == RobotState.MANUAL:
                stream_sender.start_stream()

            elif snapshot.state == RobotState.FOLLOW_LINE:
                stream_sender.stop_stream()
                if obstacle_detector.is_obstacle_detected():
                    motor_controller.stop()
                    lcd_handler.show_message("Obstaculo", "Detectado")
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
                runtime_context["captured_frames"] = camera.capture_burst(3)
                lcd_handler.show_message("Capturando", "L F R")
                state_machine.begin_classification()

            elif snapshot.state == RobotState.CLASSIFYING:
                result = classify_burst(
                    runtime_context.get("captured_frames", []),
                    interpreter,
                    input_details,
                    output_details,
                    settings,
                )
                runtime_context["last_result"] = result
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
                result = runtime_context.get("last_result") or {"class": "atencion", "confidence": 0.0}
                encoded = [
                    camera.frame_to_base64(frame)
                    for frame in frames
                    if isinstance(frame, np.ndarray) and frame.size > 0
                ]
                for _ in range(3):
                    if backend_client.send_patrol_result(
                        patrol_id=snapshot.patrol_id or "manual-patrol",
                        plant_qr=snapshot.current_plant_qr or "UNKNOWN",
                        ai_result=str(result["class"]),
                        ai_confidence=float(result["confidence"]),
                        images_base64=encoded,
                    ):
                        break
                    time.sleep(1)
                state_machine.resume_follow_line()

            time.sleep(0.05)
    except KeyboardInterrupt:
        LOGGER.info("KeyboardInterrupt received")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
