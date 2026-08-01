from typing import Tuple, Optional
import cv2
import numpy as np

class Canvas:
    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        color: Tuple[int, int, int] = (255, 255, 0),
        thickness: int = 5,
    ):
        self.width = width
        self.height = height
        self.color = color
        self.thickness = thickness
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.prev_point: Optional[Tuple[int, int]] = None

    def draw_line(self, curr_point: Tuple[int, int]) -> None:
        if self.prev_point is not None:
            cv2.line(
                self.canvas,
                self.prev_point,
                curr_point,
                self.color,
                self.thickness,
                cv2.LINE_AA,
            )
        self.prev_point = curr_point

    def reset_stroke(self) -> None:
        self.prev_point = None

    def clear(self) -> None:
        self.canvas.fill(0)
        self.prev_point = None

    def composite(self, frame: np.ndarray) -> np.ndarray:
        h, w, _ = frame.shape
        if self.canvas.shape[0] != h or self.canvas.shape[1] != w:
            self.canvas = cv2.resize(self.canvas, (w, h))
            self.width, self.height = w, h

        mask = self.canvas > 0
        composite_frame = frame.copy()
        composite_frame[mask] = self.canvas[mask]
        return composite_frame
