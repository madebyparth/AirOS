import os
from datetime import datetime
from typing import Dict, Any
from PIL import ImageGrab
from src.core.actions import BaseAction

class TakeScreenshotAction(BaseAction):
    name = "take_screenshot"
    description = "Captures a full desktop screenshot."

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = output_dir

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)

            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            print(f"[AIR_OS ACTION] Screenshot saved to {filepath}")

            return {"success": True, "action": self.name, "filepath": filepath, "message": f"Saved {filename}"}
        except Exception as e:
            print(f"[AIR_OS ERROR] Screenshot failed: {e}")
            return {"success": False, "action": self.name, "error": str(e)}
