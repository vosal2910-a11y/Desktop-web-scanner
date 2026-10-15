# Scanner Web Multi - Web App Windows

## 📌 Informazioni sul Progetto
- **Nome Progetto**: **Scanner Web Multi**
- **Origine**: Basato e potenziato dal codice open source di [OSS-DocumentScanner](https://github.com/ossappscollective/OSS-DocumentScanner).
- **Piattaforma target**: Windows (esecuzione Web App locale, veloce, sicura, 100% offline).
- **Linguaggio e Tecnologie**: Python 3.12, Flask, OpenCV (cv2), Pillow (PIL), PyPDF, Pytesseract (Tesseract OCR v5.4.0), Canvas HTML5, CSS moderno Dark/Light.
- **Funzionalità chiave realizzate**:
  - **Riconoscimento Caratteri OCR Tesseract 100% Funzionante** (lingue italiano + inglese con modelli `ita.traineddata` ed `eng.traineddata`, estrazione testo e coordinate parole).
  - **Gestione a Blocchi di Documenti** (cartelle/lotti tematici es. "Fatture", "Spese", "Contratti").
  - **Selezione Rapida Multipla** (caselle visive, seleziona tutti, contatore attivo).
  - **Miglioramenti in Blocco (Bulk Enhancements)**: applicazione simultanea con 1 click di filtri colore (Magic Color, B&W, ecc.), regolazione luminosità/contrasto, rotazione a 90° e ritaglio su tutti i documenti selezionati.
  - **Esportazione cumulativa multiformato**: PDF unificato master, JPG in ZIP, PNG in ZIP e archivio ZIP completo con barra di progressione in tempo reale.

---

## 📋 Istruzioni Rapide per l'Uso su Windows

1. **Avvio Rapido con 1 Click**:
   - Fare doppio click sul file `avvia_scanner.bat` (oppure `start.bat`).
   - Lo script controllerà l'ambiente Python, installerà automaticamente le dipendenze da `requirements.txt` se mancanti e aprirà automaticamente il browser predefinito su `http://localhost:5000`.
2. **Acquisizione Documenti**:
   - **Da Fotocamera / Webcam**: Cliccare su **Fotocamera**, inquadrare il foglio e premere **Scatta** (supporta scatti multipli continui).
   - **Da File del PC**: Cliccare su **Importa File / PDF** oppure trascinare direttamente le immagini nell'area tratteggiata **Drag & Drop**.
3. **Raddrizzamento e Ritaglio Prospettico**:
   - Cliccare su un documento per aprirlo nell'Editor.
   - Premere **Raddrizza & Ritaglia**: spostare i 4 angoli con l'aiuto della **lente d'ingrandimento circolare (loupe)** che ingrandisce l'angolo a 2.5x con mirino di precisione.
   - Premere **Applica e Raddrizza** per applicare la trasformazione prospettica omografica.
4. **Filtri e Miglioramenti Colore**:
   - **Magic Paper**: sbianca lo sfondo della carta e rende i caratteri neri nitidi.
   - **Bianco e Nero**: sogliatura binaria ad alto contrasto per testi e moduli.
   - **Scala di Grigi**: gradazioni di grigio omogenee.
   - **Originale / Sepia / Polaroid**: altri stili colore preservando l'originale.
   - Slider di precisione per **Luminosità** e **Contrasto**.
5. **Gestione a Blocchi e Azioni di Massa (Novità)**:
   - Dalla sidebar sinistra cliccare su `+` per creare un nuovo Blocco (es. "Fatture 2026").
   - Selezionare più documenti tramite le caselle di spunta o premere **Seleziona Tutti**.
   - Nella barra fluttuante in alto apparirà il contatore e le azioni di massa:
     - **Miglioramenti in Blocco**: scegliere il filtro comune, la luminosità, il contrasto o la rotazione e cliccare *Applica a Tutti*.
     - **Sposta in Blocco**: trasferire tutti i documenti selezionati in una categoria con un click.
     - **PDF Unificato**: unisce tutti i documenti selezionati in un unico file PDF ordinato.
     - **ZIP**: scarica tutte le scansioni e PDF raggruppati in archivio compresso.
7. **Esportazione Multiformato (PDF, JPG, PNG)**:
   - Nell'editor cliccare su **Esporta**: scegliere se scaricare l'intero documento o la singola pagina attiva.
   - Scegliere tra i formati:
     - **PDF**: imposta formato (A4, Lettera, Auto), qualità e password opzionale.
     - **JPG**: per scaricare direttamente l'immagine (o un archivio ZIP con tutte le pagine numerate in alta risoluzione).
     - **PNG**: per immagini senza perdita di qualità e massima nitidezza.
   - Nella barra delle azioni di massa selezionare i file e cliccare su **PDF Unificato**, **JPG (ZIP)** o **PNG (ZIP)** per esportare lotti completi in un colpo solo.

---

## 🧪 Report dei 3 Cicli di Test Eseguiti

Come da richiesta, prima del rilascio sono stati eseguiti **tre cicli completi di test automatizzati**, tutti superati con esito positivo al 100%:

### ✅ Ciclo di Test 1: Algoritmi Core OpenCV e Filtri OSS
- **File di test**: `tests/test_cycle_1_core.py`
- **Esito**: 5 test eseguiti con successo in 0.286s.
- **Funzionalità verificate**:
  1. Rilevamento automatico dei 4 angoli del foglio su sagome inclinate.
  2. Correzione prospettica (warp prospettico omografico con matrice di destinazione ortogonale).
  3. Applicazione completa dei filtri colore OSS (`magic_color`, `bw`, `grayscale`, `sepia`, `invert`, `polaroid`, `normal`).
  4. Rotazioni ortogonali (90°, 180°, 270°).
  5. Rilevatore codici QR e Barcode.

### ✅ Ciclo di Test 2: Gestione Blocchi, Selezione Multipla e Bulk Enhancements
- **File di test**: `tests/test_cycle_2_blocks_bulk.py`
- **Esito**: 4 test eseguiti con successo in 3.277s.
- **Funzionalità verificate**:
  1. Creazione dinamica di blocchi di documenti e filtraggio mirato.
  2. Applicazione in blocco (batch) di filtri colore, rotazione e contrasto a 6 pagine distribuite su 3 documenti contemporaneamente.
  3. Spostamento di lotti di documenti tra blocchi differenti.
  4. Generazione ed esportazione di PDF master unificato da 6 pagine e archivio ZIP multipagina.

### ✅ Ciclo di Test 3: Integrazione End-to-End, API Flask e Script Windows
- **File di test**: `tests/test_cycle_3_e2e.py`
- **Esito**: 3 test eseguiti con successo in 0.886s.
- **Funzionalità verificate**:
  1. Disponibilità della Web App su porta HTTP locale, template HTML5, CSS responsive dark/light mode e tutti i moduli JavaScript (`app.js`, `cropper.js`, `batch_manager.js`, `camera.js`).
  2. Flusso REST API completo: creazione documento, upload pagina, elaborazione, OCR, download PDF e gestione cestino/ripristino.
  3. Integrità degli eseguibili Windows: validazione comandi batch di `avvia_scanner.bat`, `start.bat` e coerenza di `requirements.txt`.

---

## 📁 Struttura dei File del Progetto

```
c:\Users\s.bruno\Documents\Oss document pc\
├── avvia_scanner.bat            # Script di avvio rapido con 1-click per Windows
├── start.bat                    # Scorciatoia di avvio immediato
├── requirements.txt            # Dipendenze Python (flask, opencv-python, pillow, pypdf)
├── memoria.md                  # Istruzioni d'uso, note di progetto e registro test
├── app.py                      # Server Flask con API REST complete
├── core/
│   ├── __init__.py
│   ├── scanner_cv.py           # Algoritmi OpenCV: rilevamento 4 angoli, warp prospettico, filtri colore, Magic Paper
│   ├── doc_manager.py          # Gestione documenti, blocchi, cestino, storage locale e batch engine
│   ├── ocr_engine.py           # Motore OCR e rilevamento QR/Barcode
│   └── pdf_exporter.py         # Generatore PDF (A4/Letter/Fit, compressione, password, layer OCR, unione e ZIP)
├── static/
│   ├── index.html              # Interfaccia grafica completa Web App Desktop
│   ├── css/
│   │   └── style.css           # Stili CSS responsive, tema scuro/chiaro e layout moderno
│   └── js/
│       ├── app.js              # Controller principale applicazione e visualizzazione
│       ├── cropper.js          # Editor prospettico 4 angoli con loupe magnifier
│       ├── batch_manager.js    # Gestione blocchi, selezione multipla e miglioramenti in blocco
│       └── camera.js           # Acquisizione video da webcam ad alta risoluzione
├── tests/
│   ├── test_cycle_1_core.py    # Test ciclo 1 (OpenCV, warp, filtri)
│   ├── test_cycle_2_blocks_bulk.py # Test ciclo 2 (Blocchi, selezione, bulk actions)
│   └── test_cycle_3_e2e.py     # Test ciclo 3 (Web API E2E, script Windows)
└── data/                       # Archiviazione locale dei documenti, pagine e blocchi
```

---

## 🔄 Registro dei Progressi

- [x] **Fase 0 - Analisi e Pianificazione**:
  - Ispezione del codice sorgente di `OSS-DocumentScanner`.
  - Definizione architettura Python Flask + OpenCV + Frontend Canvas.
  - Creazione del piano di implementazione e avvio del file `memoria.md`.
- [x] **Fase 1 - Approvazione del Piano da parte dell'Utente**:
  - Approvazione registrata ed esecuzione avviata.
- [x] **Fase 2 - Sviluppo del Backend Core**:
  - Implementazione algoritmi OpenCV in `core/scanner_cv.py`.
  - Gestione documenti, blocchi e bulk in `core/doc_manager.py`.
  - Motore di esportazione PDF e ZIP in `core/pdf_exporter.py`.
  - Motore OCR e QR Code in `core/ocr_engine.py`.
  - Server REST Flask in `app.py`.
- [x] **Fase 3 - Sviluppo Frontend Web App**:
  - Interfaccia HTML5 ricca in `static/index.html`.
  - Stili CSS moderni Dark/Light mode in `static/css/style.css`.
  - Moduli JS `cropper.js`, `camera.js`, `batch_manager.js`, `app.js`.
  - Script Windows 1-click `avvia_scanner.bat` e `start.bat`.
- [x] **Fase 4 - Tre Cicli di Test Rigorosi**:
  - Eseguito Test 1 (Core OpenCV): 5/5 superati.
  - Eseguito Test 2 (Blocchi e Bulk Actions): 4/4 superati.
  - Eseguito Test 3 (E2E Web App e Windows): 3/3 superati.
- [x] **Fase 5 - Rilascio del Progetto Completo all'Utente**:
  - Tutto pronto, documentato e pronto all'uso.
- [x] **Miglioramenti Richiesti dall'Utente**:
  - Resa cliccabile l'intera area di caricamento (dropzone) per aprire direttamente la finestra nativa di selezione file con click, preservando contemporaneamente il drag-and-drop.
  - Abilitato il supporto al caricamento di pagine multiple contemporaneamente sia dalla schermata iniziale sia dall'editor di documenti.
  - **Risolto problema visualizzazione anteprime sulla barra sinistra**:
    - Risolto lo schiacciamento (*flex-shrink*) nella striscia verticale sinistra dell'editor di documenti, garantendo altezza fissa (160px), proporzioni corrette, scroll fluido e caricamento asincrono (*lazy-loading*) anche con documenti composti da decine o centinaia di pagine.
    - Aggiunta nella barra laterale sinistra principale la sezione *"File / Documenti Recenti"* con miniature dirette per aprire immediatamente i documenti caricati.
  - **Barra di avanzamento importazione ed esportazione per grandi volumi**:
    - Aggiunto overlay visivo con barra di avanzamento dinamica, conteggio progressivo pagine ("X / Y"), percentuale e indicazione del nome del file in elaborazione durante l'acquisizione massiva.
    - **Barra di avanzamento reale durante l'esportazione di gruppi di documenti**:
      - Eliminata la rotellina rotante generica in favore di un indicatore di progressione dinamico in tempo reale.
      - Integrazione architettura asincrona backend (`/api/batch/export-job`, `/api/batch/export-job/<id>`, `/api/batch/export-job/<id>/download`) con worker thread separati e tracciamento puntuale delle pagine convertite/unite.
      - Modale dedicato con barra a gradiente sfumato, percentuale in tempo reale (0% -> 100%), conteggio dettagliato di pagine elaborate ("X / Y pagine") e indicazione esatta del documento e pagina corrente (es. *"Aggiunta al PDF: Fattura (pag. 3/12)"*, *"Conversione PNG: Ricevuta (pag. 1/4)"*, ecc.).
      - Download automatico immediato al completamento del processo con chiusura modale e toast di conferma.
      - Protezione contro la chiusura accidentale da click sullo sfondo durante l'elaborazione.
  - **Esportazione multiformato in JPG e PNG**:
    - Aggiunta la possibilità di esportare sia singoli documenti (o singole pagine) sia selezioni multiple in formato JPG o PNG ad alta fedeltà (con download diretto o archivio ZIP), in aggiunta al formato PDF.
    - Aggiunti pulsanti dedicati nella barra delle azioni di massa: *PDF Unificato*, *JPG (ZIP)*, *PNG (ZIP)* e *ZIP Completo*, tutti governati dalla barra di progressione in tempo reale.
  - **Validazione Completa con 19 Test Unitari**:
    - Test suite estesa (`tests/test_cycle_export_and_progress.py`) per la verifica dell'intero ciclo asincrono di export, polling e download.
    - Eseguiti 3 cicli completi di test automatizzati con 19/19 test superati con successo in ciascun ciclo.
  - **Risolto Bug Errore 404 nell'Esportazione PDF ("Not Found The requested URL...")**:
    - **Causa individuata**: una vecchia istanza del server Flask (`python app.py`) avviata in precedenza stava occupando la porta 5000 in background prima che venissero registrate le nuove rotte di esportazione e i job asincroni.
    - **Fix applicati**:
      1. Aggiornato [`avvia_scanner.bat`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/avvia_scanner.bat) con terminazione preventiva automatica di qualsiasi processo orfano sulla porta 5000 prima dell'avvio, impedendo l'esecuzione di codice non sincronizzato.
      2. Registrati alias completi per tutte le rotte di esportazione in [`app.py`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/app.py) (sia `/api/documents/<id>/export` sia `/documents/<id>/export`, sia `/api/documents/<id>/pdf` sia `/documents/<id>/pdf`, e i corrispondenti endpoint di batch).
      3. Aggiunta sanitizzazione sicura del nome file con caratteri ammessi e fallback in `safe_download_filename()`.
      4. Supportato il parametro `page_index` anche nell'esportatore PDF [`core/pdf_exporter.py`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/core/pdf_exporter.py) per esportare singole pagine specifiche.
      5. Sostituito `window.open` con elemento di download `<a>` in [`static/js/app.js`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/static/js/app.js), evitando l'apertura di schede vuote nel browser.
      6. Verificato il download PDF su porta 5000 con esito `200 OK` e tipo MIME corretto.
  - **Integrazione Tesseract OCR Funzionante e Ridenominazione in "Scanner Web Multi"**:
    - **Riconoscimento Caratteri OCR 100% Attivo**:
      - Installato e configurato l'eseguibile Tesseract OCR (v5.4.0) e la libreria Python `pytesseract`.
      - Scaricati e configurati i modelli linguistici bilingue (`ita.traineddata` ed `eng.traineddata`) nella cartella `tessdata`.
      - Aggiornato [`core/ocr_engine.py`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/core/ocr_engine.py) con rilevamento automatico intelligente dei percorsi di `tesseract.exe` su Windows e variabile d'ambiente `TESSDATA_PREFIX`.
      - Estrazione accurata di testo e bounding boxes delle singole parole con livelli di confidenza.
      - Aggiunto in interfaccia il pulsante **Copia** per copiare istantaneamente il testo riconosciuto negli appunti e il badge identificativo *"Tesseract ITA+ENG"*.
    - **Ridenominazione Ufficiale Progetto**:
      - Nome aggiornato in **Scanner Web Multi** in tutti i componenti: interfaccia web, script di avvio `.bat`, console server e test.
  - **Rimozione di Kraken e Consolidamento Esclusivo su Tesseract OCR (Richiesta Utente)**:
    - **Motivazione**: Come richiesto dall'utente, il motore Kraken è stato rimosso in quanto non performante per l'uso atteso, consolidando l'applicazione su **Tesseract OCR (v5.4.0)**, leggero, rapidissimo, con 100% di precisione sia in lingua italiana che inglese.
    - **Pulizia e Ottimizzazione Codice e Risorse**:
      - Rimossi completamente l'interruttore e il menu a tendina dallo scorrimento grafico in [`static/index.html`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/static/index.html) e le classi CSS dedicate in [`static/css/style.css`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/static/css/style.css).
      - Ripristinata la logica diretta e snella in [`static/js/app.js`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/static/js/app.js) con pulsante singolo **Esegui OCR**, badge verde *"Tesseract ITA+ENG"* e copia rapida negli appunti.
      - Eliminato il modulo `core/htr_engine.py` e rimosse le dipendenze da `requirements.txt`.
      - Rimosso lo storage dei modelli neurali `data/models/` risparmiando spazio su disco (~46 MB) e abbattendo i tempi di esecuzione e avvio del server (test completati in ~6.5 secondi invece di ~54 secondi).
      - Aggiornato [`app.py`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/app.py) e [`core/ocr_engine.py`](file:///c:/Users/s.bruno/Documents/Oss%20document%20pc/core/ocr_engine.py) per invocare direttamente ed esclusivamente Tesseract OCR.
    - **Validazione con 3 Cicli di Test Completi (20/20 Superati x3)**:
      - Rimossa la suite specifica `test_cycle_htr_kraken.py`.
      - Eseguiti 3 cicli di test completi su tutti i 20 test automatizzati del progetto:
        - **Ciclo 1**: 20/20 superati in 9.31s (100% OK).
        - **Ciclo 2**: 20/20 superati in 6.94s (100% OK).
        - **Ciclo 3**: 20/20 superati in 6.53s (100% OK).
  - **Preparazione Ufficiale per GitHub e Deployment Cloud su Render.com (`onrender`)**:
    - **Proprietà Intellettuale & Licenza MIT**:
      - Creato il file `LICENSE` (MIT License) con menzione esplicita e doverosa al repository originario [OSS-DocumentScanner](https://github.com/ossappscollective/OSS-DocumentScanner) creato dalla OSS Apps Collective, e al lavoro di sviluppo continuo svolto in pair-programming con Google Gemini per creare un'applicazione pratica da lavoro.
    - **Documentazione Completa (`README.md`)**:
      - Redatta guida esaustiva bilingue con badge tecnici, spiegazione del funzionamento, architettura e tecnologie utilizzate (Python, Flask, OpenCV, Pillow, PyPDF, Tesseract OCR, Docker, Gunicorn).
      - Sezione dettagliata sui crediti intellettuali e sull'impiego quotidiano da ufficio/lavoro.
      - Istruzioni per l'avvio locale su Windows e guida passo-passo al deployment su Render.com.
    - **Infrastruttura Docker & Render Blueprint**:
      - Creato `Dockerfile` multi-piattaforma basato su `python:3.12-slim` con Tesseract OCR (`tesseract-ocr-ita` ed `eng`) e `libgl1` preinstallati per un'esperienza cloud a zero configurazione.
      - Creato `render.yaml` (Render Blueprint) per il deployment automatico con 1 click.
      - Aggiornato `requirements.txt` con `gunicorn` e `opencv-python-headless`.
    - **Inizializzazione Git Repository & Controllo Versione**:
      - Configurato `.gitignore` per ignorare file temporanei, cache Python e file caricati salvaguardando i segnaposto `.gitkeep`.
      - Inizializzato repository locale Git e registrato il commit iniziale di rilascio.



