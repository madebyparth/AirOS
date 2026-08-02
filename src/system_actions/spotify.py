import subprocess
from typing import Dict, Any
from src.core.actions import BaseAction

class OpenSpotifyAction(BaseAction):
    name = "open_spotify"
    description = "Launches the Spotify desktop application or protocol."

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            subprocess.Popen("start spotify:", shell=True)
            print("[AIR_OS ACTION] Spotify launched successfully.")
            return {"success": True, "action": self.name, "message": "Spotify launched"}
        except Exception as e:
            print(f"[AIR_OS ERROR] Failed to launch Spotify: {e}")
            return {"success": False, "action": self.name, "error": str(e)}
