import numpy as np
from .base import BaseExercise, ExerciseFeedback, FeedbackLevel, ExerciseStatus


class ElbowFlexionExercise(BaseExercise):

    NAME        = "Flexao de Cotovelo"
    DESCRIPTION = (
        "Com o braço colado ao corpo, flexione o cotovelo\n"
        "ate 40 graus (mao próxima ao ombro).\n"
        "Retorne lentamente a posição estendida (160 graus)."
    )
    TARGET_JOINT          = "Cotovelo"
    MIN_REPS              = 12
    ANGLE_MIN             = 40.0
    ANGLE_MAX             = 160.0
    ANGLE_TOLERANCE       = 15.0
    PHASE_UP_THRESHOLD    = 50.0
    PHASE_DOWN_THRESHOLD  = 145.0

    def __init__(self):
        super().__init__()

    def analyze(self, detector, frame) -> ExerciseFeedback:
        fb = ExerciseFeedback(reps=self._reps, status=self._status)

        if not detector.is_pose_detected():
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Pose nao detectada. Posicione-se em frente a camera."]
            return fb

        # Tenta direita primeiro, depois esquerda
        for side in ("right", "left"):
            shoulder = detector.get_landmark_coords(frame, f"{side}_shoulder")
            elbow    = detector.get_landmark_coords(frame, f"{side}_elbow")
            wrist    = detector.get_landmark_coords(frame, f"{side}_wrist")
            if all([shoulder, elbow, wrist]):
                break
        else:
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Braco nao visivel. Vire-se de lado para a camera."]
            return fb

        angle = detector.calculate_angle(shoulder, elbow, wrist)
        fb.angle      = angle
        fb.angle_name = "Cotovelo"

        at_peak = angle <= self.ANGLE_MIN + self.ANGLE_TOLERANCE
        level, msg = self._evaluate_angle(
            angle,
            self.ANGLE_MIN if at_peak else self.ANGLE_MAX,
            self.ANGLE_TOLERANCE,
        )

        self.draw_angle_arc(frame, elbow, angle, level)

        messages = [msg]

        hip = detector.get_landmark_coords(frame, f"{side}_hip")
        if hip and shoulder and elbow:
            elbow_drift = abs(elbow[0] - shoulder[0])
            if elbow_drift > 80:
                messages.append("Mantenha o cotovelo colado ao corpo.")
                if level == FeedbackLevel.OK:
                    level = FeedbackLevel.WARNING

        if self._status == ExerciseStatus.WAITING and angle >= self.PHASE_DOWN_THRESHOLD:
            self._status = ExerciseStatus.IN_MOTION

        elif self._status == ExerciseStatus.IN_MOTION and angle <= self.PHASE_UP_THRESHOLD:
            self._status = ExerciseStatus.PEAK

        elif self._status == ExerciseStatus.PEAK and angle >= self.PHASE_DOWN_THRESHOLD:
            self._status = ExerciseStatus.WAITING
            self._reps += 1
            messages.insert(0, f"Repeticao {self._reps} concluida!")

        if self._reps >= self.MIN_REPS:
            messages.insert(0, f"Meta de {self.MIN_REPS} reps atingida!")
            level = FeedbackLevel.OK

        fb.level    = level
        fb.messages = messages
        fb.reps     = self._reps
        fb.status   = self._status
        return fb
