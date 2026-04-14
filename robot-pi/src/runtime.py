from __future__ import annotations

import time

from .bridge_client import BridgeClient
from .camera import CameraAdapter
from .classifier import PlantClassifier
from .config import Settings
from .models import RobotHeartbeat, utc_now
from .qr_reader import QrReader
from .robot_controller import RobotController


def main() -> None:
    settings = Settings()
    bridge = BridgeClient(settings.bridge_base_url)
    controller = RobotController(
        robot_id=settings.robot_id,
        patrol_id=settings.patrol_id,
        camera=CameraAdapter(settings.use_simulation),
        classifier=PlantClassifier(settings.use_simulation),
        qr_reader=QrReader(settings.use_simulation),
    )

    while True:
        heartbeat = RobotHeartbeat(
            robot_id=settings.robot_id,
            battery_level=87,
            mode="AUTO" if not settings.use_simulation else "SIMULATION",
            current_plant_qr=None,
            is_connected=True,
            timestamp=utc_now(),
        )
        bridge.send_heartbeat(heartbeat)

        observation = controller.inspect_next_plant()
        bridge.send_observation(observation)

        time.sleep(settings.heartbeat_interval_seconds)
