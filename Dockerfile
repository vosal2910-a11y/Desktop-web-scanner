# Scanner Web Multi - Dockerfile ottimizzato per massima economia di risorse (Render.com 512MB RAM)
FROM python:3.12-slim

# Evita la scrittura dei file .pyc e forza il flushing di stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Ottimizzazione critica memoria glibc su Linux: impedisce la frammentazione heap con thread multipli
ENV MALLOC_ARENA_MAX=2

# Installazione dipendenze di sistema minime:
# - tesseract-ocr con modelli ita ed eng
# - librerie grafiche minime per OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ita \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e installazione requisiti Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del codice applicativo
COPY . .

# Creazione delle cartelle dati
RUN mkdir -p /app/data/documents /app/data/trash /app/data/exports

# Esposizione porta 10000 (predefinita di Render) e porta alternativa 5000
EXPOSE 10000 5000

# Avvio con Gunicorn ultra-ottimizzato per ambienti a memoria limitata (512MB RAM):
# - 1 worker e 2 threads per evitare concorrenza eccessiva sulla CPU
# - --max-requests 100 per riciclare periodicamente la memoria e azzerare memory leak
# - timeout esteso a 180s per tollerare elaborazioni batch
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 180 --max-requests 100 --max-requests-jitter 15 app:app"]
