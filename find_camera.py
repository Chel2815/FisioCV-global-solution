"""
find_camera.py
--------------
Detecta todas as câmeras disponíveis no sistema e mostra um
preview de cada uma. Use para descobrir o índice correto do
celular sendo usado como webcam (DroidCam, EpocCam, iVCam, etc.)
"""

import cv2
import sys


def scan_cameras(max_index: int = 10) -> list[int]:
    """Tenta abrir câmeras de 0 até max_index e retorna os índices que funcionam."""
    found = []
    print("Escaneando câmeras disponíveis...\n")

    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)   # CAP_DSHOW é mais estável no Windows
        if not cap.isOpened():
            cap = cv2.VideoCapture(i)               # fallback sem backend específico

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  [ENCONTRADA] Câmera índice {i}  —  {w}x{h} @ {fps:.0f}fps")
                found.append(i)
            cap.release()
        else:
            print(f"  [ ] Índice {i}: não disponível")

    return found


def preview_camera(index: int):
    """Abre um preview da câmera escolhida para confirmar que é a correta."""
    # Tenta com DirectShow primeiro (Windows), depois genérico
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Não foi possível abrir câmera {index}.")
        return

    print(f"\nMostrando preview da câmera {index}.")
    print("Pressione [Q] para fechar ou [S] para confirmar e salvar o índice.\n")

    cv2.namedWindow("Preview – FisioCV", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Preview – FisioCV", 800, 500)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        cv2.putText(
            frame, f"Camera index: {index}  |  [S] Confirmar  [Q] Fechar",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 80), 2
        )
        cv2.imshow("Preview – FisioCV", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Salva o índice num arquivo para o main.py usar automaticamente
            with open("camera_index.txt", "w") as f:
                f.write(str(index))
            print(f"✔  Índice {index} salvo em camera_index.txt")
            print(f"   Execute:  python main.py --camera {index}")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    cameras = scan_cameras()

    if not cameras:
        print("\n[ERRO] Nenhuma câmera detectada.")
        print("Verifique se:")
        print("  • O app do celular (DroidCam / EpocCam / iVCam) está aberto e conectado")
        print("  • O driver virtual da câmera foi instalado no PC")
        print("  • A câmera não está sendo usada por outro programa")
        sys.exit(1)

    print(f"\n{len(cameras)} câmera(s) encontrada(s): índices {cameras}")

    if len(cameras) == 1:
        print(f"\nApenas uma câmera disponível. Abrindo preview do índice {cameras[0]}...")
        preview_camera(cameras[0])
    else:
        print("\nEscolha qual câmera visualizar:")
        for idx in cameras:
            print(f"  [{idx}] Câmera {idx}")
        try:
            choice = int(input("Índice: ").strip())
            if choice in cameras:
                preview_camera(choice)
            else:
                print("Índice inválido.")
        except (ValueError, KeyboardInterrupt):
            pass
