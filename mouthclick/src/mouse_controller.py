from .config import (
    CONTROL_AREA_HEIGHT,
    CONTROL_AREA_WIDTH,
    REAL_CLICK_COOLDOWN_SECONDS,
    REAL_CLICK_FEEDBACK_SECONDS,
    REAL_MOUSE_PAUSE_SECONDS,
    REAL_MOUSE_BASE_MAX_STEP_PIXELS,
    REAL_MOUSE_SCREEN_MARGIN,
)
from .visual_cursor import clamp

try:
    import pyautogui
    PYAUTOGUI_IMPORT_ERROR = None
except Exception as error:
    pyautogui = None
    PYAUTOGUI_IMPORT_ERROR = error


class MouseController:
    def __init__(self):
        self.enabled = False
        self.message = "desativado"
        self.last_position = None
        self.last_real_click_at = -999.0
        self.real_click_message = "bloqueado: controle real desativado"

        if pyautogui is not None:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = REAL_MOUSE_PAUSE_SECONDS

    def is_available(self):
        return pyautogui is not None

    def toggle(self):
        if self.enabled:
            self.disable("desativado por F8")
            return

        if not self.is_available():
            self.disable("PyAutoGUI indisponivel")
            return

        self.enabled = True
        self.message = "ativado"
        self.last_position = pyautogui.position()

    def disable(self, message="desativado"):
        self.enabled = False
        self.message = message
        self.last_position = None

    def limit_step(self, target_x, target_y, sensitivity_x):
        if self.last_position is None:
            return target_x, target_y

        last_x, last_y = self.last_position
        delta_x = target_x - last_x
        delta_y = target_y - last_y
        distance = (delta_x**2 + delta_y**2) ** 0.5
        max_step = REAL_MOUSE_BASE_MAX_STEP_PIXELS * max(1.0, sensitivity_x / 2.0)

        if distance <= max_step:
            return target_x, target_y

        scale = max_step / distance
        return int(last_x + delta_x * scale), int(last_y + delta_y * scale)

    def move_from_visual_position(self, cursor_position, face_detected, has_nose_reference, detection_quality_good, sensitivity_x=2.0):
        if not self.enabled:
            return

        if not face_detected:
            self.message = "pausado: sem rosto"
            return

        if not has_nose_reference:
            self.message = "pausado: sem referencia"
            return

        try:
            screen_width, screen_height = pyautogui.size()
            cursor_x, cursor_y = cursor_position
            target_x = (cursor_x / CONTROL_AREA_WIDTH) * screen_width
            target_y = (cursor_y / CONTROL_AREA_HEIGHT) * screen_height
            target_x = int(clamp(target_x, REAL_MOUSE_SCREEN_MARGIN, screen_width - REAL_MOUSE_SCREEN_MARGIN - 1))
            target_y = int(clamp(target_y, REAL_MOUSE_SCREEN_MARGIN, screen_height - REAL_MOUSE_SCREEN_MARGIN - 1))
            target_x, target_y = self.limit_step(target_x, target_y, sensitivity_x)
            pyautogui.moveTo(target_x, target_y, duration=0)
            self.last_position = (target_x, target_y)
            self.message = "ativado"
        except Exception as error:
            self.disable(f"erro ao mover: {error}")

    def hold_movement(self, message):
        if self.enabled:
            self.message = message

    def real_click_cooldown_remaining(self, now):
        elapsed = now - self.last_real_click_at
        return max(0.0, REAL_CLICK_COOLDOWN_SECONDS - elapsed)

    def real_click_feedback_active(self, now):
        return now - self.last_real_click_at <= REAL_CLICK_FEEDBACK_SECONDS

    def real_click_block_reason(self, safety_state, face_detected, has_nose_reference, detection_quality_good, now):
        if not self.is_available():
            if PYAUTOGUI_IMPORT_ERROR is not None:
                return f"PyAutoGUI indisponivel: {PYAUTOGUI_IMPORT_ERROR}"
            return "PyAutoGUI indisponivel"
        if not self.enabled:
            return "controle real desativado"
        if not safety_state.armed:
            return "sistema desarmado"
        if not face_detected:
            return "rosto nao detectado"
        if not has_nose_reference:
            return "sem referencia do nariz"
        if not detection_quality_good:
            return "qualidade instavel"
        cooldown_remaining = self.real_click_cooldown_remaining(now)
        if cooldown_remaining > 0:
            return f"cooldown {cooldown_remaining:.1f}s"
        return None

    def real_click_status(self, safety_state, face_detected, has_nose_reference, detection_quality_good, now):
        if self.real_click_feedback_active(now):
            return "clicou"

        block_reason = self.real_click_block_reason(
            safety_state,
            face_detected,
            has_nose_reference,
            detection_quality_good,
            now,
        )

        if block_reason is None:
            return "pronto"

        return "bloqueado"

    def update_real_click_message(self, safety_state, face_detected, has_nose_reference, detection_quality_good, now):
        if self.real_click_feedback_active(now):
            self.real_click_message = "clique real executado"
            return

        block_reason = self.real_click_block_reason(
            safety_state,
            face_detected,
            has_nose_reference,
            detection_quality_good,
            now,
        )
        self.real_click_message = "pronto" if block_reason is None else f"bloqueado: {block_reason}"

    def try_real_left_click(self, safety_state, face_detected, has_nose_reference, detection_quality_good, now):
        block_reason = self.real_click_block_reason(
            safety_state,
            face_detected,
            has_nose_reference,
            detection_quality_good,
            now,
        )

        if block_reason is not None:
            self.real_click_message = f"bloqueado: {block_reason}"
            return False

        try:
            pyautogui.click(button="left")
            self.last_real_click_at = now
            self.real_click_message = "clique real executado"
            return True
        except Exception as error:
            self.disable(f"erro ao clicar: {error}")
            safety_state.disarm()
            self.real_click_message = f"erro ao clicar: {error}"
            return False
