#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narzędzie CLI do ręcznego oznaczania fraz z data/filtered_candidates.json

Funkcje:
- Wczytuje kandydatów z data/filtered_candidates.json
- Pozwala oznaczać frazy jako: G=GUEST, H=HOST, I=IGNORE, M=MAYBE
- Zapisuje wynik do data/feedback.json
- Pomija frazy już oznaczone wcześniej
- Obsługuje błędy i przerwania

Autor: System Podcast Trend
Data: 2025-08-03
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter
from maybe_similarity_engine import generate_similar_candidates_from_maybe


class LabelingTool:
    """Narzędzie do ręcznego oznaczania fraz."""
    
    def __init__(self, 
                 candidates_file: str = "data/filtered_candidates.json",
                 feedback_file: str = "data/feedback.json"):
        """
        Inicjalizuje narzędzie oznaczania.
        
        Args:
            candidates_file: Plik z kandydatami do oznaczenia
            feedback_file: Plik z zapisanymi oznaczeniami
        """
        self.candidates_file = Path(candidates_file)
        self.feedback_file = Path(feedback_file)
        
        # Mapowanie klawiszy na etykiety
        self.key_mappings = {
            'G': 'GUEST',
            'g': 'GUEST',
            'H': 'HOST',
            'h': 'HOST',
            'I': 'IGNORE',
            'i': 'IGNORE',
            'M': 'MAYBE',
            'm': 'MAYBE',
            '+': 'MAYBE_PLUS',  # M+ funkcja
            'Q': 'QUIT',
            'q': 'QUIT',
            'S': 'SKIP',
            's': 'SKIP'
        }
        
        # Statystyki
        self.stats = Counter()
        
    def load_candidates(self) -> List[str]:
        """
        Wczytuje kandydatów z pliku JSON.
        
        Returns:
            Lista fraz do oznaczenia
        """
        try:
            if not self.candidates_file.exists():
                print(f"❌ Plik {self.candidates_file} nie istnieje!")
                return []
            
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Wyciągnij frazy z różnych formatów
            phrases = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Format: {"phrase": "tekst", "source": "..."}
                        phrase = item.get('phrase', '')
                        if phrase.strip():
                            phrases.append(phrase.strip())
                    elif isinstance(item, str):
                        # Format: lista stringów
                        if item.strip():
                            phrases.append(item.strip())
            
            # Usuń duplikaty zachowując kolejność
            unique_phrases = []
            seen = set()
            for phrase in phrases:
                if phrase not in seen:
                    unique_phrases.append(phrase)
                    seen.add(phrase)
            
            print(f"✅ Wczytano {len(unique_phrases)} unikalnych kandydatów")
            return unique_phrases
            
        except json.JSONDecodeError as e:
            print(f"❌ Błąd parsowania JSON w {self.candidates_file}: {e}")
            return []
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania kandydatów: {e}")
            return []
    
    def load_existing_feedback(self) -> Set[str]:
        """
        Wczytuje już oznaczone frazy.
        
        Returns:
            Zbiór już oznaczonych fraz
        """
        try:
            if not self.feedback_file.exists():
                # Utwórz pusty plik feedback
                self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.feedback_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"✅ Utworzono pusty plik: {self.feedback_file}")
                return set()
            
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"⚠️  Nieprawidłowy format pliku {self.feedback_file}")
                return set()
            
            # Wyciągnij już oznaczone frazy
            labeled_phrases = set()
            for item in data:
                if isinstance(item, dict):
                    # Sprawdź różne klucze
                    phrase = item.get('text') or item.get('phrase', '')
                    if phrase.strip():
                        labeled_phrases.add(phrase.strip())
            
            print(f"✅ Znaleziono {len(labeled_phrases)} już oznaczonych fraz")
            return labeled_phrases
            
        except json.JSONDecodeError as e:
            print(f"❌ Błąd parsowania JSON w {self.feedback_file}: {e}")
            return set()
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania feedback: {e}")
            return set()
    
    def save_feedback(self, phrase: str, label: str) -> bool:
        """
        Zapisuje oznaczenie frazy do pliku feedback.
        
        Args:
            phrase: Fraza do zapisania
            label: Etykieta
            
        Returns:
            True jeśli udało się zapisać
        """
        try:
            # Wczytaj istniejące dane
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Dodaj nowe oznaczenie
            new_entry = {
                "text": phrase,
                "label": label,
                "source": "manual_cli"
            }
            
            data.append(new_entry)
            
            # Zapisz z powrotem
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania: {e}")
            return False
    
    def display_instructions(self) -> None:
        """Wyświetla instrukcje użytkowania."""
        print("\n" + "=" * 60)
        print("🏷️  NARZĘDZIE DO OZNACZANIA FRAZ")
        print("=" * 60)
        print("Instrukcje:")
        print("  G = GUEST     (gość podcastu)")
        print("  H = HOST      (prowadzący)")
        print("  I = IGNORE    (ignoruj, nieistotne)")
        print("  M = MAYBE     (może być nazwiskiem)")
        print("  + = M+ SMART  (MAYBE + generuj podobne)")
        print("  S = SKIP      (pomiń na razie)")
        print("  Q = QUIT      (zapisz i wyjdź)")
        print("=" * 60)
    
    def get_user_input(self, phrase: str, progress: str) -> str:
        """
        Pobiera oznaczenie od użytkownika.
        
        Args:
            phrase: Fraza do oznaczenia
            progress: Informacja o postępie
            
        Returns:
            Etykieta lub akcja
        """
        while True:
            print(f"\n{progress}")
            print(f"Fraza: \"{phrase}\"")
            print("Wybór [G/H/I/M/+/S/Q]: ", end="")
            
            try:
                user_input = input().strip()
                
                if not user_input:
                    print("⚠️  Proszę wpisać jedną z liter: G, H, I, M, +, S, Q")
                    continue
                
                # Obsługa klawisza "+"
                if user_input == '+':
                    key = '+'
                else:
                    key = user_input[0].upper()
                
                if key in self.key_mappings:
                    choice = self.key_mappings[key]
                    
                    if choice in ['QUIT', 'SKIP']:
                        return choice
                    
                    # Obsługa MAYBE_PLUS
                    if choice == 'MAYBE_PLUS':
                        print("🔮 MAYBE+ - zapisuję jako MAYBE i generuję podobne...")
                        return 'MAYBE_PLUS'
                    
                    # Potwierdzenie wyboru
                    confirmations = {
                        'GUEST': '👥 Gość',
                        'HOST': '🎤 Host/Prowadzący',
                        'IGNORE': '❌ Ignoruj',
                        'MAYBE': '❓ Może być nazwiskiem'
                    }
                    print(f"✅ Oznaczono jako: {confirmations[choice]}")
                    return choice
                else:
                    print("⚠️  Nieprawidłowy klawisz. Użyj: G, H, I, M, +, S, Q")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Przerwano przez użytkownika (Ctrl+C)")
                return 'QUIT'
            except EOFError:
                print("\n\n⚠️  Przerwano wejście (Ctrl+D)")
                return 'QUIT'
    
    def display_statistics(self) -> None:
        """Wyświetla statystyki oznaczania."""
        if not self.stats:
            return
        
        print("\n" + "=" * 50)
        print("📊 STATYSTYKI OZNACZANIA:")
        print("-" * 50)
        
        total = sum(self.stats.values())
        for label, count in self.stats.most_common():
            percentage = (count / total * 100) if total > 0 else 0
            
            icons = {
                'GUEST': '👥',
                'HOST': '🎤',
                'IGNORE': '❌',
                'MAYBE': '❓'
            }
            icon = icons.get(label, '📝')
            
            print(f"{icon} {label:8s}: {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n📊 ŁĄCZNIE OZNACZONO: {total}")
        print("=" * 50)
    
    def run(self) -> None:
        """Główna pętla narzędzia."""
        print("🚀 Uruchamiam narzędzie oznaczania...")
        
        # Wczytaj kandydatów
        candidates = self.load_candidates()
        if not candidates:
            print("❌ Brak kandydatów do oznaczenia!")
            return
        
        # Wczytaj już oznaczone
        labeled = self.load_existing_feedback()
        
        # Filtruj nieoznaczone
        unlabeled = [phrase for phrase in candidates if phrase not in labeled]
        
        if not unlabeled:
            print("🎉 Wszystkie frazy zostały już oznaczone!")
            return
        
        print(f"📋 Do oznaczenia: {len(unlabeled)} fraz (z {len(candidates)} łącznie)")
        
        # Wyświetl instrukcje
        self.display_instructions()
        
        # Główna pętla oznaczania
        try:
            for i, phrase in enumerate(unlabeled):
                progress = f"[{i+1}/{len(unlabeled)}]"
                
                action = self.get_user_input(phrase, progress)
                
                if action == 'QUIT':
                    print("\n💾 Zapisywanie i wyjście...")
                    break
                elif action == 'SKIP':
                    print("⏭️  Pominięto")
                    continue
                elif action == 'MAYBE_PLUS':
                    # Zapisz jako MAYBE
                    if self.save_feedback(phrase, 'MAYBE'):
                        self.stats['MAYBE'] += 1
                        print("💾 Zapisano jako MAYBE")
                        
                        # Uruchom generator podobnych kandydatów
                        print("🔮 Uruchamiam generator podobnych kandydatów...")
                        try:
                            new_suggestions = generate_similar_candidates_from_maybe()
                            if new_suggestions > 0:
                                print(f"✨ Wygenerowano {new_suggestions} nowych sugestii!")
                            else:
                                print("ℹ️ Brak nowych sugestii")
                        except Exception as e:
                            print(f"⚠️ Błąd generatora: {e}")
                    else:
                        print("❌ Błąd zapisu")
                else:
                    # Zapisz oznaczenie
                    if self.save_feedback(phrase, action):
                        self.stats[action] += 1
                        print("💾 Zapisano")
                    else:
                        print("❌ Błąd zapisu")
            
            # Wyświetl statystyki
            self.display_statistics()
            
        except Exception as e:
            print(f"\n❌ Nieoczekiwany błąd: {e}")
            print("💾 Próbuję zapisać dotychczasowy postęp...")
        
        print("\n🎉 Oznaczanie zakończone!")


def main():
    """Główna funkcja programu."""
    print("🏷️  NARZĘDZIE DO OZNACZANIA FRAZ")
    
    # Sprawdź argumenty
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("\nUżycie:")
            print("  python3 label.py                    # standardowe pliki")
            print("  python3 label.py --help             # ta pomoc")
            print("\nPliki:")
            print("  Wejście:  data/filtered_candidates.json")
            print("  Wyjście:  data/feedback.json")
            return
    
    # Uruchom narzędzie
    tool = LabelingTool()
    tool.run()


if __name__ == "__main__":
    main()