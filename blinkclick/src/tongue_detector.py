import cv2
import numpy as np

from .config import (
    TONGUE_CLICK_COOLDOWN_SECONDS,
    TONGUE_COLOR_RATIO_THRESHOLD,
    TONGUE_FEEDBACK_SECONDS,
    TONGUE_MOUTH_OPEN_THRESHOLD,
    TONGUE_TRIGGER_FRAMES,
)
from .nose_tracker import normalized_to_pixel


MOUTH_LANDMARKS = (13, 14, 61, 291, 78, 308, 81, 178, 402, 311)


def landmark_distance(point_a, point_b):
    return ((point_a.x - point_b.x) ** 2 + (point_a.y - point_b.y) ** 2) ** 0.5


class TongueDetector:
    def __init__(self):
        self.active_frames = 0
        self.last_trigger_at = -999.0
        self.mouth_open_ratio = 0.0
        self.color_ratio = 0.0
        self.message = "aguardando lingua"

    def reset(self):
        self.active_frames = 0
        self.mouth_open_ratio = 0.0
        self.color_ratio = 0.0
        self.message = "sem rosto"

    def update(self, frame, landmarks, now):
        self.mouth_open_ratio = self.calculate_mouth_open_ratio(landmarks)
        self.color_ratio = self.calculate_tongue_color_ratio(frame, landmarks)

        looks_like_tongue = (
            self.mouth_open_ratio >= TONGUE_MOUTH_OPEN_THRESHOLD
            and self.color_ratio >= TONGUE_COLOR_RATIO_THRESHOLD
        )

        if looks_like_tongue:
            self.active_frames += 1
            self.message = "lingua detectada"
        else:
            self.active_frames = 0
            self.message = "aguardando lingua"

        cooldown_ready = now - self.last_trigger_at >= TONGUE_CLICK_COOLDOWN_SECONDS

        if self.active_frames >= TONGUE_TRIGGER_FRAMES and cooldown_ready:
            self.last_trigger_at = now
            self.active_frames = 0
            self.message = "gesto de clique"
            return True

        return False

    def calculate_mouth_open_ratio(self, landmarks):
        mouth_height = landmark_distance(landmarks[13], landmarks[14])
        mouth_width = landmark_distance(landmarks[61], landmarks[291])

        if mouth_width == 0:
            return 0.0

        return mouth_height / mouth_width

    def calculate_tongue_color_ratio(self, frame, landmarks):
        frame_height, frame_width, _ = frame.shape
        points = [normalized_to_pixel(landmarks[index], frame_width, frame_height) for index in MOUTH_LANDMARKS]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        padding = 8
        left = max(0, min(xs) - padding)
        right = min(frame_width, max(xs) + padding)
        top = max(0, min(ys) - padding)
        bottom = min(frame_height, max(ys) + padding)

        if right <= left or bottom <= top:
            return 0.0

        roi = frame[top:bottom, left:right]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower_red_1 = np.array([0, 35, 45], dtype=np.uint8)
        upper_red_1 = np.array([18, 255, 255], dtype=np.uint8)
        lower_red_2 = np.array([155, 35, 45], dtype=np.uint8)
        upper_red_2 = np.array([179, 255, 255], dtype=np.uint8)

        mask_1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask_2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        mask = cv2.bitwise_or(mask_1, mask_2)

        return float(cv2.countNonZero(mask)) / float(mask.size)

    def is_feedback_active(self, now):
        return now - self.last_trigger_at <= TONGUE_FEEDBACK_SECONDS

    def status_text(self, now):
        if self.is_feedback_active(now):
            return "lingua: clique"
        return self.message
