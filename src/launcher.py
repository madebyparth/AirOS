import time
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np
from src.core.gestures import Gesture
from src.core.actions import ActionDispatcher

@dataclass
class LauncherItem:
    id: str
    label: str
    action_name: str
    subtitle: str
    color: Tuple[int, int, int]  # BGR

class AirOSLauncher:
    """
    AirOS Central Launcher Hub.
    - Opened/Closed by holding Victory (PEACE_SIGN) gesture for 1.0 second.
    - Data-driven menu items (Spotify, Chrome, VS Code, Screenshot, Settings).
    - Floating glassmorphism overlay with smooth 0.2s scale/fade animation.
    - Desktop OS cursor hidden while active; custom UI hover indicator rendered.
    """
    def __init__(self, action_dispatcher: ActionDispatcher, hold_threshold_sec: float = 1.0):
        self.dispatcher = action_dispatcher
        self.hold_threshold_sec = hold_threshold_sec

        self.items: List[LauncherItem] = [
            LauncherItem("spotify", "Spotify", "open_spotify", "Music & Podcasts", (255, 200, 0)),
            LauncherItem("chrome", "Chrome", "open_chrome", "Web Browser", (0, 215, 255)),
            LauncherItem("vscode", "VS Code", "open_vscode", "Code Editor", (255, 120, 0)),
            LauncherItem("screenshot", "Screenshot", "take_screenshot", "Capture Screen", (50, 205, 50)),
            LauncherItem("settings", "Settings", "open_settings", "AirOS Preferences", (200, 200, 200)),
        ]

        self.is_open = False
        self.animation_progress = 0.0  # 0.0 to 1.0
        self.last_anim_time = time.time()

        self.peace_sign_start_time: Optional[float] = None
        self.toggle_confirmed = False

        self.hovered_item_id: Optional[str] = None
        self.item_bounds: Dict[str, Tuple[int, int, int, int]] = {}

    def register_item(self, item: LauncherItem) -> None:
        self.items.append(item)

    def process(
        self,
        gesture: Gesture,
        index_pos: Optional[Tuple[int, int]],
        frame_shape: Tuple[int, int, int],
    ) -> Dict[str, Any]:
        result = {
            "is_open": self.is_open,
            "hide_desktop_cursor": self.is_open,
            "action_executed": None,
            "hold_countdown": None,
            "status_text": None,
        }

        current_time = time.time()
        dt = current_time - self.last_anim_time
        self.last_anim_time = current_time

        # 1. Victory (PEACE_SIGN) 1.0-second verification hold check
        if gesture == Gesture.PEACE_SIGN:
            if self.peace_sign_start_time is None:
                self.peace_sign_start_time = current_time
                self.toggle_confirmed = False

            elapsed = current_time - self.peace_sign_start_time
            remaining = max(0.0, self.hold_threshold_sec - elapsed)
            result["hold_countdown"] = round(remaining, 1)

            if elapsed >= self.hold_threshold_sec and not self.toggle_confirmed:
                self.is_open = not self.is_open
                self.toggle_confirmed = True
                result["is_open"] = self.is_open
                result["hide_desktop_cursor"] = self.is_open
                result["status_text"] = "LAUNCHER OPENED" if self.is_open else "LAUNCHER CLOSED"
        else:
            self.peace_sign_start_time = None
            self.toggle_confirmed = False

        # Smooth opening/closing animation interpolation (0.2s duration)
        target_anim = 1.0 if self.is_open else 0.0
        anim_speed = 5.0  # 1/0.2s
        if self.animation_progress < target_anim:
            self.animation_progress = min(target_anim, self.animation_progress + anim_speed * dt)
        elif self.animation_progress > target_anim:
            self.animation_progress = max(target_anim, self.animation_progress - anim_speed * dt)

        if self.animation_progress <= 0.0:
            return result

        # 2. Item Hover & Selection while Launcher is open
        if self.is_open and index_pos is not None:
            ix, iy = index_pos
            self.hovered_item_id = None

            for item_id, (x1, y1, x2, y2) in self.item_bounds.items():
                if x1 <= ix <= x2 and y1 <= iy <= y2:
                    self.hovered_item_id = item_id
                    break

            # Selection on thumb-middle pinch (PINCH_MIDDLE)
            if gesture == Gesture.PINCH_MIDDLE:
                if self.hovered_item_id:
                    matched_item = next((it for it in self.items if it.id == self.hovered_item_id), None)
                    if matched_item:
                        exec_res = self.dispatcher.execute_action(matched_item.action_name)
                        result["action_executed"] = exec_res
                        result["status_text"] = f"LAUNCHED: {matched_item.label}"
                else:
                    result["status_text"] = "DISMISSED"

                # Close launcher after selection or outside click
                self.is_open = False
                result["is_open"] = False
                result["hide_desktop_cursor"] = False

        return result

    def render_overlay(self, frame: np.ndarray, index_pos: Optional[Tuple[int, int]]) -> np.ndarray:
        if self.animation_progress <= 0.0:
            return frame

        h, w, _ = frame.shape
        t = self.animation_progress

        # Ease-out cubic curve
        scale = 1.0 - (1.0 - t) ** 3
        alpha = min(1.0, t * 1.2)

        # Card Overlay Geometry
        card_w = int(520 * scale)
        card_h = int(380 * scale)
        cx, cy = w // 2, h // 2
        x1, y1 = cx - card_w // 2, cy - card_h // 2
        x2, y2 = cx + card_w // 2, cy + card_h // 2

        overlay = frame.copy()

        # Dark glassmorphism card background
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 20, 25), -1)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 215, 255), 2, cv2.LINE_AA)

        # Header Title
        if scale > 0.6:
            cv2.putText(overlay, "AirOS Central Launcher", (x1 + 30, y1 + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.line(overlay, (x1 + 30, y1 + 60), (x2 - 30, y1 + 60), (80, 80, 90), 1, cv2.LINE_AA)

        # Item Rows Bounding Box Calculations
        self.item_bounds.clear()
        start_y = y1 + 75
        item_h = 52
        gap = 8

        for idx, item in enumerate(self.items):
            iy1 = start_y + idx * (item_h + gap)
            iy2 = iy1 + item_h
            ix1 = x1 + 25
            ix2 = x2 - 25

            if iy2 > y2 - 15:
                break

            self.item_bounds[item.id] = (ix1, iy1, ix2, iy2)

            is_hovered = (self.hovered_item_id == item.id)

            if is_hovered:
                # Glowing highlight fill for hovered launcher item
                cv2.rectangle(overlay, (ix1, iy1), (ix2, iy2), (60, 60, 75), -1)
                cv2.rectangle(overlay, (ix1, iy1), (ix2, iy2), item.color, 2, cv2.LINE_AA)
                textColor = (255, 255, 255)
            else:
                cv2.rectangle(overlay, (ix1, iy1), (ix2, iy2), (35, 35, 45), -1)
                cv2.rectangle(overlay, (ix1, iy1), (ix2, iy2), (55, 55, 65), 1, cv2.LINE_AA)
                textColor = (200, 200, 200)

            if scale > 0.8:
                cv2.circle(overlay, (ix1 + 25, iy1 + 26), 8, item.color, -1, cv2.LINE_AA)
                cv2.putText(overlay, item.label, (ix1 + 45, iy1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, textColor, 2 if is_hovered else 1, cv2.LINE_AA)
                cv2.putText(overlay, item.subtitle, (ix1 + 45, iy1 + 42), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 160, 170), 1, cv2.LINE_AA)

        # Blend glassmorphism card over frame
        blended = cv2.addWeighted(overlay, alpha * 0.85, frame, 1.0 - (alpha * 0.85), 0)

        # Custom UI Fingertip Pointer Indicator (replaces desktop OS cursor while launcher is active)
        if self.is_open and index_pos is not None:
            px, py = index_pos
            cv2.circle(blended, (px, py), 10, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(blended, (px, py), 4, (255, 255, 255), -1, cv2.LINE_AA)

        return blended
