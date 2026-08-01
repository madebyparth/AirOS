import time
import cv2

class FPSCalculator:
    def __init__(self, buffer_size: int = 10):
        self.buffer_size = buffer_size
        self.prev_time = time.time()
        self.fps = 0.0

    def update(self) -> float:
        current_time = time.time()
        delta_time = current_time - self.prev_time
        self.prev_time = current_time

        if delta_time > 0:
            self.fps = 1.0 / delta_time
        return self.fps

    def draw(self, img, pos=(10, 30), color=(0, 255, 0), scale=1, thickness=2):
        cv2.putText(
            img,
            f"FPS: {int(self.fps)}",
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        return img
