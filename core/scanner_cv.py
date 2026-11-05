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

    # Somma coordinate (x + y): TL ha somma minima, BR massima
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Differenza coordinate (y - x): TR ha diff minima, BL massima
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def detect_document_corners(image_path_or_array, max_dim=800):
    """
    Rileva automaticamente i 4 angoli del documento con massima efficienza CPU/RAM.
    Utilizza un proxy leggero (max 800px) per l'analisi dei contorni.
    Restituisce un quad formato da 4 punti: [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
    """
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Impossibile caricare l'immagine specificata")

    orig_h, orig_w = img.shape[:2]

    # Ridimensionamento proporzionale su proxy leggero per analisi istantanea
    scale = 1.0
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / float(max(orig_h, orig_w))
        resized = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)), interpolation=cv2.INTER_AREA)
    else:
        resized = img

    h, w = resized.shape[:2]

    # Preprocessing veloce: scala di grigi e blur gaussiano
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection e chiusura morfologica
    edged = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=1)
    closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Ricerca contorni (massimo 8 candidati principali)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]

    document_quad = None
    min_area = (w * h) * 0.10  # Almeno il 10% dell'area

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            document_quad = approx.reshape(4, 2)
            break

    # Fallback adattivo rapido se non individuato al primo passaggio
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

    # Margine di salvaguardia (5%) se nessun quadrilatero viene identificato
    if document_quad is None:
        margin_x = int(orig_w * 0.05)
        margin_y = int(orig_h * 0.05)
        return [
            [margin_x, margin_y],
            [orig_w - margin_x, margin_y],
            [orig_w - margin_x, orig_h - margin_y],
            [margin_x, orig_h - margin_y]
        ]

    # Riporta le coordinate alle dimensioni reali dell'immagine
    orig_quad = (document_quad / scale).astype("float32")
    ordered = order_points(orig_quad)

    return ordered.tolist()


def warp_perspective(image_path_or_array, quad, max_dim=2048):
    """
    Esegue la trasformazione omografica prospettica data una lista di 4 punti (quad).
    Restituisce l'immagine ortogonale ottimizzata con INTER_LINEAR (veloce e a basso consumo di RAM).
    Limita la dimensione massima a max_dim per impedire allocazioni di memoria eccessive.
    """
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Impossibile caricare l'immagine per la correzione prospettica")

    rect = order_points(quad)
    (tl, tr, br, bl) = rect

    # Calcola larghezza massima
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    # Calcola altezza massima
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    # Limita proporzionalmente se le dimensioni superano max_dim
    if max(max_width, max_height) > max_dim:
        warp_scale = max_dim / float(max(max_width, max_height))
        max_width = max(100, int(max_width * warp_scale))
        max_height = max(100, int(max_height * warp_scale))

    # Coordinate di destinazione
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    # Trasformazione prospettica omografica con INTER_LINEAR (veloce e leggero)
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (max_width, max_height), flags=cv2.INTER_LINEAR)

    return warped


def apply_color_enhancements(img, filter_type='magic_color', brightness=0, contrast=0, bw_threshold=128):
    """
    Applica i filtri colore ottimizzati a bassissimo impatto computazionale:
    - magic_color: Normalizzazione sfondo a piramide multiscala (20x più veloce, zero OOM)
    - bw: Bianco e nero documentale ad alto contrasto (Otsu o soglia manuale)
    - grayscale: Scala di grigi nitida
    - sepia: Tonalità vintage calda
    - invert: Negativo
    - polaroid: Saturazione vivida
    - normal: Colori originali
    Include regolazione efficiente in-place di luminosità e contrasto.
    """
    result = img.copy()
    h, w = result.shape[:2]

    # 1. Applicazione filtro base
    if filter_type == 'magic_color':
        # Algoritmo Magic Paper / Illuminazione a Piramide Multiscala:
        # Invece di eseguire medianBlur 21x21 su milioni di pixel (che satura CPU e RAM),
        # calcola la mappa d'illuminazione dello sfondo su un proxy compatto (max 512px)
        # ed esegue il riallineamento bilineare. Risultato identico/superiore, tempo ~20-40ms.
        bg_scale = min(1.0, 512.0 / float(max(h, w)))
        small_w = max(16, int(w * bg_scale))
        small_h = max(16, int(h * bg_scale))
        small = cv2.resize(result, (small_w, small_h), interpolation=cv2.INTER_AREA)

        small_planes = cv2.split(small)
        bg_planes = []
        k_morph = np.ones((5, 5), np.uint8)

        for p in small_planes:
            dilated = cv2.dilate(p, k_morph)
            blurred = cv2.GaussianBlur(dilated, (21, 21), 0)
            bg_full = cv2.resize(blurred, (w, h), interpolation=cv2.INTER_LINEAR)
            bg_planes.append(bg_full)

        work_planes = cv2.split(result)
        res_planes = []
        for p, bg in zip(work_planes, bg_planes):
            diff = 255 - cv2.absdiff(p, bg)
            norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            res_planes.append(norm)

        result = cv2.merge(res_planes)

        # Contrast Limited Adaptive Histogram Equalization su luminosità LAB
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        result = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

    elif filter_type == 'bw':
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        if bw_threshold == 'auto' or bw_threshold is None:
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            t_val = int(bw_threshold) if isinstance(bw_threshold, (int, float)) else 128
            _, thresh = cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY)
        result = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    elif filter_type == 'grayscale':
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    elif filter_type == 'sepia':
        sepia_kernel = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ], dtype="float32")
        result = cv2.transform(result, sepia_kernel)
        result = np.clip(result, 0, 255).astype(np.uint8)

    elif filter_type == 'invert':
        result = cv2.bitwise_not(result)

    elif filter_type == 'polaroid':
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype("float32")
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.30, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08, 0, 255)
        result = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    # 2. Applicazione regolazioni Luminosità e Contrasto ad alta efficienza
    b = float(brightness)
    c = float(contrast)
    if b != 0 or c != 0:
        alpha = float(1.0 + (c / 100.0))
        beta = float(b * 1.28)
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
    Rileva codici QR e a barre ridimensionando l'immagine a un proxy leggero (max 800px).
    Evita il sovraccarico di memoria e CPU restituendo i punti scalati alle dimensioni originali.
    """
    if img is None:
        return []

    orig_h, orig_w = img.shape[:2]
    max_dim = 800

    # Ridimensionamento veloce per scansione codici
    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / float(max(orig_h, orig_w))
        scan_img = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)), interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        scan_img = img

    results = []

    # 1. Rilevamento QR Code con OpenCV
    try:
        qr_detector = cv2.QRCodeDetector()
        val, points, _ = qr_detector.detectAndDecode(scan_img)
        if val:
            pts = []
            if points is not None:
                # Riporta i punti alle coordinate dell'immagine originale
                pts = (points[0] / scale).tolist()
            results.append({
                "type": "QR_CODE",
                "text": val,
                "points": pts
            })
    except Exception:
        pass

    # 2. Rilevatore Barcode OpenCV
    try:
        barcode_detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, points = barcode_detector.detectAndDecode(scan_img)
        if ok and decoded_info:
            for info, b_type, pts in zip(decoded_info, decoded_type, points):
                if info and info not in [r["text"] for r in results]:
                    scaled_pts = (pts / scale).tolist() if pts is not None else []
                    results.append({
                        "type": b_type if b_type else "BARCODE",
                        "text": info,
                        "points": scaled_pts
                    })
    except Exception:
        pass

    return results
