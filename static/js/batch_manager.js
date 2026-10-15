// Batch Selection and Bulk Enhancements Manager
class BatchManager {
  constructor(app) {
    this.app = app;
    this.selectedDocIds = new Set();
    this.toolbar = document.getElementById('batchToolbar');
    this.counterEl = document.getElementById('batchCount');

    this.initEvents();
  }

  initEvents() {
    // Pulsante Seleziona Tutti
    document.getElementById('btnSelectAll')?.addEventListener('click', () => {
      this.selectAll();
    });

    // Pulsante Deseleziona
    document.getElementById('btnDeselectAll')?.addEventListener('click', () => {
      this.clearSelection();
    });

    // Apertura modale miglioramenti in blocco
    document.getElementById('btnBatchEnhance')?.addEventListener('click', () => {
      this.openBatchEnhanceModal();
    });

    // Apertura modale sposta in blocco
    document.getElementById('btnBatchMove')?.addEventListener('click', () => {
      this.openBatchMoveModal();
    });

    // Esporta PDF Unificato
    document.getElementById('btnBatchExportPdf')?.addEventListener('click', () => {
      this.exportBatchPdf();
    });

    // Esporta JPG in blocco
    document.getElementById('btnBatchExportJpg')?.addEventListener('click', () => {
      this.exportBatchImages('jpg');
    });

    // Esporta PNG in blocco
    document.getElementById('btnBatchExportPng')?.addEventListener('click', () => {
      this.exportBatchImages('png');
    });

    // Esporta ZIP
    document.getElementById('btnBatchExportZip')?.addEventListener('click', () => {
      this.exportBatchZip();
    });

    // Sposta nel cestino in blocco
    document.getElementById('btnBatchTrash')?.addEventListener('click', () => {
      this.trashSelected();
    });

    // Conferma applicazione miglioramenti in blocco
    document.getElementById('btnConfirmBatchEnhance')?.addEventListener('click', () => {
      this.applyBatchEnhancements();
    });

    // Conferma spostamento in blocco
    document.getElementById('btnConfirmBatchMove')?.addEventListener('click', () => {
      this.applyBatchMove();
    });
  }

  toggle(docId) {
    if (this.selectedDocIds.has(docId)) {
      this.selectedDocIds.delete(docId);
    } else {
      this.selectedDocIds.add(docId);
    }
    this.updateUI();
  }

  selectAll() {
    this.app.currentDocuments.forEach(d => this.selectedDocIds.add(d.id));
    this.updateUI();
  }

  clearSelection() {
    this.selectedDocIds.clear();
    this.updateUI();
  }

  updateUI() {
    const count = this.selectedDocIds.size;
    if (this.counterEl) {
      this.counterEl.textContent = `${count} selezionat${count === 1 ? 'o' : 'i'}`;
    }

    if (count > 0) {
      this.toolbar?.classList.add('show');
    } else {
      this.toolbar?.classList.remove('show');
    }

    // Aggiorna checkbox e classi card
    document.querySelectorAll('.doc-card').forEach(card => {
      const id = card.dataset.id;
      const cb = card.querySelector('.card-select-checkbox');
      const isSel = this.selectedDocIds.has(id);
      card.classList.toggle('selected', isSel);
      if (cb) cb.checked = isSel;
    });
  }

  openBatchEnhanceModal() {
    if (this.selectedDocIds.size === 0) return;
    document.getElementById('batchModalCount').textContent = this.selectedDocIds.size;
    this.app.openModal('batchEnhanceModal');
  }

