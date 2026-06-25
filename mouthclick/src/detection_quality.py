from .config import (
    QUALITY_MISSING_FACE_FRAMES,
    QUALITY_NOSE_JUMP_PIXELS,
    QUALITY_STABLE_FRAMES,
)


class DetectionQuality:
    def __init__(self):
        self.status = "sem rosto"
        self.message = "sem rosto"
        self.missing_frames = 0
        self.stable_frames = 0
        self.last_nose_point = None
        self.last_jump = 0.0

    def update(self, face_detected, nose_point):
        if not face_detected or nose_point is None:
            self.missing_frames += 1
            self.stable_frames = 0
            self.last_nose_point = None
            self.last_jump = 0.0
            self.status = "sem rosto"
            self.message = "sem rosto" if self.missing_frames < QUALITY_MISSING_FACE_FRAMES else "rosto ausente"
            return

        self.missing_frames = 0

        if self.last_nose_point is None:
            self.last_nose_point = nose_point
            self.stable_frames = 1
            self.status = "instavel"
            self.message = "estabilizando"
            return

        previous_x, previous_y = self.last_nose_point
        nose_x, nose_y = nose_point
        jump = ((nose_x - previous_x) ** 2 + (nose_y - previous_y) ** 2) ** 0.5
        self.last_jump = jump
        self.last_nose_point = nose_point

        if jump > QUALITY_NOSE_JUMP_PIXELS:
            self.stable_frames = 0
            self.status = "instavel"
            self.message = "movimento brusco"
            return

        self.stable_frames += 1

        if self.stable_frames >= QUALITY_STABLE_FRAMES:
            self.status = "boa"
            self.message = "boa"
        else:
            self.status = "instavel"
            self.message = "estabilizando"

    def is_good(self):
        return self.status == "boa"
