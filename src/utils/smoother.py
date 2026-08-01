from typing import Tuple, Optional

class PointSmoother:
    def __init__(self, smoothing_factor: float = 0.35):
        self.alpha = min(max(smoothing_factor, 0.01), 1.0)
        self.prev_x: Optional[float] = None
        self.prev_y: Optional[float] = None

    def update(self, x: float, y: float) -> Tuple[int, int]:
        if self.prev_x is None or self.prev_y is None:
            self.prev_x = float(x)
            self.prev_y = float(y)
        else:
            self.prev_x = self.alpha * x + (1.0 - self.alpha) * self.prev_x
            self.prev_y = self.alpha * y + (1.0 - self.alpha) * self.prev_y

        return int(round(self.prev_x)), int(round(self.prev_y))

    def reset(self) -> None:
        self.prev_x = None
        self.prev_y = None
