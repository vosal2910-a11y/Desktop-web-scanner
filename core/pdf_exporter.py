import os
import io
import zipfile
from PIL import Image
import pypdf
from pypdf import PdfWriter, PdfReader
from core.doc_manager import get_document, get_doc_dir

# Dimensioni punti standard a 72 DPI
PAGE_SIZES = {
    "A4": (595, 842),
    "Letter": (612, 792)
}

QUALITY_SETTINGS = {
    "high": 92,
    "medium": 78,
    "low": 60
}

def export_document_pdf(doc_id, output_path=None, page_size="A4", quality="high", password=None, page_index=None):
    """
    Genera un file PDF multipagina per il documento indicato.
    - page_size: 'A4', 'Letter', 'Auto'
    - quality: 'high', 'medium', 'low'
    - password: stringa per crittografia password opzionale
    - page_index: indice singola pagina da esportare (opzionale)
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

    pil_images = []
    for page in pages:
        img_file = page.get("processed_file") or page.get("original_file")
        img_path = os.path.join(doc_dir, img_file)
        if not os.path.exists(img_path):
            continue

        with Image.open(img_path) as im:
            # Converti in RGB se necessario
            rgb_im = im.convert("RGB")

            # Ridimensiona in base al formato pagina richiesto
            if page_size in PAGE_SIZES:
                target_w_pt, target_h_pt = PAGE_SIZES[page_size]
                # Conversione a ~300 DPI per stampa definita
                target_w_px = int(target_w_pt * (300 / 72))
                target_h_px = int(target_h_pt * (300 / 72))

                # Adatta mantenendo le proporzioni
                rgb_im.thumbnail((target_w_px, target_h_px), Image.Resampling.LANCZOS)
                # Crea una pagina bianca con l'immagine centrata
                bg = Image.new("RGB", (target_w_px, target_h_px), (255, 255, 255))
                offset_x = (target_w_px - rgb_im.width) // 2
                offset_y = (target_h_px - rgb_im.height) // 2
                bg.paste(rgb_im, (offset_x, offset_y))
                pil_images.append(bg)
            else:
                # Modalità Auto (dimensione originale pagina)
                pil_images.append(rgb_im.copy())

    if not pil_images:
        raise ValueError("Nessuna immagine valida trovata per generare il PDF")

    # Genera PDF in memoria con Pillow
    pdf_buffer = io.BytesIO()
    first_page = pil_images[0]
    rest_pages = pil_images[1:] if len(pil_images) > 1 else []

    first_page.save(
        pdf_buffer,
        format="PDF",
        save_all=True,
        append_images=rest_pages,
        quality=jpeg_quality,
        resolution=300.0
    )
    pdf_buffer.seek(0)

    # Se è richiesta la crittografia con password, usa pypdf
    if password and password.strip():
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        writer.encrypt(password.strip())
        
        final_buffer = io.BytesIO()
        writer.write(final_buffer)
        final_buffer.seek(0)
        pdf_bytes = final_buffer.getvalue()
    else:
        pdf_bytes = pdf_buffer.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return output_path

    return pdf_bytes


def export_batch_pdf(doc_ids, output_path=None, page_size="A4", quality="high", password=None, progress_callback=None):
    """
    Unisce più documenti selezionati in un unico grande file PDF master.
    """
    writer = PdfWriter()

    total_pages = 0
    valid_metas = []
    for did in doc_ids:
        meta = get_document(did)
        if meta and meta.get("pages"):
            total_pages += len(meta["pages"])
            valid_metas.append(meta)

    total_pages = max(total_pages, 1)
    current_page = 0

    for meta in valid_metas:
        did = meta["id"]
        doc_title = meta.get("title", did)
        try:
            if progress_callback:
                progress_callback(current_page, total_pages, f"Elaborazione: {doc_title}")

            pdf_data = export_document_pdf(did, page_size=page_size, quality=quality, password=None)
            reader = PdfReader(io.BytesIO(pdf_data))
            for page in reader.pages:
                writer.add_page(page)
                current_page += 1
                if progress_callback:
                    progress_callback(current_page, total_pages, f"Aggiunta al PDF: {doc_title} (pag. {current_page}/{total_pages})")
        except Exception as e:
            print(f"Avviso: errore nell'esportazione documento {did}: {e}")

    if len(writer.pages) == 0:
        raise ValueError("Nessuna pagina valida trovata nei documenti selezionati")

    if password and password.strip():
        writer.encrypt(password.strip())

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    pdf_bytes = out_buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return output_path

    return pdf_bytes


def export_batch_zip(doc_ids, output_path=None, progress_callback=None):
    """
    Esporta i documenti selezionati in un archivio ZIP contenente
    i singoli file PDF e le immagini elaborate ad alta risoluzione.
    """
    total_docs = max(len(doc_ids), 1)
    current_doc = 0
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for did in doc_ids:
            current_doc += 1
            meta = get_document(did)
            if not meta:
                continue

            doc_title = meta.get("title", did).replace(" ", "_").replace("/", "_")
            doc_dir = get_doc_dir(did, in_trash=meta.get("in_trash", False))

            if progress_callback:
                progress_callback(current_doc, total_docs, f"Compressione ZIP: {doc_title} ({current_doc}/{total_docs})")

            # 1. Aggiungi il PDF del documento
            try:
                pdf_data = export_document_pdf(did, quality="high")
                zf.writestr(f"{doc_title}/{doc_title}.pdf", pdf_data)
            except Exception:
                pass

            # 2. Aggiungi le immagini elaborate
            for idx, p in enumerate(meta.get("pages", [])):
                proc_file = p.get("processed_file")
                if proc_file:
                    fpath = os.path.join(doc_dir, proc_file)
                    if os.path.exists(fpath):
                        zf.write(fpath, arcname=f"{doc_title}/pagina_{idx + 1}.jpg")

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(zip_bytes)
        return output_path

    return zip_bytes


def export_document_images(doc_id, img_format="jpg", quality="high", page_index=None):
    """
    Esporta il documento in formato immagine (JPG o PNG).
    - Se page_index è specificato o il doc ha 1 sola pagina: restituisce (bytes, filename, mimetype).
    - Se ha più pagine e page_index è None: restituisce un archivio ZIP contenente tutte le pagine (bytes, filename, 'application/zip').
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
    pil_fmt = "JPEG" if ext == "jpg" else "PNG"
    mimetype = "image/jpeg" if ext == "jpg" else "image/png"
    jpeg_quality = QUALITY_SETTINGS.get(quality, 85)
    doc_title = meta.get("title", doc_id).replace(" ", "_").replace("/", "_").replace("\\", "_")
    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))

    # Esportazione di una singola pagina specifica
    if page_index is not None and 0 <= page_index < len(pages):
        page = pages[page_index]
        img_file = page.get("processed_file") or page.get("original_file")
        img_path = os.path.join(doc_dir, img_file)
        with Image.open(img_path) as im:
            buf = io.BytesIO()
            if ext == "jpg":
                im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
            else:
                im.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue(), f"{doc_title}_p{page_index + 1}.{ext}", mimetype

    # Se c'è solo una pagina nel documento, esporta direttamente l'immagine
    if len(pages) == 1:
        page = pages[0]
        img_file = page.get("processed_file") or page.get("original_file")
        img_path = os.path.join(doc_dir, img_file)
        with Image.open(img_path) as im:
            buf = io.BytesIO()
            if ext == "jpg":
                im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
            else:
                im.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue(), f"{doc_title}.{ext}", mimetype

    # Documento multipagina: crea un archivio ZIP con tutte le immagini nominate
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, page in enumerate(pages):
            img_file = page.get("processed_file") or page.get("original_file")
            img_path = os.path.join(doc_dir, img_file)
            if not os.path.exists(img_path):
                continue
            with Image.open(img_path) as im:
                page_buf = io.BytesIO()
                if ext == "jpg":
                    im.convert("RGB").save(page_buf, format="JPEG", quality=jpeg_quality)
                else:
                    im.save(page_buf, format="PNG")
                page_buf.seek(0)
                zf.writestr(f"{doc_title}/pagina_{idx + 1:02d}.{ext}", page_buf.getvalue())

    zip_buf.seek(0)
    return zip_buf.getvalue(), f"{doc_title}_{ext.upper()}.zip", "application/zip"


def export_batch_images(doc_ids, img_format="jpg", quality="high", progress_callback=None):
    """
    Esporta i documenti selezionati in un archivio ZIP contenente le pagine convertite in JPG o PNG.
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
                img_path = os.path.join(doc_dir, img_file)
                if not os.path.exists(img_path):
                    continue
                with Image.open(img_path) as im:
                    buf = io.BytesIO()
                    if ext == "jpg":
                        im.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
                    else:
                        im.save(buf, format="PNG")
                    buf.seek(0)
                    zf.writestr(f"{doc_title}/pagina_{idx + 1:02d}.{ext}", buf.getvalue())

    zip_buf.seek(0)
    return zip_buf.getvalue(), f"documenti_selezionati_{ext.upper()}.zip", "application/zip"

