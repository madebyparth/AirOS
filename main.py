import cv2
import sys
from src.hand_detector import HandDetector
from src.canvas import Canvas
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
    
    canvas = Canvas(width=1280, height=720, color=(255, 255, 0), thickness=5)
    fps_calc = FPSCalculator()
    smoother = PointSmoother(smoothing_factor=0.35)

    print("==================================================")
    print(" AirDesk AI - Air Canvas (v1.0)                   ")
    print(" Controls:                                        ")
    print("   'c' / 'C' : Clear Canvas                       ")
    print("   'q' / ESC : Exit Program                       ")
    print("==================================================")

    window_name = "AirDesk AI - Air Canvas"
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

            if index_pos:
                # Smooth the fingertip coordinates
                smooth_x, smooth_y = smoother.update(index_pos[0], index_pos[1])
                # Draw continuous line onto drawing layer
                canvas.draw_line((smooth_x, smooth_y))
            else:
                # Reset stroke & filter history when hand tracking is lost
                smoother.reset()
                canvas.reset_stroke()

            # Composite the drawing canvas layer onto the camera feed
            composite_frame = canvas.composite(frame)

            # Draw HUD overlays
            fps_calc.update()
            fps_calc.draw(composite_frame, pos=(20, 50), color=(0, 255, 0), scale=1, thickness=2)

            status_text = f"Hand: {'DETECTED' if hand_detected else 'SEARCHING'}"
            status_color = (0, 255, 0) if hand_detected else (0, 165, 255)
            cv2.putText(
                composite_frame,
                status_text,
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                status_color,
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                composite_frame,
                "Press 'C' to clear canvas",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

            if index_pos:
                # Render cursor highlight on current smoothed position
                cv2.circle(composite_frame, (smooth_x, smooth_y), 8, (0, 255, 0), cv2.FILLED)
                cv2.circle(composite_frame, (smooth_x, smooth_y), 12, (0, 255, 255), 2)
                cv2.putText(
                    composite_frame,
                    f"Drawing: ({smooth_x}, {smooth_y})",
                    (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

            cv2.imshow(window_name, composite_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("Exiting AirDesk AI...")
                break
            elif key == ord('c') or key == ord('C'):
                canvas.clear()
                print("Canvas cleared.")

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Webcam & MediaPipe resources released successfully.")

if __name__ == "__main__":
    main()
