import json
import os
import sys
from typing import Dict, List
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Dodaj ścieżkę do głównego katalogu projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Import funkcji do automatycznego wyłapywania fraz
try:
    from phrase_discovery import find_new_phrases_from_reports
except ImportError:
    print("Ostrzeżenie: Nie można zaimportować phrase_discovery")
    find_new_phrases_from_reports = None

# Router dla interfejsu feedback
router = APIRouter()

# Konfiguracja szablonów
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Ścieżka do pliku z danymi treningowymi
TRAINING_DATA_PATH = os.path.join(BASE_DIR, "data", "name_training_set.json")


def load_training_data() -> Dict[str, str]:
    """
    Wczytuje dane treningowe z pliku JSON.
    Tworzy plik jeśli nie istnieje.
    """
    try:
        if os.path.exists(TRAINING_DATA_PATH):
            with open(TRAINING_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Utwórz katalog jeśli nie istnieje
            os.makedirs(os.path.dirname(TRAINING_DATA_PATH), exist_ok=True)
            # Utwórz pusty plik z przykładowymi danymi
            initial_data = {
                "Kaczyński": "MAYBE",
                "Jarosław Kaczyński": "GUEST",
                "Podcast Show": "NO",
                "Anna Nowak": "GUEST",
                "Warsaw Studio": "NO"
            }
            save_training_data(initial_data)
            return initial_data
    except Exception as e:
        print(f"Błąd podczas wczytywania danych treningowych: {e}")
        return {}


def save_training_data(data: Dict[str, str]) -> bool:
    """
    Zapisuje dane treningowe do pliku JSON.
    """
    try:
        with open(TRAINING_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Błąd podczas zapisywania danych treningowych: {e}")
        return False


def get_maybe_phrases() -> List[str]:
    """
    Zwraca listę fraz z wartością "MAYBE".
    """
    data = load_training_data()
    return [phrase for phrase, value in data.items() if value == "MAYBE"]


def auto_discover_new_phrases():
    """
    Automatycznie wyłapuje nowe frazy z raportów CSV.
    """
    if find_new_phrases_from_reports:
        try:
            print("Automatyczne wyłapywanie nowych fraz...")
            stats = find_new_phrases_from_reports()
            print(f"Znaleziono {stats['new_phrases_added']} nowych fraz z {stats['files_processed']} plików.")
            return stats
        except Exception as e:
            print(f"Błąd podczas automatycznego wyłapywania fraz: {e}")
            return None
    return None


@router.get("/annotate", response_class=HTMLResponse)
async def annotate_interface(request: Request):
    """
    Interfejs do ręcznego oznaczania fraz.
    Automatycznie wyłapuje nowe frazy z raportów CSV.
    """
    try:
        # Automatycznie wyłapuj nowe frazy przed wyświetleniem interfejsu
        discovery_stats = auto_discover_new_phrases()
        
        # Pobierz frazy do oznaczenia (włącznie z nowo znalezionymi)
        maybe_phrases = get_maybe_phrases()
        
        # Pobierz statystyki
        data = load_training_data()
        total_phrases = len(data)
        guest_count = len([v for v in data.values() if v == "GUEST"])
        no_count = len([v for v in data.values() if v == "NO"])
        maybe_count = len(maybe_phrases)
        
        # Przygotuj informacje o nowych frazach
        new_phrases_info = ""
        if discovery_stats and discovery_stats['new_phrases_added'] > 0:
            new_phrases_info = f"Znaleziono {discovery_stats['new_phrases_added']} nowych fraz z {discovery_stats['files_processed']} plików."
        
        return templates.TemplateResponse("annotate.html", {
            "request": request,
            "phrases": maybe_phrases,
            "total_phrases": total_phrases,
            "guest_count": guest_count,
            "no_count": no_count,
            "maybe_count": maybe_count,
            "new_phrases_info": new_phrases_info
        })
    except Exception as e:
        return templates.TemplateResponse("annotate.html", {
            "request": request,
            "phrases": [],
            "error": str(e),
            "total_phrases": 0,
            "guest_count": 0,
            "no_count": 0,
            "maybe_count": 0,
            "new_phrases_info": ""
        })


@router.post("/annotate/update")
async def update_annotation(phrase: str = Form(...), value: str = Form(...)):
    """
    Aktualizuje oznaczenie frazy.
    """
    try:
        # Walidacja wartości
        if value not in ["GUEST", "NO", "MAYBE"]:
            return {"success": False, "error": "Nieprawidłowa wartość"}
        
        # Wczytaj aktualne dane
        data = load_training_data()
        
        # Aktualizuj wartość
        data[phrase] = value
        
        # Zapisz dane
        if save_training_data(data):
            return {"success": True, "message": f"Zaktualizowano '{phrase}' na '{value}'"}
        else:
            return {"success": False, "error": "Błąd podczas zapisywania"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/annotate/stats")
async def get_annotation_stats():
    """
    Zwraca statystyki oznaczeń.
    """
    try:
        data = load_training_data()
        stats = {
            "total": len(data),
            "guest": len([v for v in data.values() if v == "GUEST"]),
            "no": len([v for v in data.values() if v == "NO"]),
            "maybe": len([v for v in data.values() if v == "MAYBE"])
        }
        return stats
    except Exception as e:
        return {"error": str(e)}


@router.post("/annotate/add")
async def add_phrase(phrase: str = Form(...)):
    """
    Dodaje nową frazę do oznaczenia.
    """
    try:
        if not phrase.strip():
            return {"success": False, "error": "Fraza nie może być pusta"}
        
        # Wczytaj aktualne dane
        data = load_training_data()
        
        # Dodaj frazę z wartością MAYBE
        data[phrase.strip()] = "MAYBE"
        
        # Zapisz dane
        if save_training_data(data):
            return {"success": True, "message": f"Dodano frazę '{phrase}'"}
        else:
            return {"success": False, "error": "Błąd podczas zapisywania"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test funkcji
    print("Testowanie interfejsu feedback...")
    
    # Sprawdź czy plik istnieje
    if os.path.exists(TRAINING_DATA_PATH):
        print(f"Plik {TRAINING_DATA_PATH} istnieje")
    else:
        print(f"Tworzenie pliku {TRAINING_DATA_PATH}")
        load_training_data()
    
    # Wyświetl statystyki
    data = load_training_data()
    print(f"Łącznie fraz: {len(data)}")
    print(f"GUEST: {len([v for v in data.values() if v == 'GUEST'])}")
    print(f"NO: {len([v for v in data.values() if v == 'NO'])}")
    print(f"MAYBE: {len([v for v in data.values() if v == 'MAYBE'])}")
    
    # Wyświetl frazy MAYBE
    maybe_phrases = get_maybe_phrases()
    print(f"Frazy do oznaczenia: {maybe_phrases}") 