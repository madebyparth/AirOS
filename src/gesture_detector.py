from enum import Enum
import math
from typing import List, Optional

class Gesture(Enum):
    NONE = "NONE"
    INDEX_ONLY = "INDEX_ONLY"
    PINCH = "PINCH"
    CLOSED_FIST = "CLOSED_FIST"
    OPEN_PALM = "OPEN_PALM"

class GestureDetector:
    """
    Rule-based gesture recognizer using MediaPipe hand landmark geometry.
    Decoupled from rendering and canvas logic for high reusability across features.
    """

    def __init__(self, pinch_threshold_px: float = 40.0):
        self.pinch_threshold_px = pinch_threshold_px

    def detect(self, landmarks: List[List[int]]) -> Gesture:
        """
        Analyzes 21 hand landmarks [id, x, y] and returns the detected Gesture enum.
        """
        if not landmarks or len(landmarks) < 21:
            return Gesture.NONE

        # Extract coordinates for key joints
        # Thumb: Tip 4, IP 3
        # Index: Tip 8, PIP 6, MCP 5
        # Middle: Tip 12, PIP 10, MCP 9
        # Ring: Tip 16, PIP 14, MCP 13
        # Pinky: Tip 20, PIP 18, MCP 17
        
        thumb_tip = (landmarks[4][1], landmarks[4][2])
        index_tip = (landmarks[8][1], landmarks[8][2])
        index_pip = (landmarks[6][1], landmarks[6][2])
        index_mcp = (landmarks[5][1], landmarks[5][2])

        middle_tip = (landmarks[12][1], landmarks[12][2])
        middle_pip = (landmarks[10][1], landmarks[10][2])

        ring_tip = (landmarks[16][1], landmarks[16][2])
        ring_pip = (landmarks[14][1], landmarks[14][2])

        pinky_tip = (landmarks[20][1], landmarks[20][2])
        pinky_pip = (landmarks[18][1], landmarks[18][2])

        # Finger extension checks (y-coordinate is smaller at upper parts of frame)
        index_up = index_tip[1] < index_pip[1]
        middle_up = middle_tip[1] < middle_pip[1]
        ring_up = ring_tip[1] < ring_pip[1]
        pinky_up = pinky_tip[1] < pinky_pip[1]

        # Calculate distance between thumb tip (4) and index tip (8) for PINCH
        pinch_dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
        
        # Adaptive pinch threshold scale based on hand size (wrist to index MCP distance)
        wrist = (landmarks[0][1], landmarks[0][2])
        hand_scale = math.hypot(index_mcp[0] - wrist[0], index_mcp[1] - wrist[1])
        dynamic_pinch_thresh = max(30.0, hand_scale * 0.35)

        # 1. PINCH Gesture (Thumb and Index tips in close proximity)
        if pinch_dist < dynamic_pinch_thresh:
            return Gesture.PINCH

        # 2. OPEN_PALM Gesture (All 4 main fingers extended)
        if index_up and middle_up and ring_up and pinky_up:
            return Gesture.OPEN_PALM

        # 3. CLOSED_FIST Gesture (All 4 main fingers folded)
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.CLOSED_FIST

        # 4. INDEX_ONLY Gesture (Index finger extended, middle/ring/pinky folded)
        if index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.INDEX_ONLY

        return Gesture.NONE
