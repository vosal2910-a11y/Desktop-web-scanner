// Scanner Web Multi - Main Application Controller
class ScannerApp {
  constructor() {
    this.blocks = [];
    this.currentDocuments = [];
    this.currentBlockId = 'all';
    this.currentDoc = null;
    this.activePageIndex = 0;
    this.cropper = null;
    this.camera = null;
    this.batchManager = null;
    this.theme = localStorage.getItem('theme') || 'dark';

    this.init();
  }

  async init() {
    this.applyTheme(this.theme);
    this.batchManager = new BatchManager(this);
    this.cropper = new DocumentCropper('cropCanvas', 'loupeCanvas');
    this.camera = new CameraScanner('cameraVideo', (dataUrl, count) => {
      document.getElementById('cameraShotCount').textContent = `${count} acquisit${count === 1 ? 'o' : 'i'}`;
    });

    this.initEventListeners();
    await this.loadBlocks();
    await this.loadDocuments();
  }

  applyTheme(theme) {
    this.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const themeBtn = document.getElementById('btnToggleTheme');
    if (themeBtn) {
      themeBtn.innerHTML = theme === 'dark' 
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }
  }

  initEventListeners() {
    // Cambio tema
    document.getElementById('btnToggleTheme')?.addEventListener('click', () => {
      this.applyTheme(this.theme === 'dark' ? 'light' : 'dark');
    });

    // Ricerca
    document.getElementById('searchInput')?.addEventListener('input', (e) => {
      this.filterDocuments(e.target.value);
    });

    // Nuovo documento
    document.getElementById('btnNewDocument')?.addEventListener('click', () => {
      this.promptNewDocument();
    });

    // Fotocamera
    document.getElementById('btnScanCamera')?.addEventListener('click', () => {
      this.openCameraModal();
    });
    document.getElementById('btnCaptureShot')?.addEventListener('click', () => {
      this.captureFromCamera();
    });
    document.getElementById('btnFinishScan')?.addEventListener('click', () => {
      this.closeCameraModal();
    });

    // Importazione File
    const fileInput = document.getElementById('fileInputUpload');
    document.getElementById('btnImportFiles')?.addEventListener('click', () => {
      fileInput.click();
    });
    fileInput?.addEventListener('change', (e) => {
      if (e.target.files?.length) {
        this.handleFileUpload(Array.from(e.target.files));
        e.target.value = '';
      }
    });

    // Drag & Drop e Click per apertura selezione file
    const dropzone = document.getElementById('dropZoneArea');
    if (dropzone) {
      dropzone.addEventListener('click', () => {
        fileInput.click();
      });
      ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
          e.preventDefault();
          dropzone.classList.add('dragover');
        });
      });
      ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
          e.preventDefault();
          dropzone.classList.remove('dragover');
        });
      });
      dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files?.length) {
          this.handleFileUpload(Array.from(e.dataTransfer.files));
        }
      });
    }

    // Gestione Nuovo Blocco
    document.getElementById('btnCreateBlock')?.addEventListener('click', () => {
      this.openModal('createBlockModal');
    });
    document.getElementById('btnConfirmCreateBlock')?.addEventListener('click', () => {
      this.createBlock();
    });

    // Editor Documento: Ritorna alla lista
    document.getElementById('btnBackToList')?.addEventListener('click', () => {
      this.showGridView();
    });

    // Editor: Esporta (PDF, JPG, PNG)
    document.getElementById('btnExportDocPdf')?.addEventListener('click', () => {
      this.openModal('exportModal');
    });
    document.getElementById('btnConfirmExport')?.addEventListener('click', () => {
      this.downloadCurrentDocExport();
    });

    const exportFormatSelect = document.getElementById('exportFormatSelect');
    exportFormatSelect?.addEventListener('change', () => {
      const fmt = exportFormatSelect.value;
      const pdfOpts = document.getElementById('pdfSpecificOptions');
      const qualOpts = document.getElementById('qualityOptionRow');
      if (pdfOpts) pdfOpts.style.display = fmt === 'pdf' ? 'flex' : 'none';
      if (qualOpts) qualOpts.style.display = fmt === 'png' ? 'none' : 'block';
    });

    // Editor: Apri Cropper
    document.getElementById('btnOpenCropper')?.addEventListener('click', () => {
      this.openCropperModal();
    });
    document.getElementById('btnConfirmCrop')?.addEventListener('click', () => {
      this.applyCropperChanges();
    });
    document.getElementById('btnResetCrop')?.addEventListener('click', () => {
      this.cropper.resetToDefaults();
      this.cropper.render();
    });
    document.getElementById('btnAutoDetectCrop')?.addEventListener('click', () => {
      this.autoDetectCurrentPageCrop();
    });

    // Editor: Rotazione
    document.getElementById('btnRotatePage')?.addEventListener('click', () => {
      this.rotateCurrentPage();
    });

    // Editor: OCR (Tesseract)
    document.getElementById('btnRunOCR')?.addEventListener('click', () => {
      this.runOCRCurrentPage();
    });
    document.getElementById('btnCopyOCR')?.addEventListener('click', () => {
      const text = document.getElementById('pageOcrText')?.value;
      if (!text || text.trim() === '') {
        this.showToast("Nessun testo da copiare");
        return;
      }
      navigator.clipboard.writeText(text);
      this.showToast("Testo OCR copiato negli appunti!");
    });

    // Editor: Filtri colore
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const filter = btn.dataset.filter;
        this.setPageFilter(filter);
      });
    });

    // Editor: Sliders
    const brightSlider = document.getElementById('brightnessSlider');
    const contrastSlider = document.getElementById('contrastSlider');
    const onSliderChange = () => {
      document.getElementById('brightnessVal').textContent = brightSlider.value;
      document.getElementById('contrastVal').textContent = contrastSlider.value;
      this.setPageAdjustments(parseInt(brightSlider.value), parseInt(contrastSlider.value));
    };
    brightSlider?.addEventListener('input', onSliderChange);
    contrastSlider?.addEventListener('input', onSliderChange);

    // Chiusura Modali con tasto ESC o click su backdrop
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          if (backdrop.id === 'importProgressModal' || backdrop.id === 'batchExportProgressModal') return;
          backdrop.classList.remove('active');
          if (backdrop.id === 'cameraModal') this.camera.stop();
        }
      });
    });
  }

  // --- GESTIONE BLOCCHI ---

  async loadBlocks() {
    try {
      const res = await fetch('/api/blocks');
      this.blocks = await res.json();
      this.renderSidebarBlocks();
    } catch (err) {
      console.error("Errore caricamento blocchi:", err);
    }
  }

  renderSidebarBlocks() {
    const container = document.getElementById('sidebarBlocksList');
    if (!container) return;
    container.innerHTML = '';

    this.blocks.forEach(b => {
      const item = document.createElement('div');
      item.className = `nav-item ${this.currentBlockId === b.id ? 'active' : ''}`;
      item.innerHTML = `
        <span class="block-dot" style="background-color: ${b.color};"></span>
        <span style="flex:1; overflow:hidden; text-overflow:ellipsis;">${b.name}</span>
      `;
      item.addEventListener('click', () => {
        this.selectBlock(b.id);
      });
      container.appendChild(item);
    });
  }

  selectBlock(blockId) {
    this.currentBlockId = blockId;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    this.renderSidebarBlocks();

    // Evidenzia selezione standard (Tutti / Cestino)
    if (blockId === 'all') document.getElementById('navAllDocs')?.classList.add('active');
    if (blockId === 'trash') document.getElementById('navTrashDocs')?.classList.add('active');

    this.showGridView();
    this.loadDocuments();
  }

  async createBlock() {
    const name = document.getElementById('newBlockName').value.trim();
    const color = document.getElementById('newBlockColor').value;
    const desc = document.getElementById('newBlockDesc').value.trim();
    if (!name) return alert("Inserisci un nome per il blocco");

    try {
      const res = await fetch('/api/blocks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color, description: desc })
      });
      if (!res.ok) throw new Error("Errore creazione blocco");
      await this.loadBlocks();
      this.closeModal('createBlockModal');
      this.showToast(`Blocco "${name}" creato!`);
      document.getElementById('newBlockName').value = '';
    } catch (err) {
      alert(err.message);
    }
  }

  // --- GESTIONE DOCUMENTI ---

  async loadDocuments() {
    this.batchManager.clearSelection();
    let url = '/api/documents';
    if (this.currentBlockId === 'trash') {
      url += '?trash=true';
    } else if (this.currentBlockId !== 'all') {
      url += `?block_id=${this.currentBlockId}`;
    }

    try {
      const res = await fetch(url);
      this.currentDocuments = await res.json();
      this.renderDocumentGrid(this.currentDocuments);
      this.renderSidebarRecentDocs();
    } catch (err) {
      console.error("Errore caricamento documenti:", err);
    }
  }

  renderSidebarRecentDocs() {
    const container = document.getElementById('sidebarRecentDocs');
    if (!container) return;
    container.innerHTML = '';
    const recent = this.currentDocuments.slice(0, 8);
    if (!recent.length) {
      container.innerHTML = '<span style="font-size: 11px; color: var(--text-secondary); padding: 4px 10px;">Nessun documento</span>';
      return;
    }
    recent.forEach(d => {
      const item = document.createElement('div');
      item.className = 'nav-item';
      item.style.padding = '5px 8px';
      item.style.fontSize = '12px';
      item.title = d.title;

      const thumbUrl = d.pages?.length > 0 
        ? `/files/${d.id}/${d.pages[0].thumb_file}` 
        : '';

      item.innerHTML = `
        <div style="width: 26px; height: 32px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border: 1px solid var(--border-color);">
          ${thumbUrl ? `<img src="${thumbUrl}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'">` : '<span style="font-size: 10px;">📄</span>'}
        </div>
        <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-left: 8px;">${d.title}</span>
      `;
      item.addEventListener('click', () => {
        this.openDocumentEditor(d.id);
      });
      container.appendChild(item);
    });
  }

  renderDocumentGrid(docs) {
    const grid = document.getElementById('docsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    if (docs.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-secondary);">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px; opacity: 0.5;">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <p style="font-size: 16px; font-weight: 500;">Nessun documento trovato</p>
          <p style="font-size: 13px; margin-top: 4px;">Usa il pulsante "Nuova Scansione" o trascina file qui per iniziare.</p>
        </div>
      `;
      return;
    }

    docs.forEach(doc => {
      const card = document.createElement('div');
      card.className = 'doc-card';
      card.dataset.id = doc.id;

      const pageCount = doc.pages?.length || 0;
      const thumbUrl = pageCount > 0 
        ? `/files/${doc.id}/${doc.pages[0].thumb_file}`
        : 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>';

      const block = this.blocks.find(b => b.id === doc.block_id);
      const blockBadge = block 
        ? `<span class="doc-block-badge" style="background-color: ${block.color}20; color: ${block.color}">${block.name}</span>`
        : '';

      const dateStr = new Date(doc.created_at * 1000).toLocaleDateString();

      card.innerHTML = `
        <div class="doc-thumb-container">
          <input type="checkbox" class="card-select-checkbox" data-id="${doc.id}">
          <img class="doc-thumb" src="${thumbUrl}" alt="Miniatura">
          <span class="pages-badge">${pageCount} pagin${pageCount === 1 ? 'a' : 'e'}</span>
        </div>
        <div class="doc-info">
          <span class="doc-title" title="${doc.title}">${doc.title}</span>
          <div class="doc-meta">
            <span>${dateStr}</span>
            ${blockBadge}
          </div>
        </div>
      `;

      // Click sulla checkbox di selezione
      const cb = card.querySelector('.card-select-checkbox');
      cb.addEventListener('click', (e) => {
        e.stopPropagation();
        this.batchManager.toggle(doc.id);
      });

      // Click sulla card per aprire l'editor
      card.addEventListener('click', (e) => {
        if (e.target !== cb) {
          this.openDocumentEditor(doc.id);
        }
      });

      grid.appendChild(card);
    });
  }

  filterDocuments(query) {
    const q = query.toLowerCase().trim();
    if (!q) {
      this.renderDocumentGrid(this.currentDocuments);
      return;
    }
    const filtered = this.currentDocuments.filter(d => 
      d.title.toLowerCase().includes(q) ||
      d.pages?.some(p => p.ocr_text?.toLowerCase().includes(q))
    );
    this.renderDocumentGrid(filtered);
  }

  // --- EDITOR DOCUMENTO E PAGINE ---

  async openDocumentEditor(docId) {
    try {
      const res = await fetch(`/api/documents/${docId}`);
      if (!res.ok) throw new Error("Documento non trovato");
      this.currentDoc = await res.json();
      this.activePageIndex = 0;

      // Aggiorna titolo
      document.getElementById('editorDocTitle').textContent = this.currentDoc.title;
      this.renderPagesStrip();
      this.renderActivePage();

      // Mostra vista editor
      document.getElementById('gridViewArea').style.display = 'none';
      document.getElementById('editorViewArea').classList.add('active');
    } catch (err) {
      alert(err.message);
    }
  }

  showGridView() {
    document.getElementById('editorViewArea').classList.remove('active');
    document.getElementById('gridViewArea').style.display = 'block';
    this.currentDoc = null;
    this.loadDocuments();
  }

  renderPagesStrip() {
    const strip = document.getElementById('pagesStrip');
    if (!strip || !this.currentDoc) return;
    strip.innerHTML = '';

    this.currentDoc.pages.forEach((p, idx) => {
      const box = document.createElement('div');
      const isActive = idx === this.activePageIndex;
      box.className = `page-thumb-box ${isActive ? 'active' : ''}`;
      box.title = `Pagina ${idx + 1}`;
      box.innerHTML = `
        <span class="page-number">${idx + 1}</span>
        <img src="/files/${this.currentDoc.id}/${p.thumb_file}" alt="P${idx + 1}" loading="lazy" onerror="this.onerror=null; this.src='/files/${this.currentDoc.id}/${p.processed_file}';">
      `;
      box.addEventListener('click', () => {
        this.activePageIndex = idx;
        this.renderPagesStrip();
        this.renderActivePage();
      });
      strip.appendChild(box);

      if (isActive) {
        setTimeout(() => box.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
      }
    });

    // Pulsante Aggiungi Pagina
    const addBox = document.createElement('div');
    addBox.className = 'page-thumb-box';
    addBox.style.display = 'flex';
    addBox.style.alignItems = 'center';
    addBox.style.justifyContent = 'center';
    addBox.style.borderStyle = 'dashed';
    addBox.style.flexShrink = '0';
    addBox.style.minHeight = '160px';
    addBox.style.height = '160px';
    addBox.title = 'Aggiungi nuova pagina a questo documento';
    addBox.innerHTML = `
      <span style="font-size: 26px; color: var(--accent-color); font-weight: bold;">+</span>
    `;
    addBox.addEventListener('click', () => {
      this.promptAddPageToCurrentDoc();
    });
    strip.appendChild(addBox);
  }

  renderActivePage() {
    if (!this.currentDoc || !this.currentDoc.pages[this.activePageIndex]) {
      document.getElementById('mainStageImg').src = '';
      return;
    }
    const page = this.currentDoc.pages[this.activePageIndex];
    const stageImg = document.getElementById('mainStageImg');
    stageImg.src = `/files/${this.currentDoc.id}/${page.processed_file}?t=${Date.now()}`;

    // Aggiorna filtri attivi
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.filter === (page.filter_type || 'magic_color'));
    });

    // Aggiorna sliders
    const brightSlider = document.getElementById('brightnessSlider');
    const contrastSlider = document.getElementById('contrastSlider');
    if (brightSlider) brightSlider.value = page.brightness || 0;
    if (contrastSlider) contrastSlider.value = page.contrast || 0;
    document.getElementById('brightnessVal').textContent = page.brightness || 0;
    document.getElementById('contrastVal').textContent = page.contrast || 0;

    // Aggiorna info OCR e QR
    const ocrBox = document.getElementById('pageOcrText');
    if (ocrBox) ocrBox.value = page.ocr_text || '';

    const qrContainer = document.getElementById('pageQrCodes');
    if (qrContainer) {
      qrContainer.innerHTML = '';
      if (page.qrcodes && page.qrcodes.length > 0) {
        page.qrcodes.forEach(qr => {
          const badge = document.createElement('div');
          badge.className = 'nav-item';
          badge.style.fontSize = '12px';
          badge.innerHTML = `
            <strong>${qr.type}:</strong>
            <span style="margin: 0 8px; overflow:hidden; text-overflow:ellipsis;">${qr.text}</span>
            <button class="btn btn-icon" style="padding: 2px 6px; font-size:11px;" title="Copia">Copia</button>
          `;
          badge.querySelector('button').addEventListener('click', () => {
            navigator.clipboard.writeText(qr.text);
            this.showToast("Codice copiato negli appunti!");
          });
          qrContainer.appendChild(badge);
        });
      } else {
        qrContainer.innerHTML = '<span style="font-size:12px; color:var(--text-secondary);">Nessun codice rilevato</span>';
      }
    }
  }

  async setPageFilter(filterType) {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    page.filter_type = filterType;

    this.showLoading("Applicazione filtro...");
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter_type: filterType })
      });
      const updated = await res.json();
      this.currentDoc.pages[this.activePageIndex] = updated;
      this.renderPagesStrip();
      this.renderActivePage();
    } catch (err) {
      alert("Errore filtro: " + err.message);
    } finally {
      this.hideLoading();
    }
  }

  async setPageAdjustments(brightness, contrast) {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brightness, contrast })
      });
      const updated = await res.json();
      this.currentDoc.pages[this.activePageIndex] = updated;
      document.getElementById('mainStageImg').src = `/files/${this.currentDoc.id}/${updated.processed_file}?t=${Date.now()}`;
    } catch (err) {
      console.error(err);
    }
  }

  async rotateCurrentPage() {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    const nextRot = ((page.rotation || 0) + 90) % 360;

    this.showLoading("Rotazione...");
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rotation: nextRot })
      });
      const updated = await res.json();
      this.currentDoc.pages[this.activePageIndex] = updated;
      this.renderPagesStrip();
      this.renderActivePage();
    } catch (err) {
      alert(err.message);
    } finally {
      this.hideLoading();
    }
  }

  async openCropperModal() {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    const origUrl = `/files/${this.currentDoc.id}/${page.original_file}`;

    this.openModal('cropperModal');
    this.showLoading("Caricamento ritaglio prospettico...");
    try {
      await this.cropper.loadImage(origUrl, page.quad);
    } catch (err) {
      alert("Errore caricamento immagine nel cropper");
    } finally {
      this.hideLoading();
    }
  }

  async autoDetectCurrentPageCrop() {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/detect-corners`, { method: 'POST' });
      const data = await res.json();
      if (data.quad) {
        this.cropper.points = data.quad;
        this.cropper.render();
      }
    } catch (err) {
      alert("Errore auto-detect: " + err.message);
    }
  }

  async applyCropperChanges() {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];
    const quad = this.cropper.getQuad();

    this.showLoading("Raddrizzamento prospettico in corso...");
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quad: quad })
      });
      const updated = await res.json();
      this.currentDoc.pages[this.activePageIndex] = updated;
      this.closeModal('cropperModal');
      this.renderPagesStrip();
      this.renderActivePage();
      this.showToast("Ritaglio e prospettiva aggiornati!");
    } catch (err) {
      alert(err.message);
    } finally {
      this.hideLoading();
    }
  }

  async runOCRCurrentPage() {
    if (!this.currentDoc) return;
    const page = this.currentDoc.pages[this.activePageIndex];

    this.showLoading("Riconoscimento caratteri Tesseract OCR in corso...");
    try {
      const res = await fetch(`/api/documents/${this.currentDoc.id}/pages/${page.id}/ocr`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang: 'ita+eng' })
      });
      const data = await res.json();
      page.ocr_text = data.text;
      document.getElementById('pageOcrText').value = data.text || '';
      const engineMsg = data.engine ? ` (${data.engine})` : '';
      this.showToast(`Testo riconosciuto con successo!${engineMsg}`);
    } catch (err) {
      alert("Errore OCR: " + err.message);
    } finally {
      this.hideLoading();
    }
  }

  // --- ACQUISIZIONE E CARICAMENTO FILE ---

  async handleFileUpload(files) {
    if (!files.length) return;
    this.showImportProgress(files.length, "Importazione file in corso...");

    try {
      // 1. Crea un nuovo documento
      const docRes = await fetch('/api/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Scansione ${new Date().toLocaleDateString()} (${files.length} pag.)`,
          block_id: this.currentBlockId !== 'all' && this.currentBlockId !== 'trash' ? this.currentBlockId : 'general'
        })
      });
      const doc = await docRes.json();

      // 2. Aggiungi ciascuna immagine come pagina con aggiornamento barra
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        this.updateImportProgress(i + 1, files.length, file.name);

        const formData = new FormData();
        formData.append('image', file);
        formData.append('auto_crop', 'true');
        formData.append('filter_type', 'magic_color');

        await fetch(`/api/documents/${doc.id}/pages`, {
          method: 'POST',
          body: formData
        });
      }

      this.hideImportProgress();
      this.showToast(`${files.length} pagine importate con successo!`);
      await this.loadDocuments();
      this.openDocumentEditor(doc.id);
    } catch (err) {
      this.hideImportProgress();
      alert("Errore caricamento: " + err.message);
    }
  }

  async promptAddPageToCurrentDoc() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'image/*';
    input.onchange = async (e) => {
      const files = Array.from(e.target.files || []);
      if (!files.length) return;

      if (files.length > 1) {
        this.showImportProgress(files.length, "Aggiunta pagine al documento...");
      } else {
        this.showLoading("Aggiunta pagina...");
      }

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          if (files.length > 1) {
            this.updateImportProgress(i + 1, files.length, file.name);
          }

          const formData = new FormData();
          formData.append('image', file);
          formData.append('auto_crop', 'true');
          formData.append('filter_type', 'magic_color');

          const res = await fetch(`/api/documents/${this.currentDoc.id}/pages`, {
            method: 'POST',
            body: formData
          });
          const page = await res.json();
          this.currentDoc.pages.push(page);
        }
        this.activePageIndex = this.currentDoc.pages.length - 1;
        this.renderPagesStrip();
        this.renderActivePage();
      } catch (err) {
        alert("Errore aggiunta pagina: " + err.message);
      } finally {
        if (files.length > 1) {
          this.hideImportProgress();
        } else {
          this.hideLoading();
        }
      }
    };
    input.click();
  }

  // Fotocamera Webcam
  async openCameraModal() {
    this.openModal('cameraModal');
    try {
      await this.camera.start();
    } catch (err) {
      alert("Impossibile accedere alla webcam: " + err.message);
      this.closeModal('cameraModal');
    }
  }

  async captureFromCamera() {
    const frameData = this.camera.captureFrame();
    if (!frameData) return;

    // Se stiamo già editando un documento, aggiungi la pagina al documento corrente
    if (this.currentDoc) {
      try {
        const res = await fetch(`/api/documents/${this.currentDoc.id}/pages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_base64: frameData, auto_crop: true, filter_type: 'magic_color' })
        });
        const page = await res.json();
        this.currentDoc.pages.push(page);
        this.showToast(`Pagina ${this.currentDoc.pages.length} acquisita!`);
      } catch (err) {
        console.error(err);
      }
    } else {
      // Salva in array temporaneo per creare nuovo documento alla fine
      if (!this.tempCameraFrames) this.tempCameraFrames = [];
      this.tempCameraFrames.push(frameData);
      this.showToast(`Scatto ${this.tempCameraFrames.length} memorizzato`);
    }
  }

  async closeCameraModal() {
    this.camera.stop();
    this.closeModal('cameraModal');

    if (this.tempCameraFrames && this.tempCameraFrames.length > 0) {
      this.showLoading("Salvataggio scansioni fotocamera...");
      try {
        const docRes = await fetch('/api/documents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: `Scansione Webcam ${new Date().toLocaleDateString()}`,
            block_id: this.currentBlockId !== 'all' && this.currentBlockId !== 'trash' ? this.currentBlockId : 'general'
          })
        });
        const doc = await docRes.json();

        for (const frame of this.tempCameraFrames) {
          await fetch(`/api/documents/${doc.id}/pages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: frame, auto_crop: true, filter_type: 'magic_color' })
          });
        }

        this.tempCameraFrames = [];
        await this.loadDocuments();
        this.openDocumentEditor(doc.id);
      } catch (err) {
        alert(err.message);
      } finally {
        this.hideLoading();
      }
    } else if (this.currentDoc) {
      this.renderPagesStrip();
      this.renderActivePage();
    }
  }

  // --- DOWNLOAD E ESPORTAZIONE DOCUMENTO (PDF, JPG, PNG) ---
  async downloadCurrentDocExport() {
    if (!this.currentDoc || !this.currentDoc.id) {
      this.showToast("Nessun documento attivo selezionato per l'esportazione");
      return;
    }
    const format = document.getElementById('exportFormatSelect')?.value || 'pdf';
    const scope = document.getElementById('exportScopeSelect')?.value || 'all';
    const quality = document.getElementById('exportQualitySelect')?.value || 'high';
    const pageSize = document.getElementById('exportPdfPageSize')?.value || 'A4';
    const password = document.getElementById('exportPdfPassword')?.value;

    let url = `/api/documents/${this.currentDoc.id}/export?format=${format}&quality=${quality}`;
    if (scope === 'current') {
      url += `&page=${this.activePageIndex}`;
    }
    if (format === 'pdf') {
      url += `&page_size=${pageSize}`;
      if (password) url += `&password=${encodeURIComponent(password)}`;
    }

    const a = document.createElement('a');
    a.href = url;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    a.remove();

    this.closeModal('exportModal');
    this.showToast(`Download in formato ${format.toUpperCase()} avviato!`);
  }

  // Helper per Barra di Avanzamento
  showImportProgress(total, title = "Importazione file in corso...") {
    const modal = document.getElementById('importProgressModal');
    if (!modal) return;
    document.getElementById('importProgressTitle').textContent = title;
    document.getElementById('importProgressSubtitle').textContent = `Inizializzazione di ${total} pagine...`;
    document.getElementById('importProgressBar').style.width = '0%';
    document.getElementById('importProgressCount').textContent = `0 / ${total}`;
    document.getElementById('importProgressPercent').textContent = '0%';
    modal.classList.add('active');
  }

  updateImportProgress(current, total, filename = '') {
    const percent = Math.round((current / total) * 100);
    const bar = document.getElementById('importProgressBar');
    if (bar) bar.style.width = `${percent}%`;
    const countEl = document.getElementById('importProgressCount');
    if (countEl) countEl.textContent = `${current} / ${total}`;
    const pctEl = document.getElementById('importProgressPercent');
    if (pctEl) pctEl.textContent = `${percent}%`;
    const subEl = document.getElementById('importProgressSubtitle');
    if (subEl) subEl.textContent = filename ? `Elaborazione: ${filename}` : `Pagina ${current} di ${total}...`;
  }

  hideImportProgress() {
    document.getElementById('importProgressModal')?.classList.remove('active');
  }

  // --- UTILITIES UI ---

  openModal(modalId) {
    document.getElementById(modalId)?.classList.add('active');
  }

  closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('active');
  }

  showToast(message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--success-color);">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  showLoading(text = "Elaborazione...") {
    let loader = document.getElementById('appLoader');
    if (!loader) {
      loader = document.createElement('div');
      loader.id = 'appLoader';
      loader.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:white;backdrop-filter:blur(3px);';
      loader.innerHTML = `
        <div style="width:40px;height:40px;border:3px solid rgba(255,255,255,0.2);border-top-color:#3b82f6;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
        <p id="loaderText" style="margin-top:16px;font-weight:600;font-size:15px;"></p>
        <style>@keyframes spin{to{transform:rotate(360deg)}}</style>
      `;
      document.body.appendChild(loader);
    }
    document.getElementById('loaderText').textContent = text;
    loader.style.display = 'flex';
  }

  hideLoading() {
    const loader = document.getElementById('appLoader');
    if (loader) loader.style.display = 'none';
  }
}

// Avvio applicazione al caricamento del DOM
document.addEventListener('DOMContentLoaded', () => {
  window.app = new ScannerApp();
});
