#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Set


def pre_filter_guests() -> None:
    """
    Preprocessuje dane gości z guest_trends.json i tworzy plik guest_candidates.csv
    z przefiltrowanymi kandydatami gotowymi do dalszej analizy ML.
    """
    
    # Ścieżki do plików
    trends_dir = Path("trends")
    input_file = trends_dir / "guest_trends.json"
    output_file = trends_dir / "guest_candidates.csv"
    
    # Lista słów do wykluczenia
    EXCLUDED_WORDS = {
        "Jak", "Dlaczego", "Co", "Czy", "To", "Kiedy", "Gdzie",
        "Kto", "Gdzie", "Dokąd", "Skąd", "Ile", "Który", "Jaki",
        "Jaka", "Jakie", "Ten", "Ta", "To", "Ci", "Te", "Tamten",
        "Tamta", "Tamto", "Ów", "Owa", "Owo", "Ówczesny", "Ówczesna"
    }
    
    # Znaki do wykluczenia
    EXCLUDED_CHARS = {'?', '!', ':', ';', '.', ',', '"', "'"}
    
    def is_valid_guest_name(name: str) -> bool:
        """
        Sprawdza czy nazwa gościa spełnia kryteria filtrowania.
        
        Args:
            name: Nazwa do sprawdzenia
            
        Returns:
            True jeśli nazwa spełnia kryteria, False w przeciwnym razie
        """
        # Sprawdź czy zawiera niedozwolone znaki
        if any(char in EXCLUDED_CHARS for char in name):
            return False
            
        # Podziel na słowa
        words = name.strip().split()
        
        # Sprawdź minimum 2 słowa
        if len(words) < 2:
            return False
            
        # Sprawdź każde słowo
        for word in words:
            # Sprawdź czy słowo zaczyna się wielką literą
            if not word or not word[0].isupper():
                return False
                
            # Sprawdź czy słowo nie jest w liście wykluczonych
            if word in EXCLUDED_WORDS:
                return False
                
            # Sprawdź czy słowo zawiera tylko litery, spacje i myślniki
            if not re.match(r'^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s\-]*$', word):
                return False
        
        return True
    
    def extract_unique_names(data: Dict) -> Set[str]:
        """
        Wyciąga wszystkie unikalne nazwy z danych guest_trends.json.
        
        Args:
            data: Słownik z danymi z guest_trends.json
            
        Returns:
            Zbiór unikalnych nazw
        """
        unique_names = set()
        
        for guest_name in data.keys():
            # Dodaj oryginalną nazwę
            unique_names.add(guest_name.strip())
            
            # Jeśli nazwa zawiera przecinki, podziel na części
            if ',' in guest_name:
                parts = [part.strip() for part in guest_name.split(',')]
                unique_names.update(parts)
        
        return unique_names
    
    try:
        # Wczytaj dane z JSON
        print(f"📖 Wczytywanie danych z {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            guest_data = json.load(f)
        
        print(f"✅ Wczytano {len(guest_data)} wpisów z guest_trends.json")
        
        # Wyciągnij unikalne nazwy
        print("🔍 Wyciąganie unikalnych nazw...")
        all_names = extract_unique_names(guest_data)
        print(f"📊 Znaleziono {len(all_names)} unikalnych nazw")
        
        # Filtruj nazwy
        print("🔧 Filtrowanie nazw według kryteriów...")
        filtered_names = []
        
        for name in all_names:
            if is_valid_guest_name(name):
                filtered_names.append(name)
        
        print(f"✅ Po filtrowaniu: {len(filtered_names)} kandydatów")
        
        # Utwórz DataFrame
        candidates_df = pd.DataFrame({
            'candidate': filtered_names,
            'is_guest': 'unknown'
        })
        
        # Sortuj alfabetycznie
        candidates_df = candidates_df.sort_values('candidate').reset_index(drop=True)
        
        # Zapisz do CSV
        print(f"💾 Zapisuję wyniki do {output_file}...")
        candidates_df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"✅ Zapisano {len(candidates_df)} kandydatów do {output_file}")
        
        # Wyświetl przykłady
        print("\n📋 Przykłady przefiltrowanych kandydatów:")
        for i, candidate in enumerate(candidates_df['candidate'].head(10)):
            print(f"  {i+1}. {candidate}")
        
        if len(candidates_df) > 10:
            print(f"  ... i {len(candidates_df) - 10} więcej")
            
    except FileNotFoundError:
        print(f"❌ Błąd: Plik {input_file} nie istnieje!")
        print("Upewnij się, że plik guest_trends.json znajduje się w katalogu trends/")
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON: {e}")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


def analyze_filtering_stats() -> None:
    """
    Analizuje statystyki filtrowania i wyświetla raport.
    """
    trends_dir = Path("trends")
    input_file = trends_dir / "guest_trends.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            guest_data = json.load(f)
        
        total_entries = len(guest_data)
        total_occurrences = sum(stats.get('total_count', 0) for stats in guest_data.values())
        
        print("📊 Statystyki danych wejściowych:")
        print(f"  • Liczba unikalnych wpisów: {total_entries}")
        print(f"  • Łączna liczba wystąpień: {total_occurrences}")
        
        # Sprawdź czy istnieje plik wynikowy
        output_file = trends_dir / "guest_candidates.csv"
        if output_file.exists():
            df = pd.read_csv(output_file)
            print(f"\n📊 Statystyki po filtrowaniu:")
            print(f"  • Liczba kandydatów: {len(df)}")
            print(f"  • Współczynnik filtrowania: {len(df)/total_entries*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Błąd analizy statystyk: {e}")


if __name__ == "__main__":
    print("🚀 Uruchamianie preprocessingu gości...")
    pre_filter_guests()
    print("\n" + "="*50)
    analyze_filtering_stats()
    print("\n✅ Preprocessing zakończony!") 