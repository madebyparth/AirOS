import os
import time
from enum import Enum
from typing import Tuple, Optional, Dict, Any
from src.gesture_detector import Gesture

class AppMode(Enum):
    DRAW = "DRAW"
    MOUSE = "MOUSE"
    PRESENTATION = "PRESENTATION"
    MEDIA_CONTROL = "MEDIA_CONTROL"

class DrawingState(Enum):
    IDLE = "IDLE"
    HOVER = "HOVER"
    DRAWING = "DRAWING"
    ERASING = "ERASING"
    CLEARING = "CLEARING"
    SAVING = "SAVING"

class BaseModeHandler:
    def handle_gesture(
        self,
        gesture: Gesture,
        position: Optional[Tuple[int, int]],
        smoother: Any,
        canvas: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError

class DrawModeHandler(BaseModeHandler):
    def __init__(self, save_hold_seconds: float = 2.0, clear_hold_seconds: float = 2.0):
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

    def handle_gesture(
        self,
        gesture: Gesture,
        position: Optional[Tuple[int, int]],
        smoother: Any,
        canvas: Any,
    ) -> Dict[str, Any]:
        result = {
            "active_mode": AppMode.DRAW.value,
            "state": DrawingState.IDLE.value,
            "is_drawing": False,
            "is_erasing": False,
            "cursor_pos": None,
            "action_text": "IDLE",
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

        if gesture == Gesture.PINCH and position is not None:
            smooth_x, smooth_y = smoother.update(position[0], position[1])
            canvas.draw_line((smooth_x, smooth_y))
            self.state = DrawingState.DRAWING
            result["is_drawing"] = True
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "DRAWING (Red Pen)"

        elif gesture == Gesture.INDEX_ONLY and position is not None:
            smooth_x, smooth_y = smoother.update(position[0], position[1])
            canvas.reset_stroke()
            self.state = DrawingState.HOVER
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "HOVER (Cursor Move)"

        elif gesture == Gesture.CLOSED_FIST and position is not None:
            smooth_x, smooth_y = smoother.update(position[0], position[1])
            canvas.erase_at((smooth_x, smooth_y))
            self.state = DrawingState.ERASING
            result["is_erasing"] = True
            result["cursor_pos"] = (smooth_x, smooth_y)
            result["action_text"] = "ERASING"

        elif gesture == Gesture.PEACE_SIGN:
            canvas.reset_stroke()
            self.state = DrawingState.CLEARING

            if self.peace_sign_start_time is None:
                self.peace_sign_start_time = current_time
                self.clear_confirmed = False

            elapsed = current_time - self.peace_sign_start_time
            remaining = max(0.0, self.clear_hold_seconds - elapsed)

            if elapsed >= self.clear_hold_seconds and not self.clear_confirmed:
                canvas.clear()
                smoother.reset()
                self.clear_confirmed = True
                self.cleared_banner_until = current_time + 2.0

            if not self.clear_confirmed:
                result["clear_countdown"] = round(remaining, 1)
                result["action_text"] = f"HOLD PEACE TO CLEAR: {remaining:.1f}s"
            else:
                result["action_text"] = "CANVAS CLEARED"

        elif gesture == Gesture.THUMBS_UP:
            canvas.reset_stroke()
            smoother.reset()
            self.state = DrawingState.SAVING

            if self.thumbs_up_start_time is None:
                self.thumbs_up_start_time = current_time
                self.save_confirmed = False

            elapsed = current_time - self.thumbs_up_start_time
            remaining = max(0.0, self.save_hold_seconds - elapsed)

            if elapsed >= self.save_hold_seconds and not self.save_confirmed:
                self.last_saved_path = canvas.save()
                self.save_confirmed = True
                self.saved_banner_until = current_time + 3.0

            if not self.save_confirmed:
                result["save_countdown"] = round(remaining, 1)
                result["action_text"] = f"HOLD TO SAVE: {remaining:.1f}s"
            else:
                result["saved_file"] = self.last_saved_path
                result["action_text"] = f"SAVED: {os.path.basename(self.last_saved_path)}"

        else:
            smoother.reset()
            canvas.reset_stroke()
            self.state = DrawingState.IDLE

            if current_time < self.saved_banner_until and self.last_saved_path:
                result["action_text"] = f"SAVED: {os.path.basename(self.last_saved_path)}"
            elif current_time < self.cleared_banner_until:
                result["action_text"] = "CANVAS CLEARED"
            else:
                result["action_text"] = f"IDLE ({gesture.value})"

        result["state"] = self.state.value
        return result

class ModeManager:
    def __init__(self, initial_mode: AppMode = AppMode.DRAW):
        self.active_mode = initial_mode
        self.handlers: Dict[AppMode, BaseModeHandler] = {
            AppMode.DRAW: DrawModeHandler(save_hold_seconds=2.0, clear_hold_seconds=2.0),
        }

    def set_mode(self, mode: AppMode) -> None:
        if mode in self.handlers:
            self.active_mode = mode

    def process(
        self,
        gesture: Gesture,
        position: Optional[Tuple[int, int]],
        smoother: Any,
        canvas: Any,
    ) -> Dict[str, Any]:
        handler = self.handlers.get(self.active_mode)
        if handler:
            return handler.handle_gesture(gesture, position, smoother, canvas)
        
        return {
            "active_mode": self.active_mode.value,
            "state": DrawingState.IDLE.value,
            "is_drawing": False,
            "is_erasing": False,
            "cursor_pos": None,
            "action_text": "No Handler",
            "saved_file": None,
            "save_countdown": None,
            "clear_countdown": None,
        }
