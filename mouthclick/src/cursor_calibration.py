from .config import CONTROL_AREA_HEIGHT, CONTROL_AREA_WIDTH, DEFAULT_CURSOR_SENSITIVITY
from .visual_cursor import clamp


CALIBRATION_STEPS = (
    ("center", "olhe para o centro e pressione N"),
    ("left", "olhe para a esquerda e pressione N"),
    ("right", "olhe para a direita e pressione N"),
    ("up", "olhe para cima e pressione N"),
    ("down", "olhe para baixo e pressione N"),
)

MIN_DIRECTION_DISTANCE = 8.0


class CursorCalibration:
    def __init__(self, data=None):
        self.active = False
        self.step_index = 0
        self.points = {}
        self.message = "nariz nao calibrado"

        if data:
            self.load(data)

    def load(self, data):
        points = data.get("points") if isinstance(data, dict) else None

        if not isinstance(points, dict):
            return

        loaded_points = {}
        for key, value in points.items():
            if key not in {step[0] for step in CALIBRATION_STEPS}:
                continue
            if not isinstance(value, list) or len(value) != 2:
                continue
            loaded_points[key] = (float(value[0]), float(value[1]))

        self.points = loaded_points
        self.message = "calibracao do nariz carregada" if self.is_ready() else "nariz nao calibrado"

    def to_dict(self):
        if not self.is_ready():
            return None

        return {
            "points": {
                key: [round(point[0], 2), round(point[1], 2)]
                for key, point in self.points.items()
            }
        }

    def is_ready(self):
        required_keys = {step[0] for step in CALIBRATION_STEPS}
        return required_keys.issubset(self.points) and self.is_valid()

    def is_valid(self):
        try:
            center_x, center_y = self.points["center"]
            left_x, _ = self.points["left"]
            right_x, _ = self.points["right"]
            _, up_y = self.points["up"]
            _, down_y = self.points["down"]
        except KeyError:
            return False

        horizontal_ok = abs(center_x - left_x) >= MIN_DIRECTION_DISTANCE and abs(right_x - center_x) >= MIN_DIRECTION_DISTANCE
        vertical_ok = abs(center_y - up_y) >= MIN_DIRECTION_DISTANCE and abs(down_y - center_y) >= MIN_DIRECTION_DISTANCE
        return horizontal_ok and vertical_ok

    def start(self):
        self.active = True
        self.step_index = 0
        self.points = {}
        self.message = CALIBRATION_STEPS[self.step_index][1]

    def capture(self, nose_point):
        if nose_point is None:
            self.message = "calibracao do nariz: rosto nao detectado"
            return False

        if not self.active:
            self.start()
            return False

        step_key, _ = CALIBRATION_STEPS[self.step_index]
        self.points[step_key] = (float(nose_point[0]), float(nose_point[1]))
        self.step_index += 1

        if self.step_index < len(CALIBRATION_STEPS):
            self.message = CALIBRATION_STEPS[self.step_index][1]
            return False

        self.active = False

        if not self.is_ready():
            self.message = "calibracao do nariz falhou: mova mais a cabeca"
            return False

        self.message = "calibracao do nariz salva"
        return True

    def map_to_control(self, nose_point, sensitivity_x, sensitivity_y):
        center_x, center_y = self.points["center"]
        left_x, _ = self.points["left"]
        right_x, _ = self.points["right"]
        _, up_y = self.points["up"]
        _, down_y = self.points["down"]
        nose_x, nose_y = nose_point

        delta_x = nose_x - center_x
        delta_y = nose_y - center_y
        left_range = max(MIN_DIRECTION_DISTANCE, abs(center_x - left_x))
        right_range = max(MIN_DIRECTION_DISTANCE, abs(right_x - center_x))
        up_range = max(MIN_DIRECTION_DISTANCE, abs(center_y - up_y))
        down_range = max(MIN_DIRECTION_DISTANCE, abs(down_y - center_y))

        normalized_x = delta_x / (right_range if delta_x >= 0 else left_range)
        normalized_y = delta_y / (down_range if delta_y >= 0 else up_range)
        normalized_x = clamp(normalized_x, -1.0, 1.0)
        normalized_y = clamp(normalized_y, -1.0, 1.0)

        gain_x = sensitivity_x / DEFAULT_CURSOR_SENSITIVITY
        gain_y = sensitivity_y / (DEFAULT_CURSOR_SENSITIVITY + 1.0)

        target_x = CONTROL_AREA_WIDTH / 2 + normalized_x * (CONTROL_AREA_WIDTH / 2) * gain_x
        target_y = CONTROL_AREA_HEIGHT / 2 + normalized_y * (CONTROL_AREA_HEIGHT / 2) * gain_y
        return clamp(target_x, 0, CONTROL_AREA_WIDTH), clamp(target_y, 0, CONTROL_AREA_HEIGHT)

