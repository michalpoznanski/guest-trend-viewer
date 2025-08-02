#!/usr/bin/env python3
"""
Moduł do filtrowania kandydatów na dane treningowe
Pozostawia tylko frazy zawierające co najmniej dwa wyrazy
"""

import json
from pathlib import Path
from typing import List, Dict


def load_candidates(file_path: str) -> List[Dict]:
    """
    Wczytuje kandydatów z pliku JSON
    
    Args:
        file_path: Ścieżka do pliku z kandydatami
        
    Returns:
        Lista kandydatów
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        
        print(f"✅ Wczytano {len(candidates)} kandydatów z {file_path}")
        return candidates
        
    except FileNotFoundError:
        print(f"❌ Plik {file_path} nie istnieje!")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Błąd podczas parsowania JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        return []


def has_multiple_words(phrase: str) -> bool:
    """
    Sprawdza czy fraza zawiera co najmniej dwa wyrazy
    
    Args:
        phrase: Fraza do sprawdzenia
        
    Returns:
        True jeśli fraza ma co najmniej 2 wyrazy
    """
    if not phrase or not isinstance(phrase, str):
        return False
    
    # Podziel frazę na wyrazy (usuń nadmiarowe spacje)
    words = phrase.strip().split()
    
    # Sprawdź czy ma co najmniej 2 wyrazy
    return len(words) >= 2


def filter_candidates_by_word_count(candidates: List[Dict]) -> List[Dict]:
    """
    Filtruje kandydatów pozostawiając tylko te z co najmniej 2 wyrazami
    
    Args:
        candidates: Lista kandydatów do przefiltrowania
        
    Returns:
        Lista przefiltrowanych kandydatów
    """
    filtered_candidates = []
    
    for candidate in candidates:
        phrase = candidate.get('phrase', '')
        
        if has_multiple_words(phrase):
            filtered_candidates.append(candidate)
    
    return filtered_candidates


def save_filtered_candidates(candidates: List[Dict], output_path: str) -> bool:
    """
    Zapisuje przefiltrowanych kandydatów do pliku JSON
    
    Args:
        candidates: Lista kandydatów do zapisania
        output_path: Ścieżka do pliku wynikowego
        
    Returns:
        True jeśli zapisano pomyślnie
    """
    try:
        # Utwórz folder jeśli nie istnieje
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Zapisano {len(candidates)} przefiltrowanych kandydatów do {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania: {e}")
        return False


def show_filtering_statistics(original_count: int, filtered_count: int):
    """
    Wyświetla statystyki filtrowania
    
    Args:
        original_count: Liczba kandydatów przed filtrowaniem
        filtered_count: Liczba kandydatów po filtrowaniu
    """
    removed_count = original_count - filtered_count
    
    if original_count > 0:
        percentage_kept = (filtered_count / original_count) * 100
        percentage_removed = (removed_count / original_count) * 100
    else:
        percentage_kept = 0
        percentage_removed = 0
    
    print(f"\n📊 STATYSTYKI FILTROWANIA:")
    print("=" * 40)
    print(f"📋 Kandydatów oryginalnie:     {original_count:3d}")
    print(f"✅ Kandydatów zachowanych:     {filtered_count:3d} ({percentage_kept:.1f}%)")
    print(f"❌ Kandydatów usuniętych:      {removed_count:3d} ({percentage_removed:.1f}%)")


def show_examples(original_candidates: List[Dict], filtered_candidates: List[Dict]):
    """
    Pokazuje przykłady kandydatów przed i po filtrowaniu
    
    Args:
        original_candidates: Oryginalna lista kandydatów
        filtered_candidates: Przefiltrowana lista kandydatów
    """
    print(f"\n🎯 PRZYKŁADY ZACHOWANYCH KANDYDATÓW:")
    print("-" * 50)
    
    # Pokaż pierwsze 5 zachowanych kandydatów
    for i, candidate in enumerate(filtered_candidates[:5], 1):
        phrase = candidate.get('phrase', '')
        source = candidate.get('source', 'unknown')
        word_count = len(phrase.split())
        print(f"{i:2d}. \"{phrase}\" ({word_count} wyrazów, źródło: {source})")
    
    if len(filtered_candidates) > 5:
        print(f"    ... i {len(filtered_candidates) - 5} więcej")
    
    # Znajdź przykłady usuniętych kandydatów (jednwyrazowych)
    removed_examples = []
    for candidate in original_candidates:
        phrase = candidate.get('phrase', '')
        if not has_multiple_words(phrase) and len(removed_examples) < 5:
            removed_examples.append(candidate)
    
    if removed_examples:
        print(f"\n❌ PRZYKŁADY USUNIĘTYCH KANDYDATÓW (mniej niż 2 wyrazy):")
        print("-" * 50)
        for i, candidate in enumerate(removed_examples, 1):
            phrase = candidate.get('phrase', '')
            source = candidate.get('source', 'unknown')
            word_count = len(phrase.split())
            print(f"{i:2d}. \"{phrase}\" ({word_count} wyraz{'y' if word_count > 1 else ''}, źródło: {source})")


def main():
    """
    Główna funkcja filtrowania kandydatów
    """
    input_file = "data/feedback_candidates.json"
    output_file = "data/filtered_candidates.json"
    
    print("🔍 FILTROWANIE KANDYDATÓW NA DANE TRENINGOWE")
    print("=" * 60)
    print("Cel: Zachowanie tylko fraz z co najmniej 2 wyrazami")
    print("")
    
    # Wczytaj kandydatów
    original_candidates = load_candidates(input_file)
    
    if not original_candidates:
        print("❌ Brak kandydatów do przefiltrowania")
        return
    
    # Przefiltruj kandydatów
    print("🔄 Filtrowanie kandydatów...")
    filtered_candidates = filter_candidates_by_word_count(original_candidates)
    
    # Zapisz przefiltrowanych kandydatów
    if save_filtered_candidates(filtered_candidates, output_file):
        # Wyświetl statystyki
        show_filtering_statistics(len(original_candidates), len(filtered_candidates))
        
        # Pokaż przykłady
        show_examples(original_candidates, filtered_candidates)
        
        print(f"\n🎉 FILTROWANIE ZAKOŃCZONE POMYŚLNIE!")
        print(f"📁 Przefiltrowane dane dostępne w: {output_file}")
    else:
        print(f"\n❌ Filtrowanie nie powiodło się")


if __name__ == "__main__":
    main()