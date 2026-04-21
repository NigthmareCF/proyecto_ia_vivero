from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import Settings


LOGGER = logging.getLogger(__name__)

try:
    from tflite_runtime.interpreter import Interpreter  # type: ignore
except Exception:  # pragma: no cover
    try:
        from tensorflow.lite import Interpreter  # type: ignore
    except Exception:  # pragma: no cover
        Interpreter = None


def load_model(settings: Settings) -> tuple[Any, Any, Any]:
    model_path = Path(settings.model_path)
    if Interpreter is None or not model_path.exists():
        LOGGER.warning("Modelo TFLite no disponible; se usara clasificacion defensiva")
        return None, None, None
    interpreter = Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    return interpreter, interpreter.get_input_details(), interpreter.get_output_details()
