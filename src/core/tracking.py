import os
import time
import urllib.request
from typing import Tuple, List, Optional, Any
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
INDEX_FINGER_TIP = 8

class HandTracker:
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

    def process(self, frame) -> bool:
        if not self.use_tasks_api:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_rgb.flags.writeable = False
            self.results = self.hands.process(img_rgb)
            img_rgb.flags.writeable = True
            return bool(self.results and self.results.multi_hand_landmarks)
        else:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            current_timestamp = int(time.time() * 1000) - self.start_timestamp
            self.results = self.landmarker.detect_for_video(mp_image, current_timestamp)
            return bool(self.results and self.results.hand_landmarks)

    def draw_landmarks(self, frame):
        if not self.use_tasks_api:
            if self.results and self.results.multi_hand_landmarks:
                for hand_landmarks in self.results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style(),
                    )
        else:
            if self.results and self.results.hand_landmarks:
                h, w, _ = frame.shape
                for hand_landmarks in self.results.hand_landmarks:
                    for start_idx, end_idx in HAND_CONNECTIONS:
                        pt1 = (int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h))
                        pt2 = (int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h))
                        cv2.line(frame, pt1, pt2, (0, 255, 0), 2, cv2.LINE_AA)
                    for idx, lm in enumerate(hand_landmarks):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        color = (255, 255, 0) if idx in [4, 8, 12, 16, 20] else (255, 0, 255)
                        radius = 6 if idx in [4, 8, 12, 16, 20] else 4
                        cv2.circle(frame, (cx, cy), radius, color, cv2.FILLED)
        return frame

    def get_landmarks(self, frame, hand_no: int = 0) -> List[List[int]]:
        landmark_list: List[List[int]] = []
        h, w, _ = frame.shape
        if not self.use_tasks_api:
            if self.results and self.results.multi_hand_landmarks:
                if hand_no < len(self.results.multi_hand_landmarks):
                    target_hand = self.results.multi_hand_landmarks[hand_no]
                    for lm_id, lm in enumerate(target_hand.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmark_list.append([lm_id, cx, cy])
        else:
            if self.results and self.results.hand_landmarks:
                if hand_no < len(self.results.hand_landmarks):
                    target_hand = self.results.hand_landmarks[hand_no]
                    for lm_id, lm in enumerate(target_hand):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmark_list.append([lm_id, cx, cy])
        return landmark_list

    def get_index_fingertip(self, frame, hand_no: int = 0) -> Optional[Tuple[int, int]]:
        landmarks = self.get_landmarks(frame, hand_no=hand_no)
        if landmarks and len(landmarks) > INDEX_FINGER_TIP:
            return (landmarks[INDEX_FINGER_TIP][1], landmarks[INDEX_FINGER_TIP][2])
        return None

    def close(self):
        if not self.use_tasks_api and hasattr(self, "hands"):
            self.hands.close()
        elif self.use_tasks_api and hasattr(self, "landmarker"):
            self.landmarker.close()
