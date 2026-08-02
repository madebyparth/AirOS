from typing import Dict, Any
from src.core.actions import BaseAction

class ConsoleLogAction(BaseAction):
    name = "console_log"
    description = "Logs action debugging messages to console."

    def execute(self, message: str = "Action executed", **kwargs) -> Dict[str, Any]:
        print(f"[AIR_OS CONSOLE] {message}")
        return {"success": True, "action": self.name, "message": message}
