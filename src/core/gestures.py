from enum import Enum
import math
from typing import List, Tuple

class Gesture(Enum):
    NONE = "NONE"
    INDEX_ONLY = "INDEX_ONLY"
    PINCH = "PINCH"
    PINCH_MIDDLE = "PINCH_MIDDLE"
    CLOSED_FIST = "CLOSED_FIST"
    OPEN_PALM = "OPEN_PALM"
    PEACE_SIGN = "PEACE_SIGN"
    THUMBS_UP = "THUMBS_UP"

def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])

class GestureClassifier:
    def __init__(self, pinch_threshold_px: float = 40.0):
        self.pinch_threshold_px = pinch_threshold_px

    def _peace_sign_confidence(
        self,
        landmarks: List[List[int]],
        hand_scale: float,
    ) -> float:
        """
        Returns a confidence score 0.0–1.0 for the Victory/Peace gesture.
        Uses 6 geometric conditions rather than a simple 2-finger check.
        Each condition contributes equally; score is the fraction satisfied.
        """
        thumb_tip = (landmarks[4][1], landmarks[4][2])
        thumb_ip  = (landmarks[3][1], landmarks[3][2])
        index_tip = (landmarks[8][1], landmarks[8][2])
        middle_tip = (landmarks[12][1], landmarks[12][2])
        index_pip = (landmarks[6][1], landmarks[6][2])
        middle_pip = (landmarks[10][1], landmarks[10][2])
        ring_tip = (landmarks[16][1], landmarks[16][2])
        ring_pip = (landmarks[14][1], landmarks[14][2])
        pinky_tip = (landmarks[20][1], landmarks[20][2])
        pinky_pip = (landmarks[18][1], landmarks[18][2])

        # Thumb veto: if thumb is extended in ANY direction (sideways, up, diagonal), immediately
        # reject. Compare dist(thumb_tip, CMC) vs dist(thumb_ip, CMC) — ratio is ~1.0 when
        # curled and rises to 2–3× when extended, regardless of hand rotation.
        thumb_cmc = (landmarks[1][1], landmarks[1][2])
        cmc_to_ip  = _dist(thumb_ip, thumb_cmc)
        cmc_to_tip = _dist(thumb_tip, thumb_cmc)
        anatomy_ratio = (cmc_to_tip / cmc_to_ip) if cmc_to_ip > 1 else 2.0
        if anatomy_ratio >= 1.4:
            return 0.0  # thumb is out — not a peace sign

        # Remaining 5 soft conditions (4/5 required for confidence >= 0.80)
        checks: List[bool] = []

        # 1. Index extended clearly (tip well above pip)
        checks.append(index_tip[1] < index_pip[1] - hand_scale * 0.10)

        # 2. Middle extended clearly (tip well above pip)
        checks.append(middle_tip[1] < middle_pip[1] - hand_scale * 0.10)

        # 3. Ring folded (tip below pip)
        checks.append(ring_tip[1] > ring_pip[1])

        # 4. Pinky folded (tip below pip)
        checks.append(pinky_tip[1] > pinky_pip[1])

        # 5. Index & middle tips have reasonable spread (not pressed together like pinch)
        fingertip_sep = _dist(index_tip, middle_tip)
        checks.append(fingertip_sep > hand_scale * 0.12)

        return sum(checks) / len(checks)

    def classify(self, landmarks: List[List[int]], is_currently_pinching_middle: bool = False) -> Gesture:
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

        # Hysteresis thresholds for Thumb + Middle pinch: press at <=0.32 hand_scale, release at >=0.40
        middle_pinch_thresh = max(40.0, hand_scale * 0.40) if is_currently_pinching_middle else max(32.0, hand_scale * 0.32)
        middle_pinch_dist = _dist(thumb_tip, middle_tip)
        if middle_pinch_dist < middle_pinch_thresh:
            return Gesture.PINCH_MIDDLE

        dynamic_index_pinch_thresh = max(30.0, hand_scale * 0.35)
        index_pinch_dist = _dist(thumb_tip, index_tip)
        if index_pinch_dist < dynamic_index_pinch_thresh:
            return Gesture.PINCH

        # Peace sign: thumb must be tucked (hard veto in confidence), then 4/5 positional checks.
        if index_up and middle_up and not ring_up and not pinky_up:
            confidence = self._peace_sign_confidence(landmarks, hand_scale)
            if confidence >= 4 / 5:
                return Gesture.PEACE_SIGN

        if index_up and middle_up and ring_up and pinky_up:
            return Gesture.OPEN_PALM

        if index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.INDEX_ONLY

        return Gesture.NONE
