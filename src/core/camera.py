import sys
import cv2

class CameraService:
    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print(f"Error: Could not access webcam ID {camera_id}.")
            sys.exit(1)

    def read_frame(self):
        success, frame = self.cap.read()
        if not success:
            return False, None
        frame = cv2.flip(frame, 1)
        return True, frame

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
