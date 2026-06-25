from .config import (
    CONTROL_AREA_HEIGHT,
    CONTROL_AREA_WIDTH,
    CURSOR_SMOOTHING,
    DEFAULT_CURSOR_SENSITIVITY,
    MAX_CURSOR_SENSITIVITY,
    MIN_CURSOR_SENSITIVITY,
    NOSE_DEAD_ZONE_PIXELS,
    VISUAL_CURSOR_BASE_MAX_STEP_PIXELS,
)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def apply_dead_zone(value):
    if abs(value) <= NOSE_DEAD_ZONE_PIXELS:
        return 0

    if value > 0:
        return value - NOSE_DEAD_ZONE_PIXELS

    return value + NOSE_DEAD_ZONE_PIXELS


def limit_step(current_x, current_y, target_x, target_y, max_step):
    delta_x = target_x - current_x
    delta_y = target_y - current_y
    distance = (delta_x**2 + delta_y**2) ** 0.5

    if distance <= max_step:
        return target_x, target_y

    scale = max_step / distance
    return current_x + delta_x * scale, current_y + delta_y * scale


class VisualCursor:
    def __init__(self, sensitivity=DEFAULT_CURSOR_SENSITIVITY):
        self.position = (CONTROL_AREA_WIDTH / 2, CONTROL_AREA_HEIGHT / 2)
        self.sensitivity = clamp(sensitivity, MIN_CURSOR_SENSITIVITY, MAX_CURSOR_SENSITIVITY)
        self.message = "aguardando rosto"

    @property
    def sensitivity_x(self):
        return self.sensitivity

    @property
    def sensitivity_y(self):
        return self.sensitivity + 1.0

    def update_from_nose(self, nose_point, nose_reference, cursor_calibration=None):
        if nose_point is None or nose_reference is None:
            self.message = "rosto nao detectado"
            return

        current_x, current_y = self.position

        if cursor_calibration is not None and cursor_calibration.is_ready():
            target_x, target_y = cursor_calibration.map_to_control(
                nose_point,
                self.sensitivity_x,
                self.sensitivity_y,
            )
        else:
            reference_x, reference_y = nose_reference
            nose_x, nose_y = nose_point
            nose_delta_x = apply_dead_zone(nose_x - reference_x)
            nose_delta_y = apply_dead_zone(nose_y - reference_y)

            target_x = CONTROL_AREA_WIDTH / 2 + nose_delta_x * self.sensitivity_x
            target_y = CONTROL_AREA_HEIGHT / 2 + nose_delta_y * self.sensitivity_y
            target_x = clamp(target_x, 0, CONTROL_AREA_WIDTH)
            target_y = clamp(target_y, 0, CONTROL_AREA_HEIGHT)

        limited_x, limited_y = limit_step(
            current_x,
            current_y,
            target_x,
            target_y,
            self.max_step_pixels,
        )
        smoothed_x = current_x + (limited_x - current_x) * CURSOR_SMOOTHING
        smoothed_y = current_y + (limited_y - current_y) * CURSOR_SMOOTHING

        self.position = (smoothed_x, smoothed_y)
        self.message = "ativo"

    def hold_position(self, message="pausado"):
        self.message = message

    def reset(self, has_reference):
        self.position = (CONTROL_AREA_WIDTH / 2, CONTROL_AREA_HEIGHT / 2)
        self.message = "referencia redefinida" if has_reference else "aguardando rosto"

    def adjust_sensitivity(self, delta):
        self.sensitivity = clamp(
            self.sensitivity + delta,
            MIN_CURSOR_SENSITIVITY,
            MAX_CURSOR_SENSITIVITY,
        )

    @property
    def max_step_pixels(self):
        return VISUAL_CURSOR_BASE_MAX_STEP_PIXELS * (self.sensitivity_x / DEFAULT_CURSOR_SENSITIVITY)
