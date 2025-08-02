#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set


def load_guest_trends(trends_dir: Path) -> Dict:
    """
    Wczytuje dane trendów gości z pliku JSON.
    
    Args:
        trends_dir: Katalog z plikami trendów
        
    Returns:
        Słownik z danymi trendów gości
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
        json.JSONDecodeError: Jeśli plik ma nieprawidłowy format JSON
    """
    input_file = trends_dir / "guest_trends.json"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Plik {input_file} nie istnieje!")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        guest_trends = json.load(f)
    
    return guest_trends


def load_ai_classified_guests(trends_dir: Path) -> Set[str]:
    """
    Wczytuje listę gości sklasyfikowanych przez AI jako "yes".
    
    Args:
        trends_dir: Katalog z plikami trendów
        
    Returns:
        Zbiór nazwisk gości zaakceptowanych przez AI
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
    """
    input_file = trends_dir / "guest_candidates_ai.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Plik {input_file} nie istnieje!")
    
    df = pd.read_csv(input_file)
    
    # Wybierz tylko tych z is_guest == "yes"
    accepted_guests = df[df['is_guest'] == 'yes']['candidate'].tolist()
    
    return set(accepted_guests)


def filter_guest_trends(guest_trends: Dict, accepted_guests: Set[str]) -> Dict:
    """
    Filtruje trendy gości, zostawiając tylko zaakceptowanych przez AI.
    
    Args:
        guest_trends: Oryginalny słownik z trendami gości
        accepted_guests: Zbiór nazwisk zaakceptowanych przez AI
        
    Returns:
        Przefiltrowany słownik z trendami gości
    """
    filtered_trends = {}
    
    for guest_name, trend_data in guest_trends.items():
        if guest_name in accepted_guests:
            filtered_trends[guest_name] = trend_data
    
    return filtered_trends


def save_filtered_trends(filtered_trends: Dict, trends_dir: Path) -> None:
    """
    Zapisuje przefiltrowane trendy do pliku JSON.
    
    Args:
        filtered_trends: Przefiltrowany słownik z trendami
        trends_dir: Katalog docelowy
    """
    output_file = trends_dir / "guest_trends_filtered.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_trends, f, indent=2, ensure_ascii=False)


def analyze_filtering_results(original_trends: Dict, filtered_trends: Dict, 
                            accepted_guests: Set[str]) -> None:
    """
    Analizuje i wyświetla wyniki filtrowania.
    
    Args:
        original_trends: Oryginalne trendy
        filtered_trends: Przefiltrowane trendy
        accepted_guests: Lista zaakceptowanych gości
    """
    original_count = len(original_trends)
    filtered_count = len(filtered_trends)
    accepted_count = len(accepted_guests)
    
    print(f"\n📊 Analiza wyników filtrowania:")
    print(f"  • Oryginalnych gości: {original_count}")
    print(f"  • Zaakceptowanych przez AI: {accepted_count}")
    print(f"  • Po filtrowaniu: {filtered_count}")
    print(f"  • Współczynnik filtrowania: {filtered_count/original_count*100:.1f}%")
    
    # Sprawdź czy wszystkie zaakceptowane nazwiska są w oryginalnych trendach
    missing_guests = accepted_guests - set(original_trends.keys())
    if missing_guests:
        print(f"\n⚠️  Ostrzeżenie: {len(missing_guests)} zaakceptowanych gości nie ma w trendach:")
        for guest in list(missing_guests)[:5]:  # Pokaż pierwsze 5
            print(f"    • {guest}")
        if len(missing_guests) > 5:
            print(f"    ... i {len(missing_guests) - 5} więcej")
    
    # Przykłady przefiltrowanych gości
    if filtered_trends:
        print(f"\n✅ Przykłady przefiltrowanych gości:")
        for i, (guest_name, trend_data) in enumerate(list(filtered_trends.items())[:5]):
            total_count = trend_data.get('total_count', 0)
            print(f"  {i+1}. {guest_name} (wystąpienia: {total_count})")


def filter_guest_trends_main() -> None:
    """
    Główna funkcja do filtrowania trendów gości.
    """
    trends_dir = Path("trends")
    
    try:
        print("🚀 Uruchamianie filtrowania trendów gości...")
        
        # 1. Wczytaj oryginalne trendy
        print("📖 Wczytywanie oryginalnych trendów...")
        guest_trends = load_guest_trends(trends_dir)
        print(f"✅ Wczytano trendy dla {len(guest_trends)} gości")
        
        # 2. Wczytaj listę zaakceptowanych gości
        print("🤖 Wczytywanie klasyfikacji AI...")
        accepted_guests = load_ai_classified_guests(trends_dir)
        print(f"✅ Zaakceptowano {len(accepted_guests)} gości przez AI")
        
        # 3. Filtruj trendy
        print("🔧 Filtrowanie trendów...")
        filtered_trends = filter_guest_trends(guest_trends, accepted_guests)
        print(f"✅ Przefiltrowano do {len(filtered_trends)} gości")
        
        # 4. Zapisz wynik
        print("💾 Zapisuję przefiltrowane trendy...")
        save_filtered_trends(filtered_trends, trends_dir)
        print("✅ Zapisano do trends/guest_trends_filtered.json")
        
        # 5. Analiza wyników
        analyze_filtering_results(guest_trends, filtered_trends, accepted_guests)
        
        print(f"\n✅ Filtrowanie trendów gości zakończone pomyślnie!")
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        print("Upewnij się, że pliki guest_trends.json i guest_candidates_ai.csv istnieją w katalogu trends/")
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON: {e}")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


if __name__ == "__main__":
    filter_guest_trends_main() 