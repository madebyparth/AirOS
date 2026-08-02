import ctypes
from typing import Tuple, Optional
import numpy as np

class ScreenMapper:
    """
    Maps normalized camera coordinates or frame pixel positions
    to native desktop screen coordinates with smooth interpolation.
    """
    def __init__(self, frame_width: int = 1280, frame_height: int = 720, smoothing_factor: float = 0.35):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.smoothing_factor = smoothing_factor

        # Fetch desktop screen dimensions via Windows User32 API
        try:
            user32 = ctypes.windll.user32
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
        except Exception:
            self.screen_width = 1920
            self.screen_height = 1080

        self.prev_screen_x: Optional[float] = None
        self.prev_screen_y: Optional[float] = None

    def map_to_screen(self, frame_x: int, frame_y: int) -> Tuple[int, int]:
        """
        Converts webcam frame pixel position (X, Y) to Desktop Screen (X, Y).
        Applies exponential moving average for ultra-smooth movement.
        """
        raw_screen_x = (frame_x / self.frame_width) * self.screen_width
        raw_screen_y = (frame_y / self.frame_height) * self.screen_height

        # Clamp bounds
        raw_screen_x = max(0.0, min(self.screen_width - 1.0, raw_screen_x))
        raw_screen_y = max(0.0, min(self.screen_height - 1.0, raw_screen_y))

        if self.prev_screen_x is None or self.prev_screen_y is None:
            smooth_x = raw_screen_x
            smooth_y = raw_screen_y
        else:
            smooth_x = self.smoothing_factor * raw_screen_x + (1.0 - self.smoothing_factor) * self.prev_screen_x
            smooth_y = self.smoothing_factor * raw_screen_y + (1.0 - self.smoothing_factor) * self.prev_screen_y

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        return (int(round(smooth_x)), int(round(smooth_y)))

    def reset(self) -> None:
        self.prev_screen_x = None
        self.prev_screen_y = None
