import json
import os
import csv
import shutil
import unicodedata
from typing import Dict, List, Set
from datetime import datetime


class PhraseDiscovery:
    """
    Klasa do automatycznego wyłapywania nowych fraz z raportów CSV
    i dodawania ich do systemu oznaczania.
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.reports_dir = os.path.join(self.base_dir, "data", "raw_reports")
        self.training_data_path = os.path.join(self.base_dir, "data", "name_training_set.json")
        self.backup_dir = os.path.join(self.base_dir, "data", "backups")
        
        # Utwórz katalog backup jeśli nie istnieje
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _normalize_phrase(self, phrase: str) -> str:
        """
        Normalizuje frazę do porównywania:
        - usuwa białe znaki z początku i końca
        - zamienia na małe litery
        - zamienia wszelkie niewidoczne znaki (w tym zero-width space, soft hyphen)
        - normalizuje Unicode (unicodedata.normalize('NFC'))
        - zamienia powtarzające się spacje w środku na pojedynczą spację
        """
        if not phrase:
            return ""
        
        # Usuń białe znaki z początku i końca
        normalized = phrase.strip()
        
        # Zamień na małe litery
        normalized = normalized.lower()
        
        # Zamień niewidoczne znaki na spacje
        import re
        normalized = re.sub(r'[\u200B\u200C\u200D\uFEFF\u00AD\u200E\u200F]', ' ', normalized)
        
        # Normalizuj znaki Unicode (NFD -> NFC)
        normalized = unicodedata.normalize('NFC', normalized)
        
        # Zamień powtarzające się spacje na pojedynczą spację
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Usuń białe znaki z początku i końca ponownie
        normalized = normalized.strip()
        
        return normalized
    
    def _create_backup(self) -> str:
        """
        Tworzy backup pliku name_training_set.json przed modyfikacją.
        Zwraca ścieżkę do backupu.
        """
        if not os.path.exists(self.training_data_path):
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"name_training_set_backup_{timestamp}.json")
        
        try:
            shutil.copy2(self.training_data_path, backup_path)
            print(f"Utworzono backup: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Błąd podczas tworzenia backupu: {e}")
            return ""
    
    def _load_training_data(self) -> Dict[str, str]:
        """
        Wczytuje dane treningowe z pliku JSON.
        Tworzy plik jeśli nie istnieje.
        """
        try:
            if os.path.exists(self.training_data_path):
                with open(self.training_data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Utwórz katalog jeśli nie istnieje
                os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
                # Utwórz pusty plik
                initial_data = {}
                self._save_training_data(initial_data)
                return initial_data
        except Exception as e:
            print(f"Błąd podczas wczytywania danych treningowych: {e}")
            return {}
    
    def _save_training_data(self, data: Dict[str, str]) -> bool:
        """
        Zapisuje dane treningowe do pliku JSON.
        """
        try:
            with open(self.training_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania danych treningowych: {e}")
            return False
    
    def _extract_phrases_from_csv(self, csv_path: str) -> Set[str]:
        """
        Wyciąga unikalne frazy z pliku CSV.
        Szuka w kolumnach: Names_Extracted, guest, name
        """
        phrases = set()
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Sprawdź dostępne kolumny
                fieldnames = reader.fieldnames or []
                name_columns = []
                
                # Znajdź kolumny z nazwami
                for col in fieldnames:
                    if any(keyword in col.lower() for keyword in ['name', 'guest', 'extracted']):
                        name_columns.append(col)
                
                print(f"Znalezione kolumny z nazwami w {os.path.basename(csv_path)}: {name_columns}")
                
                for row in reader:
                    for col in name_columns:
                        if col in row and row[col]:
                            # Podziel na pojedyncze frazy (może być kilka oddzielonych przecinkami)
                            raw_phrases = row[col].strip()
                            if raw_phrases:
                                # Podziel po przecinkach i wyczyść
                                for phrase in raw_phrases.split(','):
                                    cleaned_phrase = phrase.strip().strip('"').strip("'")
                                    if cleaned_phrase and len(cleaned_phrase) > 1:  # Ignoruj pojedyncze znaki
                                        # Użyj oryginalnej frazy (nie znormalizowanej) do dodania do zbioru
                                        phrases.add(cleaned_phrase)
        
        except Exception as e:
            print(f"Błąd podczas przetwarzania pliku {csv_path}: {e}")
        
        return phrases
    
    def find_new_phrases_from_reports(self) -> Dict[str, int]:
        """
        Główna funkcja - przechodzi przez wszystkie raporty CSV,
        zbiera unikalne frazy i dodaje nowe do name_training_set.json.
        
        Zwraca słownik z statystykami:
        - 'total_phrases_found': całkowita liczba znalezionych fraz
        - 'new_phrases_added': liczba nowych fraz dodanych
        - 'files_processed': liczba przetworzonych plików
        """
        print("Rozpoczynam automatyczne wyłapywanie nowych fraz...")
        
        # Utwórz backup przed modyfikacją
        backup_path = self._create_backup()
        
        # Wczytaj obecne dane treningowe
        training_data = self._load_training_data()
        
        # Zbierz znormalizowane frazy już oznaczone (GUEST, HOST, NO) i istniejące frazy
        existing_phrases = set(training_data.keys())
        normalized_excluded = set()
        
        for phrase, value in training_data.items():
            if value in ["GUEST", "HOST", "NO"]:
                normalized_excluded.add(self._normalize_phrase(phrase))
        
        # Zbierz wszystkie frazy z raportów
        all_phrases = set()
        files_processed = 0
        
        if not os.path.exists(self.reports_dir):
            print(f"Katalog raportów nie istnieje: {self.reports_dir}")
            return {
                'total_phrases_found': 0,
                'new_phrases_added': 0,
                'files_processed': 0
            }
        
        # Przejdź przez wszystkie pliki CSV
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.csv'):
                csv_path = os.path.join(self.reports_dir, filename)
                print(f"Przetwarzam plik: {filename}")
                
                file_phrases = self._extract_phrases_from_csv(csv_path)
                all_phrases.update(file_phrases)
                files_processed += 1
        
        # Znajdź nowe frazy (wykluczając duplikaty już oznaczonych fraz)
        new_phrases = set()
        for phrase in all_phrases:
            normalized_phrase = self._normalize_phrase(phrase)
            # Sprawdź czy fraza nie istnieje w oryginalnej formie i czy nie jest duplikatem już oznaczonych fraz
            if phrase not in existing_phrases and normalized_phrase not in normalized_excluded:
                new_phrases.add(phrase)
            else:
                print(f"Pominięto frazę '{phrase}' (znormalizowana: '{normalized_phrase}') - już istnieje lub jest duplikatem")
        
        # Dodaj nowe frazy do danych treningowych ze statusem "MAYBE"
        if new_phrases:
            print(f"Znaleziono {len(new_phrases)} nowych fraz:")
            for phrase in sorted(new_phrases):
                print(f"  - {phrase}")
                training_data[phrase] = "MAYBE"
            
            # Zapisz zaktualizowane dane
            if self._save_training_data(training_data):
                print(f"Pomyślnie dodano {len(new_phrases)} nowych fraz do systemu oznaczania.")
            else:
                print("Błąd podczas zapisywania nowych fraz!")
        else:
            print("Nie znaleziono nowych fraz.")
        
        return {
            'total_phrases_found': len(all_phrases),
            'new_phrases_added': len(new_phrases),
            'files_processed': files_processed
        }


def find_new_phrases_from_reports():
    """
    Funkcja pomocnicza do łatwego wywołania procesu wyłapywania fraz.
    """
    discovery = PhraseDiscovery()
    return discovery.find_new_phrases_from_reports()


if __name__ == "__main__":
    # Test funkcji
    stats = find_new_phrases_from_reports()
    print(f"\nStatystyki:")
    print(f"- Przetworzone pliki: {stats['files_processed']}")
    print(f"- Znalezione frazy: {stats['total_phrases_found']}")
    print(f"- Nowe frazy dodane: {stats['new_phrases_added']}") 