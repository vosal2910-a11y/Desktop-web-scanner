import cv2
import numpy as np
from PIL import Image
import os

def order_points(pts):
    """
    Ordina 4 punti nel seguente ordine:
    [in alto a sinistra (TL), in alto a destra (TR), in basso a destra (BR), in basso a sinistra (BL)]
    """
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")

    # Somma coordinate (x + y):
    # il punto TL avrà la somma minima, BR la somma massima
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Differenza coordinate (y - x):
    # il punto TR avrà la differenza minima, BL la massima
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def detect_document_corners(image_path_or_array, max_dim=1200):
    """
    Rileva automaticamente i 4 angoli del documento nell'immagine.
    Restituisce un quad formato da 4 punti: [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
    """
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Impossibile caricare l'immagine specificata")

    orig_h, orig_w = img.shape[:2]

    # Ridimensionamento proporzionale per elaborazione rapida
    scale = 1.0
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / float(max(orig_h, orig_w))
        resized = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)), interpolation=cv2.INTER_AREA)
    else:
        resized = img.copy()

    h, w = resized.shape[:2]

    # Preprocessing: scala di grigi e blur
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection e chiusura morfologica
    edged = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    dilated = cv2.dilate(edged, kernel, iterations=1)
    closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Ricerca contorni
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    document_quad = None
    min_area = (w * h) * 0.10  # Almeno il 10% dell'immagine

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            # Trovato poligono a 4 vertici
            document_quad = approx.reshape(4, 2)
            break

    # Se non trovato un contorno preciso a 4 punti, tenta con la sogliatura adattiva
    if document_quad is None:
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.03 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                document_quad = approx.reshape(4, 2)
                break

    # Fallback: margine del 5% dai bordi dell'immagine
    if document_quad is None:
        margin_x = int(orig_w * 0.05)
        margin_y = int(orig_h * 0.05)
        return [
            [margin_x, margin_y],
            [orig_w - margin_x, margin_y],
            [orig_w - margin_x, orig_h - margin_y],
            [margin_x, orig_h - margin_y]
        ]

    # Riporta le coordinate alle dimensioni originali
    orig_quad = (document_quad / scale).astype("float32")
    ordered = order_points(orig_quad)

    return ordered.tolist()


def warp_perspective(image_path_or_array, quad):
    """
    Esegue la trasformazione omografica prospettica data una lista di 4 punti (quad).
    Restituisce l'immagine raddrizzata (spianata) a 90 gradi.
    """
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Impossibile caricare l'immagine per la correzione prospettica")

    rect = order_points(quad)
    (tl, tr, br, bl) = rect

    # Calcola la larghezza massima del nuovo rettangolo
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    # Calcola l'altezza massima del nuovo rettangolo
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    # Punti di destinazione ortogonali
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    # Matrice di trasformazione prospettica e warp
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (max_width, max_height), flags=cv2.INTER_CUBIC)

    return warped


def apply_color_enhancements(img, filter_type='magic_color', brightness=0, contrast=0, bw_threshold=128):
    """
    Applica i filtri colore e miglioramenti derivati da OSS Document Scanner:
    - magic_color (Enhanced Paper)
    - bw (Bianco e nero binario con soglia)
    - grayscale (Scala di grigi ottimizzata)
    - sepia (Filtro seppia)
    - invert (Negativo)
    - polaroid (Color boost)
    - normal (Originale con brightness/contrast)
    """
    result = img.copy()

    # 1. Applicazione filtro base
    if filter_type == 'magic_color':
        # Algoritmo Enhanced Paper / Magic Color:
        # Normalizzazione illuminazione tramite divisione per lo sfondo sfocato
        # e rimappatura dinamica del contrasto
        rgb_planes = cv2.split(result)
        result_planes = []
        for plane in rgb_planes:
            dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
            bg_blur = cv2.medianBlur(dilated, 21)
            diff = 255 - cv2.absdiff(plane, bg_blur)
            norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_planes.append(norm)
        result = cv2.merge(result_planes)
        # Leggera enfatizzazione contrasto con CLAHE su canale L (spazio LAB)
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        result = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

    elif filter_type == 'bw':
        # Bianco e nero documentale ad alto contrasto
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        if bw_threshold == 'auto' or bw_threshold is None:
            # Sogliatura Otsu automatica
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            t_val = int(bw_threshold) if isinstance(bw_threshold, (int, float)) else 128
            _, thresh = cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY)
        result = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    elif filter_type == 'grayscale':
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    elif filter_type == 'sepia':
        # Matrice seppia standard
        sepia_kernel = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        result = cv2.transform(result, sepia_kernel)
        result = np.clip(result, 0, 255).astype(np.uint8)

    elif filter_type == 'invert':
        result = cv2.bitwise_not(result)

    elif filter_type == 'polaroid':
        # Color boost / saturazione aumentata
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype("float32")
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.35, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.10, 0, 255)
        result = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    # 2. Applicazione regolazioni Luminosità e Contrasto
    # brightness in [-100, 100], contrast in [-100, 100]
    b = float(brightness)
    c = float(contrast)
    if b != 0 or c != 0:
        # Convert contrasto a fattore moltiplicativo: 0 -> 1.0, 50 -> 1.5, -50 -> 0.5
        alpha = float(1.0 + (c / 100.0))
        # Brightness come offset
        beta = float(b * 1.28)  # scala a ~[-128, 128]
        result = cv2.convertScaleAbs(result, alpha=alpha, beta=beta)

    return result


def rotate_image(img, angle):
    """
    Ruota l'immagine di 90, 180 o 270 gradi in senso orario.
    """
    angle = int(angle) % 360
    if angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def detect_barcodes_and_qrcodes(img):
    """
    Rileva e decodifica codici QR e codici a barre presenti nell'immagine.
    Restituisce un elenco di dizionari {type, data, bbox}.
    """
    results = []
    
    # 1. Rilevamento QR Code con OpenCV
    qr_detector = cv2.QRCodeDetector()
    val, points, _ = qr_detector.detectAndDecode(img)
    if val:
        pts = points[0].tolist() if points is not None else []
        results.append({
            "type": "QR_CODE",
            "text": val,
            "points": pts
        })

    # 2. Tentativo con rilevatore Barcode OpenCV se disponibile
    try:
        barcode_detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, points = barcode_detector.detectAndDecode(img)
        if ok and decoded_info:
            for info, b_type, pts in zip(decoded_info, decoded_type, points):
                if info and info not in [r["text"] for r in results]:
                    results.append({
                        "type": b_type if b_type else "BARCODE",
                        "text": info,
                        "points": pts.tolist() if pts is not None else []
                    })
    except Exception:
        pass

    return results
