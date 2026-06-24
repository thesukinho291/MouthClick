import time

import cv2

from .blink_detector import BlinkCalibrator, BlinkDetector, average_eye_openness
from .config import ESC_KEY_CODE, F9_KEY_CODES, LOCK_TOGGLE_KEYS, MODEL_PATH, REAL_MOUSE_TOGGLE_KEYS, WINDOW_NAME
from .detection_quality import DetectionQuality
from .drawing import draw_cursor_simulation, draw_face_mesh, draw_status
from .face_landmarker import FaceLandmarker
from .mouse_controller import MouseController
from .nose_tracker import NoseTracker
from .safety_state import SafetyState
from .tongue_detector import TongueDetector
from .ui_state import UIState
from .visual_cursor import VisualCursor


def toggle_lock(mouse_controller, safety_state):
    if mouse_controller.enabled or safety_state.armed:
        mouse_controller.disable("bloqueado por B")
        safety_state.disarm()
        return

    mouse_controller.toggle()

    if mouse_controller.enabled:
        safety_state.arm()
    else:
        safety_state.disarm()


def recenter_control(nose_tracker, visual_cursor):
    nose_tracker.reset_reference(nose_tracker.last_point)
    visual_cursor.reset(nose_tracker.reference is not None)


def run():
    try:
        face_landmarker_context = FaceLandmarker()
        face_landmarker_context.__enter__()
    except FileNotFoundError:
        print(f"Erro: modelo do MediaPipe nao encontrado em {MODEL_PATH}")
        print("Baixe o arquivo face_landmarker.task para a pasta models antes de executar.")
        return 1

    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        face_landmarker_context.__exit__(None, None, None)
        print("Erro: nao foi possivel abrir a webcam.")
        print("Verifique se a camera esta conectada, liberada no Windows e nao esta em uso por outro app.")
        return 1

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    blink_detector = BlinkDetector()
    calibrator = BlinkCalibrator()
    detection_quality = DetectionQuality()
    mouse_controller = MouseController()
    nose_tracker = NoseTracker()
    safety_state = SafetyState()
    tongue_detector = TongueDetector()
    ui_state = UIState()
    visual_cursor = VisualCursor()

    def handle_mouse_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        button_name = ui_state.button_at(x, y)

        if button_name == "toggle_lock":
            toggle_lock(mouse_controller, safety_state)
        elif button_name == "sensitivity_down":
            visual_cursor.adjust_sensitivity(-0.5)
        elif button_name == "sensitivity_up":
            visual_cursor.adjust_sensitivity(0.5)
        elif button_name == "recenter":
            recenter_control(nose_tracker, visual_cursor)

    cv2.setMouseCallback(WINDOW_NAME, handle_mouse_click)
    toggle_lock(mouse_controller, safety_state)

    try:
        while True:
            success, frame = video_capture.read()

            if not success:
                mouse_controller.disable("desativado: camera falhou")
                print("Erro: nao foi possivel ler a imagem da webcam.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_landmarker_context.detect(rgb_frame)

            face_detected = bool(results.face_landmarks)
            eye_status = "Rosto nao detectado"
            blink_detected = False
            ear_value = None
            nose_point = None
            tongue_click_detected = False
            now = time.monotonic()
            has_nose_reference = False

            if face_detected:
                landmarks = results.face_landmarks[0]
                nose_point = nose_tracker.locate(landmarks, frame.shape)
                detection_quality.update(face_detected, nose_point)
                draw_face_mesh(frame, landmarks, nose_point)

                ear_value = average_eye_openness(landmarks)
                calibrator.update(blink_detector, face_detected, ear_value, now)
                visual_cursor.update_from_nose(nose_point, nose_tracker.reference)

                if calibrator.active:
                    eye_status = "Calibrando"
                    blink_detector.reset_closed_state()
                else:
                    eye_status, blink_detected = blink_detector.update(ear_value, now)

                if detection_quality.is_good():
                    tongue_click_detected = tongue_detector.update(frame, landmarks, now)
                else:
                    tongue_detector.reset()
            else:
                detection_quality.update(face_detected, nose_point)
                calibrator.update(blink_detector, face_detected, ear_value, now)
                visual_cursor.update_from_nose(nose_point, nose_tracker.reference)
                blink_detector.reset_closed_state()
                tongue_detector.reset()

            has_nose_reference = nose_tracker.reference is not None

            mouse_controller.move_from_visual_position(
                visual_cursor.position,
                face_detected,
                has_nose_reference,
                detection_quality.is_good(),
            )

            if tongue_click_detected:
                mouse_controller.try_real_left_click(
                    safety_state,
                    face_detected,
                    has_nose_reference,
                    detection_quality.is_good(),
                    now,
                )
            else:
                mouse_controller.update_real_click_message(
                    safety_state,
                    face_detected,
                    has_nose_reference,
                    detection_quality.is_good(),
                    now,
                )

            draw_cursor_simulation(frame, visual_cursor, tongue_detector, mouse_controller, now)
            draw_status(
                frame,
                face_detected,
                eye_status,
                blink_detector,
                calibrator,
                visual_cursor,
                tongue_detector,
                detection_quality,
                mouse_controller,
                safety_state,
                ui_state,
                ear_value,
                has_nose_reference,
                now,
            )
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKeyEx(1)

            if key == ord("c"):
                calibrator.start(time.monotonic())

            if key == ord("r"):
                recenter_control(nose_tracker, visual_cursor)

            if key in (ord("+"), ord("=")):
                visual_cursor.adjust_sensitivity(0.5)

            if key in (ord("-"), ord("_")):
                visual_cursor.adjust_sensitivity(-0.5)

            if key == ord("d"):
                ui_state.toggle_diagnostic()

            if key in LOCK_TOGGLE_KEYS:
                toggle_lock(mouse_controller, safety_state)

            if key in REAL_MOUSE_TOGGLE_KEYS:
                mouse_controller.toggle()

            if key in F9_KEY_CODES:
                safety_state.toggle_armed()

            if key == ESC_KEY_CODE:
                if mouse_controller.enabled:
                    mouse_controller.disable("desativado por ESC")
                    safety_state.disarm()
                    continue
                break

            if key == ord("q"):
                mouse_controller.disable("desativado por Q")
                safety_state.disarm()
                break
    finally:
        mouse_controller.disable("desativado")
        safety_state.disarm()
        video_capture.release()
        face_landmarker_context.__exit__(None, None, None)
        cv2.destroyAllWindows()

    return 0
