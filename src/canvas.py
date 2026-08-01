import os
from datetime import datetime
from typing import Tuple, Optional
import cv2
import numpy as np

class Canvas:

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        color: Tuple[int, int, int] = (0, 0, 255),
        thickness: int = 6,
        eraser_radius: int = 25,
    ):
        self.width = width
        self.height = height
        self.color = color
        self.thickness = thickness
        self.eraser_radius = eraser_radius
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

    def erase_at(self, center_point: Tuple[int, int]) -> None:
        cv2.circle(self.canvas, center_point, self.eraser_radius, (0, 0, 0), -1)
        self.prev_point = None

    def reset_stroke(self) -> None:
        self.prev_point = None

    def clear(self) -> None:
        self.canvas.fill(0)
        self.prev_point = None

    def save(self, output_dir: str = "saved_drawings") -> str:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"air_drawing_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        cv2.imwrite(filepath, self.canvas)
        print(f"Canvas saved successfully: {filepath}")
        return filepath

    def composite(self, frame: np.ndarray) -> np.ndarray:
        h, w, _ = frame.shape
        if self.canvas.shape[0] != h or self.canvas.shape[1] != w:
            self.canvas = cv2.resize(self.canvas, (w, h))
            self.width, self.height = w, h

        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        mask = gray > 0
        composite_frame = frame.copy()
        composite_frame[mask] = self.canvas[mask]
        return composite_frame
