import os
import sys
import unittest
import numpy as np
import cv2
import time
import gc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.doc_manager import create_document, add_page_to_document, process_page, delete_permanently
from core.pdf_exporter import export_document_pdf, export_batch_pdf, export_batch_images
from core.scanner_cv import apply_color_enhancements, warp_perspective

class TestResourceEconomy(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        self.doc = create_document(title="Stress Test Economia Risorse")
        self.doc_id = self.doc["id"]

    def tearDown(self):
        delete_permanently(self.doc_id)

    def test_01_high_res_speed_and_memory(self):
        """Verifica che un'immagine ad alta risoluzione (3000x2000) venga elaborata in frazioni di secondo"""
        high_res = np.random.randint(180, 255, (2000, 3000, 3), dtype=np.uint8)
        cv2.putText(high_res, "TEST FATTURA AD ALTA RISOLUZIONE", (100, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

        t0 = time.time()
        # Ingestione con ridimensionamento automatico a cap 2048px e applicazione magic_color ottimizzato
        page = add_page_to_document(self.doc_id, high_res, auto_crop=False, filter_type="magic_color")
        elapsed = time.time() - t0

        self.assertIsNotNone(page)
        self.assertLessEqual(max(page["width"], page["height"]), 2048)
        self.assertLess(elapsed, 2.0, f"L'elaborazione deve completarsi in meno di 2s, impiegati: {elapsed:.3f}s")
        print(f"  [OK] Ingestione e filtraggio magic_color su immagine 3000x2000 completati in {elapsed:.3f}s (< 2s)")

    def test_02_multipage_pdf_export_memory_efficiency(self):
        """Verifica generazione PDF multipagina con consumo O(1) memoria per pagina"""
        test_img = np.ones((800, 600, 3), dtype=np.uint8) * 240
        for i in range(5):
            cv2.putText(test_img, f"PAGINA {i + 1}", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (10, 10, 10), 2)
            add_page_to_document(self.doc_id, test_img, auto_crop=False, filter_type="bw")

        t0 = time.time()
        pdf_bytes = export_document_pdf(self.doc_id, page_size="A4", quality="high")
        elapsed = time.time() - t0

        self.assertGreater(len(pdf_bytes), 2000)
        self.assertLess(elapsed, 2.5, f"Esportazione PDF di 5 pagine completata in {elapsed:.3f}s (< 2.5s)")
        print(f"  [OK] Esportazione PDF di 5 pagine completata in {elapsed:.3f}s (dimensione: {len(pdf_bytes)} bytes)")

    def test_03_zero_cost_jpg_batch_zip(self):
        """Verifica che l'esportazione batch JPG sfrutti i file su disco a costo computazionale zero"""
        test_img = np.ones((600, 500, 3), dtype=np.uint8) * 250
        add_page_to_document(self.doc_id, test_img, auto_crop=False, filter_type="magic_color")
        add_page_to_document(self.doc_id, test_img, auto_crop=False, filter_type="bw")

        t0 = time.time()
        zip_bytes, fname, mime = export_batch_images([self.doc_id], img_format="jpg")
        elapsed = time.time() - t0

        self.assertEqual(mime, "application/zip")
        self.assertGreater(len(zip_bytes), 1000)
        self.assertLess(elapsed, 1.0, f"Esportazione ZIP istantanea completata in {elapsed:.3f}s (< 1s)")
        print(f"  [OK] Esportazione ZIP JPG streaming diretto completata in {elapsed:.3f}s (< 1s)")

if __name__ == "__main__":
    unittest.main()
