import json
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

# Dodaj ścieżkę do loader
sys.path.append(str(Path(__file__).parent.parent))
from loader.report_loader import get_latest_report


def extract_date_from_filename(df: pd.DataFrame) -> Optional[str]:
    """
    Próbuje wyciągnąć datę z nazwy pliku CSV
    
    Args:
        df: DataFrame z danymi
        
    Returns:
        Data w formacie YYYY-MM-DD lub None
    """
    try:
        # Sprawdź czy DataFrame ma atrybut _metadata z informacją o pliku
        if hasattr(df, '_metadata') and hasattr(df._metadata, 'filename'):
            filename = df._metadata.filename
        else:
            # Spróbuj znaleźć datę w nazwach kolumn lub danych
            return None
        
        # Wzorce dat w nazwach plików
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(\d{2}_\d{2}_\d{4})',  # MM_DD_YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                # Konwertuj różne formaty na YYYY-MM-DD
                if '_' in date_str:
                    date_str = date_str.replace('_', '-')
                
                # Sprawdź czy to format MM-DD-YYYY i przekonwertuj
                if re.match(r'\d{2}-\d{2}-\d{4}', date_str):
                    parts = date_str.split('-')
                    date_str = f"{parts[2]}-{parts[0]}-{parts[1]}"
                
                # Waliduj datę
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
                except ValueError:
                    continue
        
        return None
        
    except Exception:
        return None


def determine_data_date(df: pd.DataFrame) -> str:
    """
    Określa datę danych na podstawie różnych źródeł
    
    Args:
        df: DataFrame z danymi
        
    Returns:
        Data w formacie YYYY-MM-DD
    """
    # 1. Sprawdź czy istnieje kolumna report_date
    if 'report_date' in df.columns:
        try:
            # Pobierz pierwszą niepustą datę
            for date_val in df['report_date'].dropna():
                if pd.notna(date_val) and str(date_val).strip():
                    # Próbuj różne formaty daty
                    date_str = str(date_val).strip()
                    
                    # Jeśli to już format YYYY-MM-DD
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        return date_str
                    
                    # Próbuj przekonwertować z innych formatów
                    for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
        except Exception:
            pass
    
    # 2. Spróbuj wyciągnąć datę z nazwy pliku
    date_from_filename = extract_date_from_filename(df)
    if date_from_filename:
        return date_from_filename
    
    # 3. Użyj dzisiejszej daty
    return datetime.today().strftime('%Y-%m-%d')


def build_guest_summary_json(df: pd.DataFrame, ranked_data: List[Dict], output_folder: str) -> None:
    """
    Generuje plik JSON z podsumowaniem gości
    
    Args:
        df: DataFrame z danymi raportu
        ranked_data: Lista słowników z rankingiem gości
        output_folder: Folder do zapisu pliku
    """
    # Określ datę danych
    data_date = determine_data_date(df)
    
    # Przygotuj dane do zapisu
    summary_data = {
        "data_date": data_date,
        "guest_ranking": []
    }
    
    # Dodaj dane rankingowe
    for guest in ranked_data:
        guest_entry = {
            "name": guest.get('name', ''),
            "strength": round(float(guest.get('strength', 0)), 2),
            "total_views": int(guest.get('total_views', 0)),
            "mentions": int(guest.get('mentions', 0))
        }
        summary_data["guest_ranking"].append(guest_entry)
    
    # Utwórz folder jeśli nie istnieje
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Nazwa pliku wynikowego
    filename = f"guest_summary_{data_date}.json"
    file_path = output_path / filename
    
    # Zapisz plik JSON
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Zapisano plik: {file_path}")
        print(f"📊 Liczba gości w rankingu: {len(summary_data['guest_ranking'])}")
        print(f"📅 Data raportu: {data_date}")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania pliku: {e}")


def load_config() -> dict:
    """
    Wczytuje konfigurację z pliku config.json
    """
    config_path = Path('./config.json')
    if not config_path.exists():
        raise FileNotFoundError("Plik config.json nie został znaleziony")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    # Testowanie funkcji
    print("🧪 TESTOWANIE GENEROWANIA JSON")
    print("=" * 50)
    
    try:
        # Wczytaj najnowszy raport
        df = get_latest_report()
        print(f"✅ Wczytano raport z {len(df)} rekordami")
        
        # Wczytaj konfigurację
        config = load_config()
        output_folder = config['results_folder']
        print(f"📁 Folder wyników: {output_folder}")
        
    except Exception as e:
        print(f"❌ Błąd podczas wczytywania danych: {e}")
        print("Używam przykładowych danych...")
        
        # Przykładowe dane
        df = pd.DataFrame({
            'title': ['Podcast z Janem Kowalskim', 'Rozmowa z Kuba Wojewódzki'],
            'description': ['Wspaniała rozmowa z Janem Kowalskim', 'Kuba Wojewódzki opowiada'],
            'views': [1000, 5000],
            'report_date': ['2025-01-15', '2025-01-15']
        })
        
        output_folder = './data/analysis_results/'
    
    # Przykładowa lista ranked_data
    ranked_data = [
        {
            "name": "Jan Kowalski",
            "strength": 7500.0,
            "total_views": 120000,
            "mentions": 3
        },
        {
            "name": "Kuba Wojewódzki",
            "strength": 5000.0,
            "total_views": 80000,
            "mentions": 2
        },
        {
            "name": "Piotr Przywarski",
            "strength": 3000.0,
            "total_views": 45000,
            "mentions": 1
        }
    ]
    
    print(f"\n📝 Przykładowe dane rankingowe:")
    for i, guest in enumerate(ranked_data, 1):
        print(f"  {i}. {guest['name']} - Siła: {guest['strength']}")
    
    # Wygeneruj plik JSON
    print(f"\n🔄 Generuję plik JSON...")
    build_guest_summary_json(df, ranked_data, output_folder)
    
    print(f"\n🎉 Testowanie zakończone!") 