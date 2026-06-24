import cv2
from mediapipe.tasks.python import vision

from .config import (
    CONTROL_AREA_HEIGHT,
    CONTROL_AREA_WIDTH,
    CURSOR_SMOOTHING,
    UI_CONTROL_MIN_HEIGHT,
    UI_CONTROL_MIN_WIDTH,
    UI_MARGIN,
    UI_PANEL_MAX_WIDTH,
    UI_PANEL_MIN_WIDTH,
)
from .nose_tracker import normalized_to_pixel


WHITE = (238, 242, 245)
MUTED = (165, 172, 178)
GREEN = (88, 210, 132)
RED = (80, 95, 235)
YELLOW = (0, 220, 255)
MAGENTA = (235, 80, 230)
PANEL_BG = (18, 22, 26)
PANEL_BORDER = (68, 76, 84)


def draw_text(frame, text, position, color=WHITE, scale=0.48, thickness=1):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def draw_panel(frame, left, top, right, bottom, alpha=0.68):
    overlay = frame.copy()
    cv2.rectangle(overlay, (left, top), (right, bottom), PANEL_BG, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (left, top), (right, bottom), PANEL_BORDER, 1)


def fit_panel_width(frame_width):
    available_width = max(140, frame_width - UI_MARGIN * 2)
    preferred_width = int(frame_width * 0.46)
    return min(max(UI_PANEL_MIN_WIDTH, preferred_width), UI_PANEL_MAX_WIDTH, available_width)


def label_color(value, good_value):
    return GREEN if value == good_value else MUTED


def short_eye_status(eye_status, face_detected):
    if not face_detected:
        return "sem rosto", RED
    if eye_status == "Piscada detectada":
        return "piscada", YELLOW
    if eye_status == "Calibrando":
        return "calibrando", YELLOW
    if eye_status == "Olhos fechados":
        return "fechados", YELLOW
    return "abertos", GREEN


def short_tongue_status(tongue_detector, now):
    if tongue_detector.is_feedback_active(now):
        return "clique", YELLOW
    if tongue_detector.message == "lingua detectada":
        return "detectada", YELLOW
    if tongue_detector.message == "gesto de clique":
        return "clique", YELLOW
    return "aguardando", MUTED


def draw_button(frame, text, rect, active=False):
    left, top, right, bottom = rect
    fill = (45, 58, 68) if active else (32, 38, 44)
    border = GREEN if active else PANEL_BORDER
    cv2.rectangle(frame, (left, top), (right, bottom), fill, -1)
    cv2.rectangle(frame, (left, top), (right, bottom), border, 1)
    text_x = left + 7
    text_y = top + 16
    draw_text(frame, text, (text_x, text_y), WHITE, scale=0.34, thickness=1)


def draw_face_mesh(frame, landmarks, nose_point):
    frame_height, frame_width, _ = frame.shape

    for connection in vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION:
        start_point = normalized_to_pixel(landmarks[connection.start], frame_width, frame_height)
        end_point = normalized_to_pixel(landmarks[connection.end], frame_width, frame_height)
        cv2.line(frame, start_point, end_point, (0, 135, 90), 1)

    for index, landmark in enumerate(landmarks):
        if index % 3 == 0:
            point = normalized_to_pixel(landmark, frame_width, frame_height)
            cv2.circle(frame, point, 1, (88, 195, 124), -1)

    if nose_point is not None:
        cv2.circle(frame, nose_point, 6, YELLOW, -1)
        cv2.circle(frame, nose_point, 11, (0, 150, 255), 2)


def draw_status_line(frame, label, value, x, y, color):
    draw_text(frame, label, (x, y), MUTED, scale=0.42, thickness=1)
    draw_text(frame, value, (x + 84, y), color, scale=0.46, thickness=1)


