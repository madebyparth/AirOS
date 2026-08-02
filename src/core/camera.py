import sys
import time
import threading
import cv2

class CameraService:
    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720):
        self.camera_id = camera_id
        self.width = width
        self.height = height

        # DirectShow with CAP_PROP_BUFFERSIZE = 1 flushes driver queues for real-time capture
        if sys.platform.startswith("win"):
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_id)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            print(f"Error: Could not access webcam ID {camera_id}.")
            sys.exit(1)

        self.ret, frame = self.cap.read()
        self.current_frame = cv2.flip(frame, 1) if (self.ret and frame is not None) else None

        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                flipped = cv2.flip(frame, 1)
                with self.lock:
                    self.ret = ret
                    self.current_frame = flipped
            else:
                time.sleep(0.001)

    def read_frame(self):
        with self.lock:
            if self.current_frame is None:
                return False, None
            return self.ret, self.current_frame.copy()

    def release(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        if self.cap and self.cap.isOpened():
            self.cap.release()
