from __future__ import annotations

from collections import defaultdict
from typing import Any

import cv2
import numpy as np

from src.config import CLASSES, Settings


def classify(frame: np.ndarray, interpreter: Any, input_details: Any, output_details: Any) -> dict[str, Any]:
    if interpreter is None or input_details is None or output_details is None:
        return {
            "class": "atencion",
            "confidence": 0.0,
            "raw_scores": [0.0, 0.0, 0.0],
        }

    resized = cv2.resize(frame, (224, 224)).astype("float32") / 255.0
    input_tensor = np.expand_dims(resized, axis=0)
    interpreter.set_tensor(input_details[0]["index"], input_tensor)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])[0]
    index = int(np.argmax(output))
    return {
        "class": CLASSES[index],
        "confidence": float(output[index]),
        "raw_scores": output.tolist(),
    }


def classify_burst(
    frames: list[np.ndarray],
    interpreter: Any,
    input_details: Any,
    output_details: Any,
    settings: Settings,
) -> dict[str, Any]:
    if not frames:
        return {"class": "atencion", "confidence": 0.0, "raw_scores": [0.0, 0.0, 0.0]}

    aggregate: dict[str, list[float]] = defaultdict(list)
    last_scores = [0.0, 0.0, 0.0]
    for frame in frames:
        result = classify(frame, interpreter, input_details, output_details)
        aggregate[result["class"]].append(float(result["confidence"]))
        last_scores = result["raw_scores"]

    best_class = max(aggregate.items(), key=lambda item: sum(item[1]) / len(item[1]))[0]
    best_confidence = sum(aggregate[best_class]) / len(aggregate[best_class])
    if best_confidence < settings.ai_confidence_threshold:
        best_class = "atencion"
    return {
        "class": best_class,
        "confidence": round(best_confidence, 4),
        "raw_scores": last_scores,
    }
