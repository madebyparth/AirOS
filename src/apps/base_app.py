from typing import Dict, Any, Tuple, Optional
from src.core.gestures import Gesture

class BaseAirApp:
    """
    Abstract Interface for modular AirOS Applications (e.g. Whiteboard, AI Assistant, Presentation Remote).
    """
    name: str = "BaseAirApp"
    description: str = "Abstract AirOS Application"

    def process_frame(
        self,
        gesture: Gesture,
        position: Optional[Tuple[int, int]],
        frame_shape: Tuple[int, int, int],
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def composite_overlay(self, frame):
        return frame

    def reset(self):
        pass