  openBatchMoveModal() {
    if (this.selectedDocIds.size === 0) return;
    const select = document.getElementById('batchTargetBlockSelect');
    select.innerHTML = '';
    this.app.blocks.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.name;
      select.appendChild(opt);
    });
    this.app.openModal('batchMoveModal');
  }

  async applyBatchEnhancements() {
    const filterType = document.getElementById('batchFilterSelect').value;
    const brightness = parseInt(document.getElementById('batchBrightnessSlider').value) || 0;
    const contrast = parseInt(document.getElementById('batchContrastSlider').value) || 0;
    const rotationDelta = parseInt(document.getElementById('batchRotationSelect').value) || 0;
    const autoCrop = document.getElementById('batchAutoCropCheck').checked;

    this.app.showLoading("Applicazione miglioramenti in blocco in corso...");
    try {
      const res = await fetch('/api/batch/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_ids: Array.from(this.selectedDocIds),
          filter_type: filterType === 'no_change' ? null : filterType,
          brightness: brightness,
          contrast: contrast,
          rotation_delta: rotationDelta,
          auto_crop: autoCrop
        })
      });

      if (!res.ok) throw new Error("Errore durante l'elaborazione");
      const data = await res.json();
      this.app.showToast(`Miglioramento applicato a ${data.processed_count} documenti!`);
      this.app.closeModal('batchEnhanceModal');
      await this.app.loadDocuments();
    } catch (err) {
      alert("Errore nell'applicazione in blocco: " + err.message);
    } finally {
      this.app.hideLoading();
    }
  }

  async applyBatchMove() {
    const targetBlock = document.getElementById('batchTargetBlockSelect').value;
    this.app.showLoading("Spostamento documenti in corso...");
    try {
      const res = await fetch('/api/batch/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_ids: Array.from(this.selectedDocIds),
          target_block_id: targetBlock
        })
      });
      const data = await res.json();
      this.app.showToast(`${data.modified_count} documenti spostati con successo!`);
      this.app.closeModal('batchMoveModal');
      this.clearSelection();
      await this.app.loadDocuments();
    } catch (err) {
      alert("Errore spostamento: " + err.message);
    } finally {
      this.app.hideLoading();
    }
  }

  async trashSelected() {
    if (!confirm(`Spostare ${this.selectedDocIds.size} documenti nel cestino?`)) return;
    this.app.showLoading("Spostamento nel cestino...");
    try {
      const res = await fetch('/api/batch/trash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_ids: Array.from(this.selectedDocIds) })
      });
      const data = await res.json();
      this.app.showToast(`${data.trashed_count} documenti spostati nel cestino.`);
      this.clearSelection();
      await this.app.loadDocuments();
    } catch (err) {
      alert("Errore cestino: " + err.message);
    } finally {
      this.app.hideLoading();
    }
  }

  async runExportJobWithProgress({ type, title, quality = 'high', pageSize = 'A4' }) {
    const docIds = Array.from(this.selectedDocIds);
    if (docIds.length === 0) return;

    const modal = document.getElementById('batchExportProgressModal');
    const titleEl = document.getElementById('batchExportProgressTitle');
    const subtitleEl = document.getElementById('batchExportProgressSubtitle');
    const barEl = document.getElementById('batchExportProgressBar');
    const countEl = document.getElementById('batchExportProgressCount');
    const pctEl = document.getElementById('batchExportProgressPercent');

    if (titleEl) titleEl.textContent = title;
    if (subtitleEl) subtitleEl.textContent = `Inizializzazione esportazione per ${docIds.length} documenti...`;
    if (barEl) barEl.style.width = '0%';
    if (countEl) countEl.textContent = '0 / 0';
    if (pctEl) pctEl.textContent = '0%';
    if (modal) modal.classList.add('active');

    let pollInterval = null;

    try {
      // 1. Avvia il job asincrono in background sul server
      const initRes = await fetch('/api/batch/export-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: type,
          doc_ids: docIds,
          quality: quality,
          page_size: pageSize
        })
      });

      if (!initRes.ok) {
        const errJson = await initRes.json().catch(() => ({}));
        throw new Error(errJson.error || "Impossibile avviare il processo di esportazione");
      }

      const { job_id } = await initRes.json();

      // 2. Polling ciclico ad alta frequenza per aggiornamento fluido della barra di progressione
      await new Promise((resolve, reject) => {
        pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(`/api/batch/export-job/${job_id}`);
            if (!statusRes.ok) throw new Error("Errore nel recupero dello stato dell'esportazione");

            const job = await statusRes.json();
            const percent = Math.min(Math.max(job.percent || 0, 0), 100);

            if (barEl) barEl.style.width = `${percent}%`;
            if (pctEl) pctEl.textContent = `${percent}%`;
            if (countEl) countEl.textContent = `${job.current || 0} / ${job.total || 0}`;
            if (subtitleEl && job.message) subtitleEl.textContent = job.message;

            if (job.status === 'completed') {
              clearInterval(pollInterval);
              pollInterval = null;
              if (barEl) barEl.style.width = '100%';
              if (pctEl) pctEl.textContent = '100%';
              if (subtitleEl) subtitleEl.textContent = 'Esportazione completata! Avvio del download...';

              // Trigger download del file
              const downloadUrl = `/api/batch/export-job/${job_id}/download`;
              const a = document.createElement('a');
              a.href = downloadUrl;
              document.body.appendChild(a);
              a.click();
              a.remove();

              setTimeout(() => {
                if (modal) modal.classList.remove('active');
                this.app.showToast('Esportazione completata con successo!');
                resolve();
              }, 500);
            } else if (job.status === 'error') {
              clearInterval(pollInterval);
              pollInterval = null;
              reject(new Error(job.error || "Errore sconosciuto durante l'esportazione"));
            }
          } catch (e) {
            clearInterval(pollInterval);
            pollInterval = null;
            reject(e);
          }
        }, 220);
      });

    } catch (err) {
      if (pollInterval) clearInterval(pollInterval);
      if (modal) modal.classList.remove('active');
      alert("Errore esportazione in blocco: " + err.message);
    }
  }

  async exportBatchPdf() {
    await this.runExportJobWithProgress({
      type: 'pdf',
      title: 'Generazione PDF Unificato...'
    });
  }

  async exportBatchZip() {
    await this.runExportJobWithProgress({
      type: 'zip',
      title: 'Creazione Archivio ZIP Completo...'
    });
  }

  async exportBatchImages(format = 'jpg') {
    const label = format.toUpperCase();
    await this.runExportJobWithProgress({
      type: format,
      title: `Esportazione Immagini ${label} in blocco...`
    });
  }
}
