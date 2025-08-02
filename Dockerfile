# Użyj oficjalnego obrazu Python
FROM python:3.11-slim

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki requirements i zainstaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj kod aplikacji
COPY . .

# Utwórz folder trends jeśli nie istnieje
RUN mkdir -p trends

# Utwórz folder static jeśli nie istnieje
RUN mkdir -p static

# Ustaw zmienne środowiskowe
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Otwórz port
EXPOSE 8000

# Uruchom aplikację
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 