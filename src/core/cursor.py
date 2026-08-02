import ctypes
import math
from typing import Tuple, Optional

class ScreenMapper:
    def __init__(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
        margin_x: float = 0.15,
        margin_y: float = 0.15,
        sensitivity: float = 1.20,
        min_alpha: float = 0.10,
        max_alpha: float = 0.75,
        deadzone_px: float = 4.5,
        cutoff_speed: float = 12.0,
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.sensitivity = sensitivity
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.deadzone_px = deadzone_px
        self.cutoff_speed = cutoff_speed

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
        min_x = self.frame_width * self.margin_x
        max_x = self.frame_width * (1.0 - self.margin_x)
        min_y = self.frame_height * self.margin_y
        max_y = self.frame_height * (1.0 - self.margin_y)

        norm_x = (frame_x - min_x) / (max_x - min_x) if max_x > min_x else 0.5
        norm_y = (frame_y - min_y) / (max_y - min_y) if max_y > min_y else 0.5
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        center_x, center_y = 0.5, 0.5
        norm_x = center_x + (norm_x - center_x) * self.sensitivity
        norm_y = center_y + (norm_y - center_y) * self.sensitivity
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        target_screen_x = norm_x * (self.screen_width - 1.0)
        target_screen_y = norm_y * (self.screen_height - 1.0)

        if self.prev_screen_x is None or self.prev_screen_y is None:
            smooth_x = target_screen_x
            smooth_y = target_screen_y
        else:
            dx = target_screen_x - self.prev_screen_x
            dy = target_screen_y - self.prev_screen_y
            dist = math.hypot(dx, dy)

            # Ignore micro-jitter below deadzone threshold
            if dist < self.deadzone_px:
                return (int(round(self.prev_screen_x)), int(round(self.prev_screen_y)))

            ratio = min(1.0, (dist / self.cutoff_speed) ** 1.5)
            alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * ratio

            smooth_x = self.prev_screen_x + alpha * dx
            smooth_y = self.prev_screen_y + alpha * dy

        smooth_x = max(0.0, min(self.screen_width - 1.0, smooth_x))
        smooth_y = max(0.0, min(self.screen_height - 1.0, smooth_y))

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        return (int(round(smooth_x)), int(round(smooth_y)))

    def reset(self) -> None:
        self.prev_screen_x = None
        self.prev_screen_y = None
