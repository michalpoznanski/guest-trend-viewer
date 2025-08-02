#!/usr/bin/env python3
"""
Moduł do przygotowania kandydatów na dane treningowe dla modelu spaCy NER
"""

import json
import pandas as pd
import re
import glob
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class TrainingSetBuilder:
    """
    Klasa do budowania zestawu kandydatów na dane treningowe
    """
    
    def __init__(self, csv_folder: str = "data/raw_reports/"):
        """
        Inicjalizacja
        
        Args:
            csv_folder: Folder z plikami CSV
        """
        self.csv_folder = Path(csv_folder)
        self.candidates = []
        self.unique_phrases = set()
        
        # Wzorce do wykrywania potencjalnych nazwisk
        self.name_patterns = [
            # Frazy z "ft.", "feat.", "z", "gość", "rozmowa" (najważniejsze)
            r'(?:ft\.|feat\.|z\s+|gość[:\s]+|rozmowa\s+z\s+)([A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]{2,30})',
            
            # Frazy typu "ZAPRASZA MATEUSZ"
            r'\b(?:ZAPRASZA|GOŚĆ|HOST|PROWADZI|ROZMAWIA)\s+([A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20}(?:\s+[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20})?)\b',
            
            # 2-3 słowa z dużej litery (Jan Kowalski, Anna Maria Nowak) - tylko jeśli oba słowa są nazwiskami
            r'\b[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,15}\s+[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20}(?:\s+[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20})?\b',
            
            # Pseudonimy/artyści (KIZO, BEDOES) - ale nie za krótkie
            r'\b[A-Z]{3,10}\b',
            
            # Mieszane wzorce (TroyBoi, KęKę, Małpa) - ale tylko z charakterystycznymi wzorcami
            r'\b[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}[A-Z][a-ząćęłńóśźż]{2,}\b'
        ]
        
        # Słowa do filtrowania (nie są nazwiskami)
        self.exclude_words = {
            'PODCAST', 'YOUTUBE', 'CHANNEL', 'VIDEO', 'MUSIC', 'SONG', 'ALBUM',
            'LIVE', 'STREAM', 'RADIO', 'TV', 'NEWS', 'SPORT', 'GAME', 'GAMING',
            'REVIEW', 'REACT', 'REACTION', 'TUTORIAL', 'GUIDE', 'TIPS', 'TRICKS',
            'BEST', 'TOP', 'WORST', 'FUNNY', 'EPIC', 'FAIL', 'WIN', 'COMPILATION',
            'OFFICIAL', 'FULL', 'COMPLETE', 'PART', 'EPISODE', 'SEASON', 'SERIES',
            'TRAILER', 'TEASER', 'BEHIND', 'SCENES', 'MAKING', 'DOCUMENTARY',
            'INTERVIEW', 'TALK', 'SHOW', 'PROGRAM', 'EMISJA', 'ODCINEK',
            'POLSKA', 'POLAND', 'POLISH', 'ENGLISH', 'GERMAN', 'FRENCH',
            'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
            'STYCZEŃ', 'LUTY', 'MARZEC', 'KWIECIEŃ', 'MAJ', 'CZERWIEC',
            'LIPIEC', 'SIERPIEŃ', 'WRZESIEŃ', 'PAŹDZIERNIK', 'LISTOPAD', 'GRUDZIEŃ',
            'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'JUNE', 'JULY',
            'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
            'ZDJĘCIE', 'FOTOGRAFIA', 'PHOTO', 'PICTURE', 'IMAGE', 'ART', 'DESIGN',
            'SHORTS', 'LONG', 'LONGS', 'ELEKTRYCZNYCH', 'OWCACH', 'BOTÓW', 'DWÓCH',
            'PROF', 'DLACZEGO', 'HOSTEL', 'JEST', 'LEPSZY', 'HOTELU', 'BŁAGAŁEM',
            'ŻEBYM', 'PRZETRWAŁ', 'RANA', 'ROSJANIE', 'REAGUJĄ', 'POLAKÓW',
            'NAPRAWDĘ', 'WYGLĄDA', 'ŻYCIE', 'KOREI', 'PÓŁNOCNEJ', 'POMYSŁY',
            'BIZNES', 'POLSCE', 'PREMIUM', 'PREMIERY', 'WTOREK', 'GODZINIE'
        }
    
    def load_csv_files(self) -> List[pd.DataFrame]:
        """
        Wczytuje wszystkie pliki CSV z folderu
        
        Returns:
            Lista DataFrame z danymi
        """
        print(f"📁 Wczytywanie plików CSV z {self.csv_folder}")
        
        if not self.csv_folder.exists():
            print(f"❌ Folder {self.csv_folder} nie istnieje!")
            return []
        
        # Znajdź wszystkie pliki CSV
        csv_files = list(self.csv_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"⚠️  Nie znaleziono plików CSV w {self.csv_folder}")
            return []
        
        dataframes = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                print(f"✅ Wczytano: {csv_file.name} ({len(df)} rekordów)")
                dataframes.append(df)
            except Exception as e:
                print(f"❌ Błąd podczas wczytywania {csv_file.name}: {e}")
        
        return dataframes
    
    def clean_text(self, text: str) -> str:
        """
        Oczyszcza tekst przed analizą
        
        Args:
            text: Tekst do oczyszczenia
            
        Returns:
            Oczyszczony tekst
        """
        if pd.isna(text) or not text:
            return ""
        
        text = str(text)
        
        # Usuń nadmiarowe białe znaki
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Usuń znaki specjalne ale zostaw polskie znaki
        text = re.sub(r'[^\w\s\.\,\:\|\-\(\)\"\'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', ' ', text)
        
        return text
    
    def is_valid_phrase(self, phrase: str) -> bool:
        """
        Sprawdza czy fraza jest potencjalnym nazwiskiem
        
        Args:
            phrase: Fraza do sprawdzenia
            
        Returns:
            True jeśli fraza może być nazwiskiem
        """
        phrase = phrase.strip()
        
        # Sprawdź długość
        if len(phrase) < 2 or len(phrase) > 50:
            return False
        
        # Sprawdź czy nie zawiera cyfr
        if any(char.isdigit() for char in phrase):
            return False
        
        # Sprawdź czy nie jest w liście wykluczeń
        phrase_upper = phrase.upper()
        for exclude_word in self.exclude_words:
            if exclude_word in phrase_upper:
                return False
        
        # Sprawdź czy zawiera przynajmniej jedną literę
        if not any(char.isalpha() for char in phrase):
            return False
        
        # Sprawdź czy nie ma za dużo znaków specjalnych
        special_chars = sum(1 for char in phrase if not char.isalnum() and char != ' ')
        if special_chars > len(phrase) * 0.3:
            return False
        
        return True
    
    def extract_candidates_from_text(self, text: str, source: str) -> List[Dict]:
        """
        Wyciąga kandydatów z tekstu
        
        Args:
            text: Tekst do analizy
            source: Źródło tekstu (title, description, tags)
            
        Returns:
            Lista kandydatów
        """
        candidates = []
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            return candidates
        
        # Zastosuj wszystkie wzorce
        for pattern in self.name_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            
            for match in matches:
                # Jeśli match to tuple (z grup), weź pierwszą grupę
                if isinstance(match, tuple):
                    phrase = match[0] if match[0] else match[1] if len(match) > 1 else ""
                else:
                    phrase = match
                
                phrase = phrase.strip()
                
                if self.is_valid_phrase(phrase) and phrase not in self.unique_phrases:
                    candidates.append({
                        "phrase": phrase,
                        "source": source
                    })
                    self.unique_phrases.add(phrase)
        
        return candidates
    
    def build_training_candidates(self, max_candidates: int = 200) -> List[Dict]:
        """
        Buduje listę kandydatów na dane treningowe
        
        Args:
            max_candidates: Maksymalna liczba kandydatów
            
        Returns:
            Lista kandydatów
        """
        print(f"🔍 WYSZUKIWANIE KANDYDATÓW NA DANE TRENINGOWE")
        print("=" * 60)
        
        # Wczytaj pliki CSV
        dataframes = self.load_csv_files()
        
        if not dataframes:
            return []
        
        # Połącz wszystkie DataFrame
        all_data = pd.concat(dataframes, ignore_index=True)
        print(f"📊 Łącznie {len(all_data)} rekordów do analizy")
        
        # Kolumny do analizy
        text_columns = ['Title', 'Description', 'Tags']
        
        # Sprawdź które kolumny istnieją
        available_columns = []
        for col in text_columns:
            if col in all_data.columns:
                available_columns.append(col)
                print(f"✅ Znaleziono kolumnę: {col}")
            else:
                print(f"⚠️  Brak kolumny: {col}")
        
        if not available_columns:
            print("❌ Nie znaleziono żadnych kolumn tekstowych!")
            return []
        
        # Wyciągnij kandydatów z każdej kolumny
        source_mapping = {
            'Title': 'title',
            'Description': 'description',
            'Tags': 'tags'
        }
        
        for column in available_columns:
            source = source_mapping.get(column, column.lower())
            print(f"\n🔍 Analizuję kolumnę: {column}")
            
            processed = 0
            for _, row in all_data.iterrows():
                text = row.get(column, '')
                new_candidates = self.extract_candidates_from_text(text, source)
                self.candidates.extend(new_candidates)
                processed += 1
                
                if processed % 100 == 0:
                    print(f"   Przetworzono {processed} rekordów...")
                
                # Limit kandydatów
                if len(self.candidates) >= max_candidates:
                    break
            
            print(f"   Znaleziono {len([c for c in self.candidates if c['source'] == source])} kandydatów")
            
            if len(self.candidates) >= max_candidates:
                break
        
        # Ogranicz do max_candidates
        if len(self.candidates) > max_candidates:
            self.candidates = self.candidates[:max_candidates]
        
        print(f"\n✅ Łącznie znaleziono {len(self.candidates)} unikalnych kandydatów")
        
        return self.candidates
    
    def save_candidates(self, output_file: str = "data/feedback_candidates.json"):
        """
        Zapisuje kandydatów do pliku JSON
        
        Args:
            output_file: Ścieżka do pliku wynikowego
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.candidates, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Zapisano kandydatów: {output_file}")
            
            # Statystyki
            source_stats = defaultdict(int)
            for candidate in self.candidates:
                source_stats[candidate['source']] += 1
            
            print(f"\n📊 Statystyki źródeł:")
            for source, count in source_stats.items():
                print(f"   {source}: {count}")
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania: {e}")


def main():
    """
    Główna funkcja do budowania kandydatów
    """
    builder = TrainingSetBuilder()
    candidates = builder.build_training_candidates(max_candidates=200)
    
    if candidates:
        builder.save_candidates()
        
        print(f"\n🎯 PRZYKŁADOWE KANDYDACI:")
        print("-" * 40)
        for i, candidate in enumerate(candidates[:10], 1):
            print(f"{i:2d}. \"{candidate['phrase']}\" ({candidate['source']})")
        
        if len(candidates) > 10:
            print(f"    ... i {len(candidates) - 10} więcej")
    
    print(f"\n🎉 BUDOWANIE KANDYDATÓW ZAKOŃCZONE!")


if __name__ == "__main__":
    main()