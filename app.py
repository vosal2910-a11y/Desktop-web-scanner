import os
import io
import time
import json
import base64
import threading
import uuid
import re
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

def safe_download_filename(title, ext="pdf"):
    if not title:
        title = "documento"
    clean = re.sub(r'[\\/*?:"<>|]', "_", str(title)).strip()
    clean = clean.strip(". ")
    if not clean:
        clean = "documento"
    return f"{clean}.{ext.lstrip('.')}"

from core.doc_manager import (
    list_documents,
    create_document,
    get_document,
    update_document,
    move_to_trash,
    restore_from_trash,
    delete_permanently,
    add_page_to_document,
    process_page,
    reorder_pages,
    delete_page,
    list_blocks,
    create_block,
    update_block,
    delete_block,
    batch_move_documents,
    batch_apply_enhancements,
    batch_trash_documents,
    batch_restore_documents,
    batch_delete_documents,
    get_doc_dir
)
from core.pdf_exporter import (
    export_document_pdf,
    export_batch_pdf,
    export_batch_zip,
    export_document_images,
    export_batch_images
)
from core.ocr_engine import run_ocr_on_image
from core.scanner_cv import detect_document_corners

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB max upload

# --- SERVIZIO FILE STATICI E PAGINA PRINCIPALE ---

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/files/<doc_id>/<filename>')
def serve_doc_file(doc_id, filename):
    safe_doc = secure_filename(doc_id)
    safe_file = secure_filename(filename)
    # Cerca prima nei documenti attivi, poi nel cestino
    doc_dir = get_doc_dir(safe_doc, in_trash=False)
    if not os.path.exists(os.path.join(doc_dir, safe_file)):
        doc_dir = get_doc_dir(safe_doc, in_trash=True)
    return send_from_directory(doc_dir, safe_file)


# --- API BLOCCHI DI DOCUMENTI ---

@app.route('/api/blocks', methods=['GET'])
def api_list_blocks():
    return jsonify(list_blocks())

@app.route('/api/blocks', methods=['POST'])
def api_create_block():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Il nome del blocco è obbligatorio"}), 400
    color = data.get("color", "#3b82f6")
    description = data.get("description", "")
    new_block = create_block(name, color, description)
    return jsonify(new_block), 201

@app.route('/api/blocks/<block_id>', methods=['PUT'])
def api_update_block(block_id):
    data = request.json or {}
    updated = update_block(
        block_id,
        name=data.get("name"),
        color=data.get("color"),
        description=data.get("description")
    )
    if not updated:
        return jsonify({"error": "Blocco non trovato"}), 404
    return jsonify(updated)

@app.route('/api/blocks/<block_id>', methods=['DELETE'])
def api_delete_block(block_id):
    if block_id == "general":
        return jsonify({"error": "Impossibile eliminare il blocco Generale predefinito"}), 400
    delete_block(block_id)
    return jsonify({"success": True})


# --- API DOCUMENTI ---

@app.route('/api/documents', methods=['GET'])
def api_list_documents():
    block_id = request.args.get('block_id')
    include_trash = request.args.get('trash', 'false').lower() == 'true'
    search = request.args.get('search')
    tag = request.args.get('tag')
    docs = list_documents(block_id=block_id, include_trash=include_trash, search=search, tag=tag)
    return jsonify(docs)

@app.route('/api/documents', methods=['POST'])
def api_create_document():
    data = request.json or {}
    title = data.get("title")
    block_id = data.get("block_id", "general")
    tags = data.get("tags", [])
    doc = create_document(title=title, block_id=block_id, tags=tags)
    return jsonify(doc), 201

@app.route('/api/documents/<doc_id>', methods=['GET'])
def api_get_document(doc_id):
    doc = get_document(doc_id)
    if not doc:
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(doc)

@app.route('/api/documents/<doc_id>', methods=['PUT'])
def api_update_document(doc_id):
    data = request.json or {}
    updated = update_document(
        doc_id,
        title=data.get("title"),
        block_id=data.get("block_id"),
        tags=data.get("tags"),
        notes=data.get("notes")
    )
    if not updated:
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(updated)

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def api_trash_document(doc_id):
    success = move_to_trash(doc_id)
    if not success:
        return jsonify({"error": "Impossibile spostare nel cestino"}), 404
    return jsonify({"success": True})

