from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import json
from analysis.guest_trend_generator import generate_guest_summary_from_latest_report
from frontend.feedback_interface import router as feedback_router

# Import funkcji do automatycznego wyłapywania fraz
try:
    from phrase_discovery import find_new_phrases_from_reports
except ImportError:
    print("Ostrzeżenie: Nie można zaimportować phrase_discovery")
    find_new_phrases_from_reports = None

app = FastAPI()

# Konfiguracja szablonów i plików statycznych
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Dodaj router dla interfejsu feedback
app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])

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

def load_feedback_data():
    """Ładuje dane adnotacji z pliku name_training_set.json"""
    try:
        file_path = os.path.join(BASE_DIR, "data", "name_training_set.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        print(f"Błąd podczas ładowania danych adnotacji: {e}")
        return {}

def filter_guests_by_feedback(guests, feedback_data):
    """Filtruje listę gości na podstawie adnotacji - tylko GUEST"""
    if not feedback_data:
        return guests
    
    filtered_guests = []
    for guest in guests:
        guest_name = guest.get('name', '')
        if guest_name in feedback_data:
            # Tylko frazy oznaczone jako GUEST przechodzą przez filtr
            if feedback_data[guest_name] == "GUEST":
                filtered_guests.append(guest)
        else:
            # Frazy bez adnotacji są pomijane (nie są w rankingu)
            continue
    
    return filtered_guests


def get_maybe_phrases_count():
    """Zwraca liczbę fraz do oznaczenia (MAYBE)"""
    try:
        from frontend.feedback_interface import get_maybe_phrases
        maybe_phrases = get_maybe_phrases()
        return len(maybe_phrases)
    except Exception as e:
        print(f"Błąd podczas pobierania liczby fraz do oznaczenia: {e}")
        return 0

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Główna strona z tabelą gości - ranking nie jest filtrowany domyślnie"""
    guests = load_guest_data()
    maybe_count = get_maybe_phrases_count()
    
    # Załaduj dane adnotacji dla statystyk
    feedback_data = load_feedback_data()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "guests": guests,
        "maybe_count": maybe_count,
        "total_annotated": len(feedback_data),
        "guest_count": len([v for v in feedback_data.values() if v == "GUEST"]),
        "host_count": len([v for v in feedback_data.values() if v == "HOST"]),
        "no_count": len([v for v in feedback_data.values() if v == "NO"]),
        "maybe_count_annotated": len([v for v in feedback_data.values() if v == "MAYBE"])
    })

@app.get("/api/status")
def status():
    """Endpoint API zwracający status aplikacji"""
    return {"message": "Guest Trend Viewer is working!"}

@app.post("/api/update-ranking")
async def update_ranking():
    """Aktualizuje ranking na podstawie aktualnych adnotacji - tylko GUEST"""
    try:
        # Załaduj dane gości i adnotacji
        guests = load_guest_data()
        feedback_data = load_feedback_data()
        
        # Przefiltruj gości - tylko GUEST
        filtered_guests = filter_guests_by_feedback(guests, feedback_data)
        
        # Zwróć zaktualizowany ranking
        return {
            "success": True,
            "guests": filtered_guests,
            "total_guests": len(filtered_guests),
            "total_annotated": len(feedback_data),
            "guest_count": len([v for v in feedback_data.values() if v == "GUEST"]),
            "host_count": len([v for v in feedback_data.values() if v == "HOST"]),
            "no_count": len([v for v in feedback_data.values() if v == "NO"]),
            "maybe_count": len([v for v in feedback_data.values() if v == "MAYBE"])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/export-annotations")
async def export_annotations():
    """Eksportuje dane adnotacji do pobrania"""
    try:
        from fastapi.responses import FileResponse
        import tempfile
        
        feedback_data = load_feedback_data()
        
        # Utwórz tymczasowy plik z adnotacjami
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name
        
        # Zwróć plik do pobrania
        return FileResponse(
            path=temp_file_path,
            filename="annotations_export.json",
            media_type="application/json"
        )
    except Exception as e:
        return {"success": False, "error": str(e)}




if __name__ == "__main__":
    # Automatycznie wyłapuj nowe frazy przed uruchomieniem serwera
    if find_new_phrases_from_reports:
        try:
            print("Automatyczne wyłapywanie nowych fraz z raportów...")
            stats = find_new_phrases_from_reports()
            print(f"Znaleziono {stats['new_phrases_added']} nowych fraz z {stats['files_processed']} plików.")
        except Exception as e:
            print(f"Błąd podczas automatycznego wyłapywania fraz: {e}")
    
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