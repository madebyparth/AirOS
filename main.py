import cv2
import sys
from src.hand_detector import HandDetector
from src.canvas import Canvas
from src.gesture_detector import GestureDetector, Gesture
from src.mode_manager import ModeManager, AppMode, DrawingState
from src.utils.fps_calculator import FPSCalculator
from src.utils.smoother import PointSmoother

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        sys.exit(1)

    detector = HandDetector(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    
    canvas = Canvas(width=1280, height=720, color=(0, 0, 255), thickness=6, eraser_radius=25)
    fps_calc = FPSCalculator()
    smoother = PointSmoother(smoothing_factor=0.35)
    gesture_detector = GestureDetector()
    mode_manager = ModeManager(initial_mode=AppMode.DRAW)

    print("==================================================")
    print(" AirDesk AI - Action Framework & Mode Dispatcher ")
    print(" Active Mode: DRAW                                ")
    print(" Controls:                                        ")
    print("   'm' / 'M'      : Switch Mode (DRAW <-> SYSTEM) ")
    print("   'c' / 'C'      : Clear Canvas                   ")
    print("   'q' / ESC      : Exit Program                   ")
    print("==================================================")

    window_name = "AirDesk AI - Workspace"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Warning: Empty frame received from webcam. Retrying...")
                continue

            frame = cv2.flip(frame, 1)
            frame, hand_detected = detector.find_hands(frame, draw=True)
            landmarks = detector.find_positions(frame, draw=False)
            index_pos = detector.get_index_fingertip(frame, draw=False)

            gesture = gesture_detector.detect(landmarks)
            mode_action = mode_manager.process(gesture, index_pos, smoother, canvas)
            composite_frame = canvas.composite(frame)

            fps_calc.update()
            fps_calc.draw(composite_frame, pos=(20, 45), color=(0, 255, 0), scale=0.9, thickness=2)

            mode_color = (255, 200, 0) if mode_action['active_mode'] == AppMode.DRAW.value else (255, 100, 255)
            cv2.putText(
                composite_frame,
                f"Mode: {mode_action['active_mode']}  (Press 'M' to switch)",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                mode_color,
                2,
                cv2.LINE_AA,
            )

            status_text = f"Hand: {'DETECTED' if hand_detected else 'SEARCHING'}"
            status_color = (0, 255, 0) if hand_detected else (0, 165, 255)
            cv2.putText(
                composite_frame,
                status_text,
                (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                status_color,
                1,
                cv2.LINE_AA,
            )

            gesture_color = (0, 255, 255) if gesture != Gesture.NONE else (150, 150, 150)
            cv2.putText(
                composite_frame,
                f"Gesture: {gesture.value}",
                (20, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                gesture_color,
                1,
                cv2.LINE_AA,
            )

            state_str = mode_action["state"]
            if state_str == DrawingState.DRAWING.value:
                action_color = (0, 0, 255) 
            elif state_str == DrawingState.ERASING.value:
                action_color = (255, 255, 255)  
            elif state_str == DrawingState.HOVER.value:
                action_color = (0, 255, 255)  
            elif state_str in [DrawingState.SAVING.value, DrawingState.CLEARING.value]:
                action_color = (0, 255, 0) 
            else:
                action_color = (180, 180, 180)

            cv2.putText(
                composite_frame,
                f"Action: {mode_action['action_text']}",
                (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                action_color,
                2 if state_str in [DrawingState.DRAWING.value, DrawingState.ERASING.value, DrawingState.SAVING.value] else 1,
                cv2.LINE_AA,
            )

            # 2-Second Save Banner Overlay
            save_countdown = mode_action.get("save_countdown")
            if save_countdown is not None and save_countdown > 0:
                h, w, _ = composite_frame.shape
                banner_x = w // 2 - 200
                banner_y = 40
                banner_w = 400
                banner_h = 60

                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (30, 30, 30), cv2.FILLED)
                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (0, 255, 255), 2)
                progress_ratio = (2.0 - save_countdown) / 2.0
                fill_w = int(banner_w * progress_ratio)
                cv2.rectangle(composite_frame, (banner_x + 2, banner_y + 2), (banner_x + fill_w, banner_y + banner_h - 2), (0, 180, 0), cv2.FILLED)
                cv2.putText(composite_frame, f"HOLD TO SAVE: {save_countdown:.1f}s", (banner_x + 60, banner_y + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

            # 2-Second Clear Banner Overlay
            clear_countdown = mode_action.get("clear_countdown")
            if clear_countdown is not None and clear_countdown > 0:
                h, w, _ = composite_frame.shape
                banner_x = w // 2 - 200
                banner_y = 40
                banner_w = 400
                banner_h = 60

                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (30, 30, 30), cv2.FILLED)
                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (0, 100, 255), 2)
                progress_ratio = (2.0 - clear_countdown) / 2.0
                fill_w = int(banner_w * progress_ratio)
                cv2.rectangle(composite_frame, (banner_x + 2, banner_y + 2), (banner_x + fill_w, banner_y + banner_h - 2), (0, 140, 255), cv2.FILLED)
                cv2.putText(composite_frame, f"HOLD PEACE TO CLEAR: {clear_countdown:.1f}s", (banner_x + 30, banner_y + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

            # 2-Second System Action Banner Overlay (Spotify / Screenshot)
            action_countdown = mode_action.get("action_countdown")
            action_target = mode_action.get("action_target")
            if action_countdown is not None and action_countdown > 0:
                h, w, _ = composite_frame.shape
                banner_x = w // 2 - 220
                banner_y = 40
                banner_w = 440
                banner_h = 60

                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (30, 30, 30), cv2.FILLED)
                cv2.rectangle(composite_frame, (banner_x, banner_y), (banner_x + banner_w, banner_y + banner_h), (255, 100, 255), 2)
                progress_ratio = (2.0 - action_countdown) / 2.0
                fill_w = int(banner_w * progress_ratio)
                cv2.rectangle(composite_frame, (banner_x + 2, banner_y + 2), (banner_x + fill_w, banner_y + banner_h - 2), (200, 0, 200), cv2.FILLED)
                cv2.putText(composite_frame, f"HOLD FOR {action_target}: {action_countdown:.1f}s", (banner_x + 20, banner_y + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

            if mode_action['active_mode'] == AppMode.DRAW.value:
                guide_msg = "[DRAW MODE: Index=Draw(Red) | Palm=Erase | Fist=Hover | Peace=Hold 2s Clear | ThumbUp=Hold 2s Save]"
            else:
                guide_msg = "[SYSTEM MODE: Hold Palm 2s=Spotify | Hold ThumbUp 2s=Screenshot | Index=Console Log]"

            cv2.putText(
                composite_frame,
                guide_msg,
                (20, composite_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )

            cursor_pos = mode_action.get("cursor_pos")
            if cursor_pos:
                cx, cy = cursor_pos
                if state_str == DrawingState.DRAWING.value:
                    cv2.circle(composite_frame, (cx, cy), 8, (0, 0, 255), cv2.FILLED)
                    cv2.circle(composite_frame, (cx, cy), 12, (0, 0, 255), 2)
                elif state_str == DrawingState.HOVER.value or mode_action['active_mode'] == AppMode.SYSTEM_CONTROL.value:
                    cv2.circle(composite_frame, (cx, cy), 6, (255, 255, 0), 2)
                elif state_str == DrawingState.ERASING.value:
                    cv2.circle(composite_frame, (cx, cy), canvas.eraser_radius, (255, 255, 255), 2)
                    cv2.circle(composite_frame, (cx, cy), 3, (255, 255, 255), cv2.FILLED)

            cv2.imshow(window_name, composite_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("Exiting AirDesk AI...")
                break
            elif key == ord('c') or key == ord('C'):
                canvas.clear()
                print("Canvas cleared.")
            elif key == ord('m') or key == ord('M'):
                new_mode = AppMode.SYSTEM_CONTROL if mode_manager.active_mode == AppMode.DRAW else AppMode.DRAW
                mode_manager.set_mode(new_mode)
                print(f"[MODE SWITCH] Active Mode changed to: {new_mode.value}")

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Webcam & MediaPipe resources released successfully.")

if __name__ == "__main__":
    main()
