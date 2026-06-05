"""
exercises/base.py
-----------------
Classe base abstrata para todos os exercícios de fisioterapia.
Define a interface e utilitários comuns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import numpy as np
import cv2


class ExerciseStatus(Enum):
    WAITING   = auto()   # Aguardando posição inicial
    IN_MOTION = auto()   # Em movimento (subida)
    PEAK      = auto()   # No pico do movimento
    RETURNING = auto()   # Retornando à posição inicial
    COMPLETED = auto()   # Repetição concluída


class FeedbackLevel(Enum):
    OK      = "OK"
    WARNING = "ATENÇÃO"
    ERROR   = "ERRO"


@dataclass
class ExerciseFeedback:
    level: FeedbackLevel = FeedbackLevel.OK
    messages: list[str]  = field(default_factory=list)
    angle: Optional[float] = None
    angle_name: str = ""
    reps: int = 0
    status: ExerciseStatus = ExerciseStatus.WAITING


class BaseExercise(ABC):
    """Interface comum para todos os exercícios."""

    # Subclasses devem preencher estes atributos
    NAME: str = "Exercício"
    DESCRIPTION: str = ""
    TARGET_JOINT: str = ""          # Ex.: "Ombro", "Joelho"
    MIN_REPS: int = 10              # Meta de repetições
    ANGLE_MIN: float = 0.0          # Ângulo mínimo esperado (posição de repouso)
    ANGLE_MAX: float = 180.0        # Ângulo máximo esperado (pico)
    ANGLE_TOLERANCE: float = 15.0   # Tolerância em graus para considerar "correto"

    # Limiares de transição de fase (subclasses podem sobrescrever)
    PHASE_UP_THRESHOLD: float   = 0.0   # Ângulo que indica início do movimento
    PHASE_DOWN_THRESHOLD: float = 0.0   # Ângulo que indica retorno

    def __init__(self):
        self._reps: int = 0
        self._status: ExerciseStatus = ExerciseStatus.WAITING
        self._angle_history: list[float] = []
        self._feedback = ExerciseFeedback()

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    @abstractmethod
    def analyze(self, detector, frame: np.ndarray) -> ExerciseFeedback:
        """
        Recebe o PoseDetector e o frame atual.
        Deve calcular ângulos, atualizar estado e retornar feedback.
        """
        ...

    @property
    def reps(self) -> int:
        return self._reps

    @property
    def status(self) -> ExerciseStatus:
        return self._status

    # ------------------------------------------------------------------
    # Helpers de contagem
    # ------------------------------------------------------------------

    def _count_rep_if_complete(self, angle: float) -> bool:
        """
        Máquina de estados simples para contar repetições.
        Retorna True quando uma repetição é completada.
        """
        if self._status == ExerciseStatus.WAITING:
            if angle <= self.PHASE_DOWN_THRESHOLD:
                self._status = ExerciseStatus.IN_MOTION

        elif self._status == ExerciseStatus.IN_MOTION:
            if angle >= self.PHASE_UP_THRESHOLD:
                self._status = ExerciseStatus.PEAK

        elif self._status == ExerciseStatus.PEAK:
            if angle <= self.PHASE_DOWN_THRESHOLD:
                self._status = ExerciseStatus.WAITING
                self._reps += 1
                return True

        return False

    # ------------------------------------------------------------------
    # Helpers de feedback
    # ------------------------------------------------------------------

    def _evaluate_angle(self, angle: float, target: float, tolerance: float) -> tuple[FeedbackLevel, str]:
        """Compara ângulo atual com o alvo e retorna nível de feedback."""
        diff = abs(angle - target)
        if diff <= tolerance:
            return FeedbackLevel.OK, f"Ângulo correto: {angle}°"
        elif diff <= tolerance * 2:
            direction = "maior" if angle > target else "menor"
            return FeedbackLevel.WARNING, f"Ângulo {direction} que o ideal ({target}°)"
        else:
            direction = "muito alto" if angle > target else "muito baixo"
            return FeedbackLevel.ERROR, f"Ângulo {direction} ({angle}° / ideal: {target}°)"

    # ------------------------------------------------------------------
    # Helpers de desenho
    # ------------------------------------------------------------------

    @staticmethod
    def draw_angle_arc(
        frame: np.ndarray,
        center: tuple[int, int],
        angle: float,
        level: FeedbackLevel,
        radius: int = 40,
    ) -> None:
        """Desenha o valor do ângulo sobre o frame com cor indicativa."""
        color_map = {
            FeedbackLevel.OK:      (0, 220, 80),
            FeedbackLevel.WARNING: (0, 200, 255),
            FeedbackLevel.ERROR:   (0, 60, 255),
        }
        color = color_map[level]
        cv2.circle(frame, center, radius, color, 2)
        cv2.putText(
            frame, f"{int(angle)}°",
            (center[0] - 20, center[1] + 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA
        )
