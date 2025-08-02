#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple


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


def load_guest_spikes(trends_dir: Path) -> pd.DataFrame:
    """
    Wczytuje dane skoków gości z pliku CSV.
    
    Args:
        trends_dir: Katalog z plikami trendów
        
    Returns:
        DataFrame z danymi skoków
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
    """
    input_file = trends_dir / "guest_spikes.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Plik {input_file} nie istnieje!")
    
    df = pd.read_csv(input_file)
    return df


def calculate_recommendation_score(total_count: int, has_spike: bool) -> int:
    """
    Oblicza punktację rekomendacji dla gościa.
    
    Args:
        total_count: Łączna liczba wystąpień
        has_spike: Czy gość ma skok popularności
        
    Returns:
        Liczba punktów rekomendacji
    """
    score = 0
    
    # +1 za skok popularności
    if has_spike:
        score += 1
    
    # +1 za total_count >= 10
    if total_count >= 10:
        score += 1
    
    # +1 za total_count >= 25
    if total_count >= 25:
        score += 1
    
    return score


def generate_guest_recommendations() -> None:
    """
    Główna funkcja do generowania rekomendacji gości.
    """
    
    trends_dir = Path("trends")
    output_file = trends_dir / "guest_recommendations.csv"
    
    try:
        print("🚀 Uruchamianie generowania rekomendacji gości...")
        
        # 1. Wczytaj przefiltrowane trendy
        print("📖 Wczytywanie przefiltrowanych trendów...")
        filtered_trends = load_filtered_trends(trends_dir)
        print(f"✅ Wczytano trendy dla {len(filtered_trends)} gości")
        
        # 2. Wczytaj dane skoków
        print("📈 Wczytywanie danych skoków...")
        spikes_df = load_guest_spikes(trends_dir)
        print(f"✅ Wczytano dane skoków dla {len(spikes_df)} gości")
        
        # 3. Przygotuj dane do analizy
        print("🔧 Przygotowywanie danych do analizy...")
        recommendations_data = []
        
        for guest_name, guest_data in filtered_trends.items():
            total_count = guest_data.get('total_count', 0)
            
            # Sprawdź czy gość ma skok
            spike_row = spikes_df[spikes_df['guest'] == guest_name]
            has_spike = False
            if not spike_row.empty:
                has_spike = spike_row.iloc[0]['spike']
            
            # Oblicz punktację
            score = calculate_recommendation_score(total_count, has_spike)
            
            recommendations_data.append({
                'guest': guest_name,
                'total_count': total_count,
                'spike': has_spike,
                'score': score
            })
        
        # 4. Utwórz DataFrame
        df = pd.DataFrame(recommendations_data)
        
        # 5. Sortuj wyniki
        df_sorted = df.sort_values(['score', 'total_count'], ascending=[False, False])
        
        # 6. Zapisz wyniki
        print(f"💾 Zapisuję rekomendacje do {output_file}...")
        df_sorted.to_csv(output_file, index=False, encoding='utf-8')
        
        # 7. Statystyki
        total_guests = len(df)
        high_score_guests = len(df[df['score'] >= 2])
        spike_guests = len(df[df['spike'] == True])
        popular_guests = len(df[df['total_count'] >= 10])
        
        print(f"\n📊 Statystyki rekomendacji:")
        print(f"  • Analizowanych gości: {total_guests}")
        print(f"  • Gości z wysoką punktacją (≥2): {high_score_guests}")
        print(f"  • Gości ze skokami: {spike_guests}")
        print(f"  • Popularnych gości (≥10 wystąpień): {popular_guests}")
        
        # 8. Top rekomendacje
        print(f"\n🏆 Top 10 rekomendowanych gości:")
        for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            spike_icon = "🔥" if row['spike'] else "📊"
            print(f"  {i:2d}. {row['guest']:<25} | Punkty: {row['score']} | Wystąpienia: {row['total_count']:3d} {spike_icon}")
        
        # 9. Analiza punktacji
        print(f"\n📈 Analiza punktacji:")
        score_counts = df['score'].value_counts().sort_index()
        for score, count in score_counts.items():
            percentage = (count / total_guests) * 100
            print(f"  • {score} punktów: {count} gości ({percentage:.1f}%)")
        
        print(f"\n✅ Generowanie rekomendacji zakończone pomyślnie!")
        print(f"📁 Plik: {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        print("Upewnij się, że pliki guest_trends_filtered.json i guest_spikes.csv istnieją w katalogu trends/")
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON: {e}")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


def analyze_recommendation_patterns() -> None:
    """
    Analizuje wzorce rekomendacji.
    """
    trends_dir = Path("trends")
    recommendations_file = trends_dir / "guest_recommendations.csv"
    
    if not recommendations_file.exists():
        print("❌ Plik guest_recommendations.csv nie istnieje!")
        return
    
    try:
        df = pd.read_csv(recommendations_file)
        
        print(f"\n🔍 Analiza wzorców rekomendacji:")
        
        # Goście z najwyższą punktacją
        top_scorers = df[df['score'] == df['score'].max()]
        print(f"\n🥇 Goście z najwyższą punktacją ({df['score'].max()} pkt):")
        for _, row in top_scorers.iterrows():
            spike_icon = "🔥" if row['spike'] else "📊"
            print(f"  • {row['guest']} ({row['total_count']} wystąpień) {spike_icon}")
        
        # Goście ze skokami ale niską popularnością
        spike_low_popular = df[(df['spike'] == True) & (df['total_count'] < 10)]
        if not spike_low_popular.empty:
            print(f"\n📈 Goście ze skokami ale niską popularnością:")
            for _, row in spike_low_popular.head(5).iterrows():
                print(f"  • {row['guest']} ({row['total_count']} wystąpień)")
        
        # Popularni goście bez skoków
        popular_no_spike = df[(df['spike'] == False) & (df['total_count'] >= 10)]
        if not popular_no_spike.empty:
            print(f"\n📊 Popularni goście bez skoków:")
            for _, row in popular_no_spike.head(5).iterrows():
                print(f"  • {row['guest']} ({row['total_count']} wystąpień)")
        
    except Exception as e:
        print(f"❌ Błąd analizy wzorców: {e}")


if __name__ == "__main__":
    generate_guest_recommendations()
    analyze_recommendation_patterns() 