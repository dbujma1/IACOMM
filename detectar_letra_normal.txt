"""
detectar_letra.py
-----------------
Puente entre el frame de la cámara (OpenCV/numpy) y el modelo Keras
de reconocimiento de lenguaje de signos.

Modelo: best_sign_model_1.keras
  - Base:    MobileNetV2 (96×96×3)
  - Salida:  26 clases  →  A, B, C … Z  (softmax)
"""

"""
detectar_letra.py
-----------------
Pipeline mejorado: MediaPipe Hands → recorte de mano → modelo Keras
"""

from pathlib import Path
import numpy as np
import cv2
import mediapipe as mp

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
MODEL_PATH           = Path(__file__).resolve().parent / "best_sign_model_1.keras"
IMG_SIZE             = 96
CONFIDENCE_THRESHOLD = 0.85          # subido de 0.60 a 0.85
CLASES               = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
PADDING              = 0.20          # margen alrededor de la mano (20%)

# ---------------------------------------------------------------------------
# MediaPipe Hands (una sola vez)
# ---------------------------------------------------------------------------
_mp_hands = mp.solutions.hands
_hands    = _mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)

# ---------------------------------------------------------------------------
# Carga del modelo (una sola vez al importar)
# ---------------------------------------------------------------------------
_model = None

def _get_model():
    global _model
    if _model is None:
        import keras
        _model = keras.models.load_model(str(MODEL_PATH))
    return _model

# ---------------------------------------------------------------------------
# Preprocesado
# ---------------------------------------------------------------------------
def _preprocesar(frame_bgr: np.ndarray) -> np.ndarray:
    from keras.applications.mobilenet_v2 import preprocess_input
    img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    img = img.astype("float32")
    img = preprocess_input(img)
    return np.expand_dims(img, axis=0)

# ---------------------------------------------------------------------------
# Detección y recorte de mano con MediaPipe
# ---------------------------------------------------------------------------
def _recortar_mano(frame_bgr: np.ndarray):
    """
    Devuelve el recorte BGR de la mano si se detecta, o None si no hay mano.
    Aplica padding para incluir contexto alrededor de los dedos.
    """
    h, w = frame_bgr.shape[:2]
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    resultado = _hands.process(frame_rgb)

    if not resultado.multi_hand_landmarks:
        return None                          # ← sin mano, no clasificamos nada

    landmarks = resultado.multi_hand_landmarks[0].landmark

    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]

    # Bounding box con padding
    x_min = max(0.0, min(xs) - PADDING)
    x_max = min(1.0, max(xs) + PADDING)
    y_min = max(0.0, min(ys) - PADDING)
    y_max = min(1.0, max(ys) + PADDING)

    # Pasar a píxeles y recortar
    x1, x2 = int(x_min * w), int(x_max * w)
    y1, y2 = int(y_min * h), int(y_max * h)

    recorte = frame_bgr[y1:y2, x1:x2]

    if recorte.size == 0:
        return None

    return recorte

# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def detectar_letra_con_confianza(frame_bgr: np.ndarray):
    recorte = _recortar_mano(frame_bgr)

    if recorte is None:
        return None, 0.0               # ← no hay mano detectada, confianza 0

    modelo     = _get_model()
    entrada    = _preprocesar(recorte) # ahora el modelo ve solo la mano
    prediccion = modelo.predict(entrada, verbose=0)[0]
    idx        = int(np.argmax(prediccion))
    confianza  = float(prediccion[idx])

    if confianza < CONFIDENCE_THRESHOLD:
        return None, confianza

    return CLASES[idx], confianza


def detectar_letra(frame_bgr: np.ndarray):
    letra, _ = detectar_letra_con_confianza(frame_bgr)
    return letra