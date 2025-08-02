#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


def load_filtered_trends(trends_dir: Path) -> Dict:
    """
    Wczytuje przefiltrowane trendy gości z pliku JSON.
    
    Args:
        trends_dir: Katalog z plikami trendów
        
    Returns:
        Słownik z przefiltrowanymi trendami gości
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
        json.JSONDecodeError: Jeśli plik ma nieprawidłowy format JSON
    """
    input_file = trends_dir / "guest_trends_filtered.json"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Plik {input_file} nie istnieje!")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        filtered_trends = json.load(f)
    
    return filtered_trends


def get_all_dates(filtered_trends: Dict) -> List[str]:
    """
    Zbiera wszystkie unikalne daty z trendów gości.
    
    Args:
        filtered_trends: Słownik z trendami gości
        
    Returns:
        Lista dat posortowana rosnąco
    """
    all_dates = set()
    
    for guest_data in filtered_trends.values():
        daily_counts = guest_data.get('daily_counts', {})
        all_dates.update(daily_counts.keys())
    
    return sorted(all_dates)


def calculate_spike_metrics(guest_name: str, guest_data: Dict, 
                          all_dates: List[str]) -> Dict:
    """
    Oblicza metryki skoku popularności dla gościa.
    
    Args:
        guest_name: Nazwa gościa
        guest_data: Dane trendu gościa
        all_dates: Lista wszystkich dostępnych dat
        
    Returns:
        Słownik z metrykami skoku
    """
    daily_counts = guest_data.get('daily_counts', {})
    
    # Dostosuj do dostępnych danych
    if len(all_dates) >= 4:
        # Ostatnie 2 dni
        last_2_dates = all_dates[-2:]
        count_last3 = sum(daily_counts.get(date, 0) for date in last_2_dates)
        
        # Poprzednie 2 dni
        prev_2_dates = all_dates[-4:-2]
        count_prev3 = sum(daily_counts.get(date, 0) for date in prev_2_dates)
    elif len(all_dates) >= 2:
        # Ostatni dzień
        last_1_date = all_dates[-1:]
        count_last3 = sum(daily_counts.get(date, 0) for date in last_1_date)
        
        # Poprzedni dzień
        prev_1_date = all_dates[-2:-1]
        count_prev3 = sum(daily_counts.get(date, 0) for date in prev_1_date)
    else:
        # Za mało danych
        return {
            'guest': guest_name,
            'count_last3': 0,
            'count_prev3': 0,
            'growth_abs': 0,
            'growth_pct': 0.0,
            'spike': False
        }
    
    # Oblicz wzrost
    growth_abs = count_last3 - count_prev3
    
    # Oblicz wzrost procentowy
    if count_prev3 > 0:
        growth_pct = (growth_abs / count_prev3) * 100
    else:
        growth_pct = 0.0
    
    # Sprawdź czy to skok (dostosowane do mniejszej ilości danych)
    is_spike = (growth_pct >= 50) or (count_last3 > 5)
    
    return {
        'guest': guest_name,
        'count_last3': count_last3,
        'count_prev3': count_prev3,
        'growth_abs': growth_abs,
        'growth_pct': round(growth_pct, 1),
        'spike': is_spike
    }


