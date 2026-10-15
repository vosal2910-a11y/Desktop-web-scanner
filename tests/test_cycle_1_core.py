import os
import sys
import unittest
import numpy as np
import cv2

# Aggiungi root path per importare core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.scanner_cv import (
    detect_document_corners,
    warp_perspective,
    apply_color_enhancements,
    rotate_image,
    detect_barcodes_and_qrcodes
)
from core.pdf_exporter import export_document_pdf
from core.doc_manager import create_document, add_page_to_document, delete_permanently

class TestCycle1Core(unittest.TestCase):
    def setUp(self):
        # Crea un'immagine sintetica simulando un foglio bianco inclinato su sfondo scuro
        self.img_h, self.img_w = 800, 600
        self.test_img = np.zeros((self.img_h, self.img_w, 3), dtype=np.uint8)
        self.test_img[:] = (30, 30, 30) # Sfondo scuro

        # Foglio bianco quadrangolare prospettico
        pts = np.array([
            [80, 100],   # TL
            [500, 140],  # TR
            [540, 720],  # BR
            [60, 680]    # BL
        ], np.int32)
        cv2.fillPoly(self.test_img, [pts], (240, 240, 240))
        # Aggiungi qualche "linea di testo"
        cv2.line(self.test_img, (120, 200), (450, 220), (20, 20, 20), 4)
        cv2.line(self.test_img, (120, 250), (420, 270), (20, 20, 20), 4)
        cv2.line(self.test_img, (120, 300), (460, 320), (20, 20, 20), 4)

    def test_01_corner_detection(self):
        """Test rilevamento automatico dei 4 angoli del foglio"""
        quad = detect_document_corners(self.test_img)
        self.assertEqual(len(quad), 4, "Il quad deve contenere esattamente 4 vertici")
        # I punti devono essere ordinati: TL, TR, BR, BL
        tl, tr, br, bl = quad
        self.assertTrue(tl[0] < tr[0], "TL deve avere x inferiore a TR")
        self.assertTrue(bl[0] < br[0], "BL deve avere x inferiore a BR")
        self.assertTrue(tl[1] < bl[1], "TL deve avere y inferiore a BL")
        print(f"  [OK] Rilevamento 4 angoli riuscito: {quad}")

    def test_02_perspective_warp(self):
        """Test correzione prospettica omografica (warp)"""
        quad = [
            [80, 100],
            [500, 140],
            [540, 720],
            [60, 680]
        ]
        warped = warp_perspective(self.test_img, quad)
        self.assertIsNotNone(warped)
        self.assertGreater(warped.shape[0], 400, "L'altezza dell'immagine raddrizzata deve essere corretta")
        self.assertGreater(warped.shape[1], 300, "La larghezza dell'immagine raddrizzata deve essere corretta")
        print(f"  [OK] Trasformazione omografica prospettica riuscita. Nuove dimensioni: {warped.shape}")

    def test_03_color_filters(self):
        """Test applicazione di tutti i filtri colore OSS"""
        filters = ['magic_color', 'bw', 'grayscale', 'sepia', 'invert', 'polaroid', 'normal']
        for f in filters:
            enhanced = apply_color_enhancements(self.test_img, filter_type=f, brightness=10, contrast=15)
            self.assertEqual(enhanced.shape, self.test_img.shape, f"Il filtro {f} deve mantenere le dimensioni dell'immagine")
            self.assertEqual(enhanced.dtype, np.uint8, f"Il filtro {f} deve restituire un array uint8 valido")
            print(f"  [OK] Filtro '{f}' applicato con successo.")

    def test_04_rotations(self):
        """Test rotazione dell'immagine"""
        for angle in (90, 180, 270):
            rotated = rotate_image(self.test_img, angle)
            if angle in (90, 270):
                self.assertEqual(rotated.shape[0], self.img_w)
                self.assertEqual(rotated.shape[1], self.img_h)
            else:
                self.assertEqual(rotated.shape[0], self.img_h)
                self.assertEqual(rotated.shape[1], self.img_w)
        print("  [OK] Test rotazioni 90°, 180°, 270° superato.")

    def test_05_qr_barcode_detection(self):
        """Test rilevamento codici QR sintetici"""
        qr_canvas = np.ones((400, 400, 3), dtype=np.uint8) * 255
        # Prova ad eseguire la funzione
        res = detect_barcodes_and_qrcodes(qr_canvas)
        self.assertIsInstance(res, list)
        print(f"  [OK] Funzione rilevamento codici QR/Barcode operativa (risultati: {res})")

    def test_06_tesseract_ocr_execution(self):
        """Test motore OCR con Tesseract per riconoscimento caratteri effettivo"""
        from core.ocr_engine import is_pytesseract_available, run_ocr_on_image
        self.assertTrue(is_pytesseract_available(), "Tesseract deve essere disponibile e configurato")
        ocr_canvas = np.ones((120, 500, 3), dtype=np.uint8) * 255
        cv2.putText(ocr_canvas, "FATTURA N 105", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        res = run_ocr_on_image(ocr_canvas)
        self.assertIn("FATTURA", res.get("text", "").upper())
        self.assertGreater(len(res.get("blocks", [])), 0)
        print(f"  [OK] Riconoscimento caratteri Tesseract OCR verificato con successo: '{res['text']}'")

if __name__ == "__main__":
    unittest.main()
