from typing import Dict, Any

class BaseAction:
    """
    Abstract base class for all AirDesk AI executable actions.
    Each action represents an independent, reusable command.
    """
    name: str = "BaseAction"
    description: str = "Abstract base action"

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the action and returns a status dictionary.
        """
        raise NotImplementedError
