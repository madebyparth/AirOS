import os
import subprocess
from datetime import datetime
from typing import Dict, Any
from PIL import ImageGrab
from src.core.actions import BaseAction

class OpenSpotifyAction(BaseAction):
    name = "open_spotify"
    description = "Launches Spotify desktop app or protocol."

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            subprocess.Popen("start spotify:", shell=True)
            return {"success": True, "action": self.name, "message": "Spotify launched"}
        except Exception as e:
            return {"success": False, "action": self.name, "error": str(e)}

class OpenChromeAction(BaseAction):
    name = "open_chrome"
    description = "Launches Chrome browser."

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            subprocess.Popen("start chrome", shell=True)
            return {"success": True, "action": self.name, "message": "Chrome launched"}
        except Exception as e:
            return {"success": False, "action": self.name, "error": str(e)}

class OpenVSCodeAction(BaseAction):
    name = "open_vscode"
    description = "Launches VS Code editor."

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            subprocess.Popen("code", shell=True)
            return {"success": True, "action": self.name, "message": "VS Code launched"}
        except Exception as e:
            return {"success": False, "action": self.name, "error": str(e)}

class TakeScreenshotAction(BaseAction):
    name = "take_screenshot"
    description = "Captures full desktop screenshot."

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = output_dir

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"screenshot_{timestamp}.png")
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            return {"success": True, "action": self.name, "filepath": filepath, "message": f"Saved screenshot"}
        except Exception as e:
            return {"success": False, "action": self.name, "error": str(e)}

class OpenSettingsAction(BaseAction):
    name = "open_settings"
    description = "Opens AirOS Settings (placeholder)."

    def execute(self, **kwargs) -> Dict[str, Any]:
        print("[AirOS Launcher] Open Settings action triggered")
        return {"success": True, "action": self.name, "message": "Settings opened (placeholder)"}

class ConsoleLogAction(BaseAction):
    name = "console_log"
    description = "Logs action debug messages."

    def execute(self, message: str = "Action executed", **kwargs) -> Dict[str, Any]:
        print(f"[AirOS] {message}")
        return {"success": True, "action": self.name, "message": message}
