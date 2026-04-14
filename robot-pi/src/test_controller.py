from .camera import CameraAdapter
from .classifier import PlantClassifier
from .qr_reader import QrReader
from .robot_controller import RobotController


def run_smoke_test() -> None:
    controller = RobotController(
        robot_id="robot-pi-01",
        patrol_id=1,
        camera=CameraAdapter(True),
        classifier=PlantClassifier(True),
        qr_reader=QrReader(True),
    )
    event = controller.inspect_next_plant()
    assert event.plant_qr.startswith("QR-PLANT-")
    assert event.ai_light_result in {"HEALTHY", "ATTENTION", "DANGER"}


if __name__ == "__main__":
    run_smoke_test()