@app.route('/api/documents/<doc_id>/restore', methods=['POST'])
def api_restore_document(doc_id):
    success = restore_from_trash(doc_id)
    if not success:
        return jsonify({"error": "Impossibile ripristinare il documento"}), 404
    return jsonify({"success": True})

@app.route('/api/documents/<doc_id>/permanent', methods=['DELETE'])
def api_permanent_delete_document(doc_id):
    success = delete_permanently(doc_id)
    if not success:
        return jsonify({"error": "Impossibile eliminare definitivamente"}), 404
    return jsonify({"success": True})


# --- API PAGINE ---

@app.route('/api/documents/<doc_id>/pages', methods=['POST'])
def api_add_page(doc_id):
    auto_crop = request.form.get("auto_crop", "true").lower() == "true"
    filter_type = request.form.get("filter_type", "magic_color")

    # Verifica file allegato (multipart form)
    if 'image' in request.files:
        file = request.files['image']
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Oppure payload JSON con stringa base64
    elif request.is_json and 'image_base64' in request.json:
        b64_data = request.json['image_base64']
        if ',' in b64_data:
            b64_data = b64_data.split(',')[1]
        img_bytes = base64.b64decode(b64_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        auto_crop = request.json.get("auto_crop", True)
        filter_type = request.json.get("filter_type", "magic_color")
    else:
        return jsonify({"error": "Nessuna immagine fornita"}), 400

    if img_np is None:
        return jsonify({"error": "Decodifica immagine fallita"}), 400

    try:
        page = add_page_to_document(doc_id, img_np, auto_crop=auto_crop, filter_type=filter_type)
        return jsonify(page), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<doc_id>/pages/<page_id>/process', methods=['POST'])
def api_process_page(doc_id, page_id):
    data = request.json or {}
    try:
        page = process_page(
            doc_id,
            page_id,
            quad=data.get("quad"),
            filter_type=data.get("filter_type"),
            brightness=data.get("brightness"),
            contrast=data.get("contrast"),
            rotation=data.get("rotation"),
            bw_threshold=data.get("bw_threshold")
        )
        return jsonify(page)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<doc_id>/pages/<page_id>/detect-corners', methods=['POST'])
def api_detect_page_corners(doc_id, page_id):
    meta = get_document(doc_id)
    if not meta:
        return jsonify({"error": "Documento non trovato"}), 404
    page = next((p for p in meta["pages"] if p["id"] == page_id), None)
    if not page:
        return jsonify({"error": "Pagina non trovata"}), 404

    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    orig_path = os.path.join(doc_dir, page["original_file"])
    try:
        quad = detect_document_corners(orig_path)
        return jsonify({"quad": quad})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<doc_id>/pages/<page_id>/ocr', methods=['POST'])
def api_run_page_ocr(doc_id, page_id):
    meta = get_document(doc_id)
    if not meta:
        return jsonify({"error": "Documento non trovato"}), 404
    page = next((p for p in meta["pages"] if p["id"] == page_id), None)
    if not page:
        return jsonify({"error": "Pagina non trovata"}), 404

    data = request.json or {}
    lang = data.get("lang", "ita+eng")

    doc_dir = get_doc_dir(doc_id, in_trash=meta.get("in_trash", False))
    proc_path = os.path.join(doc_dir, page["processed_file"])

    try:
        from core.ocr_engine import run_ocr_on_image
        rec_result = run_ocr_on_image(proc_path, lang=lang)
        page["ocr_text"] = rec_result.get("text", "")
        page["ocr_blocks"] = rec_result.get("blocks", [])
        from core.doc_manager import save_doc_meta
        save_doc_meta(doc_id, meta, in_trash=meta.get("in_trash", False))
        return jsonify(rec_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/recognition-capabilities', methods=['GET'])
def api_get_recognition_capabilities():
    from core.ocr_engine import is_pytesseract_available

    return jsonify({
        "ocr": {
            "available": is_pytesseract_available(),
            "engine": "Tesseract OCR v5.4.0",
            "languages": ["ita", "eng"]
        }
    })

@app.route('/api/documents/<doc_id>/reorder', methods=['POST'])
def api_reorder_pages(doc_id):
    data = request.json or {}
    new_order = data.get("page_ids", [])
    updated = reorder_pages(doc_id, new_order)
    if not updated:
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(updated)

@app.route('/api/documents/<doc_id>/pages/<page_id>', methods=['DELETE'])
def api_delete_page(doc_id, page_id):
    updated = delete_page(doc_id, page_id)
    if not updated:
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(updated)


# --- API OPERAZIONI IN BLOCCO (BATCH / BULK) ---

@app.route('/api/batch/move', methods=['POST'])
def api_batch_move():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    target_block_id = data.get("target_block_id")
    if not doc_ids or not target_block_id:
        return jsonify({"error": "doc_ids e target_block_id sono obbligatori"}), 400
    modified = batch_move_documents(doc_ids, target_block_id)
    return jsonify({"modified_count": len(modified), "doc_ids": modified})

@app.route('/api/batch/apply', methods=['POST'])
def api_batch_apply_enhancements():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    if not doc_ids:
        return jsonify({"error": "Nessun documento selezionato"}), 400

    filter_type = data.get("filter_type")
    brightness = data.get("brightness")
    contrast = data.get("contrast")
    rotation_delta = data.get("rotation_delta", 0)
    auto_crop = data.get("auto_crop", False)
    bw_threshold = data.get("bw_threshold")

    results = batch_apply_enhancements(
        doc_ids,
        filter_type=filter_type,
        brightness=brightness,
        contrast=contrast,
        rotation_delta=rotation_delta,
        auto_crop=auto_crop,
        bw_threshold=bw_threshold
    )
    return jsonify({"success": True, "processed_count": len(results)})

@app.route('/api/batch/trash', methods=['POST'])
def api_batch_trash():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    count = batch_trash_documents(doc_ids)
    return jsonify({"trashed_count": count})

@app.route('/api/batch/restore', methods=['POST'])
def api_batch_restore():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    count = batch_restore_documents(doc_ids)
    return jsonify({"restored_count": count})

@app.route('/api/batch/delete', methods=['POST'])
def api_batch_delete():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    count = batch_delete_documents(doc_ids)
    return jsonify({"deleted_count": count})


# --- API ESPORTAZIONE PDF E ZIP ---

@app.route('/documents/<doc_id>/pdf', methods=['GET'])
@app.route('/api/documents/<doc_id>/pdf', methods=['GET'])
def api_export_document_pdf(doc_id):
    return api_export_document(doc_id)

@app.route('/api/batch/export-pdf', methods=['POST'])
@app.route('/batch/export-pdf', methods=['POST'])
def api_export_batch_pdf():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    page_size = data.get("page_size", "A4")
    quality = data.get("quality", "high")
    password = data.get("password")

    if not doc_ids:
        return jsonify({"error": "Nessun documento specificato"}), 400

    try:
        pdf_bytes = export_batch_pdf(doc_ids, page_size=page_size, quality=quality, password=password)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="raccolta_documenti_scansionati.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documents/<doc_id>/export', methods=['GET'])
@app.route('/api/documents/<doc_id>/export', methods=['GET'])
def api_export_document(doc_id):
    export_format = request.args.get("format", "pdf").lower().strip()
    page_size = request.args.get("page_size", "A4")
    quality = request.args.get("quality", "high")
    password = request.args.get("password")
    page_str = request.args.get("page")
    page_index = int(page_str) if page_str is not None and page_str.isdigit() else None

    try:
        if export_format in ("jpg", "jpeg", "png"):
            file_bytes, filename, mimetype = export_document_images(
                doc_id,
                img_format=export_format,
                quality=quality,
                page_index=page_index
            )
            return send_file(
                io.BytesIO(file_bytes),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        else:
            # Formato PDF predefinito
            pdf_bytes = export_document_pdf(
                doc_id,
                page_size=page_size,
                quality=quality,
                password=password,
                page_index=page_index
            )
            meta = get_document(doc_id)
            doc_title = meta.get("title", "documento") if meta else "documento"
            filename = safe_download_filename(doc_title, "pdf")
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch/export-images', methods=['POST'])
def api_export_batch_images():
    data = request.json or {}
    doc_ids = data.get("doc_ids", [])
    img_format = data.get("format", "jpg")
    quality = data.get("quality", "high")

    if not doc_ids:
        return jsonify({"error": "Nessun documento specificato"}), 400

    try:
        zip_bytes, filename, mimetype = export_batch_images(doc_ids, img_format=img_format, quality=quality)
        return send_file(
            io.BytesIO(zip_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

EXPORT_JOBS = {}

@app.route('/batch/export-job', methods=['POST'])
@app.route('/api/batch/export-job', methods=['POST'])
def api_create_export_job():
    data = request.json or {}
    job_type = data.get("type", "pdf").lower()  # "pdf", "jpg", "png", "zip"
    doc_ids = data.get("doc_ids", [])
    page_size = data.get("page_size", "A4")
    quality = data.get("quality", "high")
    password = data.get("password")

    if not doc_ids:
        return jsonify({"error": "Nessun documento specificato"}), 400

    job_id = "job_" + uuid.uuid4().hex[:10]
    EXPORT_JOBS[job_id] = {
        "status": "processing",
        "current": 0,
        "total": 1,
        "percent": 0,
        "message": "Inizializzazione esportazione...",
        "result_bytes": None,
        "filename": "esportazione",
        "mimetype": "application/octet-stream",
        "error": None
    }

    def run_job():
        try:
            def on_progress(cur, tot, msg):
                if job_id in EXPORT_JOBS:
                    EXPORT_JOBS[job_id]["current"] = cur
                    EXPORT_JOBS[job_id]["total"] = tot
                    EXPORT_JOBS[job_id]["percent"] = int((cur / max(tot, 1)) * 100)
                    EXPORT_JOBS[job_id]["message"] = msg

            if job_type == "pdf":
                pdf_bytes = export_batch_pdf(
                    doc_ids,
                    page_size=page_size,
                    quality=quality,
                    password=password,
                    progress_callback=on_progress
                )
                EXPORT_JOBS[job_id]["result_bytes"] = pdf_bytes
                EXPORT_JOBS[job_id]["filename"] = "raccolta_documenti_scansionati.pdf"
                EXPORT_JOBS[job_id]["mimetype"] = "application/pdf"

            elif job_type in ("jpg", "jpeg", "png"):
                zip_bytes, fname, mime = export_batch_images(
                    doc_ids,
                    img_format=job_type,
                    quality=quality,
                    progress_callback=on_progress
                )
                EXPORT_JOBS[job_id]["result_bytes"] = zip_bytes
                EXPORT_JOBS[job_id]["filename"] = fname
                EXPORT_JOBS[job_id]["mimetype"] = mime

            elif job_type == "zip":
                zip_bytes = export_batch_zip(
                    doc_ids,
                    progress_callback=on_progress
                )
                EXPORT_JOBS[job_id]["result_bytes"] = zip_bytes
                EXPORT_JOBS[job_id]["filename"] = "documenti_scansionati.zip"
                EXPORT_JOBS[job_id]["mimetype"] = "application/zip"

            EXPORT_JOBS[job_id]["percent"] = 100
            EXPORT_JOBS[job_id]["status"] = "completed"
            EXPORT_JOBS[job_id]["message"] = "Esportazione completata!"
        except Exception as e:
            if job_id in EXPORT_JOBS:
                EXPORT_JOBS[job_id]["status"] = "error"
                EXPORT_JOBS[job_id]["error"] = str(e)

    threading.Thread(target=run_job, daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route('/batch/export-job/<job_id>', methods=['GET'])
@app.route('/api/batch/export-job/<job_id>', methods=['GET'])
def api_get_export_job_status(job_id):
    job = EXPORT_JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job non trovato"}), 404
    return jsonify({
        "status": job["status"],
        "current": job["current"],
        "total": job["total"],
        "percent": job["percent"],
        "message": job["message"],
        "error": job["error"]
    })

@app.route('/batch/export-job/<job_id>/download', methods=['GET'])
@app.route('/api/batch/export-job/<job_id>/download', methods=['GET'])
def api_download_export_job(job_id):
    job = EXPORT_JOBS.get(job_id)
    if not job or job["status"] != "completed" or not job["result_bytes"]:
        return jsonify({"error": "File non pronto o non trovato"}), 404
    return send_file(
        io.BytesIO(job["result_bytes"]),
        mimetype=job["mimetype"],
        as_attachment=True,
        download_name=job["filename"]
    )


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"=== Scanner Web Multi Server avviato su http://localhost:{port} ===")
    app.run(host='0.0.0.0', port=port, debug=False)
