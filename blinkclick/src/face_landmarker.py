import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .config import MODEL_PATH


class FaceLandmarker:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self._landmarker = None

    def __enter__(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo do MediaPipe nao encontrado em {self.model_path}")

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._landmarker is not None:
            self._landmarker.close()

    def detect(self, rgb_frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.monotonic() * 1000)
        return self._landmarker.detect_for_video(mp_image, timestamp_ms)
