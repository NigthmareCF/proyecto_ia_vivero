from __future__ import annotations

import base64


class CameraAdapter:
    def __init__(self, use_simulation: bool) -> None:
        self.use_simulation = use_simulation

    def capture_base64(self) -> tuple[str, str]:
        if self.use_simulation:
            return base64.b64encode(b"simulated-image").decode("ascii"), "image/jpeg"

        raise RuntimeError("Real camera integration requires OpenCV support in this environment")
