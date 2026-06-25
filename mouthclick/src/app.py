import time

import cv2

from .blink_detector import BlinkCalibrator, BlinkDetector, average_eye_openness
from .config import ESC_KEY_CODE, F9_KEY_CODES, LOCK_TOGGLE_KEYS, MODEL_PATH, REAL_MOUSE_TOGGLE_KEYS, WINDOW_NAME
from .cursor_calibration import CursorCalibration
from .detection_quality import DetectionQuality
from .drawing import compose_interface, draw_face_mesh
from .event_log import setup_event_logger
from .face_landmarker import FaceLandmarker
from .mouse_controller import MouseController
from .nose_tracker import NoseTracker
from .safety_state import SafetyState
from .settings import AppSettings
from .tongue_detector import TongueCalibrator, TongueDetector
from .ui_state import UIState
from .visual_cursor import VisualCursor


def toggle_lock(mouse_controller, safety_state, logger=None):
    if mouse_controller.enabled or safety_state.armed:
        mouse_controller.disable("bloqueado por B")
        safety_state.disarm()
        if logger:
            logger.info("sistema bloqueado")
        return

    mouse_controller.toggle()

    if mouse_controller.enabled:
        safety_state.arm()
        if logger:
            logger.info("sistema desbloqueado")
    else:
        safety_state.disarm()
        if logger:
            logger.info("falha ao desbloquear: %s", mouse_controller.message)


def recenter_control(nose_tracker, visual_cursor):
    nose_tracker.reset_reference(nose_tracker.last_point)
    visual_cursor.reset(nose_tracker.reference is not None)


def adjust_sensitivity(visual_cursor, settings, delta):
    visual_cursor.adjust_sensitivity(delta)
    settings.set_value("sensitivity", visual_cursor.sensitivity)
    settings.save()


def capture_nose_calibration(cursor_calibration, nose_tracker, settings, logger):
    completed = cursor_calibration.capture(nose_tracker.last_point)

    if completed:
        settings.set_nose_calibration(cursor_calibration.to_dict())
        settings.save()
        logger.info("calibracao do nariz salva")


