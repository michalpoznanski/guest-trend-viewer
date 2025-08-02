import json
import os
import pandas as pd
from typing import Dict, List
from loader.report_loader import load_latest_podcast_report
from analysis.name_filter import is_likely_person


def generate_guest_summary_from_latest_report(report_dir: str = "/mnt/volume/reports/", output_path: str = "data/guest_trend_summary.json"):
    """
    Ładuje najnowszy raport z katalogu report_dir i generuje plik guest_trend_summary.json
    
    Args:
        report_dir (str): Ścieżka do katalogu z raportami
        output_path (str): Ścieżka do pliku wyjściowego JSON
        
    Returns:
        List[Dict]: Lista słowników z danymi gości
    """
    try:
        # 1. Wczytaj najnowszy raport
        print(f"Wczytywanie najnowszego raportu z: {report_dir}")
        df = load_latest_podcast_report(report_dir)
        
        # 2. Przefiltruj dane tylko z kategorii 'long' (jeśli kolumna video_type istnieje)
        if 'video_type' in df.columns:
            print("Filtrowanie danych tylko z kategorii 'long'")
            df = df[df['video_type'] == 'long']
            print(f"Po filtrowaniu: {len(df)} wierszy")
        else:
            print("Kolumna 'video_type' nie istnieje, używam wszystkich danych")
        
        # 3. Sprawdź czy kolumna 'guest' istnieje
        if 'guest' not in df.columns:
            raise ValueError("Kolumna 'guest' nie istnieje w raporcie")
        
        # 4. Filtruj nazwiska gości używając is_likely_person
        print("Filtrowanie nazwisk gości...")
        filtered_guest_stats = {}
        rejected_names = []
        
        for _, row in df.iterrows():
            guest_name = row['guest']
            views = row.get('views', 0)
            
            if pd.isna(guest_name) or guest_name == '':
                continue
            
            # Sprawdź czy nazwa wygląda na imię i nazwisko osoby
            is_person, reason = is_likely_person(guest_name)
            
            if is_person:
                if guest_name not in filtered_guest_stats:
                    filtered_guest_stats[guest_name] = {
                        'total_mentions': 0,
                        'total_views': 0
                    }
                
                filtered_guest_stats[guest_name]['total_mentions'] += 1
                filtered_guest_stats[guest_name]['total_views'] += int(views) if pd.notna(views) else 0
            else:
                rejected_names.append((guest_name, reason))
        
        # Wyświetl statystyki filtrowania
        print(f"Przefiltrowane nazwiska: {len(filtered_guest_stats)}")
        if rejected_names:
            print(f"Odrzucone nazwiska: {len(rejected_names)}")
            print("Przykłady odrzuconych nazwisk:")
            for name, reason in rejected_names[:5]:
                print(f"  - {name}: {reason}")
            if len(rejected_names) > 5:
                print(f"  ... i {len(rejected_names) - 5} więcej")
        
        guest_stats = filtered_guest_stats
        
        # 5. Konwertuj na listę słowników z wymaganymi kolumnami
        guests_list = []
        for guest_name, stats in guest_stats.items():
            strength = stats['total_views'] * stats['total_mentions']
            
            guest_data = {
                'name': guest_name,
                'type': 'Guest',
                'appearances': stats['total_mentions'],
                'total_views': stats['total_views'],
                'strength': strength
            }
            guests_list.append(guest_data)
        
        # 6. Posortuj malejąco po strength
        guests_list.sort(key=lambda x: x['strength'], reverse=True)
        
        # 7. Upewnij się, że katalog wyjściowy istnieje
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Utworzono katalog: {output_dir}")
        
        # 8. Zapisz do pliku JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(guests_list, f, ensure_ascii=False, indent=2)
        
        print(f"Zapisano dane {len(guests_list)} gości do: {output_path}")
        print(f"Top 5 gości według strength:")
        for i, guest in enumerate(guests_list[:5], 1):
            print(f"{i}. {guest['name']}: {guest['strength']:.2f} strength")
        
        return guests_list
        
    except Exception as e:
        print(f"Błąd podczas generowania podsumowania gości: {str(e)}")
        raise


if __name__ == "__main__":
    # Przykład użycia
    try:
        guests = generate_guest_summary_from_latest_report()
        print(f"\nPomyślnie wygenerowano podsumowanie dla {len(guests)} gości")
    except Exception as e:
        print(f"Błąd: {e}") 