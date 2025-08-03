#!/usr/bin/env python3
import sys
import os

# Dodaj ścieżkę do głównego katalogu projektu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from frontend.feedback_interface import load_training_data, get_maybe_phrases, debug_kaczynski_variants

# Test debug wariantów frazy "Kaczyński"
print("Test debug wariantów frazy 'Kaczyński'...")

# Wczytaj dane
data = load_training_data()
maybe_phrases = get_maybe_phrases()

print(f"Łącznie fraz w danych: {len(data)}")
print(f"Frazy do oznaczenia (MAYBE): {len(maybe_phrases)}")

# Ręcznie wywołaj debug
debug_kaczynski_variants(data, maybe_phrases) 