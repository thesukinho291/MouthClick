from .config import NOSE_TIP_INDEX


def normalized_to_pixel(landmark, frame_width, frame_height):
    return int(landmark.x * frame_width), int(landmark.y * frame_height)


class NoseTracker:
    def __init__(self):
        self.last_point = None
        self.reference = None

    def locate(self, landmarks, frame_shape):
        frame_height, frame_width, _ = frame_shape
        nose_point = normalized_to_pixel(landmarks[NOSE_TIP_INDEX], frame_width, frame_height)
        self.last_point = nose_point

        if self.reference is None:
            self.reference = nose_point

        return nose_point

    def reset_reference(self, nose_point=None):
        self.reference = nose_point
