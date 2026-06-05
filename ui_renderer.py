"""
ui_renderer.py
--------------
Responsável por toda a camada de interface visual sobreposta
ao frame de vídeo: painel de status, barra de progresso,
mensagens de feedback e HUD de informações.
"""

import cv2
import numpy as np
from exercises.base import ExerciseFeedback, FeedbackLevel, ExerciseStatus


# Paleta de cores BGR
COLORS = {
    "ok":        (40, 200, 80),
    "warning":   (0, 200, 255),
    "error":     (0, 60, 230),
    "bg_dark":   (20, 20, 20),
    "bg_panel":  (30, 30, 30),
    "white":     (255, 255, 255),
    "gray":      (160, 160, 160),
    "accent":    (80, 180, 255),
    "gold":      (0, 200, 240),
}

FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD  = cv2.FONT_HERSHEY_DUPLEX


def _level_color(level: FeedbackLevel) -> tuple:
    return {
        FeedbackLevel.OK:      COLORS["ok"],
        FeedbackLevel.WARNING: COLORS["warning"],
        FeedbackLevel.ERROR:   COLORS["error"],
    }[level]


def _overlay_rect(frame, x, y, w, h, color, alpha=0.55):
    """Desenha retângulo semitransparente."""
    sub = frame[y:y+h, x:x+w].copy()
    rect = np.full_like(sub, color)
    cv2.addWeighted(rect, alpha, sub, 1 - alpha, 0, sub)
    frame[y:y+h, x:x+w] = sub


