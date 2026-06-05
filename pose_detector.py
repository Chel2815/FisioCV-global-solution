"""
pose_detector.py
----------------
Wrapper sobre o MediaPipe Pose para detecção e extração
de landmarks do esqueleto humano em tempo real.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional


class PoseDetector:
    """Encapsula o pipeline do MediaPipe Pose."""

    # Índices dos landmarks principais (MediaPipe Pose)
    LANDMARKS = {
        "nose": 0,
        "left_shoulder": 11,  "right_shoulder": 12,
        "left_elbow": 13,     "right_elbow": 14,
        "left_wrist": 15,     "right_wrist": 16,
        "left_hip": 23,       "right_hip": 24,
        "left_knee": 25,      "right_knee": 26,
        "left_ankle": 27,     "right_ankle": 28,
    }

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ):
        self._mp_pose = mp.solutions.pose
        self._mp_draw = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles

        self.pose = self._mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.results = None

    # ------------------------------------------------------------------
    # Processamento
    # ------------------------------------------------------------------

    def process(self, frame: np.ndarray) -> Optional[object]:
        """
        Processa um frame BGR e armazena os resultados internamente.
        Retorna os landmarks detectados (ou None).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.pose.process(rgb)
        return self.results.pose_landmarks if self.results else None

    # ------------------------------------------------------------------
    # Extração de coordenadas
    # ------------------------------------------------------------------

    def get_landmark_coords(
        self, frame: np.ndarray, landmark_name: str
    ) -> Optional[tuple[int, int]]:
        """
        Retorna as coordenadas (x, y) em pixels de um landmark pelo nome.
        Retorna None se o landmark não foi detectado.
        """
        if not self.results or not self.results.pose_landmarks:
            return None

        idx = self.LANDMARKS.get(landmark_name)
        if idx is None:
            return None

        h, w = frame.shape[:2]
        lm = self.results.pose_landmarks.landmark[idx]
        if lm.visibility < 0.3:
            return None
        return int(lm.x * w), int(lm.y * h)

    def get_landmark_coords_normalized(
        self, landmark_name: str
    ) -> Optional[tuple[float, float]]:
        """Retorna coordenadas normalizadas [0,1] de um landmark."""
        if not self.results or not self.results.pose_landmarks:
            return None
        idx = self.LANDMARKS.get(landmark_name)
        if idx is None:
            return None
        lm = self.results.pose_landmarks.landmark[idx]
        if lm.visibility < 0.3:
            return None
        return lm.x, lm.y

    # ------------------------------------------------------------------
    # Cálculo de ângulo
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_angle(
        a: tuple[int, int],
        b: tuple[int, int],
        c: tuple[int, int],
    ) -> float:
        """
        Calcula o ângulo ABC (em graus) formado pelos três pontos,
        onde B é o vértice.
        """
        a, b, c = np.array(a, dtype=float), np.array(b, dtype=float), np.array(c, dtype=float)
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        return round(angle, 1)

    # ------------------------------------------------------------------
    # Renderização do esqueleto
    # ------------------------------------------------------------------

    def draw_skeleton(self, frame: np.ndarray) -> np.ndarray:
        """Desenha o esqueleto MediaPipe sobre o frame."""
        if self.results and self.results.pose_landmarks:
            self._mp_draw.draw_landmarks(
                frame,
                self.results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self._mp_draw.DrawingSpec(
                    color=(0, 255, 150), thickness=2, circle_radius=3
                ),
                connection_drawing_spec=self._mp_draw.DrawingSpec(
                    color=(255, 255, 255), thickness=2
                ),
            )
        return frame

    def is_pose_detected(self) -> bool:
        return bool(self.results and self.results.pose_landmarks)

    def release(self):
        self.pose.close()
