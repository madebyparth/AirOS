import os
import subprocess
from datetime import datetime
from typing import Dict, Any
from PIL import ImageGrab
from src.actions.base_action import BaseAction

class OpenSpotifyAction(BaseAction):
    name = "open_spotify"
    description = "Launches the Spotify desktop application or URI protocol."

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            # Launch Spotify URI handler on Windows
            subprocess.Popen("start spotify:", shell=True)
            print("[ACTION EXECUTION] Spotify launched successfully.")
            return {
                "success": True,
                "action": self.name,
                "message": "Spotify launched",
            }
        except Exception as e:
            print(f"[ACTION ERROR] Failed to launch Spotify: {e}")
            return {
                "success": False,
                "action": self.name,
                "error": str(e),
            }

class TakeScreenshotAction(BaseAction):
    name = "take_screenshot"
    description = "Captures a full desktop screenshot and saves it as a PNG image."

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = output_dir

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)

            # Capture desktop screenshot using Pillow
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            print(f"[ACTION EXECUTION] Screenshot saved to {filepath}")

            return {
                "success": True,
                "action": self.name,
                "filepath": filepath,
                "message": f"Saved screenshot to {filename}",
            }
        except Exception as e:
            print(f"[ACTION ERROR] Screenshot failed: {e}")
            return {
                "success": False,
                "action": self.name,
                "error": str(e),
            }

class ConsoleLogAction(BaseAction):
    name = "console_log"
    description = "Prints a custom log message to the system console."

    def execute(self, message: str = "Action triggered", **kwargs) -> Dict[str, Any]:
        print(f"[ACTION CONSOLE LOG] {message}")
        return {
            "success": True,
            "action": self.name,
            "message": message,
        }