def draw_status(
    frame,
    face_detected,
    eye_status,
    blink_detector,
    calibrator,
    cursor,
    tongue_detector,
    detection_quality,
    mouse_controller,
    safety_state,
    ui_state,
    ear_value,
    has_nose_reference,
    now,
):
    frame_height, frame_width, _ = frame.shape
    panel_width = fit_panel_width(frame_width)
    panel_height = 266 if ui_state.diagnostic_enabled else 172
    panel_height = min(panel_height, frame_height - UI_MARGIN * 2)
    left = UI_MARGIN
    top = UI_MARGIN
    right = left + panel_width
    bottom = top + panel_height

    draw_panel(frame, left, top, right, bottom)

    draw_text(frame, "MouthClick", (left + 12, top + 23), WHITE, scale=0.58, thickness=2)
    draw_text(frame, "D diag  ESC/Q sair", (left + 12, bottom - 10), MUTED, scale=0.32, thickness=1)

    face_value = "ok" if face_detected else "sem rosto"
    face_color = GREEN if face_detected else RED
    eye_value, eye_color = short_eye_status(eye_status, face_detected)
    tongue_value, tongue_color = short_tongue_status(tongue_detector, now)
    quality_value = detection_quality.status
    quality_color = GREEN if detection_quality.is_good() else (RED if quality_value == "sem rosto" else YELLOW)
    real_control_value = "on" if mouse_controller.enabled else "off"
    safety_value = "armado" if safety_state.armed else "desarmado"
    real_click_status = mouse_controller.real_click_status(
        safety_state,
        face_detected,
        has_nose_reference,
        detection_quality.is_good(),
        now,
    )
    real_click_color = GREEN if real_click_status == "pronto" else (YELLOW if real_click_status == "clicou" else MUTED)

    draw_status_line(frame, "Rosto", face_value, left + 12, top + 49, face_color)
    draw_status_line(frame, "Lingua", tongue_value, left + 12, top + 69, tongue_color)
    draw_status_line(frame, "Real", f"{real_control_value} | {safety_value} | {real_click_status}", left + 12, top + 89, real_click_color)
    draw_status_line(frame, "Sens", f"x{cursor.sensitivity_x:.1f} y{cursor.sensitivity_y:.1f}", left + 12, top + 109, WHITE)

    quality_x = left + panel_width - 112
    draw_text(frame, f"Qualidade: {quality_value}", (quality_x, top + 23), quality_color, scale=0.36, thickness=1)

    button_top = top + 124
    button_height = 22
    lock_text = "Bloquear" if mouse_controller.enabled or safety_state.armed else "Desbloq."
    button_regions = {
        "toggle_lock": (left + 12, button_top, left + 84, button_top + button_height),
        "sensitivity_down": (left + 90, button_top, left + 116, button_top + button_height),
        "sensitivity_up": (left + 176, button_top, left + 202, button_top + button_height),
        "recenter": (left + 208, button_top, min(right - 10, left + 304), button_top + button_height),
    }
    draw_button(frame, lock_text, button_regions["toggle_lock"], active=mouse_controller.enabled or safety_state.armed)
    draw_button(frame, "-", button_regions["sensitivity_down"])
    draw_button(frame, f"X {cursor.sensitivity_x:.1f}", (left + 120, button_top, left + 172, button_top + button_height))
    draw_button(frame, "+", button_regions["sensitivity_up"])
    draw_button(frame, "Centro", button_regions["recenter"])
    ui_state.set_button_regions(button_regions)

    if ui_state.diagnostic_enabled:
        cursor_x, cursor_y = cursor.position
        diagnostics = [
            f"Olhos {eye_value}  piscadas {blink_detector.blink_count}",
            f"Lingua boca={tongue_detector.mouth_open_ratio:.2f} cor={tongue_detector.color_ratio:.2f}",
            f"Olhos {ear_value:.2f}" if ear_value is not None else "Olhos --",
            f"Limite {blink_detector.blink_threshold:.2f}  suav {CURSOR_SMOOTHING:.2f}",
            f"Cursor x={int(cursor_x)} y={int(cursor_y)}  sens x={cursor.sensitivity_x:.1f} y={cursor.sensitivity_y:.1f}",
            f"Calibracao: {calibrator.message}",
            f"Mouse: {mouse_controller.message}",
            f"Bloqueio: {mouse_controller.real_click_message}",
            f"Cooldown clique: {mouse_controller.real_click_cooldown_remaining(now):.1f}s",
        ]

        y = top + 170
        for line in diagnostics:
            if y > bottom - 28:
                break
            draw_text(frame, line, (left + 12, y), MUTED, scale=0.35, thickness=1)
            y += 13


def control_area_rect(frame):
    frame_height, frame_width, _ = frame.shape
    area_width = int(max(UI_CONTROL_MIN_WIDTH, min(270, frame_width * 0.32)))
    area_height = int(max(UI_CONTROL_MIN_HEIGHT, min(170, frame_height * 0.26)))
    area_width = min(area_width, frame_width - UI_MARGIN * 2)
    area_height = min(area_height, frame_height - UI_MARGIN * 2)
    left = frame_width - area_width - UI_MARGIN
    top = frame_height - area_height - UI_MARGIN
    return left, top, area_width, area_height


def draw_cursor_simulation(frame, cursor, tongue_detector, mouse_controller, now):
    left, top, area_width, area_height = control_area_rect(frame)
    right = left + area_width
    bottom = top + area_height

    draw_panel(frame, left, top, right, bottom, alpha=0.52)
    draw_text(frame, "Cursor", (left + 10, top + 20), WHITE, scale=0.42, thickness=1)
    draw_text(frame, cursor.message, (left + 10, bottom - 9), MUTED, scale=0.32, thickness=1)

    center_x = left + area_width // 2
    center_y = top + area_height // 2
    cv2.line(frame, (center_x, top + 30), (center_x, bottom - 24), (70, 76, 82), 1)
    cv2.line(frame, (left + 10, center_y), (right - 10, center_y), (70, 76, 82), 1)

    cursor_x, cursor_y = cursor.position
    draw_x = int(left + (cursor_x / CONTROL_AREA_WIDTH) * area_width)
    draw_y = int(top + (cursor_y / CONTROL_AREA_HEIGHT) * area_height)
    draw_x = max(left + 8, min(right - 8, draw_x))
    draw_y = max(top + 8, min(bottom - 8, draw_y))

    if mouse_controller.real_click_feedback_active(now):
        cv2.circle(frame, (draw_x, draw_y), 28, GREEN, 3)
        cv2.circle(frame, (draw_x, draw_y), 12, GREEN, -1)
        draw_text(frame, "clique real", (left + 10, top + 40), GREEN, scale=0.42, thickness=1)
    elif tongue_detector.is_feedback_active(now):
        cv2.circle(frame, (draw_x, draw_y), 24, YELLOW, 2)
        cv2.circle(frame, (draw_x, draw_y), 10, YELLOW, -1)
        draw_text(frame, "lingua", (left + 10, top + 40), YELLOW, scale=0.38, thickness=1)
    else:
        cv2.circle(frame, (draw_x, draw_y), 8, MAGENTA, -1)
        cv2.circle(frame, (draw_x, draw_y), 13, WHITE, 1)
