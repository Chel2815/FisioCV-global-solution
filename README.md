# FisioCV 🦾

Sistema de verificação de exercícios de fisioterapia em tempo real utilizando **Visão Computacional**, **MediaPipe Pose** e **OpenCV**.

---

## 📋 Descrição

O **FisioCV** captura vídeo via webcam (ou arquivo de vídeo), detecta a pose do paciente com o MediaPipe e analisa se o exercício está sendo executado corretamente — fornecendo feedback visual em tempo real: ângulos articulares, contagem de repetições e alertas de postura.

### Exercícios disponíveis

| # | Exercício | Articulação | Meta |
|---|-----------|-------------|------|
| 1 | Abdução de Ombro | Ombro | 10 reps |
| 2 | Flexão de Cotovelo | Cotovelo | 12 reps |
| 3 | Agachamento | Joelho | 10 reps |

---

## 🛠 Bibliotecas utilizadas

- **OpenCV** (`opencv-python`) — captura de vídeo, renderização e manipulação de frames
- **MediaPipe** — detecção de pose e extração de landmarks do esqueleto
- **NumPy** — cálculo vetorial de ângulos articulares

---

## 🚀 Instruções de execução

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/fisio-cv.git
cd fisio-cv
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

> Recomenda-se Python 3.10+ e o uso de um ambiente virtual.

### 3. Execute

**Webcam padrão (com menu de seleção):**
```bash
python find_camera.py
````
Rodar o comando acima para identificar a Webcam utilizada, após isso rodar o comando:

````
python main.py
````

**Selecionar exercício diretamente:**
```bash
python main.py --exercise 1   # Abdução de Ombro
python main.py --exercise 2   # Flexão de Cotovelo
python main.py --exercise 3   # Agachamento
```

**Usar arquivo de vídeo:**
```bash
python main.py --source meu_video.mp4
```

### Teclas durante a sessão

| Tecla | Ação |
|-------|------|
| `Q` | Encerrar |
| `R` | Reiniciar contagem |
| `E` | Voltar ao menu de exercícios |

---

## 🗂 Estrutura do projeto

```
fisio-cv/
├── main.py               # Ponto de entrada e loop principal
├── pose_detector.py      # Wrapper MediaPipe Pose
├── ui_renderer.py        # HUD e elementos visuais
├── exercises/
│   ├── __init__.py       # Registro de exercícios
│   ├── base.py           # Classe base abstrata
│   ├── shoulder_abduction.py
│   ├── elbow_flexion.py
│   └── squat.py
├── requirements.txt
└── README.md
```

---

## 🔬 Pipeline de Visão Computacional

```
Webcam / Vídeo
     │
     ▼
Captura de Frame (OpenCV)
     │
     ▼
Detecção de Pose (MediaPipe Pose)
     │
     ▼
Extração de Landmarks (33 pontos)
     │
     ▼
Cálculo de Ângulos Articulares (NumPy)
     │
     ▼
Análise do Exercício (máquina de estados)
     │
     ▼
Feedback Visual em Tempo Real (OpenCV)
```

---

## 👥 Integrantes

RM 99856 – Marchel Augusto
RM 557538 – David Cordeiro
RM 555619 – Tiago Morais
RM 557065 – Vinicius Augusto
RM 556892 – Guilherme Lunghini