def run():
    settings = AppSettings.load()
    settings.set_value("start_unlocked", True)
    logger = setup_event_logger()
    logger.info("aplicacao iniciada")

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
    blink_detector.blink_threshold = settings.get_float("blink_threshold", blink_detector.blink_threshold)
    calibrator = BlinkCalibrator()
    cursor_calibration = CursorCalibration(settings.data.get("nose_calibration"))
    detection_quality = DetectionQuality()
    mouse_controller = MouseController()
    nose_tracker = NoseTracker()
    safety_state = SafetyState()
    tongue_thresholds = settings.tongue_thresholds()
    tongue_detector = TongueDetector(*tongue_thresholds)
    tongue_calibrator = TongueCalibrator()
    ui_state = UIState()
    ui_state.diagnostic_enabled = settings.get_bool("diagnostic_enabled", False)
    visual_cursor = VisualCursor(settings.get_float("sensitivity", 3.0))

    def handle_mouse_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        button_name = ui_state.button_at(x, y)

        if button_name == "toggle_lock":
            toggle_lock(mouse_controller, safety_state, logger)
        elif button_name == "sensitivity_down":
            adjust_sensitivity(visual_cursor, settings, -0.5)
        elif button_name == "sensitivity_up":
            adjust_sensitivity(visual_cursor, settings, 0.5)
        elif button_name == "recenter":
            recenter_control(nose_tracker, visual_cursor)
            logger.info("controle recentralizado pelo botao")
        elif button_name == "calibrate_nose":
            capture_nose_calibration(cursor_calibration, nose_tracker, settings, logger)
        elif button_name == "calibrate_tongue":
            tongue_calibrator.start(time.monotonic())
            logger.info("calibracao da lingua iniciada pelo botao")
        elif button_name == "toggle_diagnostic":
            ui_state.toggle_diagnostic()
            settings.set_value("diagnostic_enabled", ui_state.diagnostic_enabled)
            settings.save()
        elif button_name == "exit":
            mouse_controller.disable("desativado pelo botao sair")
            safety_state.disarm()
            ui_state.request_exit()
            logger.info("aplicacao encerrada pelo botao sair")

    cv2.setMouseCallback(WINDOW_NAME, handle_mouse_click)

    if settings.get_bool("start_unlocked", True):
        toggle_lock(mouse_controller, safety_state, logger)

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
            cursor_hold_active = False
            now = time.monotonic()
            has_nose_reference = False

            if face_detected:
                landmarks = results.face_landmarks[0]
                nose_point = nose_tracker.locate(landmarks, frame.shape)
                detection_quality.update(face_detected, nose_point)
                draw_face_mesh(frame, landmarks, nose_point)

                ear_value = average_eye_openness(landmarks)
                calibrator.update(blink_detector, face_detected, ear_value, now)

                if calibrator.active:
                    eye_status = "Calibrando"
                    blink_detector.reset_closed_state()
                else:
                    eye_status, blink_detected = blink_detector.update(ear_value, now)

                if detection_quality.is_good():
                    tongue_click_detected = tongue_detector.update(
                        frame,
                        landmarks,
                        now,
                        allow_trigger=not tongue_calibrator.active,
                    )
                    tongue_calibrator.update(tongue_detector, face_detected, now)
                else:
                    tongue_detector.reset()
                    tongue_calibrator.update(tongue_detector, False, now)

                cursor_hold_active = tongue_calibrator.active or tongue_detector.is_cursor_hold_active(now)

                if cursor_hold_active:
                    visual_cursor.hold_position("pausado: lingua")
                else:
                    visual_cursor.update_from_nose(nose_point, nose_tracker.reference, cursor_calibration)
            else:
                detection_quality.update(face_detected, nose_point)
                calibrator.update(blink_detector, face_detected, ear_value, now)
                visual_cursor.update_from_nose(nose_point, nose_tracker.reference, cursor_calibration)
                blink_detector.reset_closed_state()
                tongue_detector.reset()
                tongue_calibrator.update(tongue_detector, face_detected, now)

                if mouse_controller.enabled:
                    mouse_controller.disable("desativado: sem rosto")
                    safety_state.disarm()
                    logger.info("controle real desativado por perda de rosto")

            if calibrator.consume_completed():
                settings.set_value("blink_threshold", blink_detector.blink_threshold)
                settings.save()
                logger.info("calibracao de piscadas salva")

            if tongue_calibrator.consume_completed():
                settings.set_tongue_thresholds(
                    tongue_detector.mouth_open_threshold,
                    tongue_detector.color_ratio_threshold,
                )
                settings.save()
                logger.info("calibracao da lingua salva")

            has_nose_reference = nose_tracker.reference is not None

            if cursor_hold_active:
                mouse_controller.hold_movement("pausado: lingua")
            else:
                mouse_controller.move_from_visual_position(
                    visual_cursor.position,
                    face_detected,
                    has_nose_reference,
                    detection_quality.is_good(),
                    visual_cursor.sensitivity_x,
                )

            if tongue_click_detected and not tongue_calibrator.active:
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

            frame = compose_interface(
                frame,
                face_detected,
                eye_status,
                blink_detector,
                calibrator,
                visual_cursor,
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
            )
            cv2.imshow(WINDOW_NAME, frame)

            if ui_state.exit_requested:
                break

            key = cv2.waitKeyEx(1)

            if key == ord("c"):
                calibrator.start(time.monotonic())

            if key == ord("r"):
                recenter_control(nose_tracker, visual_cursor)
                logger.info("controle recentralizado por tecla")

            if key in (ord("+"), ord("=")):
                adjust_sensitivity(visual_cursor, settings, 0.5)

            if key in (ord("-"), ord("_")):
                adjust_sensitivity(visual_cursor, settings, -0.5)

            if key == ord("d"):
                ui_state.toggle_diagnostic()
                settings.set_value("diagnostic_enabled", ui_state.diagnostic_enabled)
                settings.save()

            if key == ord("n"):
                capture_nose_calibration(cursor_calibration, nose_tracker, settings, logger)

            if key == ord("t"):
                tongue_calibrator.start(time.monotonic())
                logger.info("calibracao da lingua iniciada por tecla")

            if key in LOCK_TOGGLE_KEYS:
                toggle_lock(mouse_controller, safety_state, logger)

            if key in REAL_MOUSE_TOGGLE_KEYS:
                mouse_controller.toggle()
                logger.info("controle real alternado por atalho: %s", mouse_controller.message)

            if key in F9_KEY_CODES:
                safety_state.toggle_armed()
                logger.info("sistema armado alternado por atalho: %s", safety_state.status_text)

            if key == ESC_KEY_CODE:
                if mouse_controller.enabled:
                    mouse_controller.disable("desativado por ESC")
                    safety_state.disarm()
                    logger.info("controle real desativado por ESC")
                    continue
                break

            if key == ord("q"):
                mouse_controller.disable("desativado por Q")
                safety_state.disarm()
                logger.info("aplicacao encerrada por Q")
                break
    finally:
        settings.set_value("sensitivity", visual_cursor.sensitivity)
        settings.set_value("diagnostic_enabled", ui_state.diagnostic_enabled)
        settings.save()
        mouse_controller.disable("desativado")
        safety_state.disarm()
        video_capture.release()
        face_landmarker_context.__exit__(None, None, None)
        cv2.destroyAllWindows()
        logger.info("aplicacao finalizada")

    return 0
