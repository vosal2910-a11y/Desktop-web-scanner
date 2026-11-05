import os
import io
import gc
import zipfile
from PIL import Image
import pypdf
from pypdf import PdfWriter, PdfReader
from core.doc_manager import get_document, get_doc_dir

# Dimensioni punti standard a 72 DPI (formati tipici)
PAGE_SIZES = {
    "A4": (595, 842),
    "Letter": (612, 792)
}

# Impostazioni DPI ottimizzate per economia risorse e rendering nitido
DPI_SETTINGS = {
    "high": 180,
    "medium": 140,
    "low": 96
}

QUALITY_SETTINGS = {
    "high": 88,
    "medium": 76,
    "low": 60
}

def export_document_pdf(doc_id, output_path=None, page_size="A4", quality="high", password=None, page_index=None):
    """
    Genera un file PDF multipagina per il documento in modalità a basso consumo di memoria (O(1) RAM):
    elabora una singola pagina per volta e la aggiunge incrementalmente a PdfWriter,
    senza mantenere tutti i bitmap non compressi contemporaneamente in RAM.
    """
    meta = get_document(doc_id)
    if not meta:
        raise ValueError(f"Documento {doc_id} non trovato")

    pages = meta.get("pages", [])
    if not pages:
        raise ValueError("Il documento non contiene pagine da esportare")

    if page_index is not None and 0 <= page_index < len(pages):
        pages = [pages[page_index]]

    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    jpeg_quality = QUALITY_SETTINGS.get(quality, 85)
    target_dpi = DPI_SETTINGS.get(quality, 180)

    writer = PdfWriter()
    pages_added = 0

    for page in pages:
        img_file = page.get("processed_file") or page.get("original_file")
        if not img_file:
            continue
        img_path = os.path.join(doc_dir, img_file)
        if not os.path.exists(img_path):
            continue

        with Image.open(img_path) as im:
            rgb_im = im.convert("RGB")

            # Ridimensionamento e centratura su pagina bianca A4 / Letter se specificato
            if page_size in PAGE_SIZES:
                target_w_pt, target_h_pt = PAGE_SIZES[page_size]
                target_w_px = int(target_w_pt * (target_dpi / 72.0))
                target_h_px = int(target_h_pt * (target_dpi / 72.0))

                rgb_im.thumbnail((target_w_px, target_h_px), Image.Resampling.LANCZOS)
                bg = Image.new("RGB", (target_w_px, target_h_px), (255, 255, 255))
                offset_x = (target_w_px - rgb_im.width) // 2
                offset_y = (target_h_px - rgb_im.height) // 2
                bg.paste(rgb_im, (offset_x, offset_y))
                page_img = bg
            else:
                page_img = rgb_im

            # Salva la singola pagina in un buffer PDF compatto
            page_buf = io.BytesIO()
            page_img.save(
                page_buf,
                format="PDF",
                quality=jpeg_quality,
                resolution=float(target_dpi)
            )
            page_buf.seek(0)
            writer.append(page_buf)
            pages_added += 1

            # Rilascia immediatamente il bitmap dalla memoria
            del rgb_im
            if page_size in PAGE_SIZES:
                del bg

    if pages_added == 0:
        raise ValueError("Nessuna immagine valida trovata per generare il PDF")

    # Crittografia con password opzionale
    if password and str(password).strip():
        writer.encrypt(str(password).strip())

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)
        gc.collect()
        return output_path

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    pdf_bytes = out_buf.getvalue()
    gc.collect()
    return pdf_bytes


