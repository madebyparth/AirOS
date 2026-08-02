import time
from typing import Tuple, Optional
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, Slot
from src.core.camera import CameraService
from src.core.tracking import HandTracker
from src.core.gestures import GestureClassifier, Gesture
from src.core.actions import ActionDispatcher
from src.mouse.mode_handler import MouseModeHandler, MouseState
from src.apps.whiteboard import WhiteboardApp

class TrackingWorker(QThread):
    """
    Decoupled Background Tracking Worker Thread.
    Runs camera capture, MediaPipe tracking, gesture classification, and mouse handler.
    Emits Qt Signals to drive PySide6 Desktop Overlay UI without thread blocking.
    """
    frame_processed = Signal(object)              # Debug Frame (np.ndarray)
    victory_hold_progress = Signal(float)         # Remaining countdown seconds
    victory_toggle_triggered = Signal()           # Victory 1.0s hold met
    cursor_position_updated = Signal(object)       # tuple[int, int] (screen_x, screen_y)
    pinch_click_triggered = Signal(object)         # tuple[int, int] (screen_x, screen_y)
    status_message_updated = Signal(str)

    def __init__(self, action_dispatcher: ActionDispatcher, hold_threshold_sec: float = 1.0):
        super().__init__()
        self.dispatcher = action_dispatcher
        self.hold_threshold_sec = hold_threshold_sec

        self.running = False
        self.show_debug_window = False

        self.victory_start_time: Optional[float] = None
        self.victory_confirmed = False

    def run(self):
        camera = CameraService(camera_id=0, width=1280, height=720)
        tracker = HandTracker(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        classifier = GestureClassifier()
        mouse_handler = MouseModeHandler(frame_width=1280, frame_height=720)
        whiteboard_app = WhiteboardApp()

        self.running = True

        try:
            while self.running:
                success, frame = camera.read_frame()
                if not success:
                    time.sleep(0.005)
                    continue

                current_time = time.time()

                hand_detected = tracker.process(frame)
                landmarks = tracker.get_landmarks(frame) if hand_detected else []
                index_pos = tracker.get_index_fingertip(frame) if hand_detected else None

                is_pinching = (mouse_handler.state in [MouseState.CLICK_PENDING, MouseState.DRAG])
                gesture = classifier.classify(landmarks, is_currently_pinching_middle=is_pinching) if hand_detected else Gesture.NONE

                # 1. Victory (PEACE_SIGN) 1.0s Hold Check
                if gesture == Gesture.PEACE_SIGN:
                    if self.victory_start_time is None:
                        self.victory_start_time = current_time
                        self.victory_confirmed = False

                    elapsed = current_time - self.victory_start_time
                    remaining = max(0.0, self.hold_threshold_sec - elapsed)
                    self.victory_hold_progress.emit(round(remaining, 1))

                    if elapsed >= self.hold_threshold_sec and not self.victory_confirmed:
                        self.victory_confirmed = True
                        self.victory_toggle_triggered.emit()
                else:
                    self.victory_start_time = None
                    self.victory_confirmed = False

                # 2. Mouse Controller & Cursor Tracking
                mouse_res = mouse_handler.handle_frame(gesture, index_pos) if hand_detected else None
                screen_pos = mouse_res["screen_pos"] if (mouse_res and mouse_res["screen_pos"]) else None

                if screen_pos:
                    self.cursor_position_updated.emit(screen_pos)

                if gesture == Gesture.PINCH_MIDDLE:
                    self.pinch_click_triggered.emit(screen_pos)

                # 3. Optional Debug Preview Frame
                if self.show_debug_window:
                    frame = tracker.draw_landmarks(frame)
                    cv2.putText(frame, f"Gesture: {gesture.value} | Hand: {'DETECTED' if hand_detected else 'SEARCHING'}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
                    self.frame_processed.emit(frame)

                time.sleep(0.001)

        finally:
            mouse_handler.reset()
            tracker.close()
            camera.release()

    def stop(self):
        self.running = False
        self.wait(timeout=1000)
