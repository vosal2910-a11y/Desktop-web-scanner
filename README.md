# Scanner Web Multi 📄🔍

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Headless-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract_OCR-5.4-blue?style=flat)](https://github.com/tesseract-ocr/tesseract)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Deploy%20on-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Scanner Web Multi** è una moderna applicazione web documentale e scanner avanzato, concepita per digitalizzare, raddrizzare, migliorare visivamente, estrarre testo con OCR e organizzare documenti cartacei, note, fatture, ricevute e contratti in maniera veloce, intuitiva e sicura.

---

## 💡 Scopo del Progetto & Genesi

**Scanner Web Multi** nasce dall'esigenza concreta di avere uno **strumento pratico e immediato per il lavoro d'ufficio e di studio quotidiano**:
- Permette di importare rapidamente pile di documenti sia tramite **Drag & Drop** che tramite la classica **finestra di selezione file al click**.
- Consente il **ritaglio prospettico a 4 angoli con lente di ingrandimento (loupe)** per raddrizzare fotografie di fogli inclinati o deformati.
- Integra potenti **filtri di miglioramento dell'immagine** (Magico, Bianco e Nero, Grigio, Contrasto) per sbiancare gli sfondi grigi o con ombre e rendere i testi nitidi e leggibili come copie originali.
- Include un motore **OCR completo basato su Tesseract v5** per convertire le immagini scansionate in testo digitale modificabile e ricercabile (con modelli italiano e inglese).
- Supporta l'**esportazione multi-formato (PDF, JPG, PNG, archivi ZIP)** completa di una **barra di avanzamento in tempo reale** per il monitoraggio dei file pesanti o delle elaborazioni di gruppo.

> 🤖 **Pair-Programming con Google Gemini**:  
> Il progetto è stato ideato, espanso, testato e perfezionato in sessione di pair-programming continuo con l'intelligenza artificiale **Google Gemini**, combinando standard ingegneristici solidi (test unitari, modularità, architettura Docker multi-piattaforma) e usabilità orientata all'esperienza utente.

---

## 🏛️ Proprietà Intellettuale & Crediti

Il presente software rispetta pienamente la proprietà intellettuale e la paternità del codice originario:

- **Progetto Originario di Riferimento**:  
  Derivato e sviluppato a partire da [**`OSS-DocumentScanner`**](https://github.com/ossappscollective/OSS-DocumentScanner), repository open source curato dalla [**OSS Apps Collective**](https://github.com/ossappscollective), rilasciato sotto licenza libera **MIT License** (Copyright © 2024 OSS Apps Collective).
- **Evoluzione in "Scanner Web Multi"**:  
  Il nucleo di base è stato trasformato in una piattaforma autonoma, espansa con:
  1. **Tesseract OCR nativo** (italiano ed inglese) integrato a livello di backend con autodetection e fallback pulito.
  2. **Interfaccia Drag-and-Drop + Click nativo** per una rapida selezione dei file.
  3. **Barra di avanzamento visuale e dinamica** per l'importazione e l'esportazione batch (PDF/ZIP/Immagini).
  4. **Esportazione flessibile** in formati **PDF multipagina**, **JPG ad alta fedeltà** e **PNG lossless**.
  5. **Compatibilità cloud istantanea per Render.com** tramite containerizzazione Docker e configurazione Blueprint `render.yaml`.
  6. **Suite di test automatizzati completa** per garantire affidabilità e non-regressione.

Tutti i diritti sul software originario appartengono ai rispettivi autori. Il presente progetto è rilasciato a sua volta sotto licenza **MIT** (vedere file [LICENSE](LICENSE)).

---

## 🚀 Tecnologie Utilizzate

### Backend & Core
- **Python 3.12**: Linguaggio principale, performante e pulito.
- **Flask**: Framework web leggero e flessibile per la gestione delle API REST e del routing.
- **Gunicorn**: Server WSGI di livello industriale per gestire connessioni concorrenti in ambiente di produzione cloud.
- **OpenCV (`opencv-python-headless`)**: Elaborazione d'immagine avanzata (rilevamento automatico bordi, trasformazione omografica prospettica, filtri colore e de-shading).
- **NumPy**: Operazioni su matrici di pixel e manipolazione geometrica ultra-rapida.
- **Pillow (PIL)** & **PyPDF**: Gestione di immagini bitmap e generazione/unione di documenti PDF multipagina ad alta risoluzione.
- **PyTesseract & Tesseract OCR v5**: Motore OCR allo stato dell'arte con dizionari `ita` ed `eng`.

### Frontend
- **HTML5 & CSS3 Responsive**: Layout moderno, pulito e funzionale sia su desktop che su tablet, con supporto tema chiaro/scuro.
- **JavaScript Moderno (ES6+)**: Gestione asincrona tramite `Fetch API`, rendering reattivo dei thumbnail e polling dello stato dei job di esportazione.
- **HTML5 Canvas Interattivo**: Tracciamento dei 4 vertici del documento con coordinate fisiche originali, zoom con lente d'ingrandimento e de-warp prospettico in tempo reale.

### DevOps & Cloud
- **Docker**: Immagine container basata su `python:3.12-slim` con Tesseract OCR preconfigurato.
- **Render.com (`onrender`)**: Compatibilità nativa sia come Web Service Docker sia come Render Blueprint.

---

## ✨ Funzionalità Chiave

| Funzionalità | Descrizione |
| :--- | :--- |
| 📥 **Importazione Flessibile** | Carica immagini (JPG, PNG, WebP) o documenti PDF sia trascinandoli (Drag & Drop) sia cliccando per aprire la finestra di esplorazione file. |
| 📐 **Raddrizzamento Prospettico** | Regola i 4 angoli del foglio con precisione sub-pixel grazie alla lente di ingrandimento interattiva. |
| 🎨 **Filtri di Ottimizzazione** | Scegli tra *Originale*, *Magico* (rimuove ombre e fa risaltare il bianco), *Bianco e Nero*, *Scala di Grigi* e *Colore*. |
| 🔠 **OCR Completo (Italiano/Inglese)** | Riconosci il testo contenuto nelle pagine con un click ed esportalo in formato `.txt`. |
| 📊 **Barra di Avanzamento Live** | Monitora in tempo reale il progresso sia durante l'importazione di grandi file sia durante l'esportazione batch. |
| 📦 **Esportazione Multi-formato** | Scarica i tuoi documenti scansionati come **PDF singolo o unito**, immagini **JPG**, immagini **PNG** trasparenti o pacchetti **ZIP**. |
| 📁 **Gestione Fascicoli & Cestino** | Organizza i documenti in categorie, cestina gli scarti e ripristina o elimina definitivamente con facilità. |

---

## 💻 Come Eseguire in Locale (Windows)

### 1. Avvio Rapido (con Python preinstallato)
1. Fai doppio clic sul file **`avvia_scanner.bat`** (oppure su `start.bat`).
2. Lo script installerà automaticamente le dipendenze da `requirements.txt` (se non presenti) e aprirà il browser predefinito all'indirizzo:
   ```text
   http://localhost:5000
   ```

### 2. Abilitare Tesseract OCR su Windows
Per il funzionamento dell'OCR anche sulla tua macchina locale Windows:
1. Scarica l'installer ufficiale di Tesseract per Windows da:  
   👉 [UB-Mannheim Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) (versione a 64 bit raccomandata).
2. Durante l'installazione, nella sezione **"Additional language data (download)"**, seleziona **Italian** (Italiano).
3. Scanner Web Multi cercherà automaticamente Tesseract nei percorsi standard di Windows (`C:\Program Files\Tesseract-OCR\tesseract.exe` o `AppData\Local\Programs\Tesseract-OCR`). Non è richiesta alcuna configurazione manuale di variabili d'ambiente.

---

## ☁️ Come Pubblicare su Render.com (`onrender`)

Scanner Web Multi è stato configurato per essere distribuito in pochi minuti su **Render** in modo gratuito o a basso costo, mantenendo Tesseract OCR perfettamente funzionante grazie al container Docker.

### Passo 1: Inizializzare e Caricare il Progetto su GitHub
1. Crea un nuovo repository sul tuo account [GitHub](https://github.com/new) (es. `scanner-web-multi`).
2. Nella cartella del progetto sul tuo PC, esegui i seguenti comandi:
   ```powershell
   git init
   git add .
   git commit -m "Primo rilascio Scanner Web Multi"
   git branch -M main
   git remote add origin https://github.com/<tuo-utente>/<tuo-repo>.git
   git push -u origin main
   ```

### Passo 2: Distribuzione su Render (Metodo Consigliato: Docker Web Service)
1. Accedi alla tua dashboard su [Render.com](https://dashboard.render.com/).
2. Clicca su **New +** e seleziona **Web Service**.
3. Collega il tuo repository GitHub appena creato.
4. Render rileverà automaticamente la presenza del **`Dockerfile`**:
   - **Name**: `scanner-web-multi`
   - **Language / Runtime**: `Docker`
   - **Region**: Francoforte (Frankfurt EU) o la regione più vicina
   - **Instance Type**: `Free` (o Starter)
5. Clicca su **Deploy Web Service**.
6. Render scaricherà l'immagine, installerà Tesseract OCR con i dizionari `ita+eng` e avvierà il server Gunicorn. Al termine, avrai un link pubblico HTTPS funzionante tipo:
   ```text
   https://scanner-web-multi.onrender.com
   ```

> 💡 **Nota sui Piani Gratuiti di Render**:  
> Sui piani gratuiti di Render i container possono andare in sospensione dopo 15 minuti di inattività. Al primo accesso successivo possono impiegare circa 30-50 secondi per riavviarsi. I documenti caricati risiedono nella memoria del container. Se desideri una persistenza a lungo termine tra un riavvio e l'altro, puoi associare un *Render Disk* alla cartella `/app/data`.

---

## 🧪 Esecuzione dei Test Automatizzati

Il progetto include una suite completa di 20 test di regressione che validano:
- API REST di gestione documenti, pagine e fascicoli.
- De-warping prospettico e trasformazioni matriciali OpenCV.
- Algoritmi di compressione ed esportazione PDF, ZIP, JPG e PNG.
- Gestione asincrona dei job con monitoraggio percentuale.
- Fallback e rilevamento del motore OCR Tesseract.

Per eseguire i test:
```powershell
python -m unittest discover -s tests -v
```

---

## 📂 Struttura del Repository

```text
├── app.py                  # Server Flask, routing API ed endpoint asincroni
├── core/                   # Moduli di logica di business e computer vision
│   ├── doc_manager.py      # Gestione archivio, cartelle e persistenza documenti
│   ├── scanner_cv.py       # Algoritmi OpenCV, rilevamento angoli e correzione prospettiva
│   ├── pdf_exporter.py     # Generatore di PDF, JPG, PNG e pacchetti ZIP
│   └── ocr_engine.py       # Integrazione Tesseract OCR (auto-detect Windows & Linux)
├── static/                 # Frontend (HTML, CSS, JavaScript, icone)
│   ├── index.html          # Interfaccia grafica utente a pagina singola
│   ├── css/style.css       # Fogli di stile responsive e moderni
│   └── js/app.js           # Logica canvas, drag-and-drop, gestione code ed export
├── tests/                  # Suite di test unitari e di integrazione
├── Dockerfile              # Immagine di produzione con Tesseract OCR per Render/Linux
├── render.yaml             # Blueprint per deploy con un click su Render.com
├── requirements.txt        # Dipendenze Python (Flask, OpenCV, PyPDF, Tesseract, Gunicorn)
├── avvia_scanner.bat       # Script di avvio rapido per Windows con auto-apertura browser
├── LICENSE                 # Licenza MIT con attribuzione a OSS Apps Collective e Gemini
└── README.md               # Documentazione completa e guida all'uso
```

---

## 📄 Licenza

Questo progetto è distribuito con licenza **MIT**.  
Consulta il file [LICENSE](LICENSE) per tutti i dettagli e i crediti legati al progetto d'origine *OSS-DocumentScanner* e al lavoro di sviluppo svolto.
