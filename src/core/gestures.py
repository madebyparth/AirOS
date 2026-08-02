from enum import Enum
import math
from typing import List

class Gesture(Enum):
    NONE = "NONE"
    INDEX_ONLY = "INDEX_ONLY"
    PINCH = "PINCH"                  # Thumb + Index
    PINCH_MIDDLE = "PINCH_MIDDLE"    # Thumb + Middle
    CLOSED_FIST = "CLOSED_FIST"
    OPEN_PALM = "OPEN_PALM"
    PEACE_SIGN = "PEACE_SIGN"
    THUMBS_UP = "THUMBS_UP"

class GestureClassifier:
    def __init__(self, pinch_threshold_px: float = 40.0):
        self.pinch_threshold_px = pinch_threshold_px

    def classify(self, landmarks: List[List[int]]) -> Gesture:
        if not landmarks or len(landmarks) < 21:
            return Gesture.NONE

        wrist = (landmarks[0][1], landmarks[0][2])
        thumb_tip = (landmarks[4][1], landmarks[4][2])
        thumb_ip = (landmarks[3][1], landmarks[3][2])

        index_tip = (landmarks[8][1], landmarks[8][2])
        index_pip = (landmarks[6][1], landmarks[6][2])
        index_mcp = (landmarks[5][1], landmarks[5][2])

        middle_tip = (landmarks[12][1], landmarks[12][2])
        middle_pip = (landmarks[10][1], landmarks[10][2])

        ring_tip = (landmarks[16][1], landmarks[16][2])
        ring_pip = (landmarks[14][1], landmarks[14][2])

        pinky_tip = (landmarks[20][1], landmarks[20][2])
        pinky_pip = (landmarks[18][1], landmarks[18][2])

        index_up = index_tip[1] < index_pip[1]
        middle_up = middle_tip[1] < middle_pip[1]
        ring_up = ring_tip[1] < ring_pip[1]
        pinky_up = pinky_tip[1] < pinky_pip[1]

        hand_scale = math.hypot(index_mcp[0] - wrist[0], index_mcp[1] - wrist[1])
        thumb_up = (thumb_tip[1] < index_mcp[1] - hand_scale * 0.15) and (thumb_tip[1] < thumb_ip[1])

        all_folded = not index_up and not middle_up and not ring_up and not pinky_up

        if all_folded:
            if thumb_up:
                return Gesture.THUMBS_UP
            return Gesture.CLOSED_FIST

        dynamic_pinch_thresh = max(30.0, hand_scale * 0.35)

        # Check Thumb + Middle Pinch first (Mouse Left Click / Drag Trigger)
        middle_pinch_dist = math.hypot(thumb_tip[0] - middle_tip[0], thumb_tip[1] - middle_tip[1])
        if middle_pinch_dist < dynamic_pinch_thresh:
            return Gesture.PINCH_MIDDLE

        # Check Thumb + Index Pinch
        index_pinch_dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
        if index_pinch_dist < dynamic_pinch_thresh:
            return Gesture.PINCH

        if index_up and middle_up and not ring_up and not pinky_up:
            return Gesture.PEACE_SIGN

        if index_up and middle_up and ring_up and pinky_up:
            return Gesture.OPEN_PALM

        if index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.INDEX_ONLY

        return Gesture.NONE
