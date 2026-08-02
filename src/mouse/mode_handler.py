from enum import Enum
from typing import Tuple, Optional, Dict, Any
from src.core.gestures import Gesture
from src.core.cursor import ScreenMapper
from src.mouse.controller import NativeMouseController

class MouseState(Enum):
    HOVER = "HOVER"
    CLICK_START = "CLICK_START"
    DRAG = "DRAG"
    RELEASE = "RELEASE"

class MouseModeHandler:
    """
    AirOS Mouse Mode State Machine.
    Decouples cursor movement & click state transitions from raw gesture classification.
    """
    def __init__(self, frame_width: int = 1280, frame_height: int = 720):
        self.mouse_controller = NativeMouseController()
        self.screen_mapper = ScreenMapper(frame_width=frame_width, frame_height=frame_height, smoothing_factor=0.45)
        self.state = MouseState.HOVER
        self.is_button_down = False

    def handle_frame(
        self,
        gesture: Gesture,
        fingertip_pos: Optional[Tuple[int, int]],
    ) -> Dict[str, Any]:
        result = {
            "mode": "MOUSE",
            "state": self.state.value,
            "screen_pos": None,
            "is_dragging": False,
            "action_text": "MOUSE MODE ACTIVE",
        }

        if fingertip_pos is None:
            # Hand lost: ensure left button is released if it was down
            if self.is_button_down:
                self.mouse_controller.left_release()
                self.is_button_down = False
            self.state = MouseState.HOVER
            self.screen_mapper.reset()
            result["action_text"] = "SEARCHING FOR HAND"
            return result

        # Map webcam frame position to screen desktop coordinates
        screen_x, screen_y = self.screen_mapper.map_to_screen(fingertip_pos[0], fingertip_pos[1])
        result["screen_pos"] = (screen_x, screen_y)

        # Move system mouse pointer
        self.mouse_controller.move_to(screen_x, screen_y)

        # State Machine Transitions
        is_pinch = (gesture == Gesture.PINCH)

        if is_pinch:
            if not self.is_button_down:
                # Transition: HOVER -> CLICK_START -> DRAG
                self.mouse_controller.left_press()
                self.is_button_down = True
                self.state = MouseState.CLICK_START
                result["action_text"] = "LEFT CLICK DOWN"
            else:
                # Continuous Hold: DRAG
                self.state = MouseState.DRAG
                result["is_dragging"] = True
                result["action_text"] = "DRAGGING"
        else:
            if self.is_button_down:
                # Transition: DRAG/CLICK -> RELEASE -> HOVER
                self.mouse_controller.left_release()
                self.is_button_down = False
                self.state = MouseState.RELEASE
                result["action_text"] = "CLICK RELEASED"
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
        self.screen_mapper.reset()
