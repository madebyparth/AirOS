import time
from enum import Enum
from typing import Tuple, Optional, Dict, Any
from src.core.gestures import Gesture
from src.core.cursor import ScreenMapper
from src.mouse.controller import NativeMouseController

class MouseState(Enum):
    HOVER = "HOVER"
    CLICK_PENDING = "CLICK_PENDING"
    SINGLE_CLICK = "SINGLE_CLICK"
    DRAG = "DRAG"
    RELEASE = "RELEASE"

class MouseModeHandler:
    """
    AirOS Mouse Mode State Machine.
    Index fingertip anchors cursor position.
    Thumb + Middle finger pinch (PINCH_MIDDLE) triggers stable Left Click & Drag.
    """
    def __init__(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
        margin_x: float = 0.18,
        margin_y: float = 0.18,
        sensitivity: float = 1.25,
        drag_threshold_sec: float = 0.30,
    ):
        self.mouse_controller = NativeMouseController()
        self.screen_mapper = ScreenMapper(
            frame_width=frame_width,
            frame_height=frame_height,
            margin_x=margin_x,
            margin_y=margin_y,
            sensitivity=sensitivity,
            min_alpha=0.12,
            max_alpha=0.85,
        )
        self.drag_threshold_sec = drag_threshold_sec

        self.state = MouseState.HOVER
        self.pinch_start_time: Optional[float] = None
        self.is_button_down = False
        self.click_executed = False

    def handle_frame(
        self,
        gesture: Gesture,
        index_pos: Optional[Tuple[int, int]],
    ) -> Dict[str, Any]:
        result = {
            "mode": "MOUSE",
            "state": self.state.value,
            "screen_pos": None,
            "is_dragging": False,
            "action_text": "MOUSE MODE ACTIVE",
        }

        current_time = time.time()

        if index_pos is None:
            if self.is_button_down:
                self.mouse_controller.left_release()
                self.is_button_down = False
            self.state = MouseState.HOVER
            self.pinch_start_time = None
            self.click_executed = False
            self.screen_mapper.reset()
            result["action_text"] = "SEARCHING FOR HAND"
            return result

        # Index fingertip always anchors desktop screen cursor
        screen_x, screen_y = self.screen_mapper.map_to_screen(index_pos[0], index_pos[1])
        result["screen_pos"] = (screen_x, screen_y)
        self.mouse_controller.move_to(screen_x, screen_y)

        is_pinch_middle = (gesture == Gesture.PINCH_MIDDLE)

        # State Machine Evaluation
        if is_pinch_middle:
            if self.pinch_start_time is None:
                # 1. Pinch initiated: Enter CLICK_PENDING
                self.pinch_start_time = current_time
                self.state = MouseState.CLICK_PENDING
                self.click_executed = False
                result["action_text"] = "CLICK PENDING..."
            else:
                elapsed = current_time - self.pinch_start_time

                # 2. Pinch held past 300ms threshold: Transition to DRAG
                if elapsed >= self.drag_threshold_sec and not self.is_button_down:
                    self.mouse_controller.left_press()
                    self.is_button_down = True
                    self.state = MouseState.DRAG
                    result["is_dragging"] = True
                    result["action_text"] = "DRAGGING"
                elif self.is_button_down:
                    self.state = MouseState.DRAG
                    result["is_dragging"] = True
                    result["action_text"] = "DRAGGING"
                else:
                    self.state = MouseState.CLICK_PENDING
                    result["action_text"] = f"HOLDING ({elapsed:.2f}s)"

        else:
            # Pinch released
            if self.pinch_start_time is not None:
                elapsed = current_time - self.pinch_start_time

                if self.is_button_down:
                    # Released while in DRAG: Trigger left_release
                    self.mouse_controller.left_release()
                    self.is_button_down = False
                    self.state = MouseState.RELEASE
                    result["action_text"] = "DRAG RELEASED"
                elif elapsed < self.drag_threshold_sec and not self.click_executed:
                    # Released before 300ms threshold: Trigger SINGLE LEFT CLICK
                    self.mouse_controller.left_click()
                    self.click_executed = True
                    self.state = MouseState.SINGLE_CLICK
                    result["action_text"] = "SINGLE LEFT CLICK"
                else:
                    self.state = MouseState.HOVER
                    result["action_text"] = f"MOVING ({screen_x}, {screen_y})"

                self.pinch_start_time = None
            else:
                self.state = MouseState.HOVER
                result["action_text"] = f"MOVING ({screen_x}, {screen_y})"

        result["state"] = self.state.value
        return result

    def reset(self):
        if self.is_button_down:
            self.mouse_controller.left_release()
            self.is_button_down = False
        self.state = MouseState.HOVER
        self.pinch_start_time = None
        self.click_executed = False
        self.screen_mapper.reset()