def export_batch_pdf(doc_ids, output_path=None, page_size="A4", quality="high", password=None, progress_callback=None):
    """
    Unisce più documenti selezionati in un unico file PDF master con progressione dinamica.
    Flusso incrementale a memoria costante per prevenire OOM su Render.
    """
    total_pages = 0
    valid_metas = []
    for did in doc_ids:
        meta = get_document(did)
        if meta and meta.get("pages"):
            total_pages += len(meta["pages"])
            valid_metas.append(meta)

    total_pages = max(total_pages, 1)
    current_page = 0
    writer = PdfWriter()

    jpeg_quality = QUALITY_SETTINGS.get(quality, 85)
    target_dpi = DPI_SETTINGS.get(quality, 180)

    for meta in valid_metas:
        did = meta["id"]
        doc_title = meta.get("title", did)
        doc_dir = get_doc_dir(did, in_trash=meta.get("in_trash", False))

        for idx, page in enumerate(meta.get("pages", [])):
            current_page += 1
            if progress_callback:
                progress_callback(current_page, total_pages, f"Aggiunta al PDF: {doc_title} (pag. {current_page}/{total_pages})")

            img_file = page.get("processed_file") or page.get("original_file")
            if not img_file:
                continue
            img_path = os.path.join(doc_dir, img_file)
            if not os.path.exists(img_path):
                continue

            try:
                with Image.open(img_path) as im:
                    rgb_im = im.convert("RGB")
                    if page_size in PAGE_SIZES:
                        target_w_pt, target_h_pt = PAGE_SIZES[page_size]
                        target_w_px = int(target_w_pt * (target_dpi / 72.0))
                        target_h_px = int(target_h_pt * (target_dpi / 72.0))
                        rgb_im.thumbnail((target_w_px, target_h_px), Image.Resampling.LANCZOS)
                        bg = Image.new("RGB", (target_w_px, target_h_px), (255, 255, 255))
                        offset_x = (target_w_px - rgb_im.width) // 2
                        offset_y = (target_h_px - rgb_im.height) // 2
                        bg.paste(rgb_im, (offset_x, offset_y))
                        page_img = bg
                    else:
                        page_img = rgb_im

                    page_buf = io.BytesIO()
                    page_img.save(page_buf, format="PDF", quality=jpeg_quality, resolution=float(target_dpi))
                    page_buf.seek(0)
                    writer.append(page_buf)

                    del rgb_im
                    if page_size in PAGE_SIZES:
                        del bg
            except Exception as e:
                print(f"Avviso: errore pagina {idx + 1} di {did}: {e}")

        gc.collect()

    if len(writer.pages) == 0:
        raise ValueError("Nessuna pagina valida trovata nei documenti selezionati")

    if password and str(password).strip():
        writer.encrypt(str(password).strip())

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)
        gc.collect()
        return output_path

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    pdf_bytes = out_buf.getvalue()
    gc.collect()
    return pdf_bytes


def export_batch_zip(doc_ids, output_path=None, progress_callback=None):
    """
    Esporta i documenti selezionati in un archivio ZIP contenente
    i singoli file PDF e le immagini con streaming diretto da disco (zero overhead di conversione).
    """
    total_docs = max(len(doc_ids), 1)
    current_doc = 0

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        zf_target = output_path
    else:
        zf_target = io.BytesIO()

    with zipfile.ZipFile(zf_target, "w", zipfile.ZIP_DEFLATED) as zf:
        for did in doc_ids:
            current_doc += 1
            meta = get_document(did)
            if not meta:
                continue

            doc_title = meta.get("title", did).replace(" ", "_").replace("/", "_").replace("\\", "_")
            doc_dir = get_doc_dir(did, in_trash=meta.get("in_trash", False))

            if progress_callback:
                progress_callback(current_doc, total_docs, f"Compressione ZIP: {doc_title} ({current_doc}/{total_docs})")

            # 1. Genera e aggiunge il PDF del documento
            try:
                pdf_data = export_document_pdf(did, quality="high")
                zf.writestr(f"{doc_title}/{doc_title}.pdf", pdf_data)
            except Exception:
                pass

            # 2. Aggiunge le immagini elaborate direttamente da file (zero consumo CPU/RAM)
            for idx, p in enumerate(meta.get("pages", [])):
                proc_file = p.get("processed_file") or p.get("original_file")
                if proc_file:
                    fpath = os.path.join(doc_dir, proc_file)
                    if os.path.exists(fpath):
                        ext = os.path.splitext(proc_file)[1].lower() or ".jpg"
                        zf.write(fpath, arcname=f"{doc_title}/pagina_{idx + 1:02d}{ext}")

    gc.collect()
    if output_path:
        return output_path

    zf_target.seek(0)
    return zf_target.getvalue()


