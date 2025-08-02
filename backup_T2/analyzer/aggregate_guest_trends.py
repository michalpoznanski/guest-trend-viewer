import json
import glob
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def aggregate_guest_trends(input_folder: str, output_file: str) -> None:
    """
    Agreguje dane z wielu plików guest_summary_YYYY-MM-DD.json
    
    Args:
        input_folder: Folder z plikami JSON do agregacji
        output_file: Ścieżka do pliku wynikowego
    """
    print(f"🔄 AGREGACJA DANYCH Z FOLDERU: {input_folder}")
    print("=" * 50)
    
    # Sprawdź czy folder istnieje
    input_path = Path(input_folder)
    if not input_path.exists():
        print(f"❌ Folder {input_folder} nie istnieje!")
        return
    
    # Znajdź wszystkie pliki guest_summary_*.json
    pattern = str(input_path / "guest_summary_*.json")
    json_files = glob.glob(pattern)
    
    if not json_files:
        print(f"⚠️  Nie znaleziono plików guest_summary_*.json w {input_folder}")
        return
    
    print(f"📁 Znaleziono {len(json_files)} plików do agregacji")
    
    # Słownik do agregacji danych
    guest_data = defaultdict(lambda: {
        'total_strength': 0.0,
        'total_views': 0,
        'total_mentions': 0,
        'active_days': 0
    })
    
    # Przetwórz każdy plik
    processed_files = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sprawdź czy plik ma wymaganą strukturę
            if 'guest_ranking' not in data:
                print(f"⚠️  Pomijam {Path(json_file).name} - brak guest_ranking")
                continue
            
            # Przetwórz każdego gościa
            for guest in data['guest_ranking']:
                name = guest.get('name', '')
                if not name:
                    continue
                
                # Dodaj dane do agregacji
                guest_data[name]['total_strength'] += float(guest.get('strength', 0))
                guest_data[name]['total_views'] += int(guest.get('total_views', 0))
                guest_data[name]['total_mentions'] += int(guest.get('mentions', 0))
                guest_data[name]['active_days'] += 1
            
            processed_files += 1
            print(f"✅ Przetworzono: {Path(json_file).name}")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Błąd podczas przetwarzania {Path(json_file).name}: {e}")
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd w {Path(json_file).name}: {e}")
    
    if not guest_data:
        print("❌ Nie udało się przetworzyć żadnych danych!")
        return
    
    # Konwertuj na listę i posortuj
    aggregated_results = []
    for name, data in guest_data.items():
        aggregated_results.append({
            'name': name,
            'total_strength': round(data['total_strength'], 2),
            'total_views': data['total_views'],
            'total_mentions': data['total_mentions'],
            'active_days': data['active_days']
        })
    
    # Sortuj malejąco po total_strength
    aggregated_results.sort(key=lambda x: x['total_strength'], reverse=True)
    
    print(f"📊 Przetworzono {processed_files} plików")
    print(f"👥 Znaleziono {len(aggregated_results)} unikalnych gości")
    
    # Utwórz folder wynikowy jeśli nie istnieje
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Zapisz wynik
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Zapisano agregowane dane: {output_file}")
        print(f"📈 TOP 3 goście:")
        for i, guest in enumerate(aggregated_results[:3], 1):
            print(f"  {i}. {guest['name']} - Siła: {guest['total_strength']:.2f}, Dni: {guest['active_days']}")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania pliku: {e}")


def get_aggregated_stats(output_file: str) -> Dict[str, Any]:
    """
    Zwraca statystyki z agregowanych danych
    
    Args:
        output_file: Ścieżka do pliku z agregowanymi danymi
        
    Returns:
        Dict ze statystykami
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return {}
        
        total_guests = len(data)
        total_strength = sum(guest['total_strength'] for guest in data)
        total_views = sum(guest['total_views'] for guest in data)
        total_mentions = sum(guest['total_mentions'] for guest in data)
        avg_active_days = sum(guest['active_days'] for guest in data) / total_guests
        
        return {
            'total_guests': total_guests,
            'total_strength': round(total_strength, 2),
            'total_views': total_views,
            'total_mentions': total_mentions,
            'avg_active_days': round(avg_active_days, 2)
        }
        
    except Exception as e:
        print(f"❌ Błąd podczas odczytu statystyk: {e}")
        return {}


if __name__ == "__main__":
    # Przykładowe użycie
    input_folder = "./data/analysis_results/"
    output_file = "./data/aggregated/guest_trend_summary.json"
    
    aggregate_guest_trends(input_folder, output_file)
    
    # Wyświetl statystyki
    stats = get_aggregated_stats(output_file)
    if stats:
        print(f"\n📊 STATYSTYKI AGREGACJI:")
        print(f"   Łączna liczba gości: {stats['total_guests']}")
        print(f"   Łączna siła: {stats['total_strength']:.2f}")
        print(f"   Łączne wyświetlenia: {stats['total_views']:,}")
        print(f"   Łączne wystąpienia: {stats['total_mentions']}")
        print(f"   Średnia liczba aktywnych dni: {stats['avg_active_days']}") 