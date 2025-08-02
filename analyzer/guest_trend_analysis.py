import json
import glob
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime


def load_guest_summary_files(input_folder: str) -> List[Dict[str, Any]]:
    """
    Wczytuje wszystkie pliki guest_summary_*.json z folderu
    
    Args:
        input_folder: Folder z plikami JSON
        
    Returns:
        Lista słowników z danymi z każdego pliku
    """
    input_path = Path(input_folder)
    if not input_path.exists():
        print(f"❌ Folder {input_folder} nie istnieje!")
        return []
    
    # Znajdź wszystkie pliki guest_summary_*.json
    pattern = str(input_path / "guest_summary_*.json")
    json_files = glob.glob(pattern)
    
    if not json_files:
        print(f"⚠️  Nie znaleziono plików guest_summary_*.json w {input_folder}")
        return []
    
    print(f"📁 Znaleziono {len(json_files)} plików do analizy")
    
    loaded_data = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sprawdź czy plik ma wymaganą strukturę
            if 'data_date' not in data or 'guest_ranking' not in data:
                print(f"⚠️  Pomijam {Path(json_file).name} - nieprawidłowa struktura")
                continue
            
            loaded_data.append(data)
            print(f"✅ Wczytano: {Path(json_file).name} (data: {data['data_date']})")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Błąd podczas wczytywania {Path(json_file).name}: {e}")
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd w {Path(json_file).name}: {e}")
    
    return loaded_data


