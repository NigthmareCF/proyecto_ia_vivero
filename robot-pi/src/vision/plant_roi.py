from __future__ import annotations

from typing import Any

import numpy as np

from src.config import Settings


def _float_value(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _x_offset_factor(camera_name: str, settings: Settings) -> float:
    if camera_name == "left":
        return settings.plant_roi_left_x_offset_factor
    if camera_name == "right":
        return settings.plant_roi_right_x_offset_factor
    return settings.plant_roi_front_x_offset_factor


def _roi_dimensions(
    orientation: str,
    qr_width: float,
    qr_height: float,
    frame_width: int,
    frame_height: int,
    settings: Settings,
) -> tuple[int, int]:
    if orientation == "vertical":
        width_factor = settings.plant_roi_vertical_width_factor
        height_factor = settings.plant_roi_vertical_height_factor
    elif orientation == "horizontal":
        width_factor = settings.plant_roi_horizontal_width_factor
        height_factor = settings.plant_roi_horizontal_height_factor
    else:
        width_factor = settings.plant_roi_width_factor
        height_factor = settings.plant_roi_height_factor

    roi_width = int(max(settings.plant_roi_min_width_px, qr_width * width_factor))
    roi_height = int(max(settings.plant_roi_min_height_px, qr_height * height_factor))
    return min(roi_width, frame_width), min(roi_height, frame_height)


def _placement(
    width: int,
    height: int,
    frame_width: int,
    frame_height: int,
    center_x: float,
    center_y: float,
    qr_width: float,
    qr_height: float,
    camera_name: str,
    settings: Settings,
) -> tuple[int, int, float]:
    roi_center_x = center_x + (qr_width * _x_offset_factor(camera_name, settings))
    roi_center_y = center_y + (qr_height * settings.plant_roi_y_offset_factor)
    raw_x = int(round(roi_center_x - (width / 2)))
    raw_y = int(round(roi_center_y - (height / 2)))
    x = _clamp(raw_x, 0, max(frame_width - width, 0))
    y = _clamp(raw_y, 0, max(frame_height - height, 0))
    shift_ratio = (abs(raw_x - x) / max(frame_width, 1)) + (abs(raw_y - y) / max(frame_height, 1))
    return x, y, shift_ratio


def _resolve_orientation(
    requested: str,
    qr_width: float,
    qr_height: float,
    frame_width: int,
    frame_height: int,
    center_x: float,
    center_y: float,
    camera_name: str,
    settings: Settings,
) -> str:
    if requested in {"vertical", "horizontal"}:
        return requested

    scores: dict[str, float] = {}
    for orientation in ("vertical", "horizontal"):
        width, height = _roi_dimensions(orientation, qr_width, qr_height, frame_width, frame_height, settings)
        _, _, shift_ratio = _placement(
            width,
            height,
            frame_width,
            frame_height,
            center_x,
            center_y,
            qr_width,
            qr_height,
            camera_name,
            settings,
        )
        area_ratio = (width * height) / max(frame_width * frame_height, 1)
        shape_bonus = 0.05 if orientation == "vertical" and height >= width else 0.0
        scores[orientation] = area_ratio + shape_bonus - (shift_ratio * 2.0)

    return "vertical" if scores["vertical"] >= scores["horizontal"] else "horizontal"


def compute_plant_roi(
    frame: np.ndarray | None,
    qr_candidate: dict[str, Any] | None,
    settings: Settings,
) -> dict[str, int | float | str | bool] | None:
    if not settings.plant_roi_enabled or frame is None or frame.size == 0 or not qr_candidate:
        return None

    frame_height, frame_width = frame.shape[:2]
    if frame_width <= 0 or frame_height <= 0:
        return None

    camera_name = str(qr_candidate.get("camera") or "front").lower()
    qr_width = max(_float_value(qr_candidate.get("width")), 1.0)
    qr_height = max(_float_value(qr_candidate.get("height")), 1.0)
    center_x = _float_value(qr_candidate.get("center_x"), frame_width / 2.0)
    center_y = _float_value(qr_candidate.get("center_y"), frame_height / 2.0)

    requested_orientation = settings.plant_roi_orientation
    orientation = _resolve_orientation(
        requested_orientation,
        qr_width,
        qr_height,
        frame_width,
        frame_height,
        center_x,
        center_y,
        camera_name,
        settings,
    )
    roi_width, roi_height = _roi_dimensions(orientation, qr_width, qr_height, frame_width, frame_height, settings)
    x, y, shift_ratio = _placement(
        roi_width,
        roi_height,
        frame_width,
        frame_height,
        center_x,
        center_y,
        qr_width,
        qr_height,
        camera_name,
        settings,
    )

    return {
        "enabled": True,
        "camera": camera_name,
        "orientation": orientation,
        "requestedOrientation": requested_orientation,
        "x": x,
        "y": y,
        "width": roi_width,
        "height": roi_height,
        "centerShiftRatio": round(shift_ratio, 4),
        "frameWidth": frame_width,
        "frameHeight": frame_height,
        "qrCenterX": center_x,
        "qrCenterY": center_y,
        "qrWidth": qr_width,
        "qrHeight": qr_height,
    }


def crop_frame_to_roi(frame: np.ndarray | None, roi: dict[str, Any] | None) -> np.ndarray | None:
    if frame is None or frame.size == 0 or not roi:
        return frame

    frame_height, frame_width = frame.shape[:2]
    x = _clamp(int(roi.get("x", 0)), 0, max(frame_width - 1, 0))
    y = _clamp(int(roi.get("y", 0)), 0, max(frame_height - 1, 0))
    width = _clamp(int(roi.get("width", frame_width)), 1, frame_width - x)
    height = _clamp(int(roi.get("height", frame_height)), 1, frame_height - y)

    return frame[y:y + height, x:x + width].copy()


def crop_frames_to_roi(frames: list[np.ndarray], roi: dict[str, Any] | None) -> list[np.ndarray]:
    if not roi:
        return frames
    cropped: list[np.ndarray] = []
    for frame in frames:
        cropped_frame = crop_frame_to_roi(frame, roi)
        if cropped_frame is not None and cropped_frame.size > 0:
            cropped.append(cropped_frame)
    return cropped
