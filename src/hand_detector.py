import os
import time
import urllib.request
from typing import List, Tuple, Optional, Any
import cv2
import numpy as np
import mediapipe as mp

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

class HandDetector:
    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
        model_dir: str = "models"
    ):
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.results: Optional[Any] = None

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            self.use_tasks_api = False
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.max_num_hands,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self.mp_draw = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
        else:
            self.use_tasks_api = True
            from mediapipe.tasks.python import vision, BaseOptions

            os.makedirs(model_dir, exist_ok=True)
            self.model_path = os.path.join(model_dir, "hand_landmarker.task")
            if not os.path.exists(self.model_path):
                print(f"Downloading hand landmarker model to {self.model_path}...")
                urllib.request.urlretrieve(MODEL_URL, self.model_path)
                print("Model downloaded successfully.")

            options = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self.model_path),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.max_num_hands,
                min_hand_detection_confidence=self.min_detection_confidence,
                min_hand_presence_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            self.start_timestamp = int(time.time() * 1000)

    def find_hands(self, img, draw: bool = True) -> Tuple[Any, bool]:
        """
        Processes BGR image frame and optionally renders 21 hand landmarks and connections.
        """
        hand_detected = False

        if not self.use_tasks_api:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb.flags.writeable = False
            self.results = self.hands.process(img_rgb)
            img_rgb.flags.writeable = True

            if self.results and self.results.multi_hand_landmarks:
                hand_detected = True
                if draw:
                    for hand_landmarks in self.results.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(
                            img,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style(),
                        )
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            current_timestamp = int(time.time() * 1000) - self.start_timestamp
            self.results = self.landmarker.detect_for_video(mp_image, current_timestamp)

            if self.results and self.results.hand_landmarks:
                hand_detected = True
                if draw:
                    h, w, _ = img.shape
                    for hand_landmarks in self.results.hand_landmarks:
                        for start_idx, end_idx in HAND_CONNECTIONS:
                            pt1 = (int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h))
                            pt2 = (int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h))
                            cv2.line(img, pt1, pt2, (0, 255, 0), 2, cv2.LINE_AA)
                        for idx, lm in enumerate(hand_landmarks):
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            color = (255, 255, 0) if idx in [4, 8, 12, 16, 20] else (255, 0, 255)
                            radius = 6 if idx in [4, 8, 12, 16, 20] else 4
                            cv2.circle(img, (cx, cy), radius, color, cv2.FILLED)

        return img, hand_detected

    def find_positions(self, img, hand_no: int = 0, draw: bool = False) -> List[List[int]]:
        """
        Extracts pixel coordinates [id, cx, cy] for all 21 landmarks of target hand.
        """
        landmark_list: List[List[int]] = []
        h, w, _ = img.shape

        if not self.use_tasks_api:
            if self.results and self.results.multi_hand_landmarks:
                if hand_no < len(self.results.multi_hand_landmarks):
                    target_hand = self.results.multi_hand_landmarks[hand_no]
                    for lm_id, lm in enumerate(target_hand.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmark_list.append([lm_id, cx, cy])
                        if draw:
                            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        else:
            if self.results and self.results.hand_landmarks:
                if hand_no < len(self.results.hand_landmarks):
                    target_hand = self.results.hand_landmarks[hand_no]
                    for lm_id, lm in enumerate(target_hand):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmark_list.append([lm_id, cx, cy])
                        if draw:
                            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        return landmark_list

    def get_handedness(self, hand_no: int = 0) -> Optional[str]:

        if not self.use_tasks_api:
            if self.results and self.results.multi_handedness:
                if hand_no < len(self.results.multi_handedness):
                    return self.results.multi_handedness[hand_no].classification[0].label
        else:
            if self.results and self.results.handedness:
                if hand_no < len(self.results.handedness):
                    return self.results.handedness[hand_no][0].category_name
        return None

    def close(self):

        if not self.use_tasks_api and hasattr(self, "hands"):
            self.hands.close()
        elif self.use_tasks_api and hasattr(self, "landmarker"):
            self.landmarker.close()