class UIRenderer:
    """Renderiza todos os elementos de HUD sobre o frame."""

    PANEL_W = 300
    PANEL_H = 220
    MARGIN  = 12

    def __init__(self, exercise_name: str, min_reps: int):
        self.exercise_name = exercise_name
        self.min_reps      = min_reps

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------

    def render(self, frame: np.ndarray, feedback: ExerciseFeedback) -> np.ndarray:
        h, w = frame.shape[:2]

        self._draw_title_bar(frame, w)
        self._draw_status_panel(frame, feedback, w)
        self._draw_rep_bar(frame, feedback.reps, w, h)
        self._draw_angle_hud(frame, feedback)
        self._draw_status_badge(frame, feedback.status)
        self._draw_controls_hint(frame, h, w)
        return frame

    # ------------------------------------------------------------------
    # Componentes individuais
    # ------------------------------------------------------------------

    def _draw_title_bar(self, frame, w):
        """Barra superior com nome do exercício."""
        bar_h = 42
        _overlay_rect(frame, 0, 0, w, bar_h, COLORS["bg_dark"], alpha=0.75)
        cv2.putText(
            frame, f"FisioCV  |  {self.exercise_name}",
            (self.MARGIN, 28), FONT_BOLD, 0.7, COLORS["accent"], 2, cv2.LINE_AA
        )

    def _draw_status_panel(self, frame, feedback: ExerciseFeedback, w):
        """Painel lateral direito com feedback textual."""
        px = w - self.PANEL_W - self.MARGIN
        py = 50
        pw = self.PANEL_W
        ph = self.PANEL_H

        _overlay_rect(frame, px, py, pw, ph, COLORS["bg_panel"], alpha=0.65)
        border_color = _level_color(feedback.level)
        cv2.rectangle(frame, (px, py), (px + pw, py + ph), border_color, 2)

        # Título do nível
        level_text = {
            FeedbackLevel.OK:      "✔  CORRETO",
            FeedbackLevel.WARNING: "⚠  ATENÇÃO",
            FeedbackLevel.ERROR:   "✘  CORRIGIR",
        }[feedback.level]

        cv2.putText(
            frame, level_text,
            (px + 10, py + 28), FONT_BOLD, 0.65, border_color, 2, cv2.LINE_AA
        )
        cv2.line(frame, (px + 8, py + 36), (px + pw - 8, py + 36), border_color, 1)

        # Mensagens de feedback
        y_off = py + 58
        for msg in feedback.messages[:4]:
            # quebra linhas longas
            for chunk in self._wrap_text(msg, 34):
                cv2.putText(
                    frame, chunk, (px + 10, y_off),
                    FONT, 0.48, COLORS["white"], 1, cv2.LINE_AA
                )
                y_off += 22

        # Contador de reps
        reps_y = py + ph - 18
        cv2.putText(
            frame, f"Repetições:  {feedback.reps} / {self.min_reps}",
            (px + 10, reps_y), FONT_BOLD, 0.6, COLORS["gold"], 2, cv2.LINE_AA
        )

    def _draw_rep_bar(self, frame, reps: int, w, h):
        """Barra de progresso horizontal na parte inferior."""
        bar_y  = h - 28
        bar_x  = self.MARGIN
        bar_w  = w - 2 * self.MARGIN
        bar_h  = 16

        _overlay_rect(frame, 0, h - 40, w, 40, COLORS["bg_dark"], alpha=0.7)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), COLORS["gray"], 1)

        progress = min(reps / max(self.min_reps, 1), 1.0)
        fill_w   = int(bar_w * progress)
        fill_color = COLORS["ok"] if progress >= 1.0 else COLORS["accent"]
        if fill_w > 0:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), fill_color, -1)

        label = f"{reps}/{self.min_reps} reps"
        cv2.putText(
            frame, label,
            (bar_x + bar_w // 2 - 30, bar_y + 12),
            FONT, 0.42, COLORS["white"], 1, cv2.LINE_AA
        )

    def _draw_angle_hud(self, frame, feedback: ExerciseFeedback):
        """Exibe o ângulo atual no canto inferior esquerdo."""
        if feedback.angle is None:
            return
        x, y = self.MARGIN, frame.shape[0] - 55
        color = _level_color(feedback.level)
        cv2.putText(
            frame, f"{feedback.angle_name}: {feedback.angle:.0f}°",
            (x, y), FONT_BOLD, 0.8, color, 2, cv2.LINE_AA
        )

    def _draw_status_badge(self, frame, status: ExerciseStatus):
        """Badge pequeno mostrando a fase do exercício."""
        labels = {
            ExerciseStatus.WAITING:   "AGUARDANDO",
            ExerciseStatus.IN_MOTION: "SUBINDO ▲",
            ExerciseStatus.PEAK:      "PICO ●",
            ExerciseStatus.RETURNING: "DESCENDO ▼",
            ExerciseStatus.COMPLETED: "CONCLUÍDO ✔",
        }
        label = labels.get(status, "")
        x, y = self.MARGIN, 75
        _overlay_rect(frame, x - 4, y - 18, 160, 24, COLORS["bg_dark"], alpha=0.7)
        cv2.putText(frame, label, (x, y), FONT, 0.5, COLORS["gray"], 1, cv2.LINE_AA)

    def _draw_controls_hint(self, frame, h, w):
        """Dica de teclas no canto superior esquerdo."""
        hints = "[Q] Sair   [R] Reiniciar   [E] Exercício"
        cv2.putText(
            frame, hints,
            (self.MARGIN, h - 48),
            FONT, 0.42, COLORS["gray"], 1, cv2.LINE_AA
        )

    # ------------------------------------------------------------------
    # Tela de seleção de exercício
    # ------------------------------------------------------------------

    @staticmethod
    def draw_selection_screen(frame: np.ndarray, exercises: dict) -> np.ndarray:
        """Sobreposição de menu para seleção de exercício."""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        cx = w // 2
        cv2.putText(frame, "FisioCV", (cx - 90, 70), FONT_BOLD, 1.8, COLORS["accent"], 3, cv2.LINE_AA)
        cv2.putText(frame, "Selecione o exercício", (cx - 130, 110), FONT, 0.7, COLORS["white"], 1, cv2.LINE_AA)
        cv2.line(frame, (cx - 200, 120), (cx + 200, 120), COLORS["accent"], 1)

        for key, cls in exercises.items():
            y = 160 + int(key) * 55
            _overlay_rect(frame, cx - 220, y - 30, 440, 48, COLORS["bg_panel"], alpha=0.7)
            cv2.putText(frame, f"[{key}]  {cls.NAME}", (cx - 200, y), FONT_BOLD, 0.75, COLORS["gold"], 2, cv2.LINE_AA)
            for i, line in enumerate(cls.DESCRIPTION.split("\n")[:1]):
                cv2.putText(frame, line, (cx - 200, y + 18), FONT, 0.42, COLORS["gray"], 1, cv2.LINE_AA)

        cv2.putText(frame, "Pressione o número correspondente", (cx - 165, h - 40), FONT, 0.5, COLORS["gray"], 1, cv2.LINE_AA)
        return frame

    # ------------------------------------------------------------------
    # Utilidade
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_text(text: str, max_chars: int) -> list[str]:
        words, lines, cur = text.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 <= max_chars:
                cur = (cur + " " + w).strip()
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or [text]
