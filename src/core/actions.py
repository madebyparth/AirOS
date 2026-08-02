import time
from typing import Dict, Optional, Any, Tuple
from src.core.gestures import Gesture

class BaseAction:
    name: str = "BaseAction"
    description: str = ""

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

class ActionDispatcher:
    def __init__(self, default_cooldown_sec: float = 2.0):
        self.default_cooldown_sec = default_cooldown_sec
        self.last_execution_time: Dict[str, float] = {}
        self.registry: Dict[str, BaseAction] = {}
        self.bindings: Dict[Tuple[str, Gesture], str] = {}

    def register_action(self, action: BaseAction) -> None:
        self.registry[action.name] = action

    def bind_gesture(self, mode_str: str, gesture: Gesture, action_name: str) -> None:
        self.bindings[(mode_str, gesture)] = action_name

    def execute_action(self, action_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        action = self.registry.get(action_name)
        if not action:
            return None

        current_time = time.time()
        last_time = self.last_execution_time.get(action_name, 0.0)

        if current_time - last_time < self.default_cooldown_sec:
            return None

        self.last_execution_time[action_name] = current_time
        return action.execute(**kwargs)

    def dispatch(self, mode_str: str, gesture: Gesture, **kwargs) -> Optional[Dict[str, Any]]:
        action_name = self.bindings.get((mode_str, gesture))
        if action_name:
            return self.execute_action(action_name, **kwargs)
        return None
