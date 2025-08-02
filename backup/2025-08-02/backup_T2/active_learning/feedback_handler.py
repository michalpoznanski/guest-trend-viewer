import json
import os
from pathlib import Path
from typing import Optional, Dict


class FeedbackHandler:
    """
    Klasa do obsługi aktywnego uczenia offline - zbieranie feedbacku użytkownika
    """
    
    def __init__(self, feedback_file: str):
        """
        Inicjalizacja FeedbackHandler
        
        Args:
            feedback_file: Ścieżka do pliku JSON z feedbackiem
        """
        self.feedback_file = Path(feedback_file)
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict[str, str]:
        """
        Wczytuje feedback z pliku JSON
        
        Returns:
            Dict z frazami i ich etykietami
        """
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Błąd podczas wczytywania feedback: {e}")
                return {}
        else:
            # Utwórz folder jeśli nie istnieje
            self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
            return {}
    
    def _save_feedback(self):
        """
        Zapisuje feedback do pliku JSON
        """
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"❌ Błąd podczas zapisywania feedback: {e}")
    
    def ask_feedback(self, phrase: str) -> str:
        """
        Pyta użytkownika o feedback dla danej frazy
        
        Args:
            phrase: Fraza do sklasyfikowania
            
        Returns:
            Etykieta przypisana przez użytkownika
        """
        print(f"\n{'='*60}")
        print(f"🔎 Model nie jest pewny lub napotkał nową frazę:")
        print(f"Fraza: \"{phrase}\"")
        print(f"{'='*60}")
        print()
        print("Czy jest to nazwisko gościa?")
        print()
        print("[1] TAK (GUEST)")
        print("[2] NIE (błąd, OTHER)")
        print("[3] HOST (prowadzący)")
        print()
        
        while True:
            try:
                choice = input("Twój wybór: ").strip()
                
                if choice == "1":
                    label = "GUEST"
                    break
                elif choice == "2":
                    label = "OTHER"
                    break
                elif choice == "3":
                    label = "HOST"
                    break
                else:
                    print("⚠️  Nieprawidłowy wybór! Wpisz 1, 2 lub 3.")
            except KeyboardInterrupt:
                print("\n\n❌ Anulowano przez użytkownika")
                return "OTHER"  # Domyślna wartość
            except EOFError:
                print("\n\n❌ Błąd wejścia")
                return "OTHER"  # Domyślna wartość
        
        # Zapisz feedback
        self.save_feedback(phrase, label)
        
        print(f"\n✅ Zapisano feedback: \"{phrase}\" jako {label}")
        return label
    
    def save_feedback(self, phrase: str, label: str):
        """
        Zapisuje feedback do pamięci i pliku
        
        Args:
            phrase: Fraza
            label: Etykieta (GUEST/HOST/OTHER)
        """
        self.feedback_data[phrase] = label
        self._save_feedback()
    
    def has_feedback(self, phrase: str) -> bool:
        """
        Sprawdza czy fraza ma już feedback
        
        Args:
            phrase: Fraza do sprawdzenia
            
        Returns:
            True jeśli fraza ma feedback, False w przeciwnym razie
        """
        return phrase in self.feedback_data
    
    def get_label(self, phrase: str) -> Optional[str]:
        """
        Zwraca etykietę przypisaną do frazy
        
        Args:
            phrase: Fraza
            
        Returns:
            Etykieta lub None jeśli fraza nie ma feedbacku
        """
        return self.feedback_data.get(phrase)
    
    def get_all_feedback(self) -> Dict[str, str]:
        """
        Zwraca wszystkie dane feedbacku
        
        Returns:
            Dict z wszystkimi frazami i etykietami
        """
        return self.feedback_data.copy()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Zwraca statystyki feedbacku
        
        Returns:
            Dict z liczbą wystąpień każdej etykiety
        """
        stats = {"GUEST": 0, "HOST": 0, "OTHER": 0}
        for label in self.feedback_data.values():
            if label in stats:
                stats[label] += 1
        return stats


if __name__ == "__main__":
    # Testowanie klasy
    fb = FeedbackHandler('../data/feedback.json')
    
    test_phrase = "BANK KACZYŃSKI"
    
    if not fb.has_feedback(test_phrase):
        print(f"🔍 Sprawdzam frazę: {test_phrase}")
        fb.ask_feedback(test_phrase)
    else:
        print(f"✅ Fraza '{test_phrase}' ma już feedback: {fb.get_label(test_phrase)}")
    
    # Wyświetl statystyki
    stats = fb.get_stats()
    print(f"\n📊 Statystyki feedbacku:")
    for label, count in stats.items():
        print(f"   {label}: {count}") 