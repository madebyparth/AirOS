import ctypes
import math
from typing import Tuple, Optional

class ScreenMapper:
    """
    Advanced AirOS Adaptive Cursor Controller.
    Features:
    1. Active Interaction Box (ROI): Smaller hand movements cover 100% of desktop screen.
    2. Speed-Adaptive Dynamic Smoothing: Heavy filtering when still (zero jitter), zero lag when fast.
    3. Configurable Sensitivity & Pointer Acceleration.
    """
    def __init__(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
        margin_x: float = 0.18,
        margin_y: float = 0.18,
        sensitivity: float = 1.2,
        min_alpha: float = 0.12,
        max_alpha: float = 0.85,
        speed_threshold: float = 15.0,
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.sensitivity = sensitivity
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.speed_threshold = speed_threshold

        # Query desktop screen resolution via Windows User32 API
        try:
            user32 = ctypes.windll.user32
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
        except Exception:
            self.screen_width = 1920
            self.screen_height = 1080

        self.prev_norm_x: Optional[float] = None
        self.prev_norm_y: Optional[float] = None
        self.prev_screen_x: Optional[float] = None
        self.prev_screen_y: Optional[float] = None

    def map_to_screen(self, frame_x: int, frame_y: int) -> Tuple[int, int]:
        """
        Maps webcam frame pixel (X, Y) to Desktop Screen (X, Y) with
        Active ROI scaling, dynamic velocity-adaptive smoothing, and cursor acceleration.
        """
        # 1. Active Interaction Area (ROI Box Mapping)
        min_x = self.frame_width * self.margin_x
        max_x = self.frame_width * (1.0 - self.margin_x)
        min_y = self.frame_height * self.margin_y
        max_y = self.frame_height * (1.0 - self.margin_y)

        # Normalize position to [0.0, 1.0] within the ROI box
        norm_x = (frame_x - min_x) / (max_x - min_x) if max_x > min_x else 0.5
        norm_y = (frame_y - min_y) / (max_y - min_y) if max_y > min_y else 0.5

        # Clamp normalized values to [0.0, 1.0]
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Apply center-offset sensitivity scaling
        center_x, center_y = 0.5, 0.5
        norm_x = center_x + (norm_x - center_x) * self.sensitivity
        norm_y = center_y + (norm_y - center_y) * self.sensitivity
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Raw desktop screen target
        target_screen_x = norm_x * (self.screen_width - 1.0)
        target_screen_y = norm_y * (self.screen_height - 1.0)

        # 2. Adaptive Speed-Based Dynamic Smoothing
        if self.prev_screen_x is None or self.prev_screen_y is None:
            smooth_x = target_screen_x
            smooth_y = target_screen_y
        else:
            # Measure movement velocity in screen pixels
            dx = target_screen_x - self.prev_screen_x
            dy = target_screen_y - self.prev_screen_y
            speed = math.hypot(dx, dy)

            # Dynamically compute alpha: low speed -> heavy filtering (low alpha), high speed -> responsive (high alpha)
            speed_factor = min(1.0, speed / self.speed_threshold)
            alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * (speed_factor ** 1.5)

            # Apply acceleration for fast flicks
            accel_gain = 1.0 + (0.35 * speed_factor)
            target_screen_x = self.prev_screen_x + dx * accel_gain
            target_screen_y = self.prev_screen_y + dy * accel_gain

            smooth_x = alpha * target_screen_x + (1.0 - alpha) * self.prev_screen_x
            smooth_y = alpha * target_screen_y + (1.0 - alpha) * self.prev_screen_y

        # Clamp bounds to screen resolution
        smooth_x = max(0.0, min(self.screen_width - 1.0, smooth_x))
        smooth_y = max(0.0, min(self.screen_height - 1.0, smooth_y))

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        return (int(round(smooth_x)), int(round(smooth_y)))

    def reset(self) -> None:
        self.prev_norm_x = None
        self.prev_norm_y = None
        self.prev_screen_x = None
        self.prev_screen_y = None
