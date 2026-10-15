import os
import sys
import unittest
import io
import zipfile
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.doc_manager import create_document, add_page_to_document, delete_permanently
from core.pdf_exporter import export_document_images, export_batch_images

class TestExportAndProgress(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Crea un'immagine di test
        self.img = np.ones((500, 400, 3), dtype=np.uint8) * 230
        cv2.putText(self.img, "EXPORT TEST", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (20, 20, 20), 2)

        # Crea un documento con 2 pagine
        self.doc = create_document(title="Doc Multiformato")
        self.doc_id = self.doc["id"]
        add_page_to_document(self.doc_id, self.img, auto_crop=False, filter_type="magic_color")
        add_page_to_document(self.doc_id, self.img, auto_crop=False, filter_type="bw")

    def tearDown(self):
        delete_permanently(self.doc_id)

    def test_01_export_images_multipage(self):
        """Test esportazione documento multipagina in ZIP di JPG e PNG"""
        # JPG ZIP
        jpg_bytes, filename_jpg, mime_jpg = export_document_images(self.doc_id, img_format="jpg")
        self.assertEqual(mime_jpg, "application/zip")
        self.assertTrue(filename_jpg.endswith(".zip"))
        zf_jpg = zipfile.ZipFile(io.BytesIO(jpg_bytes))
        self.assertEqual(len(zf_jpg.namelist()), 2)
        self.assertTrue(all(name.endswith(".jpg") for name in zf_jpg.namelist()))

        # PNG ZIP
        png_bytes, filename_png, mime_png = export_document_images(self.doc_id, img_format="png")
        self.assertEqual(mime_png, "application/zip")
        self.assertTrue(filename_png.endswith(".zip"))
        zf_png = zipfile.ZipFile(io.BytesIO(png_bytes))
        self.assertEqual(len(zf_png.namelist()), 2)
        self.assertTrue(all(name.endswith(".png") for name in zf_png.namelist()))
        print("  [OK] Esportazione multipagina in archivi ZIP JPG e PNG verificata con successo.")

    def test_02_export_single_page_image(self):
        """Test esportazione singola pagina specifica in JPG e PNG diretto"""
        # Pagina 1 come JPG
        jpg_p1, name_p1, mime_p1 = export_document_images(self.doc_id, img_format="jpg", page_index=0)
        self.assertEqual(mime_p1, "image/jpeg")
        self.assertTrue(name_p1.endswith(".jpg"))
        self.assertGreater(len(jpg_p1), 500)

        # Pagina 2 come PNG
        png_p2, name_p2, mime_p2 = export_document_images(self.doc_id, img_format="png", page_index=1)
        self.assertEqual(mime_p2, "image/png")
        self.assertTrue(name_p2.endswith(".png"))
        self.assertGreater(len(png_p2), 500)
        print("  [OK] Esportazione di singola pagina in JPG e PNG diretto verificata con successo.")

    def test_03_batch_images_export(self):
        """Test esportazione in blocco (batch) di più documenti in JPG e PNG"""
        zip_bytes, fname, mime = export_batch_images([self.doc_id], img_format="jpg")
        self.assertEqual(mime, "application/zip")
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        self.assertGreaterEqual(len(zf.namelist()), 2)
        print(f"  [OK] Esportazione batch immagini ({fname}) verificata con successo.")

    def test_04_api_endpoints_export(self):
        """Test endpoint REST API per esportazione JPG e PNG"""
        # GET /api/documents/<id>/export?format=jpg
        res_jpg = self.client.get(f'/api/documents/{self.doc_id}/export?format=jpg')
        self.assertEqual(res_jpg.status_code, 200)

        # GET /api/documents/<id>/export?format=png&page=0 (singola pagina diretta)
        res_png = self.client.get(f'/api/documents/{self.doc_id}/export?format=png&page=0')
        self.assertEqual(res_png.status_code, 200)
        self.assertEqual(res_png.mimetype, 'image/png')

        # POST /api/batch/export-images
        res_batch = self.client.post('/api/batch/export-images', json={"doc_ids": [self.doc_id], "format": "png"})
        self.assertEqual(res_batch.status_code, 200)
        self.assertEqual(res_batch.mimetype, 'application/zip')
        print("  [OK] Tutte le API di esportazione multiformato (JPG, PNG) verificate con successo.")

    def test_05_progress_bar_elements_in_html(self):
        """Verifica presenza degli elementi per la barra di avanzamento importazione ed esportazione nel DOM"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"importProgressModal", res.data)
        self.assertIn(b"importProgressBar", res.data)
        self.assertIn(b"importProgressPercent", res.data)
        self.assertIn(b"batchExportProgressModal", res.data)
        self.assertIn(b"batchExportProgressBar", res.data)
        self.assertIn(b"batchExportProgressCount", res.data)
        self.assertIn(b"batchExportProgressPercent", res.data)
        self.assertIn(b"exportModal", res.data)
        self.assertIn(b"exportFormatSelect", res.data)
        print("  [OK] Presenza degli elementi HTML della barra di avanzamento import/export e modale verificata.")

    def test_06_async_batch_export_job(self):
        """Test ciclo completo job asincrono di esportazione in blocco con tracciamento progressione"""
        import time

        # 1. Avvio Job di esportazione PDF
        res = self.client.post('/api/batch/export-job', json={"type": "pdf", "doc_ids": [self.doc_id]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("job_id", data)
        job_id = data["job_id"]

        # 2. Polling progressione fino a completamento
        completed = False
        for _ in range(50):
            status_res = self.client.get(f'/api/batch/export-job/{job_id}')
            self.assertEqual(status_res.status_code, 200)
            status_data = status_res.get_json()
            if status_data["status"] == "completed":
                self.assertEqual(status_data["percent"], 100)
                self.assertGreaterEqual(status_data["total"], 2)
                completed = True
                break
            time.sleep(0.05)

        self.assertTrue(completed, "Il job di esportazione PDF asincrono non è stato completato nei tempi previsti")

        # 3. Download del risultato
        dl_res = self.client.get(f'/api/batch/export-job/{job_id}/download')
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.mimetype, 'application/pdf')
        self.assertGreater(len(dl_res.data), 1000)
        print("  [OK] Job asincrono di esportazione PDF con barra di progressione e download verificato con successo.")

    def test_07_async_batch_export_job_images(self):
        """Test job asincrono di esportazione immagini ZIP con callback di progressione"""
        import time

        res = self.client.post('/api/batch/export-job', json={"type": "jpg", "doc_ids": [self.doc_id]})
        self.assertEqual(res.status_code, 200)
        job_id = res.get_json()["job_id"]

        completed = False
        for _ in range(50):
            status_res = self.client.get(f'/api/batch/export-job/{job_id}')
            self.assertEqual(status_res.status_code, 200)
            status_data = status_res.get_json()
            if status_data["status"] == "completed":
                self.assertEqual(status_data["percent"], 100)
                completed = True
                break
            time.sleep(0.05)

        self.assertTrue(completed, "Il job di esportazione immagini JPG asincrono non è stato completato nei tempi previsti")

        dl_res = self.client.get(f'/api/batch/export-job/{job_id}/download')
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.mimetype, 'application/zip')
        self.assertGreater(len(dl_res.data), 1000)
        print("  [OK] Job asincrono di esportazione JPG (ZIP) con barra di progressione verificato con successo.")

if __name__ == "__main__":
    unittest.main()