def build_guest_trends(loaded_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Buduje historię zmian siły gości w czasie
    
    Args:
        loaded_data: Lista danych z plików JSON
        
    Returns:
        Lista z historią trendów dla każdego gościa
    """
    # Sortuj dane po dacie
    sorted_data = sorted(loaded_data, key=lambda x: x['data_date'])
    
    # Słownik do zbierania danych o gościach
    guest_trends = defaultdict(lambda: {
        'daily_strength': {},
        'total_change': 0.0,
        'days_active': 0
    })
    
    # Przetwórz każdego gościa z każdego dnia
    for day_data in sorted_data:
        date = day_data['data_date']
        
        for guest in day_data['guest_ranking']:
            name = guest.get('name', '')
            strength = float(guest.get('strength', 0))
            
            if not name:
                continue
            
            # Dodaj siłę dla danego dnia
            guest_trends[name]['daily_strength'][date] = strength
            guest_trends[name]['days_active'] += 1
    
    # Oblicz total_change dla każdego gościa
    for name, trend_data in guest_trends.items():
        daily_strength = trend_data['daily_strength']
        
        if len(daily_strength) >= 2:
            # Sortuj daty
            sorted_dates = sorted(daily_strength.keys())
            first_strength = daily_strength[sorted_dates[0]]
            last_strength = daily_strength[sorted_dates[-1]]
            
            trend_data['total_change'] = round(last_strength - first_strength, 2)
        else:
            trend_data['total_change'] = 0.0
    
    # Konwertuj na listę i posortuj malejąco po total_change
    result = []
    for name, trend_data in guest_trends.items():
        result.append({
            'name': name,
            'daily_strength': trend_data['daily_strength'],
            'total_change': trend_data['total_change'],
            'days_active': trend_data['days_active']
        })
    
    # Sortuj malejąco po total_change
    result.sort(key=lambda x: x['total_change'], reverse=True)
    
    return result


def analyze_guest_trends(input_folder: str, output_file: str) -> None:
    """
    Główna funkcja analizy trendów gości
    
    Args:
        input_folder: Folder z plikami JSON
        output_file: Ścieżka do pliku wynikowego
    """
    print(f"📊 ANALIZA TRENDÓW GOŚCI")
    print("=" * 50)
    
    # 1. Wczytaj pliki
    loaded_data = load_guest_summary_files(input_folder)
    
    if not loaded_data:
        print("❌ Brak danych do analizy!")
        return
    
    # 2. Zbuduj trendy
    print(f"\n🔄 BUDOWANIE TRENDÓW...")
    guest_trends = build_guest_trends(loaded_data)
    
    print(f"✅ Przeanalizowano {len(guest_trends)} gości")
    
    # 3. Wyświetl podsumowanie
    print(f"\n📈 TOP 5 GOŚCI WG ZMIANY POPULARNOŚCI:")
    print("-" * 50)
    
    for i, guest in enumerate(guest_trends[:5], 1):
        change_symbol = "📈" if guest['total_change'] > 0 else "📉" if guest['total_change'] < 0 else "➡️"
        print(f"{i}. {guest['name']}")
        print(f"   {change_symbol} Zmiana: {guest['total_change']:+.2f}")
        print(f"   📅 Dni aktywności: {guest['days_active']}")
        
        # Pokaż pierwsze i ostatnie wartości
        daily_strength = guest['daily_strength']
        if len(daily_strength) >= 2:
            sorted_dates = sorted(daily_strength.keys())
            first_date = sorted_dates[0]
            last_date = sorted_dates[-1]
            first_strength = daily_strength[first_date]
            last_strength = daily_strength[last_date]
            print(f"   📊 {first_date}: {first_strength:.2f} → {last_date}: {last_strength:.2f}")
        print()
    
    # 4. Zapisz wynik
    print(f"💾 ZAPISYWANIE WYNIKÓW...")
    
    # Utwórz folder wynikowy jeśli nie istnieje
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(guest_trends, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Zapisano analizę trendów: {output_file}")
        
        # Statystyki
        total_guests = len(guest_trends)
        positive_changes = sum(1 for guest in guest_trends if guest['total_change'] > 0)
        negative_changes = sum(1 for guest in guest_trends if guest['total_change'] < 0)
        no_changes = sum(1 for guest in guest_trends if guest['total_change'] == 0)
        
        print(f"\n📊 STATYSTYKI TRENDÓW:")
        print(f"   Łączna liczba gości: {total_guests}")
        print(f"   📈 Wzrost popularności: {positive_changes}")
        print(f"   📉 Spadek popularności: {negative_changes}")
        print(f"   ➡️  Bez zmian: {no_changes}")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania pliku: {e}")


def get_trend_statistics(output_file: str) -> Dict[str, Any]:
    """
    Zwraca statystyki z analizy trendów
    
    Args:
        output_file: Ścieżka do pliku z analizą trendów
        
    Returns:
        Dict ze statystykami
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return {}
        
        total_guests = len(data)
        total_change = sum(guest['total_change'] for guest in data)
        avg_days_active = sum(guest['days_active'] for guest in data) / total_guests
        
        # Znajdź największy wzrost i spadek
        max_increase = max(data, key=lambda x: x['total_change'])
        max_decrease = min(data, key=lambda x: x['total_change'])
        
        return {
            'total_guests': total_guests,
            'total_change': round(total_change, 2),
            'avg_days_active': round(avg_days_active, 2),
            'max_increase': {
                'name': max_increase['name'],
                'change': max_increase['total_change']
            },
            'max_decrease': {
                'name': max_decrease['name'],
                'change': max_decrease['total_change']
            }
        }
        
    except Exception as e:
        print(f"❌ Błąd podczas odczytu statystyk: {e}")
        return {}


if __name__ == "__main__":
    # Przykładowe użycie
    input_folder = "./data/analysis_results/"
    output_file = "./data/aggregated/guest_trend_evolution.json"
    
    analyze_guest_trends(input_folder, output_file)
    
    # Wyświetl statystyki
    stats = get_trend_statistics(output_file)
    if stats:
        print(f"\n📊 SZCZEGÓŁOWE STATYSTYKI:")
        print(f"   Łączna liczba gości: {stats['total_guests']}")
        print(f"   Łączna zmiana popularności: {stats['total_change']:+.2f}")
        print(f"   Średnia liczba dni aktywności: {stats['avg_days_active']}")
        print(f"   📈 Największy wzrost: {stats['max_increase']['name']} (+{stats['max_increase']['change']:.2f})")
        print(f"   📉 Największy spadek: {stats['max_decrease']['name']} ({stats['max_decrease']['change']:+.2f})") 