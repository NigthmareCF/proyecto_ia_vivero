from __future__ import annotations

from .camera import CameraAdapter
from .classifier import PlantClassifier
from .models import ObservationEvent
from .qr_reader import QrReader
from .models import utc_now


class RobotController:
    def __init__(
        self,
        robot_id: str,
        patrol_id: int | None,
        camera: CameraAdapter,
        classifier: PlantClassifier,
        qr_reader: QrReader,
    ) -> None:
        self.robot_id = robot_id
        self.patrol_id = patrol_id
        self.camera = camera
        self.classifier = classifier
        self.qr_reader = qr_reader

    def inspect_next_plant(self) -> ObservationEvent:
        image_base64, mime_type = self.camera.capture_base64()
        plant_qr = self.qr_reader.next_plant()
        label, confidence = self.classifier.classify(image_base64)

        return ObservationEvent(
            robot_id=self.robot_id,
            patrol_id=self.patrol_id,
            plant_qr=plant_qr,
            ai_light_result=label,
            ai_light_confidence=confidence,
            operator_notes="Generado en modo simulacion",
            image_base64=image_base64,
            mime_type=mime_type,
            timestamp=utc_now(),
        )
