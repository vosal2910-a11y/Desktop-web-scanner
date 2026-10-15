# Scanner Web Multi - Dockerfile per deployment su Render.com o container Linux
FROM python:3.12-slim

# Evita la scrittura dei file .pyc e forza il flushing di stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Installazione dipendenze di sistema:
# - tesseract-ocr con pacchetti linguistici italiano e inglese
# - librerie grafiche di supporto per OpenCV (libgl1, libglib2.0-0)
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

# Copia dell'intero progetto
COPY . .

# Creazione delle cartelle dati persistenti
RUN mkdir -p /app/data/documents /app/data/trash

# Esposizione porta (Render assegna dinamicamente $PORT a runtime)
EXPOSE 5000

# Avvio con server WSGI di produzione Gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 app:app"]
