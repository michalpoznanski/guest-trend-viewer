import json
import os
import sys
import unicodedata
from typing import Dict, List, Set
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


def normalize_phrase(phrase: str) -> str:
    """
    Normalizuje frazę do porównywania:
    - usuwa białe znaki z początku i końca
    - zamienia na małe litery
    - zamienia wszelkie niewidoczne znaki (w tym zero-width space, soft hyphen)
    - normalizuje Unicode (unicodedata.normalize('NFC'))
    - zamienia powtarzające się spacje w środku na pojedynczą spację
    """
    if not phrase:
        return ""
    
    # Usuń białe znaki z początku i końca
    normalized = phrase.strip()
    
    # Zamień na małe litery
    normalized = normalized.lower()
    
    # Zamień niewidoczne znaki na spacje
    import re
    normalized = re.sub(r'[\u200B\u200C\u200D\uFEFF\u00AD\u200E\u200F]', ' ', normalized)
    
    # Normalizuj znaki Unicode (NFD -> NFC)
    normalized = unicodedata.normalize('NFC', normalized)
    
    # Zamień powtarzające się spacje na pojedynczą spację
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Usuń białe znaki z początku i końca ponownie
    normalized = normalized.strip()
    
    return normalized


def get_normalized_phrases(data: Dict[str, str]) -> Set[str]:
    """
    Zwraca zbiór znormalizowanych fraz z danych treningowych.
    """
    return {normalize_phrase(phrase) for phrase in data.keys()}


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
    Zwraca listę fraz z wartością "MAYBE", wykluczając frazy już oznaczone jako GUEST, HOST lub NO.
    Dodatkowo sprawdza podobne frazy i sugeruje parowanie.
    """
    data = load_training_data()
    maybe_phrases = []
    normalized_excluded = set()
    
    # Zbierz znormalizowane frazy już oznaczone (GUEST, HOST, NO)
    for phrase, value in data.items():
        if value in ["GUEST", "HOST", "NO"]:
            normalized_excluded.add(normalize_phrase(phrase))
    
    # Dodaj tylko frazy MAYBE, które nie są duplikatami już oznaczonych fraz
    for phrase, value in data.items():
        if value == "MAYBE":
            normalized_phrase = normalize_phrase(phrase)
            if normalized_phrase not in normalized_excluded:
                maybe_phrases.append(phrase)
    
    # Sprawdź czy są podobne frazy MAYBE, które można sparować
    maybe_pairs = get_maybe_pairs()
    if maybe_pairs:
        print(f"Znaleziono {len(maybe_pairs)} par fraz MAYBE do oceny:")
        for i, pair in enumerate(maybe_pairs[:3], 1):  # Pokaż pierwsze 3 pary
            print(f"  {i}. {pair['phrase1']} + {pair['phrase2']}")
        if len(maybe_pairs) > 3:
            print(f"  ... i {len(maybe_pairs) - 3} więcej par")
    
    # Debug: wypisz wszystkie warianty frazy "Kaczyński"
    debug_kaczynski_variants(data, maybe_phrases)
    
    return maybe_phrases


def debug_kaczynski_variants(data: Dict[str, str], maybe_phrases: List[str]):
    """
    Debug: wypisuje wszystkie warianty frazy "Kaczyński" w pliku feedback i kolejce do oznaczenia.
    """
    print("\n=== DEBUG: Warianty frazy 'Kaczyński' ===")
    
    # Znajdź wszystkie frazy zawierające "kaczy" (case insensitive)
    kaczynski_variants = []
    for phrase, value in data.items():
        if 'kaczy' in phrase.lower():
            normalized = normalize_phrase(phrase)
            kaczynski_variants.append({
                'original': phrase,
                'normalized': normalized,
                'value': value,
                'in_maybe_queue': phrase in maybe_phrases
            })
    
    print(f"Znaleziono {len(kaczynski_variants)} wariantów frazy 'Kaczyński':")
    for i, variant in enumerate(kaczynski_variants, 1):
        print(f"  {i}. Oryginalna: '{variant['original']}'")
        print(f"     Znormalizowana: '{variant['normalized']}'")
        print(f"     Status: {variant['value']}")
        print(f"     W kolejce MAYBE: {variant['in_maybe_queue']}")
        print()
    
    # Sprawdź czy są duplikaty po normalizacji
    normalized_versions = [v['normalized'] for v in kaczynski_variants]
    duplicates = set([x for x in normalized_versions if normalized_versions.count(x) > 1])
    if duplicates:
        print(f"DUPLIKATY po normalizacji: {duplicates}")
    else:
        print("Brak duplikatów po normalizacji")
    
    print("=== KONIEC DEBUG ===\n")


def get_maybe_pairs() -> List[Dict[str, str]]:
    """
    Zwraca pary fraz MAYBE do oceny. Najpierw z pliku data/maybe_pairs.json, jeśli istnieje, w przeciwnym razie generuje losowo.
    """
    import random
    pairs_path = os.path.join(BASE_DIR, "data", "maybe_pairs.json")
    if os.path.exists(pairs_path):
        try:
            with open(pairs_path, "r", encoding="utf-8") as f:
                pairs_data = json.load(f)
            # Filtrowanie: tylko pary, gdzie obie frazy są nadal MAYBE
            data = load_training_data()
            filtered = [p for p in pairs_data if data.get(p["phrase1"]) == "MAYBE" and data.get(p["phrase2"]) == "MAYBE"]
            return filtered
        except Exception:
            pass
    # Fallback: generuj losowo
    data = load_training_data()
    maybe_phrases = [phrase for phrase, value in data.items() if value == "MAYBE"]
    if len(maybe_phrases) < 2:
        return []
    pairs = []
    random.shuffle(maybe_phrases)
    for i in range(0, len(maybe_phrases) - 1, 2):
        pairs.append({
            "phrase1": maybe_phrases[i],
            "phrase2": maybe_phrases[i + 1]
        })
    if len(maybe_phrases) % 2 == 1:
        pairs.append({
            "phrase1": maybe_phrases[-1],
            "phrase2": maybe_phrases[0]
        })
    return pairs


def check_similar_phrases(phrase: str) -> List[str]:
    """
    Sprawdza czy istnieją podobne frazy w systemie.
    Zwraca listę fraz, które mogą być powiązane z daną frazą.
    """
    data = load_training_data()
    similar_phrases = []
    
    # Sprawdź czy fraza zawiera się w innych frazach lub inne frazy zawierają się w niej
    for existing_phrase, value in data.items():
        if existing_phrase != phrase:
            # Sprawdź czy frazy mają wspólne słowa
            phrase_words = set(normalize_phrase(phrase).split())
            existing_words = set(normalize_phrase(existing_phrase).split())
            
            if phrase_words & existing_words:  # Jeśli mają wspólne słowa
                similar_phrases.append(existing_phrase)
    
    return similar_phrases


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
        host_count = len([v for v in data.values() if v == "HOST"])
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
            "host_count": host_count,
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
            "host_count": 0,
            "no_count": 0,
            "maybe_count": 0,
            "new_phrases_info": ""
        })


@router.post("/annotate/update")
async def update_annotation(phrase: str = Form(...), value: str = Form(...)):
    """
    Aktualizuje oznaczenie frazy.
    Fraza natychmiast znika z listy do oznaczenia po zapisaniu.
    Automatycznie aktualizuje ranking po każdej adnotacji.
    Dodatkowo: po adnotacji GUEST/HOST/NO sprawdza podobne frazy MAYBE i dodaje pary do kolejki.
    """
    try:
        # Walidacja wartości
        if value not in ["GUEST", "HOST", "NO", "MAYBE"]:
            return {"success": False, "error": "Nieprawidłowa wartość"}
        
        # Wczytaj aktualne dane
        data = load_training_data()
        
        # Aktualizuj wartość
        data[phrase] = value
        
        # Zapisz dane
        if save_training_data(data):
            # Automatycznie aktualizuj ranking po każdej adnotacji
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from main import rebuild_guest_ranking_from_annotations
                rebuild_guest_ranking_from_annotations()
                print(f"Automatycznie zaktualizowano ranking po oznaczeniu '{phrase}' jako '{value}'")
            except Exception as e:
                print(f"Błąd podczas automatycznej aktualizacji rankingu: {e}")

            # --- NOWA LOGIKA: automatyczne parowanie podobnych fraz ---
            if value in ["GUEST", "HOST", "NO"]:
                similar = check_similar_phrases(phrase)
                # Zapisz pary do pliku (np. data/maybe_pairs.json)
                pairs_path = os.path.join(BASE_DIR, "data", "maybe_pairs.json")
                try:
                    if os.path.exists(pairs_path):
                        with open(pairs_path, "r", encoding="utf-8") as f:
                            pairs_data = json.load(f)
                    else:
                        pairs_data = []
                except Exception:
                    pairs_data = []
                # Zbierz już istniejące pary (jako set frozenset)
                existing_pairs = set(frozenset((p["phrase1"], p["phrase2"])) for p in pairs_data)
                # Dodaj nowe pary tylko dla fraz MAYBE
                for sim in similar:
                    if data.get(sim) == "MAYBE":
                        pair = frozenset((phrase, sim))
                        if pair not in existing_pairs:
                            pairs_data.append({"phrase1": phrase, "phrase2": sim})
                            existing_pairs.add(pair)
                # Zapisz zaktualizowane pary
                with open(pairs_path, "w", encoding="utf-8") as f:
                    json.dump(pairs_data, f, ensure_ascii=False, indent=2)
            
            # --- NOWA LOGIKA: automatyczne parowanie dla fraz MAYBE ---
            elif value == "MAYBE":
                print(f"DEBUG: Automatyczne parowanie dla MAYBE: {phrase}")
                similar = check_similar_phrases(phrase)
                # Zapisz pary do pliku (np. data/maybe_pairs.json)
                pairs_path = os.path.join(BASE_DIR, "data", "maybe_pairs.json")
                try:
                    if os.path.exists(pairs_path):
                        with open(pairs_path, "r", encoding="utf-8") as f:
                            pairs_data = json.load(f)
                    else:
                        pairs_data = []
                except Exception:
                    pairs_data = []
                # Zbierz już istniejące pary (jako set frozenset)
                existing_pairs = set(frozenset((p["phrase1"], p["phrase2"])) for p in pairs_data)
                # Dodaj nowe pary dla fraz MAYBE z podobnymi frazami MAYBE
                for sim in similar:
                    if data.get(sim) == "MAYBE":
                        print(f"DEBUG: Dodaję parę MAYBE: {phrase} + {sim}")
                        pair = frozenset((phrase, sim))
                        if pair not in existing_pairs:
                            pairs_data.append({"phrase1": phrase, "phrase2": sim})
                            existing_pairs.add(pair)
                # Zapisz zaktualizowane pary
                with open(pairs_path, "w", encoding="utf-8") as f:
                    json.dump(pairs_data, f, ensure_ascii=False, indent=2)

            # Pobierz zaktualizowane statystyki i listę fraz do oznaczenia
            updated_maybe_phrases = get_maybe_phrases()
            updated_stats = {
                "total_phrases": len(data),
                "guest_count": len([v for v in data.values() if v == "GUEST"]),
                "host_count": len([v for v in data.values() if v == "HOST"]),
                "no_count": len([v for v in data.values() if v == "NO"]),
                "maybe_count": len(updated_maybe_phrases)
            }
            
            return {
                "success": True, 
                "message": f"Zaktualizowano '{phrase}' na '{value}'",
                "stats": updated_stats,
                "remaining_phrases": updated_maybe_phrases,
                "force_reload": True  # Wymuś reload kolejki na frontendzie
            }
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
            "host": len([v for v in data.values() if v == "HOST"]),
            "no": len([v for v in data.values() if v == "NO"]),
            "maybe": len([v for v in data.values() if v == "MAYBE"])
        }
        return stats
    except Exception as e:
        return {"error": str(e)}


@router.get("/annotate/pairs")
async def get_maybe_pairs_endpoint():
    """
    Zwraca pary fraz MAYBE do oceny.
    """
    try:
        pairs = get_maybe_pairs()
        return {
            "success": True,
            "pairs": pairs,
            "total_pairs": len(pairs)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/annotate/pair-evaluate")
async def evaluate_pair(phrase1: str = Form(...), phrase2: str = Form(...), decision: str = Form(...)):
    """
    Ocenia parę fraz MAYBE.
    """
    try:
        # Walidacja decyzji
        if decision not in ["GUEST", "HOST", "NO", "MAYBE"]:
            return {"success": False, "error": "Nieprawidłowa decyzja"}
        
        # Wczytaj aktualne dane
        data = load_training_data()
        
        # Sprawdź czy frazy istnieją i mają status MAYBE
        if phrase1 not in data or phrase2 not in data:
            return {"success": False, "error": "Jedna z fraz nie istnieje"}
        
        if data[phrase1] != "MAYBE" or data[phrase2] != "MAYBE":
            return {"success": False, "error": "Jedna z fraz nie ma statusu MAYBE"}
        
        # Zastosuj decyzję do obu fraz
        data[phrase1] = decision
        data[phrase2] = decision
        
        # Zapisz dane
        if save_training_data(data):
            # Usuń parę z maybe_pairs.json jeśli istnieje i decyzja != MAYBE
            pairs_path = os.path.join(BASE_DIR, "data", "maybe_pairs.json")
            if decision in ["GUEST", "HOST", "NO"] and os.path.exists(pairs_path):
                try:
                    with open(pairs_path, "r", encoding="utf-8") as f:
                        pairs_data = json.load(f)
                    # Usuń parę (niezależnie od kolejności)
                    pairs_data = [p for p in pairs_data if not ((p["phrase1"] == phrase1 and p["phrase2"] == phrase2) or (p["phrase1"] == phrase2 and p["phrase2"] == phrase1))]
                    with open(pairs_path, "w", encoding="utf-8") as f:
                        json.dump(pairs_data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            # Automatycznie aktualizuj ranking jeśli decyzja to GUEST
            if decision == "GUEST":
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from main import rebuild_guest_ranking_from_annotations
                    rebuild_guest_ranking_from_annotations()
                    print(f"Automatycznie zaktualizowano ranking po ocenie pary: {phrase1} + {phrase2} = {decision}")
                except Exception as e:
                    print(f"Błąd podczas automatycznej aktualizacji rankingu: {e}")
            return {
                "success": True,
                "message": f"Oceniono parę: {phrase1} + {phrase2} = {decision}",
                "remaining_pairs": get_maybe_pairs()
            }
        else:
            return {"success": False, "error": "Błąd podczas zapisywania"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/annotate/similar/{phrase}")
async def get_similar_phrases(phrase: str):
    """
    Zwraca frazy podobne do podanej frazy.
    """
    try:
        similar = check_similar_phrases(phrase)
        return {
            "success": True,
            "phrase": phrase,
            "similar_phrases": similar,
            "count": len(similar)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/annotate/pairs-view", response_class=HTMLResponse)
async def maybe_pairs_view(request: Request):
    """
    Widok do oceny par fraz MAYBE.
    """
    try:
        return templates.TemplateResponse("maybe_pairs.html", {
            "request": request
        })
    except Exception as e:
        return templates.TemplateResponse("maybe_pairs.html", {
            "request": request,
            "error": str(e)
        })





@router.post("/annotate/add")
async def add_phrase(phrase: str = Form(...)):
    """
    Dodaje nową frazę do oznaczenia, sprawdzając duplikaty.
    """
    try:
        if not phrase.strip():
            return {"success": False, "error": "Fraza nie może być pusta"}
        
        # Wczytaj aktualne dane
        data = load_training_data()
        
        # Sprawdź czy fraza już istnieje (po normalizacji)
        normalized_new_phrase = normalize_phrase(phrase.strip())
        normalized_existing = get_normalized_phrases(data)
        
        if normalized_new_phrase in normalized_existing:
            return {"success": False, "error": f"Fraza '{phrase.strip()}' już istnieje w systemie (znormalizowana: '{normalized_new_phrase}')"}
        
        # Dodaj frazę z wartością MAYBE
        data[phrase.strip()] = "MAYBE"
        
        # Zapisz dane
        if save_training_data(data):
            return {"success": True, "message": f"Dodano frazę '{phrase.strip()}'"}
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