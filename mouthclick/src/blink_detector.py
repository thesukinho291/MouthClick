from .config import (
    BLINK_COOLDOWN_SECONDS,
    BLINK_MESSAGE_SECONDS,
    CALIBRATION_SECONDS,
    CALIBRATION_THRESHOLD_FACTOR,
    DEFAULT_EYE_CLOSED_THRESHOLD,
    LEFT_EYE_POINTS,
    MAX_BLINK_SECONDS,
    MIN_BLINK_SECONDS,
    MIN_CALIBRATION_SAMPLES,
    RIGHT_EYE_POINTS,
)


def landmark_distance(point_a, point_b):
    return ((point_a.x - point_b.x) ** 2 + (point_a.y - point_b.y) ** 2) ** 0.5


def eye_aspect_ratio(landmarks, eye_points):
    left_corner, upper_outer, upper_inner, right_corner, lower_inner, lower_outer = eye_points

    vertical_1 = landmark_distance(landmarks[upper_outer], landmarks[lower_outer])
    vertical_2 = landmark_distance(landmarks[upper_inner], landmarks[lower_inner])
    horizontal = landmark_distance(landmarks[left_corner], landmarks[right_corner])

    if horizontal == 0:
        return 0

    return (vertical_1 + vertical_2) / (2 * horizontal)


def average_eye_openness(landmarks):
    left_eye = eye_aspect_ratio(landmarks, LEFT_EYE_POINTS)
    right_eye = eye_aspect_ratio(landmarks, RIGHT_EYE_POINTS)
    return (left_eye + right_eye) / 2


class BlinkDetector:
    def __init__(self):
        self.blink_count = 0
        self.eyes_closed = False
        self.closed_at = 0.0
        self.last_blink_at = -999.0
        self.blink_threshold = DEFAULT_EYE_CLOSED_THRESHOLD

    def reset_closed_state(self):
        self.eyes_closed = False

    def update(self, ear_value, now):
        is_closed = ear_value < self.blink_threshold
        blink_detected = False
        cooldown_finished = now - self.last_blink_at >= BLINK_COOLDOWN_SECONDS

        if is_closed and not self.eyes_closed:
            self.eyes_closed = True
            self.closed_at = now

        if not is_closed and self.eyes_closed:
            closed_duration = now - self.closed_at
            self.eyes_closed = False

            if MIN_BLINK_SECONDS <= closed_duration <= MAX_BLINK_SECONDS and cooldown_finished:
                self.blink_count += 1
                self.last_blink_at = now
                blink_detected = True

        recently_blinked = now - self.last_blink_at <= BLINK_MESSAGE_SECONDS

        if blink_detected or recently_blinked:
            return "Piscada detectada", blink_detected
        if is_closed:
            return "Olhos fechados", blink_detected
        return "Olhos abertos", blink_detected


class BlinkCalibrator:
    def __init__(self):
        self.active = False
        self.started_at = 0.0
        self.samples = []
        self.message = "nao calibrado (limite padrao)"
        self.completed = False

    def start(self, now):
        self.active = True
        self.started_at = now
        self.samples = []
        self.message = "olhe para a camera com olhos abertos"
        self.completed = False

    def update(self, blink_detector, face_detected, ear_value, now):
        if not self.active:
            return

        elapsed = now - self.started_at

        if face_detected and ear_value is not None:
            self.samples.append(ear_value)
            remaining = max(0.0, CALIBRATION_SECONDS - elapsed)
            self.message = f"calibrando... {remaining:.1f}s"
        else:
            self.message = "calibrando... rosto nao detectado"

        if elapsed < CALIBRATION_SECONDS:
            return

        self.active = False

        if len(self.samples) < MIN_CALIBRATION_SAMPLES:
            self.message = "falhou: rosto insuficiente"
            return

        open_eye_average = sum(self.samples) / len(self.samples)
        blink_detector.blink_threshold = open_eye_average * CALIBRATION_THRESHOLD_FACTOR
        self.message = f"ok: media {open_eye_average:.2f}, limite {blink_detector.blink_threshold:.2f}"
        self.completed = True

    def consume_completed(self):
        if not self.completed:
            return False

        self.completed = False
        return True
