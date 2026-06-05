import argparse
import os
import sys
import time
import cv2

from pose_detector import PoseDetector
from ui_renderer   import UIRenderer
from exercises     import EXERCISE_REGISTRY


def parse_args():
    parser = argparse.ArgumentParser(description="FisioCV – Fisioterapia com Visao Computacional")
    parser.add_argument("--source",   type=str, default=None, help="Caminho para arquivo de video")
    parser.add_argument("--camera",   type=int, default=0,    help="Indice da webcam (default: 0)")
    parser.add_argument("--exercise", type=str, default=None, help="Codigo do exercício (1, 2 ou 3)")
    parser.add_argument("--width",    type=int, default=1280, help="Largura do frame de captura")
    parser.add_argument("--height",   type=int, default=720,  help="Altura do frame de captura")
    return parser.parse_args()


def _try_open(index: int) -> cv2.VideoCapture | None:
    for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                return cap
            cap.release()
    return None


def _load_saved_index() -> int | None:
    try:
        with open("camera_index.txt") as f:
            return int(f.read().strip())
    except Exception:
        return None


def open_capture(args) -> cv2.VideoCapture:
    # ── Fonte de vídeo (arquivo) ──────────────────────────────────────
    if args.source:
        cap = cv2.VideoCapture(args.source)
        if not cap.isOpened():
            print(f"[ERRO] Não foi possível abrir o arquivo: {args.source}")
            sys.exit(1)
        return cap


    candidates: list[int] = []

    if args.camera != 0:
        candidates.append(args.camera)

    saved = _load_saved_index()
    if saved is not None and saved not in candidates:
        candidates.append(saved)

    candidates += [i for i in range(8) if i not in candidates]  # varredura 0-7

    print("Procurando câmera disponível...")
    for idx in candidates:
        cap = _try_open(idx)
        if cap:
            print(f"Câmera encontrada no indice {idx}")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            return cap
        else:
            print(f"  · Indice {idx}: nao disponivel")

    print("\n[ERRO] Nenhuma câmera encontrada (índices 0-7).")
    print("Dicas:")
    print("  • Abra o app do celular (DroidCam / EpocCam / iVCam) ANTES de rodar")
    print("  • Instale o driver virtual no PC (link no README do app)")
    print("  • Execute  python find_camera.py  para diagnóstico detalhado")
    print("  • Ou use um vídeo:  python main.py --source meu_video.mp4")
    sys.exit(1)


def select_exercise_screen(cap: cv2.VideoCapture, preselect: str | None) -> object:
    if preselect and preselect in EXERCISE_REGISTRY:
        return EXERCISE_REGISTRY[preselect]()

    window = "FisioCV – Seleção"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 1280, 720)

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = cv2.flip(frame, 1)
        UIRenderer.draw_selection_screen(frame, EXERCISE_REGISTRY)
        cv2.imshow(window, frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)
        key_char = chr(key)
        if key_char in EXERCISE_REGISTRY:
            cv2.destroyWindow(window)
            return EXERCISE_REGISTRY[key_char]()

def run(cap: cv2.VideoCapture, exercise, args):
    detector = PoseDetector(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    renderer = UIRenderer(exercise.NAME, exercise.MIN_REPS)

    window = "FisioCV"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 1280, 720)

    fps_counter, fps_start = 0, time.time()
    fps = 0.0

    print(f"\n Exercicio selecionado: {exercise.NAME}")
    print(f"   Meta: {exercise.MIN_REPS} repeticoes")
    print("   Teclas: [Q] Sair  [R] Reiniciar  [E] Trocar exercicio\n")

    is_file = args.source is not None

    while True:
        ret, frame = cap.read()
        if not ret:
            if is_file:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break

        if not is_file:
            frame = cv2.flip(frame, 1)

        detector.process(frame)
        feedback = exercise.analyze(detector, frame)
        detector.draw_skeleton(frame)
        renderer.render(frame, feedback)

        # FPS
        fps_counter += 1
        elapsed = time.time() - fps_start
        if elapsed >= 1.0:
            fps = fps_counter / elapsed
            fps_counter, fps_start = 0, time.time()
        cv2.putText(
            frame, f"FPS: {fps:.1f}",
            (frame.shape[1] - 110, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 1, cv2.LINE_AA
        )
        # ────────────────────────────────────────────────────────────

        cv2.imshow(window, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # Reinicia o exercício atual
            exercise.__init__()
            print("  Exercicio reiniciado.")
        elif key == ord('e'):
            # Volta para o menu de seleção
            detector.release()
            cv2.destroyWindow(window)
            new_exercise = select_exercise_screen(cap, None)
            run(cap, new_exercise, args)
            return   # encerra esta chamada recursiva

    cap.release()
    detector.release()
    cv2.destroyAllWindows()

    print(f"\n Sessão encerrada — {feedback.reps} repeticoes realizadas.")


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

if __name__ == "__main__":
    args    = parse_args()
    cap     = open_capture(args)
    exercise = select_exercise_screen(cap, args.exercise)
    run(cap, exercise, args)
