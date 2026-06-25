import cv2
import numpy as np

from .config import (
    TONGUE_CALIBRATION_SECONDS,
    TONGUE_CLICK_COOLDOWN_SECONDS,
    TONGUE_CURSOR_HOLD_SECONDS,
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
    def __init__(self, mouth_open_threshold=TONGUE_MOUTH_OPEN_THRESHOLD, color_ratio_threshold=TONGUE_COLOR_RATIO_THRESHOLD):
        self.active_frames = 0
        self.last_trigger_at = -999.0
        self.mouth_open_ratio = 0.0
        self.color_ratio = 0.0
        self.mouth_open_threshold = mouth_open_threshold
        self.color_ratio_threshold = color_ratio_threshold
        self.last_cursor_hold_at = -999.0
        self.message = "aguardando lingua"

    def set_thresholds(self, mouth_open_threshold, color_ratio_threshold):
        self.mouth_open_threshold = mouth_open_threshold
        self.color_ratio_threshold = color_ratio_threshold

    def reset(self):
        self.active_frames = 0
        self.mouth_open_ratio = 0.0
        self.color_ratio = 0.0
        self.message = "sem rosto"

    def update(self, frame, landmarks, now, allow_trigger=True):
        self.mouth_open_ratio = self.calculate_mouth_open_ratio(landmarks)
        self.color_ratio = self.calculate_tongue_color_ratio(frame, landmarks)

        looks_like_tongue = self.looks_like_tongue()

        if self.should_start_cursor_hold():
            self.last_cursor_hold_at = now

        if not allow_trigger:
            self.active_frames = 0
            self.message = "calibrando lingua"
            return False

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

    def looks_like_tongue(self):
        return (
            self.mouth_open_ratio >= self.mouth_open_threshold
            and self.color_ratio >= self.color_ratio_threshold
        )

    def should_start_cursor_hold(self):
        return self.looks_like_tongue()

    def is_cursor_hold_active(self, now):
        return now - self.last_cursor_hold_at <= TONGUE_CURSOR_HOLD_SECONDS or self.is_feedback_active(now)

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


class TongueCalibrator:
    def __init__(self):
        self.active = False
        self.phase = "idle"
        self.phase_started_at = 0.0
        self.neutral_samples = []
        self.tongue_samples = []
        self.message = "lingua nao calibrada"
        self.completed = False

    def start(self, now):
        self.active = True
        self.phase = "neutral"
        self.phase_started_at = now
        self.neutral_samples = []
        self.tongue_samples = []
        self.message = "calibrando lingua: boca normal"
        self.completed = False

    def update(self, tongue_detector, face_detected, now):
        if not self.active:
            return

        if face_detected:
            sample = (tongue_detector.mouth_open_ratio, tongue_detector.color_ratio)
            if self.phase == "neutral":
                self.neutral_samples.append(sample)
            elif self.phase == "tongue":
                self.tongue_samples.append(sample)

        elapsed = now - self.phase_started_at
        remaining = max(0.0, TONGUE_CALIBRATION_SECONDS - elapsed)

        if self.phase == "neutral":
            self.message = f"calibrando lingua: boca normal {remaining:.1f}s"
        elif self.phase == "tongue":
            self.message = f"calibrando lingua: mostre a lingua {remaining:.1f}s"

        if elapsed < TONGUE_CALIBRATION_SECONDS:
            return

        if self.phase == "neutral":
            self.phase = "tongue"
            self.phase_started_at = now
            self.message = "calibrando lingua: mostre a lingua"
            return

        self.active = False

        if len(self.neutral_samples) < 6 or len(self.tongue_samples) < 6:
            self.message = "calibracao da lingua falhou: rosto insuficiente"
            return

        neutral_mouth, neutral_color = self.average_sample(self.neutral_samples)
        tongue_mouth, tongue_color = self.average_sample(self.tongue_samples)

        if tongue_mouth <= neutral_mouth or tongue_color <= neutral_color:
            self.message = "calibracao da lingua falhou: gesto pouco diferente"
            return

        mouth_threshold = max(0.08, (neutral_mouth + tongue_mouth) / 2)
        color_threshold = max(0.03, (neutral_color + tongue_color) / 2)
        tongue_detector.set_thresholds(mouth_threshold, color_threshold)
        self.message = f"lingua calibrada: boca {mouth_threshold:.2f}, cor {color_threshold:.2f}"
        self.completed = True

    @staticmethod
    def average_sample(samples):
        mouth_average = sum(sample[0] for sample in samples) / len(samples)
        color_average = sum(sample[1] for sample in samples) / len(samples)
        return mouth_average, color_average

    def consume_completed(self):
        if not self.completed:
            return False

        self.completed = False
        return True
