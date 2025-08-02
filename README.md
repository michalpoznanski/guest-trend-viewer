# Guest Trend Viewer

Prosta aplikacja FastAPI do wyświetlania trendów gości podcastów.

## 🚀 Uruchomienie lokalne

### Wymagania
- Python 3.11+
- pip

### Instalacja i uruchomienie

1. **Sklonuj repozytorium:**
```bash
git clone https://github.com/michalpoznanski/guest-trend-viewer.git
cd guest-trend-viewer
```

2. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

3. **Uruchom aplikację:**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Otwórz przeglądarkę:**
```
http://localhost:8000
```

## 🔧 Backend i analiza danych

### Struktura backend
```
backend/
├── store.py          # Zarządzanie danymi gości (JSON)
├── analyze.py        # Parser CSV/JSON do analizy
├── watchdog.py       # Monitorowanie folderu raportów
└── __init__.py       # Inicjalizacja modułu
```

### Jak uruchomić backend lokalnie

1. **Analiza danych:**
```bash
# Uruchom analizę z przykładowymi danymi
python3 backend/analyze.py

# Lub z konkretnym katalogiem raportów
python3 backend/analyze.py /path/to/reports
```

2. **Monitorowanie folderu raportów:**
```bash
# Uruchom watchdog (monitorowanie automatyczne)
python3 backend/watchdog.py

# Lub z konkretnym katalogiem
python3 backend/watchdog.py /path/to/reports
```

### Jak trenować dane

1. **Przygotuj pliki CSV** z raportami w folderze `/mnt/volume/reports/`
2. **Format plików:** `report_{KATEGORIA}_{YYYY-MM-DD}.csv`
3. **Wymagane kolumny:** `title`, `description`, `tags`, `views`, `video_type`
4. **Uruchom analizę:**
```bash
python3 backend/analyze.py
```

### Automatyczna analiza z folderu `/mnt/volume/reports/`

1. **Watchdog monitoruje** folder `/mnt/volume/reports/` w czasie rzeczywistym
2. **Gdy pojawi się nowy plik CSV:**
   - Automatycznie wyciąga nazwiska gości z pól `title`, `description`, `tags`
   - Oblicza siłę gościa na podstawie:
     - Wystąpień w różnych polach (title: 1.5x, description: 1.0x, tags: 0.5x)
     - Typu filmu (shorts: 0.5x, longs: 1.0x)
     - Wyświetleń (normalizacja)
   - Agreguje dane z wszystkich plików
   - Zapisuje ranking do `data/guest_trend_summary.json`
3. **Dane są automatycznie** wyświetlane na stronie głównej

### API Endpoints

- **`/`** - Główna strona z listą gości
- **`/api/guest-list`** - Lista gości w formacie JSON
- **`/api/stats`** - Statystyki gości w formacie JSON

## 🐳 Uruchomienie z Docker

```bash
# Build obrazu
docker build -t guest-trend-viewer .

# Uruchom kontener
docker run -p 8000:8000 guest-trend-viewer
```

## 📦 Deployment na Railway

### Automatyczny deployment
Aplikacja jest skonfigurowana do automatycznego deploymentu na Railway:

1. **Połącz repozytorium** z Railway
2. **Automatyczny build** - Railway użyje `railway.json`
3. **Automatyczny start** - aplikacja uruchomi się na porcie 8000

### Konfiguracja Railway
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`

### Triggerowanie redeploy
Każda zmiana w plikach frontendowych i backendowych automatycznie triggeruje redeploy na Railway.

## 📁 Struktura projektu

```
guest-trend-viewer/
├── main.py                    # Główna aplikacja FastAPI
├── requirements.txt           # Zależności Python
├── railway.json              # Konfiguracja Railway
├── Dockerfile                # Konfiguracja Docker
├── README.md                 # Ten plik
├── templates/                # Szablony HTML
│   └── index.html           # Główna strona z listą gości
├── static/                   # Pliki statyczne
│   └── style.css            # Style CSS
├── backend/                  # Moduły backendowe
│   ├── store.py             # Zarządzanie danymi gości
│   ├── analyze.py           # Parser CSV/JSON
│   ├── watchdog.py          # Monitorowanie folderu raportów
│   └── __init__.py          # Inicjalizacja modułu
└── data/                     # Dane aplikacji
    └── guest_trend_summary.json  # Ranking gości
```

## 🔧 Pliki konfiguracyjne

### `railway.json`
```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt"
  },
  "start": {
    "cmd": "uvicorn main:app --host 0.0.0.0 --port 8000"
  }
}
```

### `requirements.txt`
```
fastapi
jinja2
uvicorn
watchdog
pandas
```

### `Dockerfile`
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ✅ Weryfikacja deploymentu

Po wdrożeniu sprawdź:
1. **Strona się ładuje** bez błędów
2. **Tytuł** to "Guest Trend Viewer"
3. **Tekst** to "👋 Witaj w Guest Trend Viewer"
4. **Style** są zastosowane (jasnoszare tło, sans-serif czcionka)

## 🔄 Automatyczny redeploy

- **Frontend:** Każda zmiana w `main.py`, `templates/`, `static/` triggeruje redeploy
- **Backend:** Każda zmiana w `backend/` triggeruje redeploy
- **Konfiguracja:** Zmiany w `requirements.txt`, `railway.json`, `Dockerfile` triggerują redeploy

## 📞 Support

W przypadku problemów z deploymentem:
1. Sprawdź logi w Railway
2. Zweryfikuj konfigurację w `railway.json`
3. Upewnij się, że wszystkie pliki są zacommitowane
