#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
from pathlib import Path
from typing import List, Set


def classify_guest_candidate(candidate: str) -> str:
    """
    Klasyfikuje kandydata gościa na podstawie prostej heurystyki.
    
    Args:
        candidate: Nazwa kandydata do klasyfikacji
        
    Returns:
        "yes", "no" lub "unknown"
    """
    # Usuń białe znaki
    candidate = candidate.strip()
    
    # Sprawdź czy zawiera znaki interpunkcyjne lub pytajniki
    if any(char in candidate for char in ['?', '!', ':', ';', '.', ',']):
        return "no"
    
    # Podziel na słowa
    words = candidate.split()
    
    # Jeśli mniej niż 2 słowa
    if len(words) < 2:
        return "no"
    
    # Sprawdź czy dokładnie 2 słowa i oba zaczynają się wielką literą
    if len(words) == 2:
        if (words[0] and words[0][0].isupper() and 
            words[1] and words[1][0].isupper()):
            return "yes"
    
    # Sprawdź czy wygląda jak fragment zdania (zaczyna się od słów pytających)
    question_words = {
        "Jak", "Dlaczego", "Co", "Czy", "Kiedy", "Gdzie", "Kto", 
        "Dokąd", "Skąd", "Ile", "Który", "Jaki", "Jaka", "Jakie",
        "Ten", "Ta", "To", "Ci", "Te", "Tamten", "Tamta", "Tamto"
    }
    
    if words[0] in question_words:
        return "no"
    
    # Sprawdź czy wszystkie słowa zaczynają się wielką literą
    all_capitalized = all(word and word[0].isupper() for word in words)
    
    if all_capitalized:
        return "yes"
    
    # W przeciwnym razie nie jesteśmy pewni
    return "unknown"


def ai_tag_guests() -> None:
    """
    Główna funkcja do tagowania gości z użyciem AI heurystyki.
    """
    
    # Ścieżki do plików
    trends_dir = Path("trends")
    input_file = trends_dir / "guest_candidates.csv"
    output_file = trends_dir / "guest_candidates_ai.csv"
    
    try:
        # Wczytaj dane
        print(f"📖 Wczytywanie danych z {input_file}...")
        df = pd.read_csv(input_file)
        
        print(f"✅ Wczytano {len(df)} wierszy")
        
        # Usuń duplikaty z kolumny candidate
        print("🔧 Usuwanie duplikatów...")
        df_unique = df.drop_duplicates(subset=['candidate']).copy()
        print(f"📊 Po usunięciu duplikatów: {len(df_unique)} unikalnych kandydatów")
        
        # Klasyfikuj każdego kandydata
        print("🤖 Klasyfikowanie kandydatów...")
        classifications = []
        
        for candidate in df_unique['candidate']:
            classification = classify_guest_candidate(candidate)
            classifications.append(classification)
        
        # Dodaj klasyfikacje do DataFrame
        df_unique['is_guest'] = classifications
        
        # Zapisz wynik
        print(f"💾 Zapisuję wyniki do {output_file}...")
        df_unique.to_csv(output_file, index=False, encoding='utf-8')
        
        # Statystyki
        yes_count = (df_unique['is_guest'] == 'yes').sum()
        no_count = (df_unique['is_guest'] == 'no').sum()
        unknown_count = (df_unique['is_guest'] == 'unknown').sum()
        
        print(f"\n📊 Statystyki klasyfikacji:")
        print(f"  • Tak (yes): {yes_count}")
        print(f"  • Nie (no): {no_count}")
        print(f"  • Nieznane (unknown): {unknown_count}")
        
        # Przykłady dla każdej kategorii
        print(f"\n📋 Przykłady klasyfikacji:")
        
        print(f"\n✅ Tak (yes):")
        yes_examples = df_unique[df_unique['is_guest'] == 'yes']['candidate'].head(5).tolist()
        for example in yes_examples:
            print(f"  • {example}")
        
        print(f"\n❌ Nie (no):")
        no_examples = df_unique[df_unique['is_guest'] == 'no']['candidate'].head(5).tolist()
        for example in no_examples:
            print(f"  • {example}")
        
        print(f"\n❓ Nieznane (unknown):")
        unknown_examples = df_unique[df_unique['is_guest'] == 'unknown']['candidate'].head(5).tolist()
        for example in unknown_examples:
            print(f"  • {example}")
        
        print(f"\n✅ Zapisano plik guest_candidates_ai.csv z klasyfikacją")
        
    except FileNotFoundError:
        print(f"❌ Błąd: Plik {input_file} nie istnieje!")
        print("Upewnij się, że plik guest_candidates.csv znajduje się w katalogu trends/")
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")


if __name__ == "__main__":
    print("🚀 Uruchamianie AI tagowania gości...")
    ai_tag_guests()
    print("\n✅ AI tagowanie zakończone!") 