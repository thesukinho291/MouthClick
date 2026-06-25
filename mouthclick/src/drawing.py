import cv2
import numpy as np
from mediapipe.tasks.python import vision

from .config import CONTROL_AREA_HEIGHT, CONTROL_AREA_WIDTH, CURSOR_SMOOTHING
from .nose_tracker import normalized_to_pixel


CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

BG = (16, 18, 22)
SURFACE = (24, 29, 38)
SURFACE_2 = (30, 36, 46)
BORDER = (55, 64, 78)
WHITE = (234, 238, 245)
MUTED = (145, 153, 166)
DIM = (90, 98, 112)
GREEN = (96, 225, 112)
GREEN_DARK = (38, 120, 50)
YELLOW = (0, 210, 255)
RED = (80, 90, 235)
BLUE = (255, 138, 60)


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


def draw_round_rect(frame, rect, color, radius=10, thickness=-1):
    left, top, right, bottom = rect
    radius = max(1, min(radius, (right - left) // 2, (bottom - top) // 2))

    if thickness < 0:
        cv2.rectangle(frame, (left + radius, top), (right - radius, bottom), color, -1)
        cv2.rectangle(frame, (left, top + radius), (right, bottom - radius), color, -1)
        cv2.circle(frame, (left + radius, top + radius), radius, color, -1)
        cv2.circle(frame, (right - radius, top + radius), radius, color, -1)
        cv2.circle(frame, (left + radius, bottom - radius), radius, color, -1)
        cv2.circle(frame, (right - radius, bottom - radius), radius, color, -1)
        return

    cv2.line(frame, (left + radius, top), (right - radius, top), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (left + radius, bottom), (right - radius, bottom), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (left, top + radius), (left, bottom - radius), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (right, top + radius), (right, bottom - radius), color, thickness, cv2.LINE_AA)
    cv2.ellipse(frame, (left + radius, top + radius), (radius, radius), 180, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(frame, (right - radius, top + radius), (radius, radius), 270, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(frame, (right - radius, bottom - radius), (radius, radius), 0, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(frame, (left + radius, bottom - radius), (radius, radius), 90, 0, 90, color, thickness, cv2.LINE_AA)


def draw_panel(frame, rect, fill=SURFACE, border=BORDER, radius=9):
    draw_round_rect(frame, rect, fill, radius=radius, thickness=-1)
    draw_round_rect(frame, rect, border, radius=radius, thickness=1)


def draw_pip(frame, center, color, glow=False):
    if glow:
        cv2.circle(frame, center, 12, tuple(int(channel * 0.35) for channel in color), -1, cv2.LINE_AA)
    cv2.circle(frame, center, 5, color, -1, cv2.LINE_AA)


def draw_button(frame, text, rect, active=False, primary=False):
    if primary:
        fill = (44, 150, 58) if active else (42, 120, 52)
        border = (72, 205, 88)
    else:
        fill = SURFACE_2 if active else (26, 31, 40)
        border = GREEN if active else BORDER

    draw_round_rect(frame, rect, fill, radius=8, thickness=-1)
    draw_round_rect(frame, rect, border, radius=8, thickness=1)

    left, top, right, bottom = rect
    baseline = top + (bottom - top) // 2 + 6
    draw_text(frame, text, (left + 14, baseline), WHITE, scale=0.48, thickness=1)


def ellipsize(text, max_chars):
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def draw_face_mesh(frame, landmarks, nose_point):
    frame_height, frame_width, _ = frame.shape

    for connection in vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION:
        start_point = normalized_to_pixel(landmarks[connection.start], frame_width, frame_height)
        end_point = normalized_to_pixel(landmarks[connection.end], frame_width, frame_height)
        cv2.line(frame, start_point, end_point, (38, 120, 66), 1)

    for index, landmark in enumerate(landmarks):
        if index % 4 == 0:
            point = normalized_to_pixel(landmark, frame_width, frame_height)
            cv2.circle(frame, point, 1, (88, 195, 124), -1)

    if nose_point is not None:
        cv2.circle(frame, nose_point, 6, GREEN, -1)
        cv2.circle(frame, nose_point, 15, (230, 240, 230), 2)
        cv2.line(frame, (nose_point[0] - 22, nose_point[1]), (nose_point[0] + 22, nose_point[1]), (230, 240, 230), 2)
        cv2.line(frame, (nose_point[0], nose_point[1] - 22), (nose_point[0], nose_point[1] + 22), (230, 240, 230), 2)


def status_color(ok, warn=False):
    if ok:
        return GREEN
    if warn:
        return YELLOW
    return RED


def short_tongue_status(tongue_detector, now):
    if tongue_detector.is_feedback_active(now):
        return "clique"
    if tongue_detector.message == "lingua detectada":
        return "detectada"
    if tongue_detector.message == "gesto de clique":
        return "clique"
    return "aguardando"


def quality_text(detection_quality):
    if detection_quality.status == "boa":
        return "boa", GREEN
    if detection_quality.status == "instavel":
        return "instavel", YELLOW
    return "sem rosto", RED


def fit_camera_to_rect(frame, rect):
    left, top, right, bottom = rect
    target_w = right - left
    target_h = bottom - top
    frame_h, frame_w, _ = frame.shape
    scale = min(target_w / frame_w, target_h / frame_h)
    resized_w = int(frame_w * scale)
    resized_h = int(frame_h * scale)
    resized = cv2.resize(frame, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
    x = left + (target_w - resized_w) // 2
    y = top + (target_h - resized_h) // 2
    return resized, (x, y, x + resized_w, y + resized_h)


def draw_camera_area(canvas, camera_frame, rect, face_detected, detection_quality, cursor, tongue_detector, mouse_controller, safety_state, now):
    draw_panel(canvas, rect, fill=(10, 13, 18), border=(48, 58, 68), radius=8)
    resized, image_rect = fit_camera_to_rect(camera_frame, rect)
    img_left, img_top, img_right, img_bottom = image_rect
    canvas[img_top:img_bottom, img_left:img_right] = resized

    overlay = canvas.copy()
    cv2.rectangle(overlay, (img_left, img_top), (img_right, img_bottom), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.12, canvas, 0.88, 0, canvas)

    face_label = "Rosto detectado" if face_detected else "Rosto nao detectado"
    face_fill = (42, 85, 49) if face_detected else (58, 44, 48)
    badge = (img_left + 18, img_top + 16, img_left + 185, img_top + 48)
    draw_round_rect(canvas, badge, face_fill, radius=12, thickness=-1)
    draw_pip(canvas, (img_left + 34, img_top + 32), GREEN if face_detected else RED, glow=False)
    draw_text(canvas, face_label, (img_left + 48, img_top + 38), WHITE, scale=0.45, thickness=1)

    q_text, q_color = quality_text(detection_quality)
    q_badge = (img_right - 152, img_top + 16, img_right - 12, img_top + 48)
    draw_round_rect(canvas, q_badge, (30, 33, 39), radius=10, thickness=-1)
    draw_pip(canvas, (img_right - 136, img_top + 32), q_color, glow=False)
    draw_text(canvas, f"Qualidade: {q_text}", (img_right - 124, img_top + 38), WHITE, scale=0.38, thickness=1)

    draw_camera_brackets(canvas, image_rect, face_detected)
    draw_cursor_on_camera(canvas, image_rect, cursor, tongue_detector, mouse_controller, now)

    if not mouse_controller.enabled and not safety_state.armed:
        lock_rect = (img_left + 18, img_bottom - 58, img_left + 230, img_bottom - 20)
        draw_round_rect(canvas, lock_rect, (35, 38, 45), radius=12, thickness=-1)
        draw_text(canvas, "Sistema bloqueado", (lock_rect[0] + 14, lock_rect[1] + 25), YELLOW, scale=0.48, thickness=1)


def draw_camera_brackets(canvas, rect, face_detected):
    if not face_detected:
        return

    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    bracket_color = (235, 240, 240)
    bracket = 44
    x1 = left + int(width * 0.30)
    x2 = right - int(width * 0.30)
    y1 = top + int(height * 0.19)
    y2 = bottom - int(height * 0.31)

    for x, y, sx, sy in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        cv2.line(canvas, (x, y), (x + sx * bracket, y), bracket_color, 2, cv2.LINE_AA)
        cv2.line(canvas, (x, y), (x, y + sy * bracket), bracket_color, 2, cv2.LINE_AA)


def draw_cursor_on_camera(canvas, rect, cursor, tongue_detector, mouse_controller, now):
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    cursor_x, cursor_y = cursor.position
    draw_x = int(left + (cursor_x / CONTROL_AREA_WIDTH) * width)
    draw_y = int(top + (cursor_y / CONTROL_AREA_HEIGHT) * height)
    draw_x = max(left + 20, min(right - 20, draw_x))
    draw_y = max(top + 20, min(bottom - 20, draw_y))

    if mouse_controller.real_click_feedback_active(now):
        cv2.circle(canvas, (draw_x, draw_y), 28, GREEN, 3, cv2.LINE_AA)
        cv2.circle(canvas, (draw_x, draw_y), 9, GREEN, -1, cv2.LINE_AA)
        draw_text(canvas, "clique", (draw_x + 18, draw_y - 14), GREEN, scale=0.42, thickness=1)
        return

    if tongue_detector.is_feedback_active(now):
        cv2.circle(canvas, (draw_x, draw_y), 24, YELLOW, 2, cv2.LINE_AA)
        cv2.circle(canvas, (draw_x, draw_y), 8, YELLOW, -1, cv2.LINE_AA)
        return

    cv2.circle(canvas, (draw_x, draw_y), 18, (230, 236, 245), 2, cv2.LINE_AA)
    cv2.circle(canvas, (draw_x, draw_y), 8, GREEN, -1, cv2.LINE_AA)


def draw_top_bar(canvas, mouse_controller, safety_state, detection_quality):
    cv2.rectangle(canvas, (0, 0), (CANVAS_WIDTH, 58), (11, 14, 18), -1)
    cv2.line(canvas, (0, 58), (CANVAS_WIDTH, 58), (36, 43, 52), 1)

    draw_round_rect(canvas, (20, 14, 42, 38), (18, 34, 52), radius=6, thickness=-1)
    draw_round_rect(canvas, (20, 14, 42, 38), BLUE, radius=6, thickness=1)
    draw_text(canvas, "M", (27, 32), BLUE, scale=0.42, thickness=1)
    draw_text(canvas, "MouthClick", (52, 34), WHITE, scale=0.62, thickness=2)

    ready = mouse_controller.enabled and safety_state.armed and detection_quality.is_good()
    pill_text = "Sistema pronto" if ready else "Sistema bloqueado"
    pill_color = GREEN if ready else YELLOW
    pill_left = CANVAS_WIDTH - 220
    pill = (pill_left, 12, pill_left + 168, 40)
    draw_round_rect(canvas, pill, (20, 26, 32), radius=14, thickness=-1)
    draw_round_rect(canvas, pill, (34, 42, 50), radius=14, thickness=1)
    draw_pip(canvas, (pill_left + 18, 26), pill_color, glow=ready)
    draw_text(canvas, pill_text, (pill_left + 34, 32), pill_color, scale=0.42, thickness=1)


def draw_control_panel(canvas, rect, cursor, mouse_controller, safety_state, tongue_detector, detection_quality, ui_state, tongue_calibrator, cursor_calibration):
    draw_panel(canvas, rect)
    left, top, right, _ = rect
    unlocked = mouse_controller.enabled or safety_state.armed

    button_regions = {}
    main_button = (left + 14, top + 14, right - 14, top + 70)
    draw_button(canvas, "Bloquear mouse real" if unlocked else "Ativar mouse real", main_button, active=unlocked, primary=True)
    button_regions["toggle_lock"] = main_button

    status_y = top + 100
    click_status = real_click_short_status(mouse_controller)
    draw_status_row(canvas, left + 24, status_y, "Mouse real", "ativo" if mouse_controller.enabled else "bloqueado", mouse_controller.enabled)
    draw_status_row(canvas, left + 24, status_y + 30, "Clique lingua", click_status, click_status == "pronto")

    recenter = (left + 14, top + 160, right - 14, top + 208)
    cal_nose = (left + 14, top + 218, right - 14, top + 266)
    cal_tongue = (left + 14, top + 276, right - 14, top + 324)
    diag = (left + 14, top + 334, right - 14, top + 382)
    exit_button = (left + 14, top + 392, right - 14, top + 440)
    draw_button(canvas, "Centralizar nariz", recenter)
    draw_button(canvas, "Calibrar nariz", cal_nose, active=cursor_calibration.active)
    draw_button(canvas, "Calibrar lingua", cal_tongue, active=tongue_calibrator.active)
    draw_button(canvas, "Modo diagnostico", diag, active=ui_state.diagnostic_enabled)
    draw_button(canvas, "Sair", exit_button)
    button_regions.update(
        {
            "recenter": recenter,
            "calibrate_nose": cal_nose,
            "calibrate_tongue": cal_tongue,
            "toggle_diagnostic": diag,
            "exit": exit_button,
        }
    )

    sens_panel = (left, top + 460, right, top + 590)
    draw_panel(canvas, sens_panel, fill=(18, 23, 30))
    draw_text(canvas, "Sensibilidade", (left + 16, top + 490), MUTED, scale=0.42, thickness=1)
    draw_text(canvas, f"X {cursor.sensitivity_x:.1f}", (left + 48, top + 526), WHITE, scale=0.48, thickness=1)
    draw_text(canvas, f"Y {cursor.sensitivity_y:.1f}", (left + 144, top + 526), WHITE, scale=0.48, thickness=1)

    down = (left + 16, top + 542, left + 58, top + 582)
    up = (right - 58, top + 542, right - 16, top + 582)
    draw_button(canvas, "-", down)
    draw_button(canvas, "+", up)
    button_regions["sensitivity_down"] = down
    button_regions["sensitivity_up"] = up

    ui_state.set_button_regions(button_regions)


def draw_status_row(canvas, x, y, label, value, ok):
    color = GREEN if ok else MUTED
    draw_pip(canvas, (x, y - 5), color, glow=ok)
    draw_text(canvas, f"{label}: {ellipsize(value, 18)}", (x + 18, y), WHITE if ok else MUTED, scale=0.39, thickness=1)


def real_click_short_status(mouse_controller):
    message = mouse_controller.real_click_message.replace("bloqueado: ", "")
    if message == "pronto":
        return "pronto"
    if message == "clique real executado":
        return "clicou"
    if "controle real" in message:
        return "bloqueado"
    if "sistema" in message:
        return "desarmado"
    if "cooldown" in message:
        return message
    if "qualidade" in message:
        return "qualidade ruim"
    if "rosto" in message:
        return "sem rosto"
    return ellipsize(message, 16)


def draw_security_panel(canvas, rect, face_detected, detection_quality, mouse_controller, safety_state):
    draw_panel(canvas, rect)
    left, top, right, _ = rect
    draw_text(canvas, "Seguranca", (left + 16, top + 28), GREEN, scale=0.58, thickness=2)
    cv2.line(canvas, (left, top + 48), (right, top + 48), (42, 50, 62), 1)

    q_text, _ = quality_text(detection_quality)
    rows = [
        ("Rosto detectado" if face_detected else "Sem rosto", face_detected),
        (f"Qualidade: {q_text}", detection_quality.is_good()),
        ("Sistema desbloqueado" if safety_state.armed else "Sistema bloqueado", safety_state.armed),
        ("Use Bloquear ou Sair", True),
    ]

    y = top + 86
    for label, ok in rows:
        icon_color = GREEN if ok else YELLOW
        draw_round_rect(canvas, (left + 16, y - 19, left + 46, y + 11), (34, 48, 42) if ok else (50, 45, 34), radius=15, thickness=-1)
        draw_pip(canvas, (left + 31, y - 4), icon_color, glow=False)
        draw_text(canvas, label, (left + 58, y + 2), WHITE, scale=0.43, thickness=1)
        y += 48

    if mouse_controller.enabled or safety_state.armed:
        warning = (left, rect[3] - 40, right, rect[3])
        draw_round_rect(canvas, warning, (55, 50, 15), radius=0, thickness=-1)
        draw_text(canvas, "Atencao: controle real ativo", (left + 36, rect[3] - 15), YELLOW, scale=0.43, thickness=1)
        draw_text(canvas, "!", (left + 18, rect[3] - 15), YELLOW, scale=0.55, thickness=2)


def draw_diagnostic_panel(canvas, rect, ui_state, tongue_detector, cursor, mouse_controller, calibrator, tongue_calibrator, cursor_calibration, ear_value, now):
    draw_panel(canvas, rect)
    left, top, right, _ = rect
    draw_text(canvas, "Modo diagnostico", (left + 14, top + 28), BLUE, scale=0.50, thickness=2)
    cv2.line(canvas, (left, top + 48), (right, top + 48), (42, 50, 62), 1)

    if not ui_state.diagnostic_enabled:
        draw_text(canvas, "Clique em Modo diagnostico", (left + 14, top + 82), MUTED, scale=0.38, thickness=1)
        draw_text(canvas, "Interface limpa ativa", (left + 14, top + 110), GREEN, scale=0.42, thickness=1)
        return

    cursor_x, cursor_y = cursor.position
    lines = [
        f"Boca: {tongue_detector.mouth_open_ratio:.2f}",
        f"Cor lingua: {tongue_detector.color_ratio:.2f}",
        f"Cursor: X {int(cursor_x)}  Y {int(cursor_y)}",
        f"Cooldown: {mouse_controller.real_click_cooldown_remaining(now):.1f}s",
        f"Olhos: {ear_value:.2f}" if ear_value is not None else "Olhos: --",
        f"Suavizacao: {CURSOR_SMOOTHING:.2f}",
        f"Nariz: {cursor_calibration.message}",
        f"Lingua: {tongue_calibrator.message}",
        f"Mouse: {mouse_controller.message}",
    ]

    y = top + 76
    for line in lines:
        if y > rect[3] - 16:
            break
        draw_text(canvas, line, (left + 14, y), WHITE if y < top + 158 else MUTED, scale=0.36, thickness=1)
        y += 21


def draw_bottom_info(canvas):
    draw_text(canvas, "MouthClick v0.1.0", (20, CANVAS_HEIGHT - 18), MUTED, scale=0.40, thickness=1)
    draw_pip(canvas, (CANVAS_WIDTH - 178, CANVAS_HEIGHT - 24), GREEN, glow=False)
    draw_text(canvas, "Privacidade: processamento local", (CANVAS_WIDTH - 162, CANVAS_HEIGHT - 18), GREEN, scale=0.38, thickness=1)


def compose_interface(
    camera_frame,
    face_detected,
    eye_status,
    blink_detector,
    calibrator,
    cursor,
    tongue_detector,
    tongue_calibrator,
    cursor_calibration,
    detection_quality,
    mouse_controller,
    safety_state,
    ui_state,
    ear_value,
    has_nose_reference,
    now,
):
    _ = eye_status, blink_detector, has_nose_reference
    canvas = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), BG, dtype=np.uint8)

    draw_top_bar(canvas, mouse_controller, safety_state, detection_quality)
    draw_camera_area(
        canvas,
        camera_frame,
        (14, 72, 790, 690),
        face_detected,
        detection_quality,
        cursor,
        tongue_detector,
        mouse_controller,
        safety_state,
        now,
    )
    draw_control_panel(
        canvas,
        (804, 72, 1030, 690),
        cursor,
        mouse_controller,
        safety_state,
        tongue_detector,
        detection_quality,
        ui_state,
        tongue_calibrator,
        cursor_calibration,
    )
    draw_security_panel(canvas, (1044, 72, 1266, 330), face_detected, detection_quality, mouse_controller, safety_state)
    draw_diagnostic_panel(
        canvas,
        (1044, 438, 1266, 690),
        ui_state,
        tongue_detector,
        cursor,
        mouse_controller,
        calibrator,
        tongue_calibrator,
        cursor_calibration,
        ear_value,
        now,
    )
    draw_bottom_info(canvas)
    return canvas
