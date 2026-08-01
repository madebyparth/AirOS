import cv2
import sys
from src.hand_detector import HandDetector
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
    
    fps_calc = FPSCalculator()
    smoother = PointSmoother(smoothing_factor=0.35)

    print("==================================================")
    print(" AirDesk AI - Hand Landmark & Cursor Smoothing    ")
    print(" Press 'q' or 'Esc' to exit.                      ")
    print("==================================================")

    window_name = "AirDesk AI - Hand Tracking"
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

            fps_calc.update()
            fps_calc.draw(frame, pos=(20, 50), color=(0, 255, 0), scale=1, thickness=2)

            status_text = f"Hand: {'DETECTED' if hand_detected else 'SEARCHING'}"
            status_color = (0, 255, 0) if hand_detected else (0, 165, 255)
            cv2.putText(
                frame,
                status_text,
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                status_color,
                2,
                cv2.LINE_AA,
            )

            if hand_detected and landmarks:
                cv2.putText(
                    frame,
                    f"Landmarks: {len(landmarks)}/21",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

            if index_pos:
                # Apply exponential moving average smoothing
                smooth_x, smooth_y = smoother.update(index_pos[0], index_pos[1])

                # Render raw tip position indicator (small cyan dot)
                cv2.circle(frame, index_pos, 4, (255, 255, 0), cv2.FILLED)

                # Render smoothed cursor (green filled cursor with yellow outer ring)
                cv2.circle(frame, (smooth_x, smooth_y), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(frame, (smooth_x, smooth_y), 15, (0, 255, 255), 2)

                # HUD readout for raw and smoothed positions
                cv2.putText(
                    frame,
                    f"Raw Tip: ({index_pos[0]}, {index_pos[1]})",
                    (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"Smooth Cursor: ({smooth_x}, {smooth_y})",
                    (20, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )
            else:
                # Reset filter history when tracking is lost to prevent jump lag upon re-detection
                smoother.reset()

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("Exiting AirDesk AI...")
                break

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Webcam & MediaPipe resources released successfully.")

if __name__ == "__main__":
    main()
