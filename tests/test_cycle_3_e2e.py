import os
import sys
import unittest
import io
import json
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.doc_manager import delete_permanently

class TestCycle3E2E(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Crea un'immagine JPEG di test in memoria
        dummy = np.ones((600, 400, 3), dtype=np.uint8) * 220
        cv2.putText(dummy, "E2E TEST DOC", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (10, 10, 10), 2)
        _, buf = cv2.imencode(".jpg", dummy)
        self.test_img_bytes = buf.tobytes()

    def test_01_static_assets_and_html(self):
        """Verifica la disponibilità della Web App e di tutti i file statici"""
        # Home page
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Scanner Web Multi", res.data)
        self.assertIn(b"cropperModal", res.data)
        self.assertIn(b"batchToolbar", res.data)

        # File statici
        for asset in ('/static/css/style.css', '/static/js/app.js', '/static/js/cropper.js', '/static/js/batch_manager.js', '/static/js/camera.js'):
            r = self.client.get(asset)
            self.assertEqual(r.status_code, 200, f"File statico non raggiungibile: {asset}")
        print("  [OK] Pagina principale HTML e tutte le risorse JS/CSS statiche verificate con successo.")

    def test_02_full_api_workflow(self):
        """Verifica il flusso completo API REST: crea doc -> aggiungi pagina -> filtra -> OCR -> esporta -> cestina"""
        # 1. Crea documento
        res = self.client.post('/api/documents', json={"title": "Doc E2E Test", "block_id": "general"})
        self.assertEqual(res.status_code, 201)
        doc = res.get_json()
        doc_id = doc["id"]

        try:
            # 2. Aggiungi pagina (upload multipart)
            data = {
                'image': (io.BytesIO(self.test_img_bytes), 'scan.jpg'),
                'auto_crop': 'true',
                'filter_type': 'magic_color'
            }
            res_page = self.client.post(f'/api/documents/{doc_id}/pages', data=data, content_type='multipart/form-data')
            self.assertEqual(res_page.status_code, 201)
            page = res_page.get_json()
            page_id = page["id"]
            self.assertEqual(page["filter_type"], "magic_color")

            # 3. Processa pagina (cambio filtro a B&W e luminosità)
            res_proc = self.client.post(f'/api/documents/{doc_id}/pages/{page_id}/process', json={
                "filter_type": "bw",
                "brightness": 5,
                "contrast": 10
            })
            self.assertEqual(res_proc.status_code, 200)
            proc_data = res_proc.get_json()
            self.assertEqual(proc_data["filter_type"], "bw")

            # 4. Esegui OCR sulla pagina
            res_ocr = self.client.post(f'/api/documents/{doc_id}/pages/{page_id}/ocr', json={"lang": "ita+eng"})
            self.assertEqual(res_ocr.status_code, 200)
            ocr_data = res_ocr.get_json()
            self.assertIn("text", ocr_data)

            # 5. Esporta documento in PDF
            res_pdf = self.client.get(f'/api/documents/{doc_id}/pdf?page_size=A4&quality=high')
            self.assertEqual(res_pdf.status_code, 200)
            self.assertEqual(res_pdf.mimetype, 'application/pdf')
            self.assertGreater(len(res_pdf.data), 1000)

            # 6. Sposta nel cestino
            res_trash = self.client.delete(f'/api/documents/{doc_id}')
            self.assertEqual(res_trash.status_code, 200)

            # 7. Ripristina dal cestino
            res_restore = self.client.post(f'/api/documents/{doc_id}/restore')
            self.assertEqual(res_restore.status_code, 200)

        finally:
            # Pulizia definitiva
            delete_permanently(doc_id)

        print("  [OK] Flusso API REST end-to-end (creazione, upload, filtri, OCR, PDF, cestino) completato.")

    def test_03_windows_integration_files(self):
        """Verifica la correttezza e l'integrità degli script e configurazioni Windows"""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # 1. avvia_scanner.bat
        bat_path = os.path.join(root_dir, "avvia_scanner.bat")
        self.assertTrue(os.path.exists(bat_path), "avvia_scanner.bat deve esistere")
        with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            self.assertIn("python app.py", content)
            self.assertIn("http://localhost:5000", content)

        # 2. start.bat
        self.assertTrue(os.path.exists(os.path.join(root_dir, "start.bat")))

        # 3. requirements.txt
        req_path = os.path.join(root_dir, "requirements.txt")
        self.assertTrue(os.path.exists(req_path))
        with open(req_path, "r", encoding="utf-8") as f:
            req_content = f.read()
            self.assertIn("flask", req_content)
            self.assertIn("opencv-python", req_content)
            self.assertIn("pillow", req_content)

        # 4. memoria.md
        mem_path = os.path.join(root_dir, "memoria.md")
        self.assertTrue(os.path.exists(mem_path))

        print("  [OK] File di configurazione ed eseguibili Windows (.bat, requirements.txt, memoria.md) perfettamente validati.")

if __name__ == "__main__":
    unittest.main()