def detect_guest_spikes() -> None:
    """
    Główna funkcja do wykrywania skoków popularności gości.
    """
    
    trends_dir = Path("trends")
    output_file = trends_dir / "guest_spikes.csv"
    
    try:
        print("🚀 Uruchamianie wykrywania skoków popularności gości...")
        
        # 1. Wczytaj przefiltrowane trendy
        print("📖 Wczytywanie przefiltrowanych trendów...")
        filtered_trends = load_filtered_trends(trends_dir)
        print(f"✅ Wczytano trendy dla {len(filtered_trends)} gości")
        
        # 2. Zbierz wszystkie daty
        print("📅 Analizowanie dostępnych dat...")
        all_dates = get_all_dates(filtered_trends)
        print(f"✅ Znaleziono {len(all_dates)} dni: {', '.join(all_dates)}")
        
        # 3. Oblicz metryki dla każdego gościa
        print("🔢 Obliczanie metryk skoków...")
        spike_data = []
        
        for guest_name, guest_data in filtered_trends.items():
            metrics = calculate_spike_metrics(guest_name, guest_data, all_dates)
            spike_data.append(metrics)
        
        # 4. Utwórz DataFrame
        df = pd.DataFrame(spike_data)
        
        # 5. Filtruj tylko skoki
        spikes_df = df[df['spike'] == True].copy()
        
        # 6. Sortuj po wzroście procentowym malejąco
        spikes_df = spikes_df.sort_values('growth_pct', ascending=False)
        
        # 7. Zapisz wyniki
        print(f"💾 Zapisuję wyniki do {output_file}...")
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # 8. Statystyki
        total_guests = len(df)
        spike_count = len(spikes_df)
        
        print(f"\n📊 Statystyki wykrywania skoków:")
        print(f"  • Analizowanych gości: {total_guests}")
        print(f"  • Wykrytych skoków: {spike_count}")
        print(f"  • Współczynnik skoków: {spike_count/total_guests*100:.1f}%")
        
        # 9. Przykłady skoków
        if not spikes_df.empty:
            print(f"\n🔥 Top 5 największych skoków:")
            for i, (_, row) in enumerate(spikes_df.head().iterrows(), 1):
                print(f"  {i}. {row['guest']:<25} | Wzrost: {row['growth_pct']:>6.1f}% | Ostatnie 3 dni: {row['count_last3']:>2d}")
        else:
            print(f"\nℹ️  Nie wykryto żadnych skoków spełniających kryteria")
        
        # 10. Analiza wzrostów
        print(f"\n📈 Analiza wzrostów:")
        positive_growth = df[df['growth_abs'] > 0]
        negative_growth = df[df['growth_abs'] < 0]
        no_change = df[df['growth_abs'] == 0]
        
        print(f"  • Wzrosty: {len(positive_growth)}")
        print(f"  • Spadki: {len(negative_growth)}")
        print(f"  • Bez zmian: {len(no_change)}")
        
        if not positive_growth.empty:
            avg_growth = positive_growth['growth_pct'].mean()
            print(f"  • Średni wzrost: {avg_growth:.1f}%")
        
        print(f"\n✅ Wykrywanie skoków zakończone pomyślnie!")
        print(f"📁 Plik: {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        print("Upewnij się, że plik guest_trends_filtered.json istnieje w katalogu trends/")
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON: {e}")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


def analyze_spike_patterns() -> None:
    """
    Analizuje wzorce skoków popularności.
    """
    trends_dir = Path("trends")
    spikes_file = trends_dir / "guest_spikes.csv"
    
    if not spikes_file.exists():
        print("❌ Plik guest_spikes.csv nie istnieje!")
        return
    
    try:
        df = pd.read_csv(spikes_file)
        
        print(f"\n🔍 Analiza wzorców skoków:")
        
        # Największe skoki
        top_spikes = df.nlargest(5, 'growth_pct')
        print(f"\n🚀 Największe skoki procentowe:")
        for _, row in top_spikes.iterrows():
            print(f"  • {row['guest']}: {row['growth_pct']:.1f}% ({row['count_last3']} → {row['count_prev3']})")
        
        # Najwięcej wystąpień w ostatnich 3 dniach
        top_volume = df.nlargest(5, 'count_last3')
        print(f"\n📊 Najwięcej wystąpień w ostatnich 3 dniach:")
        for _, row in top_volume.iterrows():
            print(f"  • {row['guest']}: {row['count_last3']} wystąpień")
        
    except Exception as e:
        print(f"❌ Błąd analizy wzorców: {e}")


if __name__ == "__main__":
    detect_guest_spikes()
    analyze_spike_patterns() 