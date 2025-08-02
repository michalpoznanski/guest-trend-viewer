from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import json
from analysis.guest_trend_generator import generate_guest_summary_from_latest_report

app = FastAPI()

# Konfiguracja szablonów i plików statycznych
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def load_guest_data():
    """Ładuje dane gości z pliku guest_trend_summary.json"""
    try:
        file_path = os.path.join(BASE_DIR, "data", "guest_trend_summary.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"Błąd podczas ładowania danych: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Główna strona z tabelą gości"""
    guests = load_guest_data()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "guests": guests
    })

@app.get("/api/status")
def status():
    """Endpoint API zwracający status aplikacji"""
    return {"message": "Guest Trend Viewer is working!"}

if __name__ == "__main__":
    # Generuj dane gości przed uruchomieniem serwera
    try:
        print("Generowanie danych gości z najnowszego raportu...")
        generate_guest_summary_from_latest_report(
            report_dir="/mnt/volume/reports/",
            output_path="data/guest_trend_summary.json"
        )
        print("Dane gości zostały wygenerowane pomyślnie!")
    except Exception as e:
        print(f"Błąd podczas generowania danych gości: {e}")
        print("Aplikacja uruchomi się z istniejącymi danymi (jeśli istnieją)")
    
    port = int(os.environ.get("PORT", 8000))  # Railway ustawia PORT jako zmienną środowiskową
    uvicorn.run(app, host="0.0.0.0", port=port) 