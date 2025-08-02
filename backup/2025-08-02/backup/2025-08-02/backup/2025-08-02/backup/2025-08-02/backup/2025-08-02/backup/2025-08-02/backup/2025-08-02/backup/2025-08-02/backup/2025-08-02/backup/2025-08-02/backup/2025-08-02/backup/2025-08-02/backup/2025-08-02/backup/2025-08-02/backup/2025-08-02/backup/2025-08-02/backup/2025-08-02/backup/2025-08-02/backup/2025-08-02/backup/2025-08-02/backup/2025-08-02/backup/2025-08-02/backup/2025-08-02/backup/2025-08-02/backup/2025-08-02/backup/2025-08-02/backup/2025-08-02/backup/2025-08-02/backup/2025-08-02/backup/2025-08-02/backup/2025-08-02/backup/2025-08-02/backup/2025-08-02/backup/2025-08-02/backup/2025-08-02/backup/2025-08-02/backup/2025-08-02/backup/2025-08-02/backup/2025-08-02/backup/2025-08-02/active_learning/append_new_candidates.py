#!/usr/bin/env python3
"""
Moduł do wyciągania nowych kandydatów z plików CSV i dodawania ich do istniejących kandydatów
"""

import json
import pandas as pd
import re
import glob
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class NewCandidatesExtractor:
    """
    Klasa do wyciągania nowych kandydatów z plików CSV
    """
    
    def __init__(self, csv_folder: str = "data/raw_reports/"):
        """
        Inicjalizacja
        
        Args:
            csv_folder: Folder z plikami CSV
        """
        self.csv_folder = Path(csv_folder)
        self.new_candidates = []
        self.unique_phrases = set()
        
        # Wzorce do wykrywania potencjalnych nazwisk
        self.name_patterns = [
            # Frazy z "ft.", "feat.", "z", "gość", "rozmowa" (najważniejsze)
            r'(?:ft\.|feat\.|z\s+|gość[:\s]+|rozmowa\s+z\s+)([A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]{2,30})',
            
            # Frazy typu "ZAPRASZA MATEUSZ"
            r'\b(?:ZAPRASZA|GOŚĆ|HOST|PROWADZI|ROZMAWIA)\s+([A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20}(?:\s+[A-ZŁĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,20})?)\b',
            
            # 2-3 słowa z dużej litery (Jan Kowalski, Anna Maria Nowak)
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
            'BIZNES', 'POLSCE', 'PREMIUM', 'PREMIERY', 'WTOREK', 'GODZINIE',
            'FETYSZE', 'JAPONEK', 'GOLĄ', 'POLAK', 'JAPOŃCZYK', 'SZCZERZE',
            'SPRAWY', 'ANDRZEJA', 'LEPPERA', 'POWRÓT', 'ZAINTERESOWANIE',
            'SPRAWĄ', 'PRAWDA', 'PONAD', 'WSZYSTKO', 'RZĄDZIĆ', 'POLSKĄ',
            'INWIGILACJA', 'ZWIĄZKI', 'DONALDA', 'TUSKA'
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
        
        # Usuń znaki specjalne ale zostaw polskie znaki, myślniki i spacje
        text = re.sub(r'[^\w\s\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', ' ', text)
        
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
        if len(phrase) < 4 or len(phrase) > 50:
            return False
        
        # Sprawdź czy ma co najmniej 2 wyrazy
        words = phrase.split()
        if len(words) < 2:
            return False
        
        # Sprawdź czy nie zawiera cyfr
        if any(char.isdigit() for char in phrase):
            return False
        
        # Sprawdź czy zawiera tylko litery, spacje i myślniki
        if not re.match(r'^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s\-]+$', phrase):
            return False
        
        # Sprawdź czy nie jest w liście wykluczeń
        phrase_upper = phrase.upper()
        for exclude_word in self.exclude_words:
            if exclude_word in phrase_upper:
                return False
        
        # Sprawdź czy każdy wyraz ma co najmniej 2 znaki
        for word in words:
            if len(word.strip('-')) < 2:
                return False
        
        # Sprawdź czy zawiera przynajmniej jedną literę
        if not any(char.isalpha() for char in phrase):
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
    
    def extract_new_candidates(self) -> List[Dict]:
        """
        Wyciąga nowych kandydatów z wszystkich plików CSV
        
        Returns:
            Lista nowych kandydatów
        """
        print(f"🔍 WYCIĄGANIE NOWYCH KANDYDATÓW Z PLIKÓW CSV")
        print("=" * 60)
        
        # Wczytaj pliki CSV
        dataframes = self.load_csv_files()
        
        if not dataframes:
            return []
        
        # Połącz wszystkie DataFrame
        all_data = pd.concat(dataframes, ignore_index=True)
        print(f"📊 Łącznie {len(all_data)} rekordów do analizy")
        
        # Kolumny do analizy - sprawdź które istnieją
        text_columns = ['Title', 'title', 'Description', 'description', 'Tags', 'tags']
        available_columns = []
        
        for col in text_columns:
            if col in all_data.columns:
                available_columns.append(col)
                print(f"✅ Znaleziono kolumnę: {col}")
        
        if not available_columns:
            print("❌ Nie znaleziono żadnych kolumn tekstowych!")
            return []
        
        # Mapowanie kolumn na źródła
        source_mapping = {
            'Title': 'title',
            'title': 'title',
            'Description': 'description', 
            'description': 'description',
            'Tags': 'tags',
            'tags': 'tags'
        }
        
        # Wyciągnij kandydatów z każdej kolumny
        for column in available_columns:
            source = source_mapping.get(column, column.lower())
            print(f"\n🔍 Analizuję kolumnę: {column}")
            
            processed = 0
            for _, row in all_data.iterrows():
                text = row.get(column, '')
                new_candidates = self.extract_candidates_from_text(text, source)
                self.new_candidates.extend(new_candidates)
                processed += 1
                
                if processed % 100 == 0:
                    print(f"   Przetworzono {processed} rekordów...")
            
            candidates_from_source = len([c for c in self.new_candidates if c['source'] == source])
            print(f"   Znaleziono {candidates_from_source} kandydatów")
        
        print(f"\n✅ Łącznie znaleziono {len(self.new_candidates)} unikalnych kandydatów")
        
        return self.new_candidates
    
    def load_existing_candidates(self, existing_file: str) -> Set[str]:
        """
        Wczytuje istniejących kandydatów
        
        Args:
            existing_file: Plik z istniejącymi kandydatami
            
        Returns:
            Zbiór istniejących fraz
        """
        existing_phrases = set()
        
        try:
            if Path(existing_file).exists():
                with open(existing_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                for item in existing_data:
                    existing_phrases.add(item.get('phrase', ''))
                
                print(f"📋 Wczytano {len(existing_phrases)} istniejących kandydatów z {existing_file}")
            else:
                print(f"📄 Plik {existing_file} nie istnieje - rozpoczynam od zera")
        except Exception as e:
            print(f"⚠️  Błąd podczas wczytywania {existing_file}: {e}")
        
        return existing_phrases
    
    def append_to_existing_file(self, output_file: str, new_candidates: List[Dict]) -> bool:
        """
        Dodaje nowych kandydatów do istniejącego pliku
        
        Args:
            output_file: Plik docelowy
            new_candidates: Lista nowych kandydatów
            
        Returns:
            True jeśli udało się zapisać
        """
        try:
            # Wczytaj istniejące dane
            existing_data = []
            if Path(output_file).exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Dodaj nowych kandydatów
            combined_data = existing_data + new_candidates
            
            # Utwórz folder jeśli nie istnieje
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Zapisz połączone dane
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Zapisano {len(combined_data)} kandydatów do {output_file}")
            print(f"   (w tym {len(new_candidates)} nowych)")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania: {e}")
            return False
    
    def show_statistics(self, new_candidates: List[Dict], existing_count: int):
        """
        Wyświetla statystyki nowych kandydatów
        
        Args:
            new_candidates: Lista nowych kandydatów
            existing_count: Liczba istniejących kandydatów
        """
        if not new_candidates:
            print(f"\n📊 STATYSTYKI:")
            print("-" * 40)
            print(f"📋 Istniejących kandydatów: {existing_count}")
            print(f"🆕 Nowych kandydatów: 0")
            print(f"📊 Łącznie: {existing_count}")
            return
        
        # Statystyki według źródeł
        source_stats = defaultdict(int)
        for candidate in new_candidates:
            source_stats[candidate['source']] += 1
        
        print(f"\n📊 STATYSTYKI NOWYCH KANDYDATÓW:")
        print("-" * 40)
        print(f"📋 Istniejących kandydatów: {existing_count}")
        print(f"🆕 Nowych kandydatów: {len(new_candidates)}")
        print(f"📊 Łącznie: {existing_count + len(new_candidates)}")
        
        print(f"\n📍 Nowi kandydaci według źródeł:")
        for source, count in source_stats.items():
            print(f"   {source}: {count}")
        
        # Pokaż przykłady
        print(f"\n🎯 PRZYKŁADY NOWYCH KANDYDATÓW:")
        print("-" * 50)
        for i, candidate in enumerate(new_candidates[:10], 1):
            phrase = candidate.get('phrase', '')
            source = candidate.get('source', 'unknown')
            word_count = len(phrase.split())
            print(f"{i:2d}. \"{phrase}\" ({word_count} wyrazów, źródło: {source})")
        
        if len(new_candidates) > 10:
            print(f"    ... i {len(new_candidates) - 10} więcej")


def main():
    """
    Główna funkcja do wyciągania i dodawania nowych kandydatów
    """
    extractor = NewCandidatesExtractor()
    
    # Pliki wejściowe i wyjściowe
    existing_file = "data/filtered_candidates.json"
    output_file = "data/filtered_candidates.json"
    
    print("🔍 DODAWANIE NOWYCH KANDYDATÓW")
    print("=" * 50)
    
    # Wczytaj istniejących kandydatów
    existing_phrases = extractor.load_existing_candidates(existing_file)
    
    # Wyciągnij nowych kandydatów
    all_new_candidates = extractor.extract_new_candidates()
    
    if not all_new_candidates:
        print("❌ Nie znaleziono nowych kandydatów")
        return
    
    # Odfiltruj już istniejących kandydatów
    truly_new_candidates = []
    for candidate in all_new_candidates:
        if candidate['phrase'] not in existing_phrases:
            truly_new_candidates.append(candidate)
    
    # Wyświetl statystyki
    extractor.show_statistics(truly_new_candidates, len(existing_phrases))
    
    if truly_new_candidates:
        # Zapisz nowych kandydatów
        if extractor.append_to_existing_file(output_file, truly_new_candidates):
            print(f"\n🎉 DODAWANIE NOWYCH KANDYDATÓW ZAKOŃCZONE!")
            print(f"📁 Zaktualizowany plik: {output_file}")
        else:
            print(f"\n❌ Nie udało się zapisać nowych kandydatów")
    else:
        print(f"\n💡 Wszystkie znalezione kandydaci już istnieją w pliku {existing_file}")


if __name__ == "__main__":
    main()