import time
from typing import Dict, Optional, Any, Tuple
from src.gesture_detector import Gesture
from src.actions.base_action import BaseAction
from src.actions.system_actions import (
    OpenSpotifyAction,
    TakeScreenshotAction,
    ConsoleLogAction,
)

class CommandDispatcher:
    """
    Command Dispatcher framing the Action System.
    Maps (AppMode, Gesture) triggers to registered Action instances cleanly,
    completely independent of gesture detection and UI rendering logic.
    """

    def __init__(self, action_cooldown_sec: float = 2.0):
        self.action_cooldown_sec = action_cooldown_sec
        self.last_execution_time: Dict[str, float] = {}

        # 1. Action Registry: Stores reusable Action instances
        self.registry: Dict[str, BaseAction] = {}
        self.register_action(OpenSpotifyAction())
        self.register_action(TakeScreenshotAction())
        self.register_action(ConsoleLogAction())

        # 2. Gesture-to-Action Binding Map: (ModeStr, GestureEnum) -> ActionName
        self.bindings: Dict[Tuple[str, Gesture], str] = {}

    def register_action(self, action: BaseAction) -> None:
        """
        Registers an action instance into the dispatcher registry.
        """
        self.registry[action.name] = action

    def bind_gesture(self, mode_str: str, gesture: Gesture, action_name: str) -> None:
        """
        Binds a specific gesture in a given application mode to an action name.
        """
        self.bindings[(mode_str, gesture)] = action_name

    def execute_action(self, action_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Executes a registered action by name with cooldown protection.
        """
        action = self.registry.get(action_name)
        if not action:
            print(f"[DISPATCHER WARNING] Action '{action_name}' is not registered.")
            return None

        current_time = time.time()
        last_time = self.last_execution_time.get(action_name, 0.0)

        # Enforce action cooldown debounce
        if current_time - last_time < self.action_cooldown_sec:
            return None

        self.last_execution_time[action_name] = current_time
        return action.execute(**kwargs)

    def dispatch(
        self, mode_str: str, gesture: Gesture, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Looks up bindings for (mode, gesture) and executes the bound action.
        """
        action_name = self.bindings.get((mode_str, gesture))
        if action_name:
            return self.execute_action(action_name, **kwargs)
        return None
