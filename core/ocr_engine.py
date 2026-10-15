import os
import cv2
import json

# Percorsi tipici di installazione Tesseract su Windows
POSSIBLE_TESSERACT_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.path.expanduser("~"), r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

def get_tesseract_cmd():
    for p in POSSIBLE_TESSERACT_PATHS:
        if os.path.exists(p):
            return p
    import shutil
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path
    return None

def configure_pytesseract():
    try:
        import pytesseract
        cmd = get_tesseract_cmd()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
            tessdata_dir = os.path.join(os.path.dirname(cmd), "tessdata")
            if os.path.exists(tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
        return pytesseract
    except Exception:
        return None

def is_pytesseract_available():
    try:
        pyt = configure_pytesseract()
        if pyt is None:
            return False
        pyt.get_tesseract_version()
        return True
    except Exception:
        return False

def run_ocr_on_image(image_path_or_array, lang="ita+eng"):
    """
    Esegue l'OCR sull'immagine.
    Se pytesseract e il binario Tesseract sono installati, estrae testo e bounding box delle parole.
    Altrimenti restituisce un messaggio informativo e i blocchi rilevati via analisi OpenCV.
    """
    if isinstance(image_path_or_array, (bytes, bytearray)):
        import numpy as np
        nparr = np.frombuffer(image_path_or_array, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        return {"text": "", "blocks": []}

    h, w = img.shape[:2]

    # Verifica se pytesseract è configurato
    pyt = configure_pytesseract()
    if pyt is not None and is_pytesseract_available():
        try:
            # Verifica lingue disponibili nel tessdata
            try:
                available = pyt.get_languages()
            except Exception:
                available = ["eng"]

            chosen_lang = "eng"
            if "ita" in available and "eng" in available:
                chosen_lang = "ita+eng"
            elif "ita" in available:
                chosen_lang = "ita"
            elif "eng" in available:
                chosen_lang = "eng"

            # Scala di grigi per ottimizzare Tesseract
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

            # Estrazione testo completo
            text = pyt.image_to_string(gray, lang=chosen_lang)

            # Estrazione coordinate parole (data)
            data = pyt.image_to_data(gray, lang=chosen_lang, output_type=pyt.Output.DICT)
            blocks = []
            n_boxes = len(data.get('text', []))
            for i in range(n_boxes):
                word = str(data['text'][i]).strip()
                try:
                    conf = int(data['conf'][i])
                except (ValueError, TypeError):
                    conf = 0
                if word and conf > 20:
                    blocks.append({
                        "text": word,
                        "confidence": conf,
                        "box": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    })

            clean_text = text.strip()
            return {
                "text": clean_text if clean_text else "(Nessun testo rilevato nella pagina)",
                "blocks": blocks,
                "engine": f"tesseract ({chosen_lang})"
            }
        except Exception as e:
            print(f"Errore durante l'esecuzione di Tesseract: {e}")

    # Fallback se Tesseract binario non è installato su Windows:
    # Rilevamento zone di testo ad alto contrasto con OpenCV (MSER/Morphology)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blocks = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw > 20 and bh > 8 and bw < w * 0.95:
            blocks.append({
                "text": "[Blocco testo rilevato]",
                "confidence": 80,
                "box": {"x": x, "y": y, "width": bw, "height": bh}
            })

    return {
        "text": "OCR pronto (Per riconoscimento caratteri completo, installare Tesseract OCR per Windows o utilizzare Tesseract.js nel browser).",
        "blocks": blocks,
        "engine": "opencv_fallback"
    }

def run_text_recognition(image_path_or_array, mode="ocr", lang="ita+eng", model=None):
    """
    Riconoscimento testo tramite motore Tesseract OCR (italiano e inglese).
    """
    return run_ocr_on_image(image_path_or_array, lang=lang)