def export_document_images(doc_id, img_format="jpg", quality="high", page_index=None):
    """
    Esporta il documento in formato immagine (JPG o PNG).
    Per JPG sfrutta i file già presenti su disco senza rielaborazione non necessaria.
    """
    meta = get_document(doc_id)
    if not meta:
        raise ValueError(f"Documento {doc_id} non trovato")

    pages = meta.get("pages", [])
    if not pages:
        raise ValueError("Nessuna pagina presente nel documento")

    fmt = img_format.lower().strip()
    if fmt not in ("jpg", "jpeg", "png"):
        fmt = "jpg"

    ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
    mimetype = "image/jpeg" if ext == "jpg" else "image/png"
    jpeg_quality = QUALITY_SETTINGS.get(quality, 85)
    doc_title = meta.get("title", doc_id).replace(" ", "_").replace("/", "_").replace("\\", "_")
    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))

    # Esportazione singola pagina specifica
    if page_index is not None and 0 <= page_index < len(pages):
        page = pages[page_index]
        img_file = page.get("processed_file") or page.get("original_file")
        img_path = os.path.join(doc_dir, img_file)
        if ext == "jpg" and img_file.lower().endswith((".jpg", ".jpeg")):
            with open(img_path, "rb") as f:
                return f.read(), f"{doc_title}_p{page_index + 1}.jpg", mimetype
        with Image.open(img_path) as im:
            buf = io.BytesIO()
            if ext == "jpg":
                im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
            else:
                im.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue(), f"{doc_title}_p{page_index + 1}.{ext}", mimetype

    # Se c'è solo una pagina
    if len(pages) == 1:
        page = pages[0]
        img_file = page.get("processed_file") or page.get("original_file")
        img_path = os.path.join(doc_dir, img_file)
        if ext == "jpg" and img_file.lower().endswith((".jpg", ".jpeg")):
            with open(img_path, "rb") as f:
                return f.read(), f"{doc_title}.jpg", mimetype
        with Image.open(img_path) as im:
            buf = io.BytesIO()
            if ext == "jpg":
                im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
            else:
                im.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue(), f"{doc_title}.{ext}", mimetype

    # Multipagina in ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, page in enumerate(pages):
            img_file = page.get("processed_file") or page.get("original_file")
            img_path = os.path.join(doc_dir, img_file)
            if not os.path.exists(img_path):
                continue
            if ext == "jpg" and img_file.lower().endswith((".jpg", ".jpeg")):
                zf.write(img_path, arcname=f"{doc_title}/pagina_{idx + 1:02d}.jpg")
            else:
                with Image.open(img_path) as im:
                    page_buf = io.BytesIO()
                    if ext == "jpg":
                        im.convert("RGB").save(page_buf, format="JPEG", quality=jpeg_quality)
                    else:
                        im.save(page_buf, format="PNG")
                    page_buf.seek(0)
                    zf.writestr(f"{doc_title}/pagina_{idx + 1:02d}.{ext}", page_buf.getvalue())

    gc.collect()
    zip_buf.seek(0)
    return zip_buf.getvalue(), f"{doc_title}_{ext.upper()}.zip", "application/zip"


def export_batch_images(doc_ids, img_format="jpg", quality="high", progress_callback=None):
    """
    Esporta i documenti selezionati in un archivio ZIP contenente le pagine JPG o PNG.
    Streaming diretto da disco per file JPG per zero overhead CPU/RAM.
    """
    fmt = img_format.lower().strip()
    ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
    jpeg_quality = QUALITY_SETTINGS.get(quality, 85)

    total_pages = 0
    valid_metas = []
    for did in doc_ids:
        meta = get_document(did)
        if meta and meta.get("pages"):
            total_pages += len(meta["pages"])
            valid_metas.append(meta)

    total_pages = max(total_pages, 1)
    current_page = 0

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for meta in valid_metas:
            did = meta["id"]
            doc_title = meta.get("title", did).replace(" ", "_").replace("/", "_").replace("\\", "_")
            doc_dir = get_doc_dir(did, in_trash=meta.get("in_trash", False))

            for idx, page in enumerate(meta.get("pages", [])):
                current_page += 1
                if progress_callback:
                    progress_callback(current_page, total_pages, f"Conversione {ext.upper()}: {doc_title} (pag. {idx + 1}/{len(meta['pages'])})")

                img_file = page.get("processed_file") or page.get("original_file")
                if not img_file:
                    continue
                img_path = os.path.join(doc_dir, img_file)
                if not os.path.exists(img_path):
                    continue

                if ext == "jpg" and img_file.lower().endswith((".jpg", ".jpeg")):
                    # Scrittura diretta a costo zero
                    zf.write(img_path, arcname=f"{doc_title}/pagina_{idx + 1:02d}.jpg")
                else:
                    with Image.open(img_path) as im:
                        buf = io.BytesIO()
                        if ext == "jpg":
                            im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
                        else:
                            im.save(buf, format="PNG")
                        buf.seek(0)
                        zf.writestr(f"{doc_title}/pagina_{idx + 1:02d}.{ext}", buf.getvalue())

    gc.collect()
    zip_buf.seek(0)
    return zip_buf.getvalue(), f"documenti_selezionati_{ext.upper()}.zip", "application/zip"
