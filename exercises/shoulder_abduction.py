import numpy as np
from .base import BaseExercise, ExerciseFeedback, FeedbackLevel, ExerciseStatus


class ShoulderAbductionExercise(BaseExercise):

    NAME        = "Abducao de Ombro"
    DESCRIPTION = (
        "Eleve o braco lateralmente ate 90 graus (paralelo ao chao).\n"
        "Mantenha o cotovelo estendido e o tronco ereto."
    )
    TARGET_JOINT          = "Ombro"
    MIN_REPS              = 10
    ANGLE_MIN             = 10.0
    ANGLE_MAX             = 90.0
    ANGLE_TOLERANCE       = 12.0
    PHASE_UP_THRESHOLD    = 75.0
    PHASE_DOWN_THRESHOLD  = 25.0

    def __init__(self):
        super().__init__()
        self._side = "right"

    def analyze(self, detector, frame) -> ExerciseFeedback:
        fb = ExerciseFeedback(reps=self._reps, status=self._status)

        if not detector.is_pose_detected():
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Pose nao detectada. Afaste-se da camera."]
            return fb

        side = self._side
        hip      = detector.get_landmark_coords(frame, f"{side}_hip")
        shoulder = detector.get_landmark_coords(frame, f"{side}_shoulder")
        elbow    = detector.get_landmark_coords(frame, f"{side}_elbow")

        if not all([hip, shoulder, elbow]):
            side = "left" if side == "right" else "right"
            hip      = detector.get_landmark_coords(frame, f"{side}_hip")
            shoulder = detector.get_landmark_coords(frame, f"{side}_shoulder")
            elbow    = detector.get_landmark_coords(frame, f"{side}_elbow")

        if not all([hip, shoulder, elbow]):
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Posicione-se de frente para a camera."]
            return fb

        angle = detector.calculate_angle(hip, shoulder, elbow)
        fb.angle      = angle
        fb.angle_name = "Abducao"

        level, msg = self._evaluate_angle(angle, self.ANGLE_MAX, self.ANGLE_TOLERANCE)
        self.draw_angle_arc(frame, shoulder, angle, level)

        wrist = detector.get_landmark_coords(frame, f"{side}_wrist")
        messages = [msg]

        if wrist:
            elbow_angle = detector.calculate_angle(shoulder, elbow, wrist)
            if elbow_angle < 150:
                messages.append("Mantenha o cotovelo estendido!")
                level = FeedbackLevel.WARNING

        opp_shoulder = detector.get_landmark_coords(frame, f"{'left' if side == 'right' else 'right'}_shoulder")
        if shoulder and opp_shoulder:
            tilt = abs(shoulder[1] - opp_shoulder[1])
            if tilt > 40:
                messages.append("Mantenha os ombros nivelados.")
                if level == FeedbackLevel.OK:
                    level = FeedbackLevel.WARNING

        completed = self._count_rep_if_complete(angle)
        if completed:
            messages.insert(0, f"Repetiaoo {self._reps} concluida!")

        # Meta
        if self._reps >= self.MIN_REPS:
            messages.insert(0, f"Meta de {self.MIN_REPS} reps atingida!")
            level = FeedbackLevel.OK

        fb.level    = level
        fb.messages = messages
        fb.reps     = self._reps
        fb.status   = self._status
        return fb
