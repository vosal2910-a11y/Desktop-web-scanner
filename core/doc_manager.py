import os
import json
import uuid
import time
import shutil
import cv2
import numpy as np
from PIL import Image
from core.scanner_cv import (
    detect_document_corners,
    warp_perspective,
    apply_color_enhancements,
    rotate_image,
    detect_barcodes_and_qrcodes
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
TRASH_DIR = os.path.join(DATA_DIR, "trash")
BLOCKS_FILE = os.path.join(DATA_DIR, "blocks.json")

def ensure_directories():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(TRASH_DIR, exist_ok=True)
    if not os.path.exists(BLOCKS_FILE):
        default_blocks = [
            {"id": "general", "name": "Generale", "color": "#3b82f6", "created_at": time.time(), "description": "Documenti generici"},
            {"id": "invoices", "name": "Fatture & Ricevute", "color": "#10b981", "created_at": time.time(), "description": "Spese fiscali e contabilità"},
            {"id": "ids", "name": "Documenti Identità", "color": "#8b5cf6", "created_at": time.time(), "description": "Carte d'identità, passaporti, patenti"}
        ]
        with open(BLOCKS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_blocks, f, indent=2, ensure_ascii=False)

ensure_directories()

# --- GESTIONE BLOCCHI ---

def list_blocks():
    ensure_directories()
    try:
        with open(BLOCKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_blocks(blocks):
    with open(BLOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)

def create_block(name, color="#3b82f6", description=""):
    blocks = list_blocks()
    block_id = "block_" + uuid.uuid4().hex[:8]
    new_block = {
        "id": block_id,
        "name": name.strip(),
        "color": color,
        "description": description.strip(),
        "created_at": time.time()
    }
    blocks.append(new_block)
    save_blocks(blocks)
    return new_block

def update_block(block_id, name=None, color=None, description=None):
    blocks = list_blocks()
    updated = None
    for b in blocks:
        if b["id"] == block_id:
            if name is not None:
                b["name"] = name.strip()
            if color is not None:
                b["color"] = color
            if description is not None:
                b["description"] = description.strip()
            updated = b
            break
    if updated:
        save_blocks(blocks)
    return updated

def delete_block(block_id):
    blocks = list_blocks()
    blocks = [b for b in blocks if b["id"] != block_id]
    save_blocks(blocks)
    # Aggiorna i documenti che appartenevano a questo blocco
    for doc in list_documents(include_trash=True):
        if doc.get("block_id") == block_id:
            update_document(doc["id"], block_id="general")
    return True


# --- GESTIONE DOCUMENTI ---

def get_doc_dir(doc_id, in_trash=False):
    root = TRASH_DIR if in_trash else DOCS_DIR
    return os.path.join(root, doc_id)

def get_document_meta_path(doc_id, in_trash=False):
    return os.path.join(get_doc_dir(doc_id, in_trash), "metadata.json")

def load_doc_meta(doc_id, in_trash=False):
    path = get_document_meta_path(doc_id, in_trash)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_doc_meta(doc_id, meta, in_trash=False):
    path = get_document_meta_path(doc_id, in_trash)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

def list_documents(block_id=None, include_trash=False, search=None, tag=None):
    ensure_directories()
    docs = []
    scan_dirs = [(DOCS_DIR, False)]
    if include_trash:
        scan_dirs.append((TRASH_DIR, True))

    for target_dir, is_trash in scan_dirs:
        if not os.path.exists(target_dir):
            continue
        for entry in os.listdir(target_dir):
            doc_folder = os.path.join(target_dir, entry)
            if not os.path.isdir(doc_folder):
                continue
            meta_path = os.path.join(doc_folder, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["in_trash"] = is_trash
                        docs.append(meta)
                except Exception:
                    pass

    # Filtri
    if not include_trash:
        docs = [d for d in docs if not d.get("in_trash", False)]
    if block_id and block_id != "all":
        docs = [d for d in docs if d.get("block_id") == block_id]
    if tag:
        docs = [d for d in docs if tag.lower() in [t.lower() for t in d.get("tags", [])]]
    if search:
        s = search.lower()
        docs = [d for d in docs if s in d.get("title", "").lower() or any(s in p.get("ocr_text", "").lower() for p in d.get("pages", []))]

    # Ordinamento per data di aggiornamento / creazione decrescente
    docs.sort(key=lambda d: d.get("updated_at", d.get("created_at", 0)), reverse=True)
    return docs

def create_document(title=None, block_id="general", tags=None):
    ensure_directories()
    doc_id = "doc_" + uuid.uuid4().hex[:12]
    now = time.time()
    if not title:
        title = "Scansione " + time.strftime("%Y-%m-%d %H:%M")

    meta = {
        "id": doc_id,
        "title": title.strip(),
        "block_id": block_id or "general",
        "tags": tags or [],
        "notes": "",
        "created_at": now,
        "updated_at": now,
        "pages": []
    }
    doc_folder = get_doc_dir(doc_id)
    os.makedirs(doc_folder, exist_ok=True)
    save_doc_meta(doc_id, meta)
    return meta

def get_document(doc_id):
    meta = load_doc_meta(doc_id, in_trash=False)
    if meta is None:
        meta = load_doc_meta(doc_id, in_trash=True)
        if meta:
            meta["in_trash"] = True
    else:
        meta["in_trash"] = False
    return meta

def update_document(doc_id, title=None, block_id=None, tags=None, notes=None):
    meta = get_document(doc_id)
    if not meta:
        return None
    in_trash = meta.get("in_trash", False)
    if title is not None:
        meta["title"] = title.strip()
    if block_id is not None:
        meta["block_id"] = block_id
    if tags is not None:
        meta["tags"] = tags
    if notes is not None:
        meta["notes"] = notes
    meta["updated_at"] = time.time()
    save_doc_meta(doc_id, meta, in_trash=in_trash)
    return meta

def move_to_trash(doc_id):
    src = get_doc_dir(doc_id, in_trash=False)
    dst = get_doc_dir(doc_id, in_trash=True)
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
        return True
    return False

def restore_from_trash(doc_id):
    src = get_doc_dir(doc_id, in_trash=True)
    dst = get_doc_dir(doc_id, in_trash=False)
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
        return True
    return False

def delete_permanently(doc_id):
    for in_trash in (False, True):
        path = get_doc_dir(doc_id, in_trash)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
    return False


# --- GESTIONE PAGINE ---

def add_page_to_document(doc_id, image_np_or_path, auto_crop=True, filter_type="magic_color"):
    """
    Aggiunge una nuova pagina al documento:
    1. Salva l'immagine originale
    2. Rileva i 4 angoli del documento
    3. Esegue warp prospettico e applica miglioramenti iniziali
    4. Genera miniatura (thumbnail)
    5. Cerca eventuali QR code / codici a barre
    """
    meta = get_document(doc_id)
    if not meta:
        raise ValueError(f"Documento {doc_id} non trovato")

    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    page_id = "page_" + uuid.uuid4().hex[:8]

    # Carica immagine
    if isinstance(image_np_or_path, str):
        img_orig = cv2.imread(image_np_or_path)
    else:
        img_orig = image_np_or_path

    if img_orig is None:
        raise ValueError("Impossibile decodificare l'immagine della pagina")

    h, w = img_orig.shape[:2]

    # Percorsi file
    orig_rel = f"{page_id}_orig.jpg"
    proc_rel = f"{page_id}_processed.jpg"
    thumb_rel = f"{page_id}_thumb.jpg"

    orig_path = os.path.join(doc_dir, orig_rel)
    proc_path = os.path.join(doc_dir, proc_rel)
    thumb_path = os.path.join(doc_dir, thumb_rel)

    # 1. Salva immagine originale ad alta fedeltà
    cv2.imwrite(orig_path, img_orig, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # 2. Rilevamento angoli del quad
    quad = detect_document_corners(img_orig)

    # 3. Se auto_crop è attivo, applica il warp
    if auto_crop and quad:
        warped = warp_perspective(img_orig, quad)
    else:
        warped = img_orig.copy()

    # 4. Applica miglioramento iniziale
    processed = apply_color_enhancements(warped, filter_type=filter_type)
    cv2.imwrite(proc_path, processed, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # 5. Genera thumbnail rapida (max 300px)
    thumb_scale = 300.0 / max(processed.shape[:2])
    thumb_w = int(processed.shape[1] * thumb_scale)
    thumb_h = int(processed.shape[0] * thumb_scale)
    thumb = cv2.resize(processed, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)
    cv2.imwrite(thumb_path, thumb, [cv2.IMWRITE_JPEG_QUALITY, 80])

    # 6. Rilevamento codici QR / Barcode
    qrcodes = detect_barcodes_and_qrcodes(processed)

    page_data = {
        "id": page_id,
        "width": w,
        "height": h,
        "quad": quad,
        "filter_type": filter_type,
        "brightness": 0,
        "contrast": 0,
        "rotation": 0,
        "bw_threshold": 128,
        "original_file": orig_rel,
        "processed_file": proc_rel,
        "thumb_file": thumb_rel,
        "ocr_text": "",
        "ocr_blocks": [],
        "qrcodes": qrcodes
    }

    meta["pages"].append(page_data)
    meta["updated_at"] = time.time()
    save_doc_meta(doc_id, meta, in_trash=meta.get("in_trash", False))

    return page_data

def process_page(doc_id, page_id, quad=None, filter_type=None, brightness=None, contrast=None, rotation=None, bw_threshold=None):
    """
    Rielabora la pagina partendo dall'immagine originale con i parametri aggiornati.
    """
    meta = get_document(doc_id)
    if not meta:
        raise ValueError(f"Documento {doc_id} non trovato")

    page = next((p for p in meta["pages"] if p["id"] == page_id), None)
    if not page:
        raise ValueError(f"Pagina {page_id} non trovata nel documento")

    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    orig_path = os.path.join(doc_dir, page["original_file"])
    proc_path = os.path.join(doc_dir, page["processed_file"])
    thumb_path = os.path.join(doc_dir, page["thumb_file"])

    img_orig = cv2.imread(orig_path)
    if img_orig is None:
        raise ValueError(f"Impossibile leggere l'immagine originale: {orig_path}")

    # Aggiorna impostazioni pagina
    if quad is not None:
        page["quad"] = quad
    if filter_type is not None:
        page["filter_type"] = filter_type
    if brightness is not None:
        page["brightness"] = int(brightness)
    if contrast is not None:
        page["contrast"] = int(contrast)
    if rotation is not None:
        page["rotation"] = int(rotation) % 360
    if bw_threshold is not None:
        page["bw_threshold"] = bw_threshold

    # Applica trasformazione prospettica
    if page.get("quad"):
        warped = warp_perspective(img_orig, page["quad"])
    else:
        warped = img_orig.copy()

    # Applica rotazione
    if page.get("rotation", 0) != 0:
        warped = rotate_image(warped, page["rotation"])

    # Applica filtri colore
    processed = apply_color_enhancements(
        warped,
        filter_type=page.get("filter_type", "magic_color"),
        brightness=page.get("brightness", 0),
        contrast=page.get("contrast", 0),
        bw_threshold=page.get("bw_threshold", 128)
    )

    # Salva immagine elaborata
    cv2.imwrite(proc_path, processed, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # Aggiorna miniatura
    thumb_scale = 300.0 / max(processed.shape[:2])
    thumb_w = int(processed.shape[1] * thumb_scale)
    thumb_h = int(processed.shape[0] * thumb_scale)
    thumb = cv2.resize(processed, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)
    cv2.imwrite(thumb_path, thumb, [cv2.IMWRITE_JPEG_QUALITY, 80])

    # Aggiorna QR codes
    page["qrcodes"] = detect_barcodes_and_qrcodes(processed)

    meta["updated_at"] = time.time()
    save_doc_meta(doc_id, meta, in_trash=meta.get("in_trash", False))

    return page

def reorder_pages(doc_id, new_page_id_list):
    meta = get_document(doc_id)
    if not meta:
        return None
    page_dict = {p["id"]: p for p in meta["pages"]}
    reordered = []
    for pid in new_page_id_list:
        if pid in page_dict:
            reordered.append(page_dict[pid])
    # Aggiungi eventuali pagine omesse alla fine
    for p in meta["pages"]:
        if p["id"] not in new_page_id_list:
            reordered.append(p)
    meta["pages"] = reordered
    meta["updated_at"] = time.time()
    save_doc_meta(doc_id, meta, in_trash=meta.get("in_trash", False))
    return meta

def delete_page(doc_id, page_id):
    meta = get_document(doc_id)
    if not meta:
        return None
    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    page = next((p for p in meta["pages"] if p["id"] == page_id), None)
    if page:
        for key in ("original_file", "processed_file", "thumb_file"):
            fpath = os.path.join(doc_dir, page.get(key, ""))
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
    meta["pages"] = [p for p in meta["pages"] if p["id"] != page_id]
    meta["updated_at"] = time.time()
    save_doc_meta(doc_id, meta, in_trash=meta.get("in_trash", False))
    return meta


# --- GESTIONE OPERAZIONI IN BLOCCO (BULK / BATCH) ---

def batch_move_documents(doc_ids, target_block_id):
    """
    Sposta una lista di documenti in un blocco specificato.
    """
    modified = []
    for did in doc_ids:
        res = update_document(did, block_id=target_block_id)
        if res:
            modified.append(did)
    return modified

def batch_apply_enhancements(doc_ids, filter_type=None, brightness=None, contrast=None, rotation_delta=0, auto_crop=False, bw_threshold=None):
    """
    Applica gli stessi miglioramenti a TUTTI i documenti/pagine specificati in blocco:
    - filter_type: 'magic_color', 'bw', 'grayscale', 'sepia', 'normal'
    - brightness: valore intero o None
    - contrast: valore intero o None
    - rotation_delta: 0, 90, 180, 270 (aggiunge rotazione alle pagine)
    - auto_crop: se True ricalcola automaticamente i 4 angoli dall'originale
    - bw_threshold: soglia B&W personalizzata
    """
    results = []
    for did in doc_ids:
        meta = get_document(did)
        if not meta or meta.get("in_trash"):
            continue

        doc_dir = get_doc_dir(did)
        for page in meta.get("pages", []):
            page_id = page["id"]

            # 1. Auto-crop se richiesto
            if auto_crop:
                orig_path = os.path.join(doc_dir, page["original_file"])
                img_orig = cv2.imread(orig_path)
                if img_orig is not None:
                    page["quad"] = detect_document_corners(img_orig)

            # 2. Rotazione
            if rotation_delta:
                cur_rot = page.get("rotation", 0)
                page["rotation"] = (cur_rot + int(rotation_delta)) % 360

            # 3. Parametri colore
            if filter_type is not None:
                page["filter_type"] = filter_type
            if brightness is not None:
                page["brightness"] = int(brightness)
            if contrast is not None:
                page["contrast"] = int(contrast)
            if bw_threshold is not None:
                page["bw_threshold"] = bw_threshold

            # Rielabora pagina
            process_page(
                did,
                page_id,
                quad=page.get("quad"),
                filter_type=page.get("filter_type"),
                brightness=page.get("brightness"),
                contrast=page.get("contrast"),
                rotation=page.get("rotation"),
                bw_threshold=page.get("bw_threshold")
            )

        results.append(did)
    return results

def batch_trash_documents(doc_ids):
    count = 0
    for did in doc_ids:
        if move_to_trash(did):
            count += 1
    return count

def batch_restore_documents(doc_ids):
    count = 0
    for did in doc_ids:
        if restore_from_trash(did):
            count += 1
    return count

def batch_delete_documents(doc_ids):
    count = 0
    for did in doc_ids:
        if delete_permanently(did):
            count += 1
    return count
