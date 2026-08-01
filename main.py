import cv2
import sys
from src.hand_detector import HandDetector
from src.utils.fps_calculator import FPSCalculator

def main():
    # Initialize camera capture (device index 0)
    cap = cv2.VideoCapture(0)
    
    # Configure capture resolution for optimal performance & quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        sys.exit(1)

    # Instantiate HandDetector configured for 1 hand (Milestone 1 requirement)
    detector = HandDetector(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    
    # FPS Calculator utility
    fps_calc = FPSCalculator()

    print("==================================================")
    print(" AirDesk AI - Milestone 1: Hand Landmark Tracking ")
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

            # Mirror flip frame horizontally for intuitive webcam interaction
            frame = cv2.flip(frame, 1)

            # Process frame & draw 21 MediaPipe landmarks
            frame, hand_detected = detector.find_hands(frame, draw=True)

            # Extract landmark positions if a hand is present
            landmarks = detector.find_positions(frame, draw=False)

            # Calculate and render FPS
            fps_calc.update()
            fps_calc.draw(frame, pos=(20, 50), color=(0, 255, 0), scale=1, thickness=2)

            # Render status bar overlay
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

            # Display total landmark count when detected
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

            # Render final composite frame
            cv2.imshow(window_name, frame)

            # Handle exit keys ('q' or ESC key 27)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("Exiting AirDesk AI...")
                break

            # Break loop if user closes OpenCV window via 'X' button
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        # Resource cleanup
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Webcam & MediaPipe resources released successfully.")

if __name__ == "__main__":
    main()
