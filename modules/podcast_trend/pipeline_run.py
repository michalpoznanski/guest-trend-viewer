#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
from pathlib import Path
from typing import List, Tuple


def run_module(module_name: str, function_name: str) -> Tuple[bool, str]:
    """
    Uruchamia moduł i jego główną funkcję.
    
    Args:
        module_name: Nazwa modułu do uruchomienia
        function_name: Nazwa funkcji głównej do wywołania
        
    Returns:
        Krotka (sukces, komunikat)
    """
    try:
        # Import modułu
        module = __import__(module_name)
        
        # Sprawdź czy funkcja istnieje
        if hasattr(module, function_name):
            main_function = getattr(module, function_name)
            
            # Wywołaj funkcję główną
            print(f"\n{'='*60}")
            print(f"🚀 Uruchamianie: {module_name}")
            print(f"{'='*60}")
            
            main_function()
            
            return True, f"✅ {module_name} zakończony pomyślnie"
            
        else:
            return False, f"❌ Funkcja {function_name} nie istnieje w module {module_name}"
            
    except ImportError as e:
        return False, f"❌ Nie można zaimportować modułu {module_name}: {e}"
        
    except Exception as e:
        error_msg = f"❌ Błąd w module {module_name}: {e}"
        print(f"\n{error_msg}")
        print(f"Szczegóły błędu:")
        traceback.print_exc()
        return False, error_msg


def run_pipeline() -> None:
    """
    Główna funkcja uruchamiająca pipeline przetwarzania gości.
    """
    
    # Lista modułów do uruchomienia w kolejności
    pipeline_modules = [
        ("preprocess_guests", "pre_filter_guests"),
        ("ai_tag_guests", "ai_tag_guests"),
        ("filter_guest_trends", "filter_guest_trends_main"),
        ("plot_filtered_guest_trends", "plot_filtered_guest_trends_main")
    ]
    
    # Dodaj opcjonalne moduły (jeśli istnieją)
    optional_modules = [
        ("detect_guest_spikes", "main"),
        ("recommend_guests", "main")
    ]
    
    print("🎯 Uruchamianie pipeline'u przetwarzania gości podcastów")
    print("=" * 60)
    
    # Statystyki
    successful_modules = 0
    failed_modules = 0
    results = []
    
    # Uruchom główne moduły
    for module_name, function_name in pipeline_modules:
        success, message = run_module(module_name, function_name)
        results.append((module_name, success, message))
        
        if success:
            successful_modules += 1
        else:
            failed_modules += 1
    
    # Sprawdź i uruchom opcjonalne moduły
    print(f"\n{'='*60}")
    print("🔍 Sprawdzanie opcjonalnych modułów...")
    print(f"{'='*60}")
    
    for module_name, function_name in optional_modules:
        # Sprawdź czy plik modułu istnieje
        module_file = Path(f"{module_name}.py")
        if module_file.exists():
            success, message = run_module(module_name, function_name)
            results.append((module_name, success, message))
            
            if success:
                successful_modules += 1
            else:
                failed_modules += 1
        else:
            print(f"⚠️  Moduł {module_name} nie istnieje - pomijam")
            results.append((module_name, False, f"Plik {module_name}.py nie istnieje"))
    
    # Podsumowanie
    print(f"\n{'='*60}")
    print("📊 PODSUMOWANIE PIPELINE'U")
    print(f"{'='*60}")
    
    for module_name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {module_name}: {message}")
    
    print(f"\n📈 Statystyki:")
    print(f"  • Uruchomionych modułów: {len(results)}")
    print(f"  • Pomyślnie: {successful_modules}")
    print(f"  • Z błędami: {failed_modules}")
    print(f"  • Współczynnik sukcesu: {successful_modules/len(results)*100:.1f}%")
    
    # Sprawdź kluczowe pliki wynikowe
    print(f"\n📁 Sprawdzanie plików wynikowych:")
    trends_dir = Path("trends")
    
    key_files = [
        "guest_candidates.csv",
        "guest_candidates_ai.csv", 
        "guest_trends_filtered.json",
        "filtered_guest_trends_plot.png"
    ]
    
    for file_name in key_files:
        file_path = trends_dir / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} - brak")
    
    print(f"\n✅ Pipeline zakończony")


def main() -> None:
    """
    Funkcja główna.
    """
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print(f"\n⚠️  Pipeline przerwany przez użytkownika")
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd w pipeline: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 