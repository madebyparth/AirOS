import os
import time
from enum import Enum
from typing import Tuple, Optional, Dict, Any
from src.core.gestures import Gesture
from src.utils.smoother import PointSmoother
from src.apps.base_app import BaseAirApp
from src.apps.whiteboard.canvas import Canvas

class DrawingState(Enum):
    IDLE = "IDLE"
    HOVER = "HOVER"
    DRAWING = "DRAWING"
    ERASING = "ERASING"
    CLEARING = "CLEARING"
    SAVING = "SAVING"

class WhiteboardApp(BaseAirApp):
    """
    AirOS Modular Whiteboard Application.
    Provides stateful Air Drawing & Canvas rendering.
    """
    name = "Whiteboard"
    description = "Air Drawing & Canvas Annotation App"

    def __init__(self, save_hold_seconds: float = 2.0, clear_hold_seconds: float = 2.0):
        self.canvas = Canvas()
        self.smoother = PointSmoother(smoothing_factor=0.35)
        self.state = DrawingState.IDLE
        self.save_hold_seconds = save_hold_seconds
        self.clear_hold_seconds = clear_hold_seconds

        self.thumbs_up_start_time: Optional[float] = None
        self.save_confirmed: bool = False
        self.last_saved_path: Optional[str] = None
        self.saved_banner_until: float = 0.0

        self.peace_sign_start_time: Optional[float] = None
        self.clear_confirmed: bool = False
        self.cleared_banner_until: float = 0.0

    def process_frame(
        self,
        gesture: Gesture,
        position: Optional[Tuple[int, int]],
        frame_shape: Tuple[int, int, int],
    ) -> Dict[str, Any]:
        result = {
            "app": self.name,
            "state": DrawingState.IDLE.value,
            "is_drawing": False,
            "is_erasing": False,
            "cursor_pos": None,
            "action_text": "WHITEBOARD IDLE",
            "saved_file": None,
            "save_countdown": None,
            "clear_countdown": None,
        }

        current_time = time.time()

        if gesture != Gesture.THUMBS_UP:
            self.thumbs_up_start_time = None
            self.save_confirmed = False

        if gesture != Gesture.PEACE_SIGN:
            self.peace_sign_start_time = None
            self.clear_confirmed = False

        if gesture == Gesture.INDEX_ONLY and position is not None:
            smooth_x, smooth_y = self.smoother.update(position[0], position[1])
            self.canvas.draw_line((smooth_x, smooth_y))
            self.state = DrawingState.DRAWING
            result["is_drawing"] = True
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "DRAWING (Red Pen)"

        elif gesture == Gesture.OPEN_PALM and position is not None:
            smooth_x, smooth_y = self.smoother.update(position[0], position[1])
            self.canvas.erase_at((smooth_x, smooth_y))
            self.state = DrawingState.ERASING
            result["is_erasing"] = True
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "ERASING"

        elif gesture == Gesture.CLOSED_FIST and position is not None:
            smooth_x, smooth_y = self.smoother.update(position[0], position[1])
            self.canvas.reset_stroke()
            self.state = DrawingState.HOVER
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "HOVER (Fist Move)"

        elif gesture == Gesture.PEACE_SIGN:
            self.canvas.reset_stroke()
            self.state = DrawingState.CLEARING

            if self.peace_sign_start_time is None:
                self.peace_sign_start_time = current_time
                self.clear_confirmed = False

            elapsed = current_time - self.peace_sign_start_time
            remaining = max(0.0, self.clear_hold_seconds - elapsed)

            if elapsed >= self.clear_hold_seconds and not self.clear_confirmed:
                self.canvas.clear()
                self.smoother.reset()
                self.clear_confirmed = True
                self.cleared_banner_until = current_time + 2.0

            if not self.clear_confirmed:
                result["clear_countdown"] = round(remaining, 1)
                result["action_text"] = f"HOLD PEACE TO CLEAR: {remaining:.1f}s"
            else:
                result["action_text"] = "CANVAS CLEARED"

        elif gesture == Gesture.THUMBS_UP:
            self.canvas.reset_stroke()
            self.smoother.reset()
            self.state = DrawingState.SAVING

            if self.thumbs_up_start_time is None:
                self.thumbs_up_start_time = current_time
                self.save_confirmed = False

            elapsed = current_time - self.thumbs_up_start_time
            remaining = max(0.0, self.save_hold_seconds - elapsed)

            if elapsed >= self.save_hold_seconds and not self.save_confirmed:
                self.last_saved_path = self.canvas.save()
                self.save_confirmed = True
                self.saved_banner_until = current_time + 3.0

            if not self.save_confirmed:
                result["save_countdown"] = round(remaining, 1)
                result["action_text"] = f"HOLD TO SAVE: {remaining:.1f}s"
            else:
                result["saved_file"] = self.last_saved_path
                result["action_text"] = f"SAVED: {os.path.basename(self.last_saved_path)}"

        else:
            self.smoother.reset()
            self.canvas.reset_stroke()
            self.state = DrawingState.IDLE

            if current_time < self.saved_banner_until and self.last_saved_path:
                result["action_text"] = f"SAVED: {os.path.basename(self.last_saved_path)}"
            elif current_time < self.cleared_banner_until:
                result["action_text"] = "CANVAS CLEARED"
            else:
                result["action_text"] = f"IDLE ({gesture.value})"

        result["state"] = self.state.value
        return result

    def composite_overlay(self, frame):
        return self.canvas.composite(frame)

    def clear(self):
        self.canvas.clear()

    def reset(self):
        self.smoother.reset()
        self.canvas.reset_stroke()
        self.state = DrawingState.IDLE
