import numpy as np
from .base import BaseExercise, ExerciseFeedback, FeedbackLevel, ExerciseStatus


class SquatExercise(BaseExercise):

    NAME        = "Agachamento"
    DESCRIPTION = (
        "Pes afastados na largura dos ombros.\n"
        "Desca ate o joelho atingir 90 graus.\n"
        "Mantenha joelhos alinhados com os pes."
    )
    TARGET_JOINT          = "Joelho"
    MIN_REPS              = 10
    ANGLE_MIN             = 85.0
    ANGLE_MAX             = 165.0
    ANGLE_TOLERANCE       = 15.0
    PHASE_UP_THRESHOLD    = 100.0
    PHASE_DOWN_THRESHOLD  = 150.0

    def __init__(self):
        super().__init__()

    def analyze(self, detector, frame) -> ExerciseFeedback:
        fb = ExerciseFeedback(reps=self._reps, status=self._status)

        if not detector.is_pose_detected():
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Pose nao detectada. Afaste-se e fique de lado."]
            return fb

        for side in ("left", "right"):
            hip    = detector.get_landmark_coords(frame, f"{side}_hip")
            knee   = detector.get_landmark_coords(frame, f"{side}_knee")
            ankle  = detector.get_landmark_coords(frame, f"{side}_ankle")
            if all([hip, knee, ankle]):
                break
        else:
            fb.level = FeedbackLevel.WARNING
            fb.messages = ["Posicione-se de lado para a camera."]
            return fb

        angle = detector.calculate_angle(hip, knee, ankle)
        fb.angle      = angle
        fb.angle_name = "Joelho"

        at_bottom = angle <= self.ANGLE_MIN + self.ANGLE_TOLERANCE
        target = self.ANGLE_MIN if at_bottom else self.ANGLE_MAX
        level, msg = self._evaluate_angle(angle, target, self.ANGLE_TOLERANCE)

        self.draw_angle_arc(frame, knee, angle, level, radius=45)

        messages = [msg]

        if self._status in (ExerciseStatus.IN_MOTION, ExerciseStatus.PEAK):
            if angle > self.ANGLE_MIN + 25:
                messages.append("Desca mais! Tente atingir 90 graus no joelho.")
                if level == FeedbackLevel.OK:
                    level = FeedbackLevel.WARNING

        if knee and ankle:
            knee_drift = abs(knee[0] - ankle[0])
            if knee_drift > 60:
                messages.append("Joelho desviando. Alinhe com o pe.")
                if level == FeedbackLevel.OK:
                    level = FeedbackLevel.WARNING

        shoulder = detector.get_landmark_coords(frame, f"{side}_shoulder")
        if shoulder and hip:
            trunk_lean = abs(shoulder[0] - hip[0])
            if trunk_lean > 70:
                messages.append("Mantenha o tronco mais ereto.")
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
