from __future__ import annotations

from collections import deque


class PlantClassifier:
    def __init__(self, use_simulation: bool) -> None:
        self.use_simulation = use_simulation
        self._cycle = deque(
            [
                ("HEALTHY", 0.91),
                ("ATTENTION", 0.73),
                ("DANGER", 0.88),
            ]
        )

    def classify(self, image_base64: str) -> tuple[str, float]:
        if not image_base64:
            return "UNKNOWN", 0.0

        if self.use_simulation:
            label, confidence = self._cycle[0]
            self._cycle.rotate(-1)
            return label, confidence

        raise RuntimeError("Real TFLite inference requires runtime dependencies not present here")
