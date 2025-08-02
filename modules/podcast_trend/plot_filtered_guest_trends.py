#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


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


def get_top_guests(filtered_trends: Dict, top_n: int = 10) -> List[Tuple[str, Dict]]:
    """
    Wybiera top N gości z najwyższą liczbą total_count.
    
    Args:
        filtered_trends: Słownik z trendami gości
        top_n: Liczba top gości do wybrania
        
    Returns:
        Lista krotek (nazwa_gościa, dane_trendu) posortowana malejąco po total_count
    """
    # Sortuj gości po total_count malejąco
    sorted_guests = sorted(
        filtered_trends.items(),
        key=lambda x: x[1].get('total_count', 0),
        reverse=True
    )
    
    return sorted_guests[:top_n]


def prepare_plot_data(top_guests: List[Tuple[str, Dict]]) -> Tuple[List, List, List]:
    """
    Przygotowuje dane do wykresu.
    
    Args:
        top_guests: Lista top gości z ich danymi
        
    Returns:
        Krotka (daty, wartości, nazwy_gości)
    """
    all_dates = set()
    guest_data = {}
    
    # Zbierz wszystkie unikalne daty
    for guest_name, trend_data in top_guests:
        daily_counts = trend_data.get('daily_counts', {})
        all_dates.update(daily_counts.keys())
        guest_data[guest_name] = daily_counts
    
    # Sortuj daty
    sorted_dates = sorted(all_dates)
    
    # Przygotuj dane dla każdego gościa
    plot_data = []
    guest_names = []
    
    for guest_name, daily_counts in guest_data.items():
        values = [daily_counts.get(date, 0) for date in sorted_dates]
        plot_data.append(values)
        guest_names.append(guest_name)
    
    return sorted_dates, plot_data, guest_names


def create_trend_plot(dates: List[str], plot_data: List[List], 
                     guest_names: List[str], output_file: Path) -> None:
    """
    Tworzy wykres trendów gości.
    
    Args:
        dates: Lista dat
        plot_data: Lista list z wartościami dla każdego gościa
        guest_names: Lista nazw gości
        output_file: Ścieżka do pliku wynikowego
    """
    # Konfiguracja stylu
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (14, 8)
    plt.rcParams['font.size'] = 10
    
    # Konwertuj daty na obiekty datetime
    date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
    
    # Twórz wykres
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Import numpy dla kolorów
    import numpy as np
    
    # Kolory dla linii
    colors = plt.cm.Set3(np.linspace(0, 1, len(guest_names)))
    
    # Rysuj linie dla każdego gościa
    for i, (guest_name, values, color) in enumerate(zip(guest_names, plot_data, colors)):
        ax.plot(date_objects, values, 
                marker='o', 
                linewidth=2, 
                markersize=6,
                color=color,
                label=guest_name,
                alpha=0.8)
    
    # Konfiguracja osi
    ax.set_xlabel('Data', fontsize=12, fontweight='bold')
    ax.set_ylabel('Liczba wystąpień', fontsize=12, fontweight='bold')
    ax.set_title('Trendy popularności top 10 gości podcastów', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Formatowanie osi X (daty)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Siatka
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Legenda
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
             fontsize=10, framealpha=0.9)
    
    # Dostosuj układ
    plt.tight_layout()
    
    # Zapisz wykres
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"✅ Wykres zapisany do {output_file}")


def analyze_top_guests(top_guests: List[Tuple[str, Dict]]) -> None:
    """
    Analizuje i wyświetla informacje o top gościach.
    
    Args:
        top_guests: Lista top gości z ich danymi
    """
    print(f"\n📊 Analiza top {len(top_guests)} gości:")
    
    for i, (guest_name, trend_data) in enumerate(top_guests, 1):
        total_count = trend_data.get('total_count', 0)
        daily_counts = trend_data.get('daily_counts', {})
        days_active = len(daily_counts)
        
        print(f"  {i:2d}. {guest_name:<25} | Wystąpienia: {total_count:3d} | Dni aktywny: {days_active}")
        
        # Pokaż najwyższe dzienne wystąpienia
        if daily_counts:
            max_daily = max(daily_counts.values())
            max_date = max(daily_counts.items(), key=lambda x: x[1])[0]
            print(f"       └─ Najwyższe dzienne: {max_daily} ({max_date})")


def plot_filtered_guest_trends_main() -> None:
    """
    Główna funkcja do tworzenia wykresu trendów przefiltrowanych gości.
    """
    trends_dir = Path("trends")
    output_file = trends_dir / "filtered_guest_trends_plot.png"
    
    try:
        print("🚀 Uruchamianie tworzenia wykresu trendów gości...")
        
        # 1. Wczytaj przefiltrowane trendy
        print("📖 Wczytywanie przefiltrowanych trendów...")
        filtered_trends = load_filtered_trends(trends_dir)
        print(f"✅ Wczytano trendy dla {len(filtered_trends)} gości")
        
        # 2. Wybierz top 10 gości
        print("🏆 Wybieranie top 10 gości...")
        top_guests = get_top_guests(filtered_trends, top_n=10)
        print(f"✅ Wybrano {len(top_guests)} gości")
        
        # 3. Analiza top gości
        analyze_top_guests(top_guests)
        
        # 4. Przygotuj dane do wykresu
        print("📊 Przygotowywanie danych do wykresu...")
        dates, plot_data, guest_names = prepare_plot_data(top_guests)
        print(f"✅ Przygotowano dane dla {len(dates)} dni")
        
        # 5. Utwórz wykres
        print("🎨 Tworzenie wykresu...")
        create_trend_plot(dates, plot_data, guest_names, output_file)
        
        print(f"\n✅ Wykres trendów gości został utworzony pomyślnie!")
        print(f"📁 Plik: {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        print("Upewnij się, że plik guest_trends_filtered.json istnieje w katalogu trends/")
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON: {e}")
        
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        print("Upewnij się, że biblioteka matplotlib jest zainstalowana:")
        print("pip install matplotlib")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


if __name__ == "__main__":
    # Import numpy dla kolorów
    import numpy as np
    
    plot_filtered_guest_trends_main() 