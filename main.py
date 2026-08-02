import cv2
import sys
from src.core.camera import CameraService
from src.core.tracking import HandTracker
from src.core.gestures import GestureClassifier, Gesture
from src.core.actions import ActionDispatcher
from src.mouse.mode_handler import MouseModeHandler, MouseState
from src.apps.whiteboard.app import WhiteboardApp
from src.system_actions.spotify import OpenSpotifyAction
from src.system_actions.screenshot import TakeScreenshotAction
from src.system_actions.console_log import ConsoleLogAction
from src.utils.fps_calculator import FPSCalculator

class AirOSMode:
    MOUSE = "MOUSE"
    WHITEBOARD = "WHITEBOARD"
    SYSTEM = "SYSTEM"

def main():
    print("==================================================")
    print("                 AirOS Runtime v1.0               ")
    print("      AI-Powered Desktop Interaction Platform     ")
    print("==================================================")
    print(" Mouse Interactions:                              ")
    print("   ☝️  Index Finger        : Move Desktop Cursor   ")
    print("   🤌  Thumb + Middle Pinch: Left Click / Drag     ")
    print("   ✌️  Victory Gesture     : Open AirOS Menu       ")
    print(" Controls:                                        ")
    print("   'm' / 'M' : Cycle Mode (MOUSE -> WHITEBOARD -> SYSTEM)")
    print("   'c' / 'C' : Clear Canvas (Whiteboard Mode)     ")
    print("   'q' / ESC : Exit AirOS Safely                  ")
    print("==================================================")

    camera = CameraService(camera_id=0, width=1280, height=720)
    tracker = HandTracker(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    classifier = GestureClassifier()
    fps_calc = FPSCalculator()

    mouse_handler = MouseModeHandler(frame_width=1280, frame_height=720)
    whiteboard_app = WhiteboardApp()

    dispatcher = ActionDispatcher()
    dispatcher.register_action(OpenSpotifyAction())
    dispatcher.register_action(TakeScreenshotAction())
    dispatcher.register_action(ConsoleLogAction())
    dispatcher.bind_gesture("SYSTEM", Gesture.OPEN_PALM, "open_spotify")
    dispatcher.bind_gesture("SYSTEM", Gesture.THUMBS_UP, "take_screenshot")
    dispatcher.bind_gesture("SYSTEM", Gesture.INDEX_ONLY, "console_log")

    active_mode = AirOSMode.MOUSE

    window_name = "AirOS - Desktop Workspace"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            success, frame = camera.read_frame()
            if not success:
                continue

            hand_detected = tracker.process(frame)
            landmarks = tracker.get_landmarks(frame) if hand_detected else []
            index_pos = tracker.get_index_fingertip(frame) if hand_detected else None

            is_pinching = (mouse_handler.state in [MouseState.CLICK_PENDING, MouseState.DRAG])
            gesture = classifier.classify(landmarks, is_currently_pinching_middle=is_pinching) if hand_detected else Gesture.NONE

            frame = tracker.draw_landmarks(frame)

            if active_mode == AirOSMode.MOUSE:
                mouse_res = mouse_handler.handle_frame(gesture, index_pos)
                status_text = f"Mouse State: {mouse_res['state']} | Action: {mouse_res['action_text']}"
                if mouse_res["screen_pos"]:
                    sx, sy = mouse_res["screen_pos"]
                    status_text += f" | Cursor: ({sx}, {sy})"
                display_frame = frame

            elif active_mode == AirOSMode.WHITEBOARD:
                wb_res = whiteboard_app.process_frame(gesture, index_pos, frame.shape)
                display_frame = whiteboard_app.composite_overlay(frame)
                status_text = f"Whiteboard Action: {wb_res['action_text']}"

            elif active_mode == AirOSMode.SYSTEM:
                mouse_handler.reset()
                exec_res = dispatcher.dispatch("SYSTEM", gesture, message="Pointer Active")
                display_frame = frame
                if exec_res:
                    status_text = f"Action Executed: {exec_res.get('message', exec_res.get('action'))}"
                else:
                    status_text = f"System Control Ready ({gesture.value})"

            fps_calc.update()
            fps_calc.draw(display_frame, pos=(20, 40), color=(0, 255, 0), scale=0.8, thickness=2)

            mode_color = (255, 200, 0) if active_mode == AirOSMode.MOUSE else (0, 255, 255) if active_mode == AirOSMode.WHITEBOARD else (255, 100, 255)
            cv2.putText(display_frame, f"AirOS Mode: {active_mode}  (Press 'M' to switch)", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.65, mode_color, 2, cv2.LINE_AA)
            cv2.putText(display_frame, f"Hand: {'DETECTED' if hand_detected else 'SEARCHING'} | Gesture: {gesture.value}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(display_frame, status_text, (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

            if active_mode == AirOSMode.MOUSE:
                guide = "[MOUSE MODE: Index=Cursor | Thumb+Middle Pinch=Left Click (<280ms) / Hold Drag (>280ms) | Victory=Menu]"
            elif active_mode == AirOSMode.WHITEBOARD:
                guide = "[WHITEBOARD APP: Index=Draw | Palm=Erase | Fist=Hover | Peace=Hold 2s Clear | ThumbUp=Hold 2s Save]"
            else:
                guide = "[SYSTEM MODE: Open Palm=Spotify | Thumbs Up=Screenshot | Index=Log]"

            cv2.putText(display_frame, guide, (20, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)

            cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("Shutting down AirOS...")
                break
            elif key == ord('m') or key == ord('M'):
                if active_mode == AirOSMode.MOUSE:
                    active_mode = AirOSMode.WHITEBOARD
                elif active_mode == AirOSMode.WHITEBOARD:
                    active_mode = AirOSMode.SYSTEM
                else:
                    active_mode = AirOSMode.MOUSE
                mouse_handler.reset()
                whiteboard_app.reset()
                print(f"[AirOS] Switched Active Mode to: {active_mode}")
            elif key == ord('c') or key == ord('C'):
                if active_mode == AirOSMode.WHITEBOARD:
                    whiteboard_app.clear()
                    print("[AirOS Whiteboard] Canvas cleared.")

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        mouse_handler.reset()
        tracker.close()
        camera.release()
        cv2.destroyAllWindows()
        print("AirOS runtime safely stopped.")

if __name__ == "__main__":
    main()
