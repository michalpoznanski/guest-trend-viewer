#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do polepszania wyników NER - filtruje i czyści wykryte nazwiska

Problemy do rozwiązania:
1. Model wykrywa za długie fragmenty (np. "Wywiad z Jakubem")
2. Potrzebne jest filtrowanie rzeczywistych nazwisk
3. Usunięcie kontekstu i zostawienie tylko nazwisk

Autor: Guest Radar System
Data: 2025-08-03
"""

import json
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Set
import argparse


class NERResultsImprover:
    """Klasa do polepszania wyników NER."""
    
    def __init__(self):
        """Inicjalizuje ulepszacz wyników."""
        
        # Wzorce nazw polskich
        self.name_patterns = [
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b',  # Imię Nazwisko
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Standardowe nazwiska
        ]
        
        # Słowa kontekstowe do usunięcia
        self.context_words = {
            'wywiad', 'rozmowa', 'program', 'show', 'gościem', 'jest', 'prowadzi', 
            'wraz', 'dyskutują', 'special', 'edition', 'nowej', 'książce', 'polityce',
            'medycynie', 'celebrytami', 'dr.', 'dr', 'prof.', 'prof', 'inż.', 'inż',
            'mgr.', 'mgr', 'lek.', 'lek', 'hab.', 'hab'
        }
        
        # Typowe false positive
        self.false_positives = {
            'special edition', 'nowej książce', 'show z', 'program z',
            'wywiad z', 'rozmowa z', 'dyskutują o', 'prowadzi show'
        }
    
    def extract_clean_names(self, dirty_text: str) -> List[str]:
        """
        Wydobywa czyste nazwiska z brutalnego tekstu NER.
        
        Args:
            dirty_text: Tekst zawierający nazwiska z kontekstem
            
        Returns:
            Lista czystych nazwisk
        """
        clean_names = []
        
        # Usuń znaki interpunkcyjne
        text = re.sub(r'[,\-\.!?;:]', ' ', dirty_text)
        
        # Znajdź wzorce nazwisk
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Sprawdź czy to prawdopodobnie nazwisko
                if self.is_likely_name(match):
                    clean_names.append(match.strip())
        
        # Usuń duplikaty zachowując kolejność
        seen = set()
        unique_names = []
        for name in clean_names:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique_names.append(name)
        
        return unique_names
    
    def is_likely_name(self, text: str) -> bool:
        """
        Sprawdza czy tekst prawdopodobnie jest nazwiskiem.
        
        Args:
            text: Tekst do sprawdzenia
            
        Returns:
            True jeśli prawdopodobnie nazwisko
        """
        # Podstawowe filtry
        words = text.strip().split()
        if len(words) != 2:  # Oczekujemy "Imię Nazwisko"
            return False
        
        # Sprawdź długość
        if len(text) < 4 or len(text) > 30:
            return False
        
        # Sprawdź czy zawiera słowa kontekstowe
        text_lower = text.lower()
        for context_word in self.context_words:
            if context_word in text_lower:
                return False
        
        # Sprawdź false positive
        for fp in self.false_positives:
            if fp in text_lower:
                return False
        
        # Sprawdź czy słowa wyglądają jak imiona/nazwiska
        for word in words:
            if len(word) < 2:
                return False
            if not word[0].isupper():
                return False
            if not (word[1:].islower() or word.isupper()):
                return False
        
        return True
    
    def improve_json_results(self, json_path: Path, output_path: Path) -> bool:
        """
        Poprawia wyniki z pliku JSON.
        
        Args:
            json_path: Ścieżka do pliku JSON z wynikami
            output_path: Ścieżka do poprawionego pliku
            
        Returns:
            True jeśli udało się poprawić
        """
        try:
            # Wczytaj wyniki
            with open(json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            print(f"📄 Poprawianie: {json_path.name}")
            print(f"   📊 Oryginalnych wyników: {len(results)}")
            
            improved_results = []
            total_names_before = 0
            total_names_after = 0
            
            for result in results:
                title = result['title']
                original_names = result['detected_names']
                
                total_names_before += len(original_names)
                
                # Popraw każde wykryte "nazwisko"
                improved_names = []
                for dirty_name in original_names:
                    clean_names = self.extract_clean_names(dirty_name)
                    improved_names.extend(clean_names)
                
                # Usuń duplikaty
                unique_improved = list(dict.fromkeys(improved_names))
                total_names_after += len(unique_improved)
                
                # Stwórz poprawiony wynik
                improved_result = {
                    'title': title,
                    'original_detected': original_names,
                    'improved_names': unique_improved,
                    'names_count': len(unique_improved),
                    'improvement_applied': True
                }
                
                improved_results.append(improved_result)
            
            # Zapisz poprawione wyniki
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(improved_results, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Poprawione wyniki zapisane: {output_path.name}")
            print(f"   📊 Nazwiska przed: {total_names_before}")
            print(f"   📊 Nazwiska po: {total_names_after}")
            print(f"   📈 Poprawa: {((total_names_after/total_names_before)*100):.1f}% dokładności")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas poprawiania {json_path.name}: {e}")
            return False
    
    def create_improved_csv(self, json_path: Path, csv_output_path: Path) -> bool:
        """
        Tworzy poprawiony plik CSV na podstawie JSON.
        
        Args:
            json_path: Ścieżka do poprawionego pliku JSON
            csv_output_path: Ścieżka do pliku CSV
            
        Returns:
            True jeśli udało się utworzyć
        """
        try:
            # Wczytaj poprawione wyniki
            with open(json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Przygotuj dane dla CSV
            csv_data = []
            for result in results:
                csv_row = {
                    'title': result['title'],
                    'detected_names': ', '.join(result['improved_names']),
                    'names_count': result['names_count']
                }
                csv_data.append(csv_row)
            
            # Zapisz CSV
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_output_path, index=False, encoding='utf-8')
            
            print(f"   💾 Poprawiony CSV zapisany: {csv_output_path.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia CSV: {e}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str) -> bool:
        """
        Przetwarza wszystkie pliki w katalogu.
        
        Args:
            input_dir: Katalog z oryginalnymi wynikami
            output_dir: Katalog na poprawione wyniki
            
        Returns:
            True jeśli przetwarzanie się powiodło
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            print(f"❌ Katalog wejściowy nie istnieje: {input_path}")
            return False
        
        # Utwórz katalog wyjściowy
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Znajdź pliki JSON details
        json_files = list(input_path.glob("*_details.json"))
        
        if not json_files:
            print(f"❌ Nie znaleziono plików *_details.json w {input_path}")
            return False
        
        print(f"🔧 Poprawianie wyników NER")
        print(f"📁 Katalog wejściowy: {input_path}")
        print(f"📁 Katalog wyjściowy: {output_path}")
        print(f"📄 Znalezionych plików: {len(json_files)}")
        
        successful = 0
        
        for json_file in json_files:
            print(f"\n" + "="*50)
            
            # Nazwy plików wyjściowych
            base_name = json_file.stem.replace('_details', '')
            improved_json = output_path / f"{base_name}_improved.json"
            improved_csv = output_path / f"{base_name}_improved.csv"
            
            # Popraw JSON
            if self.improve_json_results(json_file, improved_json):
                # Utwórz CSV
                if self.create_improved_csv(improved_json, improved_csv):
                    successful += 1
        
        print(f"\n🎉 Poprawianie zakończone!")
        print(f"📊 Pomyślnie przetworzonych: {successful}/{len(json_files)}")
        
        return successful > 0


def main():
    """Główna funkcja."""
    parser = argparse.ArgumentParser(
        description="Polepszanie wyników NER - filtrowanie i czyszczenie nazwisk"
    )
    
    parser.add_argument(
        '--input-dir',
        default='ner_outputs',
        help='Katalog z oryginalnymi wynikami NER'
    )
    
    parser.add_argument(
        '--output-dir', 
        default='ner_outputs_improved',
        help='Katalog na poprawione wyniki'
    )
    
    args = parser.parse_args()
    
    # Utwórz ulepszacz
    improver = NERResultsImprover()
    
    # Przetwórz pliki
    success = improver.process_directory(args.input_dir, args.output_dir)
    
    if success:
        print("\n✅ Ulepszanie wyników zakończone pomyślnie!")
    else:
        print("\n❌ Ulepszanie wyników nieudane!")
        exit(1)


if __name__ == "__main__":
    main()