"""
exercises/__init__.py
---------------------
Registro de exercícios disponíveis no sistema.
"""

from .shoulder_abduction import ShoulderAbductionExercise
from .elbow_flexion import ElbowFlexionExercise
from .squat import SquatExercise

EXERCISE_REGISTRY: dict = {
    "1": ShoulderAbductionExercise,
    "2": ElbowFlexionExercise,
    "3": SquatExercise,
}

__all__ = [
    "ShoulderAbductionExercise",
    "ElbowFlexionExercise",
    "SquatExercise",
    "EXERCISE_REGISTRY",
]
