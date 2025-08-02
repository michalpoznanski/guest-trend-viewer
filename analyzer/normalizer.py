import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher


class NameNormalizer:
    """
    Klasa do normalizacji imion i nazwisk wykrytych przez model NER
    """
    
    def __init__(self, reference_file: str = "analyzer/guest_reference.json"):
        """
        Inicjalizacja NameNormalizer
        
        Args:
            reference_file: Ścieżka do pliku z referencjami gości
        """
        self.reference_file = Path(reference_file)
        self.aliases = self._load_aliases()
        self.fuzzy_threshold = 0.93
    
    def _load_aliases(self) -> Dict[str, str]:
        """
        Wczytuje aliasy z pliku guest_reference.json
        
        Returns:
            Dict z aliasami: {"alias": "główna_nazwa"}
        """
        aliases = {}
        
        if not self.reference_file.exists():
            print(f"⚠️  Plik {self.reference_file} nie istnieje. Tworzę pusty plik.")
            self._create_empty_reference()
            return aliases
        
        try:
            with open(self.reference_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Buduj słownik aliasów
            for main_name, alias_list in data.items():
                aliases[main_name] = main_name  # główna nazwa
                for alias in alias_list:
                    aliases[alias] = main_name
                    
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Błąd podczas wczytywania referencji: {e}")
            return aliases
        
        return aliases
    
    def _create_empty_reference(self):
        """
        Tworzy pusty plik referencji z przykładowymi danymi
        """
        example_data = {
            "Piotr Przywarski": ["Piotr Polo", "Polo"],
            "Kuba Wojewódzki": ["Wojewódzki", "Kuba"]
        }
        
        try:
            with open(self.reference_file, 'w', encoding='utf-8') as f:
                json.dump(example_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Utworzono plik {self.reference_file} z przykładowymi danymi")
        except IOError as e:
            print(f"❌ Błąd podczas tworzenia pliku: {e}")
    
    def _is_valid_name(self, name: str) -> bool:
        """
        Sprawdza czy nazwa jest prawidłowa (nie jest fałszywym trafieniem)
        
        Args:
            name: Nazwa do sprawdzenia
            
        Returns:
            True jeśli nazwa jest prawidłowa
        """
        # Usuń białe znaki
        name = name.strip()
        
        # Sprawdź długość
        if len(name) <= 2:
            return False
        
        # Sprawdź czy to same cyfry
        if name.isdigit():
            return False
        
        # Sprawdź czy to oczywiste fałszywe trafienie
        false_positives = [
            "gość", "gosc", "goscie", "goście", "host", "prowadzący", 
            "prowadzacy", "autor", "redaktor", "dziennikarz", "reporter"
        ]
        
        if name.lower() in false_positives:
            return False
        
        # Sprawdź czy zawiera przynajmniej jedną literę
        if not re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', name):
            return False
        
        return True
    
    def _clean_name(self, name: str) -> str:
        """
        Oczyszcza i kapitalizuje nazwę
        
        Args:
            name: Nazwa do oczyszczenia
            
        Returns:
            Oczyszczona nazwa
        """
        # Usuń nadmiarowe białe znaki
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Kapitalizuj każde słowo
        words = name.split()
        capitalized_words = []
        
        for word in words:
            # Kapitalizuj pierwsze litery, reszta małe
            if len(word) > 1:
                capitalized = word[0].upper() + word[1:].lower()
            else:
                capitalized = word.upper()
            capitalized_words.append(capitalized)
        
        return ' '.join(capitalized_words)
    
    def _fuzzy_match(self, name: str, candidates: List[str]) -> Optional[str]:
        """
        Znajduje najlepsze dopasowanie fuzzy dla nazwy
        
        Args:
            name: Nazwa do dopasowania
            candidates: Lista kandydatów
            
        Returns:
            Najlepsze dopasowanie lub None
        """
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
            if score > best_score and score >= self.fuzzy_threshold:
                best_score = score
                best_match = candidate
        
        return best_match
    
    def normalize(self, name: str) -> str:
        """
        Normalizuje pojedynczą nazwę
        
        Args:
            name: Nazwa do normalizacji
            
        Returns:
            Znormalizowana nazwa
        """
        # Sprawdź czy nazwa jest prawidłowa
        if not self._is_valid_name(name):
            return ""
        
        # Oczyszcz nazwę
        cleaned_name = self._clean_name(name)
        
        # Sprawdź czy to jest alias
        if cleaned_name in self.aliases:
            return self.aliases[cleaned_name]
        
        # Sprawdź fuzzy matching z głównymi nazwami
        main_names = list(set(self.aliases.values()))
        fuzzy_match = self._fuzzy_match(cleaned_name, main_names)
        
        if fuzzy_match:
            return fuzzy_match
        
        # Jeśli nie znaleziono dopasowania, zwróć oczyszczoną nazwę
        return cleaned_name
    
    def normalize_all(self, names: List[str]) -> List[str]:
        """
        Normalizuje listę nazwisk
        
        Args:
            names: Lista nazw do normalizacji
            
        Returns:
            Lista unikalnych, posortowanych, znormalizowanych nazw
        """
        normalized_names = []
        
        for name in names:
            normalized = self.normalize(name)
            if normalized and normalized not in normalized_names:
                normalized_names.append(normalized)
        
        # Sortuj alfabetycznie
        return sorted(normalized_names)
    
    def add_alias(self, main_name: str, alias: str):
        """
        Dodaje nowy alias do słownika
        
        Args:
            main_name: Główna nazwa
            alias: Alias
        """
        self.aliases[alias] = main_name
        self.aliases[main_name] = main_name  # upewnij się, że główna nazwa też jest w słowniku
    
    def get_aliases(self) -> Dict[str, str]:
        """
        Zwraca słownik aliasów
        
        Returns:
            Dict z aliasami
        """
        return self.aliases.copy()


if __name__ == "__main__":
    # Testowanie klasy
    normalizer = NameNormalizer()
    
    # Przykładowe testy
    test_names = [
        "klaudii lewandowskiej",
        "Polo",
        "lewandowski",
        "Kuba",
        "gość",  # fałszywe trafienie
        "12",    # cyfry
        "a",     # za krótkie
        "Piotr Przywarski",
        "wojewódzki"
    ]
    
    print("🧪 TESTOWANIE NORMALIZACJI NAZWISK")
    print("=" * 50)
    
    for name in test_names:
        normalized = normalizer.normalize(name)
        if normalized:
            print(f"'{name}' → '{normalized}'")
        else:
            print(f"'{name}' → [ODRZUCONE]")
    
    print(f"\n📊 Normalizacja listy:")
    all_normalized = normalizer.normalize_all(test_names)
    print(f"Wynik: {all_normalized}")
    
    print(f"\n🔍 Słownik aliasów:")
    for alias, main_name in normalizer.get_aliases().items():
        print(f"  '{alias}' → '{main_name}'") 