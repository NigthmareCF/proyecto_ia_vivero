from __future__ import annotations

from collections import deque


class QrReader:
    def __init__(self, use_simulation: bool) -> None:
        self.use_simulation = use_simulation
        self._codes = deque(["QR-PLANT-001", "QR-PLANT-002", "QR-PLANT-003"])

    def next_plant(self) -> str:
        if self.use_simulation:
            value = self._codes[0]
            self._codes.rotate(-1)
            return value

        raise RuntimeError("Real QR reading requires OpenCV or pyzbar integration")
