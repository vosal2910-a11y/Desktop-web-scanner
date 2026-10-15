import os
import sys
import unittest
import numpy as np
import cv2
import zipfile
import pypdf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.doc_manager import (
    create_block,
    list_blocks,
    delete_block,
    create_document,
    get_document,
    add_page_to_document,
    delete_permanently,
    batch_move_documents,
    batch_apply_enhancements,
    list_documents
)
from core.pdf_exporter import export_batch_pdf, export_batch_zip

class TestCycle2BlocksAndBulk(unittest.TestCase):
    def setUp(self):
        # Crea un blocco di test
        self.block = create_block("Test Blocco Lotto 2026", color="#10b981", description="Blocco per test di massa")
        self.doc_ids = []

        # Crea un'immagine sintetica per le pagine
        self.dummy_page = np.ones((600, 450, 3), dtype=np.uint8) * 240
        cv2.putText(self.dummy_page, "PAGINA TEST", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

        # Crea 3 documenti con 2 pagine ciascuno assegnati al blocco
        for i in range(3):
            doc = create_document(title=f"Doc Lotto {i+1}", block_id=self.block["id"])
            did = doc["id"]
            self.doc_ids.append(did)
            add_page_to_document(did, self.dummy_page, auto_crop=False, filter_type="normal")
            add_page_to_document(did, self.dummy_page, auto_crop=False, filter_type="normal")

    def tearDown(self):
        # Pulizia documenti di test
        for did in self.doc_ids:
            delete_permanently(did)
        if hasattr(self, 'block') and self.block:
            delete_block(self.block["id"])

    def test_01_block_creation_and_filtering(self):
        """Verifica la creazione dei blocchi e il filtraggio documenti"""
        blocks = list_blocks()
        self.assertTrue(any(b["id"] == self.block["id"] for b in blocks))

        # Filtra documenti per questo blocco
        docs_in_block = list_documents(block_id=self.block["id"])
        self.assertEqual(len(docs_in_block), 3, "Il blocco deve contenere esattamente i 3 documenti creati")
        print(f"  [OK] Blocco creato e verificato: {self.block['name']} con {len(docs_in_block)} documenti")

    def test_02_bulk_enhancements_application(self):
        """Verifica applicazione in blocco (batch) dei filtri e rotazioni a tutti i documenti selezionati"""
        # Applica a tutti i 3 documenti selezionati: filtro magic_color, brightness=12, contrast=18, rotazione 90
        processed = batch_apply_enhancements(
            self.doc_ids,
            filter_type="magic_color",
            brightness=12,
            contrast=18,
            rotation_delta=90,
            auto_crop=False
        )
        self.assertEqual(len(processed), 3, "Tutti i 3 documenti devono essere stati processati")

        # Verifica che ogni pagina di ogni documento sia stata effettivamente aggiornata
        for did in self.doc_ids:
            doc = get_document(did)
            self.assertEqual(len(doc["pages"]), 2)
            for page in doc["pages"]:
                self.assertEqual(page["filter_type"], "magic_color", "Il filtro deve essere 'magic_color'")
                self.assertEqual(page["brightness"], 12, "La luminosità deve essere 12")
                self.assertEqual(page["contrast"], 18, "Il contrasto deve essere 18")
                self.assertEqual(page["rotation"], 90, "La rotazione deve essere 90 gradi")
        print("  [OK] Miglioramenti in blocco applicati con successo a tutte le 6 pagine dei 3 documenti.")

    def test_03_batch_move_documents(self):
        """Verifica lo spostamento in massa dei documenti tra blocchi"""
        new_block = create_block("Blocco Spostati", color="#f59e0b")
        moved = batch_move_documents(self.doc_ids[:2], new_block["id"])
        self.assertEqual(len(moved), 2)

        doc0 = get_document(self.doc_ids[0])
        doc1 = get_document(self.doc_ids[1])
        doc2 = get_document(self.doc_ids[2])

        self.assertEqual(doc0["block_id"], new_block["id"])
        self.assertEqual(doc1["block_id"], new_block["id"])
        self.assertEqual(doc2["block_id"], self.block["id"])

        delete_block(new_block["id"])
        print("  [OK] Spostamento in massa di documenti tra blocchi verificato con successo.")

    def test_04_batch_export_pdf_and_zip(self):
        """Verifica esportazione cumulativa in PDF unificato e archivio ZIP"""
        # 1. Esportazione PDF unificato (3 doc x 2 pagine = 6 pagine totali)
        pdf_bytes = export_batch_pdf(self.doc_ids, page_size="A4", quality="medium")
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 1000)

        # Analizza con pypdf
        import io
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        self.assertEqual(len(reader.pages), 6, "Il PDF unificato deve contenere esattamente 6 pagine")

        # 2. Esportazione ZIP
        zip_bytes = export_batch_zip(self.doc_ids)
        self.assertIsNotNone(zip_bytes)
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        file_list = zf.namelist()
        self.assertGreater(len(file_list), 5, "Lo ZIP deve contenere i PDF e le immagini elaborate dei documenti")
        print(f"  [OK] Esportazione unificata completata: PDF di 6 pagine e archivio ZIP con {len(file_list)} file.")

if __name__ == "__main__":
    unittest.main()
