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
from src.communication.local_command_listener import LocalCommandListener
from src.communication.offline_queue import OfflineObservationQueue
from src.communication.qr_label_resolver import QrLabelResolver
from src.config import Settings
from src.display import buzzer_handler, lcd_handler, led_handler
from src.navigation import line_follower, motor_controller, obstacle_detector
from src.state_machine import RobotState, RobotStateMachine
from src.vision.camera_handler import CameraHandler
from src.vision.plant_roi import compute_plant_roi, crop_frames_to_roi
from src.vision.qr_detector import detect_qr_candidates
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
    qr_resolution_events: queue.Queue[dict[str, Any]] = queue.Queue()
    qr_label_resolver = QrLabelResolver(
        settings.qr_label_cache_path,
        request_timeout_seconds=settings.qr_label_request_timeout_seconds,
    )
    interpreter = None
    input_details = None
    output_details = None
    if settings.local_ai_enabled:
        interpreter, input_details, output_details = load_model(settings)

    command_listener: CommandListener | None = None
    local_command_listener: LocalCommandListener | None = None
    local_ai_available = all(item is not None for item in (interpreter, input_details, output_details))
    runtime_context: dict[str, Any] = {
        "last_local_analysis": None,
        "last_observation_at": None,
        "last_observation_status": "idle",
        "status_summary": "AgroBot listo",
        "last_capture_count": 0,
        "last_obstacle_distance_cm": None,
        "obstacle_detected": False,
        "obstacle_count": 0,
        "stream_active": False,
        "active_camera": "front",
        "control_profile": "AUTO_LINE",
        "speed_profile": "MEDIUM",
        "custom_speed_percent": None,
        "started_at": time.monotonic(),
        "last_manual_command_at": None,
        "last_watchdog_triggered_at": None,
        "last_watchdog_reason": None,
        "last_heartbeat_at": None,
        "last_heartbeat_status": "idle",
        "rear_obstacle_left": False,
        "rear_obstacle_right": False,
        "rear_obstacle_detected": False,
        "rear_obstacle_latched": False,
        "recent_qr_detected_at": {},
        "last_stream_frame_at": None,
        "last_qr_raw_payload": None,
        "last_qr_resolved_label": None,
        "last_qr_resolution_source": None,
        "last_qr_resolution_ms": None,
        "last_qr_camera": None,
        "last_qr_candidate_order": [],
        "last_qr_roi": None,
        "target_plant_qr": None,
        "target_group_key": None,
        "target_exact_qr_label": None,
        "expected_scan_sequence": None,
        "effective_expected_sequence": None,
        "expected_window_start": None,
        "expected_window_end": None,
        "history_sequence_count": None,
        "search_start_orientation": "FORWARD",
        "history_patrol_id": None,
        "history_operational_date": None,
        "history_neighbor_before": None,
        "history_neighbor_after": None,
        "search_mode": None,
        "search_state": None,
        "search_targets": [],
        "found_state_targets": [],
        "current_scan_sequence": 0,
        "data_crossover_detected": False,
        "data_crossover_message": None,
        "window_mismatch_detected": False,
        "window_mismatch_group_key": None,
        "window_mismatch_exact_qr_label": None,
        "window_mismatch_sequence": None,
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

    def update_heartbeat_led_mode(snapshot: Any) -> None:
        if runtime_context["last_heartbeat_status"] == "failed":
            led_handler.set_heartbeat_fast_blink()
            return
        if snapshot.state == RobotState.IDLE:
            led_handler.set_heartbeat_breathe()
            return
        led_handler.set_heartbeat_blink()

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
        return offline_queue.size() + observation_events.qsize() + qr_resolution_events.qsize()

    def get_connection_quality() -> str:
        if runtime_context["last_heartbeat_status"] == "failed":
            return "DEGRADED"
        if runtime_context["last_heartbeat_status"] in {"retrying", "queued"}:
            return "UNSTABLE"
        if runtime_context["last_observation_status"] == "failed":
            return "DEGRADED"
        if runtime_context["last_observation_status"] in {"retrying", "queued"}:
            return "UNSTABLE"
        return "GOOD"

    def refresh_rear_obstacle_state() -> dict[str, bool]:
        rear_state = obstacle_detector.get_rear_obstacle_state()
        runtime_context["rear_obstacle_left"] = bool(rear_state["left"])
        runtime_context["rear_obstacle_right"] = bool(rear_state["right"])
        runtime_context["rear_obstacle_detected"] = bool(rear_state["left"] or rear_state["right"])
        if not runtime_context["rear_obstacle_detected"]:
            runtime_context["rear_obstacle_latched"] = False
        return rear_state

    def normalize_speed_value(speed: int | float | None, fallback: int) -> int:
        if speed is None:
            return max(0, min(fallback, 100))
        try:
            return max(0, min(int(speed), 100))
        except (TypeError, ValueError):
            return max(0, min(fallback, 100))

    def resolve_speed_profile_percent(profile: str | None) -> int:
        normalized_profile = str(profile or "MEDIUM").strip().upper()
        if normalized_profile.startswith("CUSTOM_"):
            custom_raw = normalized_profile.removeprefix("CUSTOM_")
            try:
                return max(0, min(int(custom_raw), 100))
            except ValueError:
                return settings.speed_profile_medium
        profile_map = {
            "LOW": settings.speed_profile_low,
            "MEDIUM": settings.speed_profile_medium,
            "HIGH": settings.speed_profile_high,
            "TURBO": settings.speed_profile_turbo,
            "CUSTOM": normalize_speed_value(runtime_context["custom_speed_percent"], settings.speed_profile_medium),
        }
        return normalize_speed_value(profile_map.get(normalized_profile, settings.speed_profile_medium), settings.speed_profile_medium)

    def current_speed_percent() -> int:
        return resolve_speed_profile_percent(str(runtime_context["speed_profile"]))

    def set_status_summary(message: str) -> None:
        runtime_context["status_summary"] = message

    def normalize_qr_value(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    def parse_qr_identity(qr_value: str | None) -> dict[str, str | None]:
        normalized = normalize_qr_value(qr_value)
        if not normalized:
            return {"exact": None, "group": None, "side": None, "plant": None, "pot": None}
        parts = normalized.split("_")
        if len(parts) >= 5 and parts[0] == "PLA" and parts[2] == "MA":
            return {
                "exact": normalized,
                "group": f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}",
                "side": parts[4],
                "plant": parts[1],
                "pot": parts[3],
            }
        return {"exact": normalized, "group": normalized, "side": None, "plant": None, "pot": None}

    def display_target_label(group_key: str | None, fallback: str | None = None) -> str:
        identity = parse_qr_identity(group_key or fallback)
        if identity["plant"] and identity["pot"]:
            return f"P{identity['plant']} M{identity['pot']}"
        return str(group_key or fallback or "Sin target")[:16]

    def reset_search_context() -> None:
        runtime_context["target_plant_qr"] = None
        runtime_context["target_group_key"] = None
        runtime_context["target_exact_qr_label"] = None
        runtime_context["expected_scan_sequence"] = None
        runtime_context["effective_expected_sequence"] = None
        runtime_context["expected_window_start"] = None
        runtime_context["expected_window_end"] = None
        runtime_context["history_sequence_count"] = None
        runtime_context["search_start_orientation"] = "FORWARD"
        runtime_context["history_patrol_id"] = None
        runtime_context["history_operational_date"] = None
        runtime_context["history_neighbor_before"] = None
        runtime_context["history_neighbor_after"] = None
        runtime_context["search_mode"] = None
        runtime_context["search_state"] = None
        runtime_context["search_targets"] = []
        runtime_context["found_state_targets"] = []
        runtime_context["current_scan_sequence"] = 0
        runtime_context["data_crossover_detected"] = False
        runtime_context["data_crossover_message"] = None
        runtime_context["window_mismatch_detected"] = False
        runtime_context["window_mismatch_group_key"] = None
        runtime_context["window_mismatch_exact_qr_label"] = None
        runtime_context["window_mismatch_sequence"] = None

    def normalize_search_start_orientation(raw_value: Any) -> str:
        normalized = str(raw_value or "FORWARD").strip().upper()
        return "REVERSE" if normalized == "REVERSE" else "FORWARD"

    def resolve_effective_expected_sequence(
        expected_sequence: Any,
        history_sequence_count: Any,
        search_start_orientation: Any,
    ) -> int | None:
        try:
            expected = int(expected_sequence)
        except (TypeError, ValueError):
            return None
        if normalize_search_start_orientation(search_start_orientation) != "REVERSE":
            return expected
        try:
            history_count = int(history_sequence_count)
        except (TypeError, ValueError):
            return expected
        if history_count <= 0:
            return expected
        return max(history_count - expected + 1, 1)

    def resolve_expected_window_metadata(
        expected_sequence: Any,
        history_sequence_count: Any,
        search_start_orientation: Any,
    ) -> dict[str, int | str | None]:
        effective_expected = resolve_effective_expected_sequence(
            expected_sequence,
            history_sequence_count,
            search_start_orientation,
        )
        if not isinstance(effective_expected, int):
            return {
                "effectiveExpectedSequence": None,
                "effectiveWindowStart": None,
                "effectiveWindowEnd": None,
                "searchStartOrientation": normalize_search_start_orientation(search_start_orientation),
            }
        tolerance = max(settings.search_history_tolerance_scans, 0)
        return {
            "effectiveExpectedSequence": effective_expected,
            "effectiveWindowStart": max(effective_expected - tolerance, 1),
            "effectiveWindowEnd": effective_expected + tolerance,
            "searchStartOrientation": normalize_search_start_orientation(search_start_orientation),
        }

    def resolve_state_signal(state: str | None) -> None:
        normalized_state = str(state or "").upper()
        if normalized_state == "SANO":
            led_handler.set_healthy()
        elif normalized_state == "PELIGRO":
            led_handler.set_danger()
        else:
            led_handler.set_attention()

    def resolve_search_targets(raw_targets: Any, default_orientation: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_targets, list):
            return []
        normalized_targets: list[dict[str, Any]] = []
        for item in raw_targets:
            if not isinstance(item, dict):
                continue
            identity = parse_qr_identity(item.get("groupKey") or item.get("exactQrLabel"))
            window_metadata = resolve_expected_window_metadata(
                item.get("expectedScanSequence"),
                item.get("historySequenceCount"),
                item.get("searchStartOrientation") or default_orientation,
            )
            normalized_targets.append({
                "groupKey": identity["group"],
                "exactQrLabel": normalize_qr_value(item.get("exactQrLabel")),
                "expectedScanSequence": item.get("expectedScanSequence"),
                "historySequenceCount": item.get("historySequenceCount"),
                "searchStartOrientation": window_metadata["searchStartOrientation"],
                "effectiveExpectedSequence": window_metadata["effectiveExpectedSequence"],
                "effectiveWindowStart": window_metadata["effectiveWindowStart"],
                "effectiveWindowEnd": window_metadata["effectiveWindowEnd"],
                "operationalDate": item.get("operationalDate"),
                "patrolId": item.get("patrolId"),
                "found": False,
            })
        return normalized_targets

    def refresh_lcd_rotation(snapshot: Any) -> None:
        activity = "Sin patrullaje"
        mode = f"Modo {map_state_to_mode(snapshot.state)}"
        screens: list[tuple[str, str]] = []

        if snapshot.state == RobotState.IDLE:
            screens = [
                ("AgroBot listo", "Esperando orden"),
                ("Modo reposo", "Sin patrullaje"),
            ]
        elif runtime_context["search_mode"] == "TARGET":
            target_label = display_target_label(runtime_context["target_group_key"], runtime_context["target_exact_qr_label"])
            screens = [
                ("Buscando planta", target_label),
                ("Modo AUTO", "Busqueda ON"),
                ("Historial+QR", f"{runtime_context['expected_window_start'] or '--'}-{runtime_context['expected_window_end'] or '--'}"),
            ]
        elif runtime_context["search_mode"] == "STATE":
            pending = sum(1 for item in runtime_context["search_targets"] if not item.get("found"))
            state_label = str(runtime_context["search_state"] or "ATENCION").upper()[:16]
            screens = [
                (f"{state_label} buscando", f"Pend: {pending:02d}"),
                ("Modo AUTO", "Patrullaje ON"),
                ("AgroBot listo", "Patrullaje ON"),
            ]
        elif snapshot.state == RobotState.MANUAL:
            screens = [
                ("Modo MANUAL", "Control remoto"),
                ("AgroBot listo", "Manejo activo"),
            ]
        elif snapshot.state == RobotState.FOLLOW_LINE:
            activity = "Patrullaje ON"
            screens = [
                ("AgroBot listo", activity),
                (mode, activity),
                ("Escaneo QR", snapshot.patrol_id or "manual-patrol"),
            ]
        else:
            screens = [("AgroBot listo", runtime_context["status_summary"][:16])]

        lcd_handler.set_rotation_screens(screens, interval_seconds=settings.lcd_rotation_interval_seconds)

    def register_scan_sequence() -> int:
        runtime_context["current_scan_sequence"] = int(runtime_context["current_scan_sequence"]) + 1
        return int(runtime_context["current_scan_sequence"])

    def is_outside_expected_window(found_sequence: int) -> bool:
        start = runtime_context["expected_window_start"]
        end = runtime_context["expected_window_end"]
        if not isinstance(start, int) or not isinstance(end, int):
            return False
        return found_sequence < start or found_sequence > end

    def observe_target_window_mismatch(detected_group_key: str | None, detected_exact_label: str | None, found_sequence: int) -> None:
        target_group_key = runtime_context["target_group_key"]
        start = runtime_context["expected_window_start"]
        end = runtime_context["expected_window_end"]
        if not target_group_key or not isinstance(start, int) or not isinstance(end, int):
            return
        if found_sequence < start or found_sequence > end:
            return
        if detected_group_key == target_group_key:
            return
        if runtime_context["window_mismatch_detected"]:
            return
        runtime_context["window_mismatch_detected"] = True
        runtime_context["window_mismatch_group_key"] = detected_group_key
        runtime_context["window_mismatch_exact_qr_label"] = detected_exact_label
        runtime_context["window_mismatch_sequence"] = found_sequence
        set_status_summary("Ventana historica no coincide")

    def build_crossover_reason(found_qr: str, found_sequence: int) -> str:
        expected_sequence = runtime_context["expected_scan_sequence"]
        mismatch_group_key = runtime_context["window_mismatch_group_key"]
        mismatch_sequence = runtime_context["window_mismatch_sequence"]
        if runtime_context["window_mismatch_detected"] and mismatch_group_key:
            return (
                f"DATA_CROSSOVER:target={runtime_context['target_group_key']}:expected={expected_sequence}:"
                f"effective={runtime_context['effective_expected_sequence']}:orientation={runtime_context['search_start_orientation']}:"
                f"windowMismatch={mismatch_group_key}@{mismatch_sequence}:found={found_qr}@{found_sequence}"
            )
        return (
            f"DATA_CROSSOVER:target={runtime_context['target_group_key']}:expected={expected_sequence}:"
            f"effective={runtime_context['effective_expected_sequence']}:orientation={runtime_context['search_start_orientation']}:"
            f"found={found_qr}@{found_sequence}"
        )

    def trigger_data_crossover(found_qr: str, found_sequence: int) -> None:
        runtime_context["data_crossover_detected"] = True
        runtime_context["data_crossover_message"] = "Cruce de datos en vivero fisico"
        runtime_context["last_observation_status"] = "data_crossover"
        set_status_summary("Cruce de datos en vivero fisico")
        motor_controller.stop()
        led_handler.set_danger()
        buzzer_handler.alert()
        lcd_handler.show_temporary_message("Cruce datos", "Rev vivero", duration_seconds=6.0)
        runtime_context["last_watchdog_triggered_at"] = datetime.now().isoformat()
        runtime_context["last_watchdog_reason"] = build_crossover_reason(found_qr, found_sequence)

    def finish_target_search(found_qr: str, found_sequence: int) -> None:
        target_label = display_target_label(runtime_context["target_group_key"], found_qr)
        if is_outside_expected_window(found_sequence):
            trigger_data_crossover(found_qr, found_sequence)
        else:
            runtime_context["last_observation_status"] = "target_found"
            set_status_summary(f"Objetivo hallado: {target_label}")
            motor_controller.stop()
            led_handler.set_attention()
            buzzer_handler.alert()
            lcd_handler.show_temporary_message("Objetivo hallado", target_label, duration_seconds=5.0)
        reset_search_context()
        state_machine.stop()

    def handle_state_search_hit(found_qr: str) -> None:
        detected_group_key = parse_qr_identity(found_qr)["group"]
        for target in runtime_context["search_targets"]:
            if not target.get("found") and target.get("groupKey") == detected_group_key:
                target["found"] = True
                runtime_context["found_state_targets"].append(detected_group_key)
                state_label = str(runtime_context["search_state"] or "ATENCION").upper()
                set_status_summary(f"{state_label} hallado: {detected_group_key}")
                resolve_state_signal(state_label)
                buzzer_handler.alert()
                lcd_handler.show_temporary_message(f"{state_label} hallado", display_target_label(detected_group_key, found_qr), duration_seconds=4.0)
                motor_controller.stop()
                time.sleep(settings.state_search_pause_seconds)
                break

        if runtime_context["search_targets"] and all(item.get("found") for item in runtime_context["search_targets"]):
            set_status_summary("Busqueda por estado completada")
            reset_search_context()
            state_machine.stop()

    def evaluate_search_detection(plant_qr: str, found_sequence: int) -> None:
        detected = parse_qr_identity(plant_qr)
        detected_group_key = detected["group"]
        detected_exact_label = detected["exact"]

        if runtime_context["search_mode"] == "TARGET":
            target_group_key = runtime_context["target_group_key"]
            target_exact_qr_label = runtime_context["target_exact_qr_label"]
            if target_exact_qr_label and detected_exact_label == target_exact_qr_label:
                finish_target_search(plant_qr, found_sequence)
                return
            if target_group_key and detected_group_key == target_group_key:
                finish_target_search(plant_qr, found_sequence)
                return
            observe_target_window_mismatch(detected_group_key, detected_exact_label, found_sequence)

        if runtime_context["search_mode"] == "STATE":
            target_groups = {item.get("groupKey") for item in runtime_context["search_targets"] if not item.get("found")}
            if detected_group_key in target_groups:
                handle_state_search_hit(plant_qr)

    def map_state_to_mode(state: RobotState) -> str:
        if state == RobotState.IDLE:
            return "IDLE"
        if state == RobotState.MANUAL:
            return "MANUAL"
        if runtime_context["target_plant_qr"]:
            return "GOTO"
        return "AUTO"

    def build_robot_health(snapshot: Any) -> dict[str, Any]:
        last_manual_command_at = runtime_context["last_manual_command_at"]
        manual_command_age_seconds = None
        if isinstance(last_manual_command_at, (int, float)):
            manual_command_age_seconds = round(max(time.monotonic() - last_manual_command_at, 0.0), 3)
        return {
            "batteryLevel": get_battery_level(),
            "temperatureCelsius": get_cpu_temperature_c(),
            "cpuUsagePercent": get_cpu_usage_percent(),
            "connectionQuality": get_connection_quality(),
            "uptimeSeconds": round(time.monotonic() - runtime_context["started_at"], 1),
            "streamActive": bool(runtime_context["stream_active"]),
            "manualDirection": snapshot.manual_direction,
            "manualSpeed": snapshot.manual_speed,
            "currentSpeedPercent": current_speed_percent(),
            "manualCommandAgeSeconds": manual_command_age_seconds,
            "manualCommandTimeoutSeconds": settings.manual_command_timeout_seconds,
            "lastWatchdogTriggeredAt": runtime_context["last_watchdog_triggered_at"],
            "lastWatchdogReason": runtime_context["last_watchdog_reason"],
            "obstacleDetected": bool(runtime_context["obstacle_detected"]),
            "obstacleDistanceCm": runtime_context["last_obstacle_distance_cm"],
            "obstacleCount": int(runtime_context["obstacle_count"]),
            "rearObstacleLeft": bool(runtime_context["rear_obstacle_left"]),
            "rearObstacleRight": bool(runtime_context["rear_obstacle_right"]),
            "rearObstacleDetected": bool(runtime_context["rear_obstacle_detected"]),
            "lastObservationAt": runtime_context["last_observation_at"],
            "lastObservationStatus": runtime_context["last_observation_status"],
            "lastHeartbeatAt": runtime_context["last_heartbeat_at"],
            "lastHeartbeatStatus": runtime_context["last_heartbeat_status"],
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
            "lastQrCamera": runtime_context["last_qr_camera"],
            "lastQrRoi": runtime_context["last_qr_roi"],
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
            "statusSummary": runtime_context["status_summary"] or runtime_context["last_observation_status"],
            "manualCommandAgeSeconds": health["manualCommandAgeSeconds"],
            "manualCommandTimeoutSeconds": health["manualCommandTimeoutSeconds"],
            "currentSpeedPercent": health["currentSpeedPercent"],
            "lastWatchdogTriggeredAt": health["lastWatchdogTriggeredAt"],
            "lastWatchdogReason": health["lastWatchdogReason"],
            "rearObstacleLeft": health["rearObstacleLeft"],
            "rearObstacleRight": health["rearObstacleRight"],
            "rearObstacleDetected": health["rearObstacleDetected"],
            "lastHeartbeatAt": health["lastHeartbeatAt"],
            "lastHeartbeatStatus": health["lastHeartbeatStatus"],
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

    def build_observation_payload(snapshot: Any, plant_qr: str, frames: list[np.ndarray], patrol_id: str | None = None) -> dict[str, Any]:
        local_analysis = runtime_context.get("last_local_analysis")
        status_hint = "PENDING_BACKEND_ANALYSIS"
        if isinstance(local_analysis, dict) and local_analysis.get("className"):
            status_hint = str(local_analysis["className"])
        return {
            "patrolId": patrol_id or snapshot.patrol_id or "manual-patrol",
            "plantQr": plant_qr or "UNKNOWN",
            "captureReason": "QR_IN_MOTION",
            "statusHint": status_hint,
            "observedAt": datetime.now().isoformat(),
            "mimeType": "image/jpeg",
            "imagesBase64": encode_observation_images(frames),
        }

    def queue_qr_resolution(
        raw_payload: str,
        found_sequence: int,
        frames: list[np.ndarray],
        capture_enabled: bool,
        search_mode: str | None,
        patrol_id: str | None,
    ) -> None:
        qr_resolution_events.put({
            "raw_payload": raw_payload,
            "found_sequence": found_sequence,
            "frames": frames,
            "capture_enabled": capture_enabled,
            "search_mode": search_mode,
            "patrol_id": patrol_id,
            "detected_at": time.time(),
        })

    def process_resolved_qr_label(result: dict[str, Any], event: dict[str, Any]) -> None:
        resolved_label = str(result.get("resolvedLabel") or event["raw_payload"]).upper()
        runtime_context["last_qr_raw_payload"] = event["raw_payload"]
        runtime_context["last_qr_resolved_label"] = resolved_label
        runtime_context["last_qr_resolution_source"] = result.get("resolutionSource")
        runtime_context["last_qr_resolution_ms"] = result.get("latencyMs")
        state_machine.qr_detected(resolved_label)

        if event.get("capture_enabled"):
            observation_events.put({
                "plant_qr": resolved_label,
                "frames": event.get("frames", []),
                "patrol_id": event.get("patrol_id"),
            })
            runtime_context["last_capture_count"] = len(event.get("frames", []))

        if event.get("search_mode") in {"TARGET", "STATE"}:
            evaluate_search_detection(resolved_label, int(event["found_sequence"]))
            return

        set_status_summary(f"QR etiquetado: {display_target_label(parse_qr_identity(resolved_label)['group'], resolved_label)}")

    def qr_resolution_worker() -> None:
        while not shutdown_event.is_set():
            try:
                event = qr_resolution_events.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                result = qr_label_resolver.resolve(event.get("raw_payload"))
                process_resolved_qr_label(result, event)
            except Exception as exc:
                LOGGER.warning("QR label resolution failed: %s", exc)
                fallback_result = {
                    "resolvedLabel": str(event.get("raw_payload") or "UNKNOWN").upper(),
                    "resolutionSource": "resolver_error",
                    "latencyMs": None,
                }
                process_resolved_qr_label(fallback_result, event)
            finally:
                qr_resolution_events.task_done()

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

        payload = build_observation_payload(snapshot, event["plant_qr"], frames, patrol_id=event.get("patrol_id"))
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
        if local_command_listener is not None:
            local_command_listener.stop()
        camera.release()
        motor_controller.stop()
        lcd_handler.cleanup()
        led_handler.cleanup()
        buzzer_handler.cleanup()
        motor_controller.cleanup()

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

    lcd_handler.set_rotation_screens([("AgroBot listo", "Esperando orden"), ("Modo reposo", "Sin patrullaje")], interval_seconds=settings.lcd_rotation_interval_seconds)
    led_handler.set_idle()
    led_handler.set_heartbeat_breathe()
    buzzer_handler.jingle()

    def status_sender() -> None:
        while not shutdown_event.is_set():
            snapshot = state_machine.snapshot()
            refresh_rear_obstacle_state()
            if backend_client.send_heartbeat(build_heartbeat(snapshot)):
                runtime_context["last_heartbeat_status"] = "sent"
                runtime_context["last_heartbeat_at"] = datetime.now().isoformat()
            else:
                runtime_context["last_heartbeat_status"] = "failed"
            update_heartbeat_led_mode(snapshot)
            shutdown_event.wait(settings.status_interval_seconds)

    def on_command(command: str, data: dict[str, Any]) -> None:
        LOGGER.info("Received command %s with data %s", command, data)
        if command == "START_PATROL":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            runtime_context["control_profile"] = "AUTO_LINE"
            reset_search_context()
            runtime_context["awaiting_patrol_approval"] = False
            set_status_summary("Patrullaje ON")
            buzzer_handler.countdown_go()
            lcd_handler.show_temporary_message("AgroBot listo", "Patrullaje ON", duration_seconds=3.0)
        elif command == "STOP":
            led_handler.stop_acro_sequence()
            state_machine.stop()
            motor_controller.stop()
            set_stream_enabled(False)
            runtime_context["control_profile"] = "SAFE_STOP"
            reset_search_context()
            runtime_context["last_manual_command_at"] = None
            set_status_summary("AgroBot listo")
            lcd_handler.show_temporary_message("AgroBot listo", "Esperando orden", duration_seconds=3.0)
            led_handler.set_idle()
            led_handler.set_heartbeat_breathe()
        elif command == "GOTO_PLANT":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            runtime_context["control_profile"] = "GOTO"
            target_value = normalize_qr_value(data.get("groupKey") or data.get("plantQr") or data.get("targetPlantQr"))
            identity = parse_qr_identity(target_value)
            runtime_context["target_plant_qr"] = target_value
            runtime_context["target_group_key"] = identity["group"]
            runtime_context["target_exact_qr_label"] = normalize_qr_value(data.get("exactQrLabel")) if data.get("exactQrLabel") else identity["exact"]
            runtime_context["expected_scan_sequence"] = int(data.get("expectedScanSequence")) if data.get("expectedScanSequence") is not None else None
            runtime_context["history_sequence_count"] = int(data.get("historySequenceCount")) if data.get("historySequenceCount") is not None else None
            runtime_context["search_start_orientation"] = normalize_search_start_orientation(data.get("searchStartOrientation"))
            window_metadata = resolve_expected_window_metadata(
                runtime_context["expected_scan_sequence"],
                runtime_context["history_sequence_count"],
                runtime_context["search_start_orientation"],
            )
            runtime_context["effective_expected_sequence"] = window_metadata["effectiveExpectedSequence"]
            runtime_context["expected_window_start"] = window_metadata["effectiveWindowStart"]
            runtime_context["expected_window_end"] = window_metadata["effectiveWindowEnd"]
            runtime_context["history_patrol_id"] = data.get("historyPatrolId")
            runtime_context["history_operational_date"] = data.get("operationalDate")
            runtime_context["history_neighbor_before"] = {
                "groupKey": normalize_qr_value(data.get("neighborBeforeGroupKey")),
                "exactQrLabel": normalize_qr_value(data.get("neighborBeforeExactQrLabel")),
                "sequence": int(data.get("neighborBeforeSequence")) if data.get("neighborBeforeSequence") is not None else None,
            } if data.get("neighborBeforeGroupKey") or data.get("neighborBeforeExactQrLabel") else None
            runtime_context["history_neighbor_after"] = {
                "groupKey": normalize_qr_value(data.get("neighborAfterGroupKey")),
                "exactQrLabel": normalize_qr_value(data.get("neighborAfterExactQrLabel")),
                "sequence": int(data.get("neighborAfterSequence")) if data.get("neighborAfterSequence") is not None else None,
            } if data.get("neighborAfterGroupKey") or data.get("neighborAfterExactQrLabel") else None
            runtime_context["search_mode"] = "TARGET"
            runtime_context["current_scan_sequence"] = 0
            runtime_context["data_crossover_detected"] = False
            runtime_context["data_crossover_message"] = None
            runtime_context["window_mismatch_detected"] = False
            runtime_context["window_mismatch_group_key"] = None
            runtime_context["window_mismatch_exact_qr_label"] = None
            runtime_context["window_mismatch_sequence"] = None
            runtime_context["awaiting_patrol_approval"] = False
            set_status_summary(f"Buscando {display_target_label(runtime_context['target_group_key'], runtime_context['target_exact_qr_label'])}")
            buzzer_handler.countdown_go()
            lcd_handler.show_temporary_message("Buscando planta", display_target_label(runtime_context["target_group_key"], runtime_context["target_exact_qr_label"]), duration_seconds=4.0)
        elif command == "SEARCH_BY_STATE":
            state_machine.start_patrol(str(data.get("patrol_id") or "manual-patrol"))
            runtime_context["control_profile"] = "SEARCH_BY_STATE"
            runtime_context["search_mode"] = "STATE"
            runtime_context["search_state"] = str(data.get("state") or "ATENCION").upper()
            runtime_context["search_start_orientation"] = normalize_search_start_orientation(data.get("searchStartOrientation"))
            runtime_context["search_targets"] = resolve_search_targets(data.get("targets"), runtime_context["search_start_orientation"])
            runtime_context["found_state_targets"] = []
            runtime_context["current_scan_sequence"] = 0
            runtime_context["awaiting_patrol_approval"] = False
            set_status_summary(f"{runtime_context['search_state']} buscando")
            resolve_state_signal(runtime_context["search_state"])
            buzzer_handler.countdown_go()
            lcd_handler.show_temporary_message(f"{runtime_context['search_state']} buscando", f"Pend: {len(runtime_context['search_targets']):02d}", duration_seconds=4.0)
        elif command == "MANUAL_CONTROL":
            led_handler.stop_acro_sequence()
            state_machine.enable_manual()
            runtime_context["control_profile"] = "MANUAL_FREE"
            runtime_context["last_manual_command_at"] = time.monotonic()
            set_status_summary("Control manual activo")
            lcd_handler.show_temporary_message("Modo MANUAL", "Control remoto", duration_seconds=3.0)
        elif command == "AUTO":
            led_handler.stop_acro_sequence()
            state_machine.enable_auto()
            set_stream_enabled(False)
            runtime_context["control_profile"] = "AUTO_LINE"
            runtime_context["last_manual_command_at"] = None
            set_status_summary("Patrullaje ON")
            lcd_handler.show_temporary_message("Modo AUTO", "Patrullaje ON", duration_seconds=3.0)
        elif command == "MOVE":
            requested_speed = normalize_speed_value(data.get("speed"), current_speed_percent())
            if state_machine.snapshot().state != RobotState.MANUAL:
                state_machine.enable_manual()
                runtime_context["control_profile"] = "MANUAL_FREE"
            state_machine.update_manual_move(
                direction=str(data.get("direction", "stop")),
                speed=requested_speed,
            )
            runtime_context["last_manual_command_at"] = time.monotonic()
            apply_manual_move(state_machine.snapshot().manual_direction, state_machine.snapshot().manual_speed)
        elif command in {"CAMERA_SELECT", "SWITCH_CAMERA"}:
            requested_camera = str(data.get("camera") or data.get("activeCamera") or "front").lower()
            runtime_context["active_camera"] = requested_camera if requested_camera in {"front", "left", "right"} else "front"
        elif command == "SPEED_PROFILE":
            raw_profile = str(data.get("profile", "MEDIUM")).strip().upper()
            if raw_profile.startswith("CUSTOM_"):
                runtime_context["custom_speed_percent"] = resolve_speed_profile_percent(raw_profile)
                runtime_context["speed_profile"] = "CUSTOM"
            else:
                runtime_context["speed_profile"] = raw_profile or "MEDIUM"
        elif command == "ACRO":
            runtime_context["control_profile"] = "ACRO"
            runtime_context["last_manual_command_at"] = None
            set_status_summary("Acrobacia en ejecucion")
            run_acro(str(data.get("sequence", "SPIN")).upper())
        elif command == "PLANT_STATE_UPDATE":
            state = str(data.get("state", "ATENCION")).upper()
            resolve_state_signal(state)
            set_status_summary(f"Estado {state}")

    def apply_manual_move(direction: str, speed: int) -> None:
        normalized_direction = direction.strip().lower().replace("-", "_").replace(" ", "_")
        direction_aliases = {
            "up": "forward",
            "down": "backward",
            "forward_left": "forward_left",
            "left_forward": "forward_left",
            "forward_right": "forward_right",
            "right_forward": "forward_right",
            "backward_left": "backward_left",
            "left_backward": "backward_left",
            "reverse_left": "backward_left",
            "left_reverse": "backward_left",
            "backward_right": "backward_right",
            "right_backward": "backward_right",
            "reverse_right": "backward_right",
            "right_reverse": "backward_right",
        }
        normalized_direction = direction_aliases.get(normalized_direction, normalized_direction)
        if normalized_direction == "forward":
            motor_controller.move_forward(speed)
        elif normalized_direction == "backward":
            if is_reverse_motion_blocked():
                state_machine.update_manual_move("stop", 0)
                return
            motor_controller.move_backward(speed)
        elif normalized_direction == "left":
            motor_controller.turn_left(speed)
        elif normalized_direction == "right":
            motor_controller.turn_right(speed)
        elif normalized_direction == "forward_left":
            motor_controller.move_forward_left(speed)
        elif normalized_direction == "forward_right":
            motor_controller.move_forward_right(speed)
        elif normalized_direction == "backward_left":
            if is_reverse_motion_blocked():
                state_machine.update_manual_move("stop", 0)
                return
            motor_controller.move_backward_left(speed)
        elif normalized_direction == "backward_right":
            if is_reverse_motion_blocked():
                state_machine.update_manual_move("stop", 0)
                return
            motor_controller.move_backward_right(speed)
        else:
            motor_controller.stop()

    def enforce_manual_watchdog(snapshot: Any) -> None:
        last_manual_command_at = runtime_context["last_manual_command_at"]
        if not isinstance(last_manual_command_at, (int, float)):
            motor_controller.stop()
            return
        if (time.monotonic() - last_manual_command_at) <= settings.manual_command_timeout_seconds:
            return
        if snapshot.manual_direction != "stop" or snapshot.manual_speed != 0:
            LOGGER.warning(
                "Manual watchdog timeout reached after %.2fs; stopping robot",
                settings.manual_command_timeout_seconds,
            )
            state_machine.update_manual_move("stop", 0)
            runtime_context["last_watchdog_triggered_at"] = datetime.now().isoformat()
            runtime_context["last_watchdog_reason"] = "MANUAL_COMMAND_TIMEOUT"
        motor_controller.stop()

    def alert_obstacle_feedback() -> None:
        led_handler.pulse_blue_with(buzzer_handler.beep)

    def is_reverse_motion_blocked() -> bool:
        rear_state = refresh_rear_obstacle_state()
        if not (rear_state["left"] or rear_state["right"]):
            return False
        if not runtime_context["rear_obstacle_latched"]:
            runtime_context["rear_obstacle_latched"] = True
            runtime_context["last_watchdog_triggered_at"] = datetime.now().isoformat()
            runtime_context["last_watchdog_reason"] = "REAR_OBSTACLE_BLOCKED_REVERSE"
            set_status_summary("Obstaculo trasero")
            lcd_handler.show_temporary_message("Obst trasero", "Retroceso no", duration_seconds=4.0)
            alert_obstacle_feedback()
        motor_controller.stop()
        return True

    def run_acro(sequence: str) -> None:
        active_speed = current_speed_percent()
        if sequence in {"CHRISTMAS", "NAVIDAD", "XMAS", "LED_LOOP", "LIGHTS"}:
            motor_controller.stop()
            led_handler.start_acro_christmas_loop()
            lcd_handler.show_temporary_message("Acrobacia", "Luces loop", duration_seconds=3.0)
            return
        led_handler.stop_acro_sequence()
        if sequence == "SPIN":
            motor_controller.turn_left(min(active_speed + 20, 100))
            time.sleep(0.8)
            motor_controller.stop()
            buzzer_handler.jingle()
            return
        motor_controller.move_forward(active_speed)
        time.sleep(0.25)
        motor_controller.turn_right(active_speed)
        time.sleep(0.35)
        if is_reverse_motion_blocked():
            return
        motor_controller.move_backward(active_speed)
        time.sleep(0.25)
        motor_controller.stop()

    def finish_row_and_wait_for_patrol() -> None:
        runtime_context["awaiting_patrol_approval"] = True
        runtime_context["last_observation_status"] = "awaiting_patrol_approval"
        set_status_summary("Fin de linea")
        lcd_handler.show_temporary_message("Fin de linea", "Esperando", duration_seconds=4.0)
        patrol_speed = current_speed_percent()
        motor_controller.move_forward(patrol_speed)
        time.sleep(settings.end_row_forward_seconds)
        motor_controller.turn_left(patrol_speed)
        time.sleep(settings.end_row_turn_seconds)
        motor_controller.move_forward(patrol_speed)
        max_seek_seconds = 8.0
        started_at = time.monotonic()
        while (time.monotonic() - started_at) < max_seek_seconds and not shutdown_event.is_set():
            if line_follower.has_black_detected():
                break
            motor_controller.move_forward(patrol_speed)
            time.sleep(0.05)
        motor_controller.stop()
        led_handler.set_attention()
        buzzer_handler.countdown_go()
        state_machine.stop()

    def has_reached_target_qr(plant_qr: str) -> bool:
        detected = parse_qr_identity(plant_qr)
        target_exact = normalize_qr_value(runtime_context["target_exact_qr_label"] or runtime_context["target_plant_qr"])
        target_group = normalize_qr_value(runtime_context["target_group_key"])
        return bool(
            (target_exact and detected["exact"] == target_exact)
            or (target_group and detected["group"] == target_group)
        )

    def is_qr_detection_fresh(plant_qr: str) -> bool:
        now = time.monotonic()
        last_seen = runtime_context["recent_qr_detected_at"].get(plant_qr)
        return last_seen is not None and (now - last_seen) < settings.qr_detection_cooldown_seconds

    def mark_qr_detection_consumed(plant_qr: str) -> None:
        runtime_context["recent_qr_detected_at"][plant_qr] = time.monotonic()

    def should_capture_plant(plant_qr: str) -> bool:
        if is_qr_detection_fresh(plant_qr):
            return False
        mark_qr_detection_consumed(plant_qr)
        return True

    def order_qr_candidates_for_camera(camera_name: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if camera_name == "left":
            ordered = sorted(candidates, key=lambda item: float(item.get("center_x", 0.0)))
        elif camera_name == "right":
            ordered = sorted(candidates, key=lambda item: float(item.get("center_x", 0.0)), reverse=True)
        else:
            ordered = list(candidates)
        for rank, candidate in enumerate(ordered):
            candidate["camera"] = camera_name
            candidate["camera_rank"] = rank
        return ordered

    def select_qr_candidate(left_frame: np.ndarray | None, right_frame: np.ndarray | None) -> dict[str, Any] | None:
        ordered_candidates: list[dict[str, Any]] = []
        left_candidates = order_qr_candidates_for_camera("left", detect_qr_candidates(left_frame))
        right_candidates = order_qr_candidates_for_camera("right", detect_qr_candidates(right_frame))
        for candidate in left_candidates:
            candidate["detection_frame"] = left_frame
        for candidate in right_candidates:
            candidate["detection_frame"] = right_frame
        ordered_candidates.extend(left_candidates)
        ordered_candidates.extend(right_candidates)

        runtime_context["last_qr_candidate_order"] = [
            f"{str(candidate.get('camera'))}:{str(candidate.get('payload'))}@x={float(candidate.get('center_x', 0.0)):.1f}"
            for candidate in ordered_candidates
        ]

        for candidate in ordered_candidates:
            payload = normalize_qr_value(str(candidate.get("payload") or ""))
            if not payload:
                continue
            if is_qr_detection_fresh(payload):
                continue
            candidate["payload"] = payload
            return candidate
        return None

    def capture_observation_burst(plant_qr: str, qr_candidate: dict[str, Any]) -> list[np.ndarray]:
        motor_controller.move_forward(settings.qr_capture_speed)
        camera_name = str(qr_candidate.get("camera") or "left").lower()
        if camera_name not in {"left", "right", "front"}:
            camera_name = "left"
        detection_frame = qr_candidate.get("detection_frame")
        selected_frames: list[np.ndarray] = []
        if isinstance(detection_frame, np.ndarray) and detection_frame.size > 0:
            selected_frames.append(detection_frame)
        selected_frames.extend(camera.capture_position_burst(
            camera_name,
            max(settings.capture_count, 4) - len(selected_frames),
            settings.burst_frame_interval_seconds,
        ))
        roi = compute_plant_roi(selected_frames[0] if selected_frames else None, qr_candidate, settings)
        runtime_context["last_qr_roi"] = roi
        selected_frames = crop_frames_to_roi(selected_frames, roi)
        set_status_summary(f"QR detectado: {display_target_label(parse_qr_identity(plant_qr)['group'], plant_qr)}")
        lcd_handler.show_temporary_message("QR detectado", display_target_label(parse_qr_identity(plant_qr)["group"], plant_qr), duration_seconds=3.0)
        return selected_frames

    command_listener = CommandListener(settings, on_command, shutdown_event)
    local_command_listener = LocalCommandListener(settings.local_command_socket_path, on_command, shutdown_event)

    status_thread = threading.Thread(target=status_sender, name="status-sender", daemon=True)
    observation_thread = threading.Thread(target=observation_worker, name="observation-worker", daemon=True)
    qr_resolution_thread = threading.Thread(target=qr_resolution_worker, name="qr-resolution-worker", daemon=True)
    offline_thread = threading.Thread(target=offline_flush_worker, name="offline-flush-worker", daemon=True)
    status_thread.start()
    observation_thread.start()
    qr_resolution_thread.start()
    offline_thread.start()
    command_listener.start()
    local_command_listener.start()

    try:
        while not shutdown_event.is_set():
            snapshot = state_machine.snapshot()
            refresh_lcd_rotation(snapshot)

            if snapshot.state == RobotState.IDLE:
                refresh_rear_obstacle_state()
                motor_controller.stop()
                set_stream_enabled(False)
                led_handler.set_idle()
                update_heartbeat_led_mode(snapshot)

            elif snapshot.state == RobotState.MANUAL:
                refresh_rear_obstacle_state()
                set_stream_enabled(True)
                enforce_manual_watchdog(snapshot)
                manual_direction = snapshot.manual_direction.strip().lower().replace("-", "_").replace(" ", "_")
                reverse_directions = {
                    "backward",
                    "down",
                    "backward_left",
                    "left_backward",
                    "reverse_left",
                    "left_reverse",
                    "backward_right",
                    "right_backward",
                    "reverse_right",
                    "right_reverse",
                }
                if manual_direction in reverse_directions and is_reverse_motion_blocked():
                    state_machine.update_manual_move("stop", 0)

            elif snapshot.state == RobotState.FOLLOW_LINE:
                refresh_rear_obstacle_state()
                set_stream_enabled(False)
                if runtime_context["awaiting_patrol_approval"]:
                    motor_controller.stop()
                    time.sleep(0.1)
                    continue
                obstacle_distance = obstacle_detector.get_distance_cm()
                runtime_context["last_obstacle_distance_cm"] = obstacle_distance
                runtime_context["obstacle_detected"] = obstacle_distance < settings.obstacle_distance_cm
                patrol_speed = current_speed_percent()
                if runtime_context["obstacle_detected"]:
                    runtime_context["obstacle_count"] += 1
                    motor_controller.stop()
                    set_status_summary("Obstaculo detectado")
                    lcd_handler.show_temporary_message("Obstaculo", "Detectado", duration_seconds=3.0)
                    alert_obstacle_feedback()
                    time.sleep(1.5)
                    motor_controller.turn_right(patrol_speed)
                    time.sleep(0.5)
                    motor_controller.stop()
                else:
                    runtime_context["obstacle_count"] = 0
                    line_follower.follow_line(patrol_speed)
                    if line_follower.is_all_white():
                        finish_row_and_wait_for_patrol()
                        time.sleep(0.1)
                        continue
                    left_frame = camera.capture_frame("left")
                    right_frame = camera.capture_frame("right")
                    qr_candidate = select_qr_candidate(left_frame, right_frame)
                    if qr_candidate:
                        plant_qr = str(qr_candidate["payload"])
                        runtime_context["last_qr_camera"] = qr_candidate.get("camera")
                    else:
                        plant_qr = None
                        runtime_context["last_qr_camera"] = None
                    if plant_qr and should_capture_plant(plant_qr):
                        found_sequence = register_scan_sequence()
                        detection_snapshot = state_machine.snapshot()
                        capture_enabled = runtime_context["search_mode"] is None
                        frames: list[np.ndarray] = []
                        if capture_enabled:
                            frames = capture_observation_burst(plant_qr, qr_candidate)
                            runtime_context["last_capture_count"] = len(frames)
                        else:
                            runtime_context["last_capture_count"] = 0
                            set_status_summary("QR detectado sin rafaga")
                            lcd_handler.show_temporary_message("QR detectado", "Sin rafaga", duration_seconds=2.0)
                        queue_qr_resolution(
                            plant_qr,
                            found_sequence,
                            frames,
                            capture_enabled=capture_enabled,
                            search_mode=runtime_context["search_mode"],
                            patrol_id=detection_snapshot.patrol_id,
                        )
                        if state_machine.snapshot().state != RobotState.IDLE:
                            state_machine.resume_follow_line()
                    elif line_follower.is_line_lost():
                        motor_controller.stop()
                        set_status_summary("Linea perdida")
                        lcd_handler.show_temporary_message("Linea perdida", "Detenido", duration_seconds=2.5)
                        time.sleep(0.25)

            time.sleep(0.05)
    except KeyboardInterrupt:
        LOGGER.info("KeyboardInterrupt received")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
