#!/usr/bin/env python3
"""
Moduł do interaktywnego oznaczania kandydatów na dane treningowe
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from .maybe_engine import MaybeEngine


class InteractiveFeedbackHandler:
    """
    Klasa do interaktywnego oznaczania fraz przez użytkownika
    """
    
    def __init__(self, 
                 candidates_file: str = "data/filtered_candidates.json",
                 feedback_file: str = "data/feedback.json"):
        """
        Inicjalizacja
        
        Args:
            candidates_file: Plik z kandydatami do oznaczenia
            feedback_file: Plik z zapisanymi etykietami
        """
        self.candidates_file = Path(candidates_file)
        self.feedback_file = Path(feedback_file)
        self.candidates = []
        self.feedback_data = []
        self.current_index = 0
        
        # Inicjalizacja silnika MAYBE
        self.maybe_engine = MaybeEngine()
        
        # Mapowanie klawiszy na etykiety
        self.key_mappings = {
            'G': 'GUEST',
            'g': 'GUEST',
            'H': 'HOST', 
            'h': 'HOST',
            'I': 'OTHER',
            'i': 'OTHER',
            'M': 'MAYBE',
            'm': 'MAYBE',
            'Q': 'QUIT',
            'q': 'QUIT'
        }
    
    def load_candidates(self) -> bool:
        """
        Wczytuje kandydatów z pliku JSON
        
        Returns:
            True jeśli udało się wczytać kandydatów
        """
        try:
            if not self.candidates_file.exists():
                print(f"❌ Plik {self.candidates_file} nie istnieje!")
                return False
            
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                self.candidates = json.load(f)
            
            print(f"✅ Wczytano {len(self.candidates)} kandydatów")
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania kandydatów: {e}")
            return False
    
    def load_existing_feedback(self) -> int:
        """
        Wczytuje istniejące oznaczenia
        
        Returns:
            Liczba już oznaczonych fraz
        """
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_data = json.load(f)
                
                # Znajdź frazy, które już zostały oznaczone
                labeled_phrases = {item['phrase'] for item in self.feedback_data}
                
                # Usuń już oznaczone frazy z kandydatów
                original_count = len(self.candidates)
                self.candidates = [
                    candidate for candidate in self.candidates 
                    if candidate['phrase'] not in labeled_phrases
                ]
                
                labeled_count = original_count - len(self.candidates)
                if labeled_count > 0:
                    print(f"📋 Pominięto {labeled_count} już oznaczonych fraz")
                
                return len(self.feedback_data)
            else:
                print("📄 Rozpoczynam nowe oznaczanie")
                return 0
                
        except Exception as e:
            print(f"⚠️  Błąd podczas wczytywania feedback: {e}")
            print("📄 Rozpoczynam nowe oznaczanie")
            self.feedback_data = []
            return 0
    
    def save_feedback(self) -> bool:
        """
        Zapisuje oznaczenia do pliku JSON
        
        Returns:
            True jeśli udało się zapisać
        """
        try:
            # Utwórz folder jeśli nie istnieje
            self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Zapisano {len(self.feedback_data)} oznaczonych fraz do {self.feedback_file}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania: {e}")
            return False
    
    def display_progress(self) -> None:
        """
        Wyświetla postęp oznaczania
        """
        total_processed = len(self.feedback_data)
        remaining = len(self.candidates) - self.current_index
        total_candidates = total_processed + len(self.candidates)
        
        if total_candidates > 0:
            progress_percent = (total_processed + self.current_index) / total_candidates * 100
            print(f"\n📊 Postęp: {total_processed + self.current_index}/{total_candidates} "
                  f"({progress_percent:.1f}%) | Pozostało: {remaining}")
        
        print("=" * 60)
    
    def get_user_input(self, phrase: str) -> str:
        """
        Pobiera decyzję użytkownika dla danej frazy
        
        Args:
            phrase: Fraza do oznaczenia
            
        Returns:
            Etykieta ('GUEST', 'HOST', 'OTHER', 'MAYBE', 'QUIT')
        """
        while True:
            print(f"\n→ Jak oznaczyć: \"{phrase}\"?")
            print("   [G]ość / [H]ost / [I]nne / [M]oże / [Q]uit: ", end="")
            
            try:
                user_input = input().strip()
                
                if not user_input:
                    print("⚠️  Proszę wpisać jedną z liter: G, H, I, M, Q")
                    continue
                
                key = user_input[0].upper()
                
                if key in self.key_mappings:
                    label = self.key_mappings[key]
                    
                    if label == 'QUIT':
                        return 'QUIT'
                    
                    # Potwierdzenie wyboru
                    label_names = {
                        'GUEST': 'Gość',
                        'HOST': 'Host/Prowadzący', 
                        'OTHER': 'Inne/Błąd',
                        'MAYBE': 'Może być nazwiskiem'
                    }
                    print(f"✅ Oznaczono jako: {label_names[label]}")
                    return label
                else:
                    print("⚠️  Nieprawidłowy klawisz. Użyj: G (gość), H (host), I (inne), M (może), Q (quit)")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Przerwano przez użytkownika")
                return 'QUIT'
            except EOFError:
                print("\n\n⚠️  Przerwano wejście")
                return 'QUIT'
    
    def process_candidates(self) -> None:
        """
        Główna pętla przetwarzania kandydatów
        """
        print(f"\n🎯 INTERAKTYWNE OZNACZANIE DANYCH TRENINGOWYCH")
        print("=" * 60)
        print("Instrukcje:")
        print("• G = GUEST (gość podcastu)")
        print("• H = HOST (prowadzący, gospodarz)")
        print("• I = OTHER (inne, błędne trafienie)")
        print("• M = MAYBE (może być nazwiskiem)")
        print("• Q = QUIT (zapisz i wyjdź)")
        
        self.display_progress()
        
        for i, candidate in enumerate(self.candidates):
            self.current_index = i
            phrase = candidate['phrase']
            source = candidate.get('source', 'unknown')
            
            print(f"\nŹródło: {source}")
            
            # Sprawdź czy to sugestia z MAYBE
            if self.maybe_engine.is_suggestion_from_maybe(phrase):
                print("🔮 Ta fraza została zasugerowana przez system MAYBE (~M)")
            
            label = self.get_user_input(phrase)
            
            if label == 'QUIT':
                print(f"\n💾 Zapisywanie postępu...")
                break
            
            # Dodaj do feedback
            self.feedback_data.append({
                'phrase': phrase,
                'label': label,
                'source': source
            })
            
            # Jeśli to MAYBE, dodaj do silnika MAYBE
            if label == 'MAYBE':
                self.maybe_engine.add_maybe_example(phrase, source)
            
            # Zapisuj co 10 oznaczień (backup)
            if (i + 1) % 10 == 0:
                self.save_feedback()
                print(f"💾 Automatyczne zapisanie postępu...")
        
        # Finalne zapisanie
        if self.save_feedback():
            print(f"\n🎉 Oznaczanie zakończone!")
            self.show_statistics()
    
    def show_statistics(self) -> None:
        """
        Wyświetla statystyki oznaczonych danych
        """
        if not self.feedback_data:
            return
        
        stats = {'GUEST': 0, 'HOST': 0, 'OTHER': 0, 'MAYBE': 0}
        source_stats = {}
        
        for item in self.feedback_data:
            label = item['label']
            source = item.get('source', 'unknown')
            
            if label in stats:
                stats[label] += 1
            
            if source not in source_stats:
                source_stats[source] = {'GUEST': 0, 'HOST': 0, 'OTHER': 0, 'MAYBE': 0}
            if label in source_stats[source]:
                source_stats[source][label] += 1
        
        print(f"\n📊 STATYSTYKI OZNACZONYCH DANYCH:")
        print("-" * 40)
        print(f"👥 GUEST (goście):     {stats['GUEST']:3d}")
        print(f"🎤 HOST (prowadzący):  {stats['HOST']:3d}")
        print(f"❌ OTHER (inne):       {stats['OTHER']:3d}")
        print(f"❓ MAYBE (może):       {stats['MAYBE']:3d}")
        print(f"📊 ŁĄCZNIE:            {sum(stats.values()):3d}")
        
        if len(source_stats) > 1:
            print(f"\n📍 Statystyki według źródeł:")
            for source, counts in source_stats.items():
                total = sum(counts.values())
                print(f"   {source}: {total} (G:{counts['GUEST']}, H:{counts['HOST']}, O:{counts['OTHER']}, M:{counts['MAYBE']})")
        
        # Dodaj statystyki MAYBE
        maybe_stats = self.maybe_engine.get_maybe_stats()
        if maybe_stats['total'] > 0:
            print(f"\n🔮 STATYSTYKI MAYBE ENGINE:")
            print("-" * 40)
            print(f"📝 Łącznie przykładów MAYBE: {maybe_stats['total']}")
            print(f"🎯 Do następnego triggera: {maybe_stats['next_trigger']}")
            if maybe_stats['recent']:
                print(f"📋 Ostatnie przykłady: {', '.join(maybe_stats['recent'][:3])}")
            if maybe_stats['sources']:
                print(f"📊 Źródła: {maybe_stats['sources']}")


def main():
    """
    Główna funkcja do uruchamiania oznaczania
    """
    handler = InteractiveFeedbackHandler()
    
    # Wczytaj kandydatów
    if not handler.load_candidates():
        return
    
    # Wczytaj istniejące oznaczenia
    existing_count = handler.load_existing_feedback()
    
    if len(handler.candidates) == 0:
        print("🎉 Wszystkie kandydaci zostali już oznaczeni!")
        if existing_count > 0:
            handler.show_statistics()
        return
    
    print(f"📋 Do oznaczenia: {len(handler.candidates)} kandydatów")
    
    # Rozpocznij proces oznaczania
    try:
        handler.process_candidates()
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {e}")
        print("💾 Próbuję zapisać dotychczasowy postęp...")
        handler.save_feedback()


if __name__ == "__main__":
    main()