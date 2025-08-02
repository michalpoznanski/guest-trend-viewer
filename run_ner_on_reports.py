#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uruchamiania lokalnego modelu NER na danych z raportów CSV

Funkcjonalności:
1. Ładuje model spaCy z ner_model_improved/
2. Iteruje po plikach CSV Podcast_*.csv
3. Uruchamia NER na kolumnie 'title' 
4. Zapisuje wykryte nazwiska PERSON do nowego CSV
5. Działa offline, bez połączenia internetowego

Użycie:
    python3 run_ner_on_reports.py [--reports-dir PATH] [--output-dir PATH]

Autor: Guest Radar System
Data: 2025-08-03
"""

import os
import pandas as pd
import spacy
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import re
import warnings
warnings.filterwarnings("ignore")


class NERReportProcessor:
    """Procesor NER dla raportów CSV."""
    
    def __init__(self, 
                 model_path: str = "ner_model_improved",
                 reports_dir: str = "/mnt/volume/reports",
                 output_dir: str = "ner_outputs"):
        """
        Inicjalizuje procesor NER.
        
        Args:
            model_path: Ścieżka do modelu spaCy
            reports_dir: Katalog z raportami CSV
            output_dir: Katalog wyjściowy dla wyników
        """
        self.model_path = model_path
        self.reports_dir = Path(reports_dir)
        self.output_dir = Path(output_dir)
        self.nlp = None
        
        # Utwórz katalog wyjściowy
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_ner_model(self) -> bool:
        """
        Ładuje model spaCy NER.
        
        Returns:
            True jeśli model załadowany pomyślnie
        """
        try:
            print(f"🤖 Ładowanie modelu NER: {self.model_path}")
            
            # Sprawdź czy model istnieje
            model_path = Path(self.model_path)
            if not model_path.exists():
                print(f"❌ Model nie istnieje: {model_path.absolute()}")
                return False
                
            # Załaduj model
            self.nlp = spacy.load(model_path)
            
            # Sprawdź komponenty
            print(f"✅ Model załadowany pomyślnie")
            print(f"   🔧 Pipeline: {self.nlp.pipe_names}")
            
            if "ner" in self.nlp.pipe_names:
                ner = self.nlp.get_pipe("ner")
                print(f"   🏷️  Etykiety NER: {ner.labels}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas ładowania modelu: {e}")
            return False
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        Wydobywa datę z nazwy pliku.
        
        Args:
            filename: Nazwa pliku, np. "Podcast_20250729_230058.csv"
            
        Returns:
            Data w formacie YYYY-MM-DD lub None
        """
        # Wzorzec dla daty w nazwie pliku Podcast_YYYYMMDD_HHMMSS.csv
        pattern = r'Podcast_(\d{4})(\d{2})(\d{2})_\d+\.csv'
        match = re.search(pattern, filename)
        
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        
        # Fallback - spróbuj znaleźć dowolną datę
        pattern_fallback = r'(\d{4}-\d{2}-\d{2})'
        match_fallback = re.search(pattern_fallback, filename)
        
        if match_fallback:
            return match_fallback.group(1)
            
        return None
    
    def find_report_files(self) -> List[Path]:
        """
        Znajduje pliki raportów CSV.
        
        Returns:
            Lista ścieżek do plików raportów
        """
        if not self.reports_dir.exists():
            print(f"❌ Katalog raportów nie istnieje: {self.reports_dir.absolute()}")
            return []
        
        # Znajdź pliki Podcast_*.csv
        pattern = "Podcast_*.csv"
        all_files = list(self.reports_dir.glob(pattern))
        
        # Dodatkowa walidacja - sprawdź końcówkę .csv (case-insensitive)
        report_files = []
        for file_path in all_files:
            if file_path.name.lower().endswith(".csv"):
                report_files.append(file_path)
        
        print(f"📁 Znaleziono {len(report_files)} plików raportów:")
        for file_path in sorted(report_files):
            print(f"   📄 {file_path.name}")
        
        return sorted(report_files)
    
    def extract_names_from_title(self, title: str) -> List[Dict[str, str]]:
        """
        Wydobywa nazwiska z tytułu używając modelu NER.
        
        Args:
            title: Tytuł do analizy
            
        Returns:
            Lista słowników z informacjami o wykrytych nazwiskach
        """
        if not title or not isinstance(title, str):
            return []
        
        try:
            # Uruchom model NER
            doc = self.nlp(title.strip())
            
            # Zbierz encje PERSON
            names = []
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    names.append({
                        "text": ent.text.strip(),
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 1.0  # spaCy nie zwraca confidence dla custom modeli
                    })
            
            return names
            
        except Exception as e:
            print(f"⚠️ Błąd podczas przetwarzania tytułu '{title}': {e}")
            return []
    
    def process_csv_file(self, csv_path: Path) -> bool:
        """
        Przetwarza pojedynczy plik CSV.
        
        Args:
            csv_path: Ścieżka do pliku CSV
            
        Returns:
            True jeśli przetwarzanie się powiodło
        """
        try:
            print(f"\n📊 Przetwarzanie: {csv_path.name}")
            
            # Wczytaj CSV
            df = pd.read_csv(csv_path)
            print(f"   📋 Wierszy: {len(df)}")
            print(f"   🏷️  Kolumny: {list(df.columns)}")
            
            # Sprawdź czy kolumna 'title' lub 'Title' istnieje
            title_column = None
            if 'title' in df.columns:
                title_column = 'title'
            elif 'Title' in df.columns:
                title_column = 'Title'
            else:
                print(f"   ❌ Brak kolumny 'title' lub 'Title' w pliku {csv_path.name}")
                return False
            
            # Przygotuj wyniki
            results = []
            processed_count = 0
            names_found = 0
            
            print(f"   🔍 Uruchamianie NER na {len(df)} tytułach z kolumny '{title_column}'...")
            
            for idx, row in df.iterrows():
                title = row.get(title_column, '')
                
                # Wydobądź nazwiska
                detected_names = self.extract_names_from_title(title)
                
                # Przygotuj listę nazw
                name_texts = [name['text'] for name in detected_names]
                
                # Dodaj do wyników
                result = {
                    'title': title,
                    'detected_names': name_texts,
                    'names_count': len(name_texts),
                    'names_details': detected_names  # pełne informacje
                }
                results.append(result)
                
                processed_count += 1
                names_found += len(name_texts)
                
                # Wyświetl postęp co 100 wierszy
                if processed_count % 100 == 0:
                    print(f"   ⏳ Przetworzono: {processed_count}/{len(df)} ({names_found} nazwisk)")
            
            print(f"   ✅ Przetwarzanie zakończone:")
            print(f"      • Wierszy: {processed_count}")
            print(f"      • Wykrytych nazwisk: {names_found}")
            print(f"      • Średnio na tytuł: {names_found/processed_count:.2f}")
            
            # Zapisz wyniki
            success = self.save_results(csv_path, results)
            
            return success
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania {csv_path.name}: {e}")
            return False
    
    def save_results(self, original_csv_path: Path, results: List[Dict]) -> bool:
        """
        Zapisuje wyniki do pliku CSV.
        
        Args:
            original_csv_path: Ścieżka do oryginalnego pliku
            results: Lista wyników do zapisania
            
        Returns:
            True jeśli zapis się powiódł
        """
        try:
            # Wydobądź datę z nazwy pliku
            date_str = self.extract_date_from_filename(original_csv_path.name)
            
            if date_str:
                output_filename = f"ner_output_{date_str}.csv"
            else:
                # Fallback - użyj timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"ner_output_{timestamp}.csv"
            
            output_path = self.output_dir / output_filename
            
            # Przygotuj DataFrame
            df_output = pd.DataFrame([
                {
                    'title': result['title'],
                    'detected_names': ', '.join(result['detected_names']),
                    'names_count': result['names_count']
                }
                for result in results
            ])
            
            # Zapisz CSV
            df_output.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"   💾 Wyniki zapisane: {output_path.name}")
            print(f"      📁 Ścieżka: {output_path.absolute()}")
            
            # Zapisz też szczegółowe wyniki jako JSON
            json_filename = output_filename.replace('.csv', '_details.json')
            json_path = self.output_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"   📄 Szczegóły zapisane: {json_filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania wyników: {e}")
            return False
    
    def show_statistics(self, results: List[Dict]) -> None:
        """
        Wyświetla statystyki przetwarzania.
        
        Args:
            results: Lista wyników ze wszystkich plików
        """
        if not results:
            print("📊 Brak wyników do analizy")
            return
        
        print(f"\n📊 STATYSTYKI OGÓLNE:")
        print("=" * 50)
        
        total_files = len(results)
        successful_files = sum(1 for r in results if r['success'])
        failed_files = total_files - successful_files
        
        print(f"📁 Pliki:")
        print(f"   • Łącznie: {total_files}")
        print(f"   • Udane: {successful_files}")
        print(f"   • Nieudane: {failed_files}")
        
        if successful_files > 0:
            total_titles = sum(r.get('titles_processed', 0) for r in results if r['success'])
            total_names = sum(r.get('names_found', 0) for r in results if r['success'])
            
            print(f"\n🔍 Przetwarzanie:")
            print(f"   • Tytułów przeanalizowanych: {total_titles}")
            print(f"   • Nazwisk wykrytych: {total_names}")
            print(f"   • Średnio na tytuł: {total_names/total_titles:.2f}")
            
            # Top nazwiska
            all_names = {}
            for r in results:
                if r['success'] and 'names_found_list' in r:
                    for name in r['names_found_list']:
                        all_names[name] = all_names.get(name, 0) + 1
            
            if all_names:
                print(f"\n👥 TOP 10 WYKRYTYCH NAZWISK:")
                sorted_names = sorted(all_names.items(), key=lambda x: x[1], reverse=True)
                for i, (name, count) in enumerate(sorted_names[:10], 1):
                    print(f"   {i:2d}. {name} ({count} wystąpień)")
    
    def run_processing(self) -> bool:
        """
        Uruchamia pełne przetwarzanie raportów.
        
        Returns:
            True jeśli przetwarzanie się powiodło
        """
        print("🚀 URUCHAMIANIE PRZETWARZANIA NER NA RAPORTACH")
        print("=" * 60)
        
        # 1. Załaduj model
        if not self.load_ner_model():
            print("❌ Nie udało się załadować modelu NER")
            return False
        
        # 2. Znajdź pliki raportów
        report_files = self.find_report_files()
        if not report_files:
            print("❌ Nie znaleziono plików raportów")
            return False
        
        # 3. Przetwórz każdy plik
        results = []
        
        for csv_path in report_files:
            print(f"\n" + "="*60)
            success = self.process_csv_file(csv_path)
            
            result = {
                'file': csv_path.name,
                'success': success
            }
            results.append(result)
        
        # 4. Podsumowanie
        print(f"\n" + "="*60)
        print(f"🎉 PRZETWARZANIE ZAKOŃCZONE")
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        print(f"📊 Wyniki: {successful}/{total} plików przetworzonych pomyślnie")
        
        if successful > 0:
            print(f"📁 Wyniki zapisane w: {self.output_dir.absolute()}")
        
        return successful > 0


def main():
    """Główna funkcja."""
    parser = argparse.ArgumentParser(
        description="Uruchamianie modelu NER na raportach CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:

1. Domyślne katalogi:
   python3 run_ner_on_reports.py

2. Własne katalogi:
   python3 run_ner_on_reports.py --reports-dir ./test_reports --output-dir ./results

3. Tylko model lokalny:
   python3 run_ner_on_reports.py --reports-dir ./data --model ner_model_improved
        """
    )
    
    parser.add_argument(
        '--model', 
        default='ner_model_improved',
        help='Ścieżka do modelu spaCy NER (default: ner_model_improved)'
    )
    
    parser.add_argument(
        '--reports-dir',
        default='/mnt/volume/reports',
        help='Katalog z raportami CSV (default: /mnt/volume/reports)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='ner_outputs',
        help='Katalog wyjściowy (default: ner_outputs)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Tryb testowy z przykładowymi danymi'
    )
    
    args = parser.parse_args()
    
    # Tryb testowy
    if args.test:
        print("🧪 TRYB TESTOWY - tworzenie przykładowych danych")
        create_test_data()
        args.reports_dir = "test_reports"
    
    # Utwórz procesor
    processor = NERReportProcessor(
        model_path=args.model,
        reports_dir=args.reports_dir,
        output_dir=args.output_dir
    )
    
    # Uruchom przetwarzanie
    success = processor.run_processing()
    
    if success:
        print("\n✅ Przetwarzanie zakończone pomyślnie!")
    else:
        print("\n❌ Przetwarzanie nieudane!")
        exit(1)


def create_test_data():
    """Tworzy przykładowe dane testowe."""
    test_dir = Path("test_reports")
    test_dir.mkdir(exist_ok=True)
    
    # Przykładowe dane
    test_data = [
        {
            'title': 'Wywiad z Jakubem Żulczykiem o nowej książce',
            'view_count': 15432,
            'duration': '01:23:45'
        },
        {
            'title': 'Anna Kowalska i Piotr Nowak dyskutują o polityce',
            'view_count': 8765,
            'duration': '00:45:12'
        },
        {
            'title': 'Program z Kubą Wojewódzkim - special edition',
            'view_count': 23456,
            'duration': '02:15:30'
        },
        {
            'title': 'Rozmowa z dr. Marią Zawadzką o medycynie',
            'view_count': 5678,
            'duration': '01:05:20'
        },
        {
            'title': 'Marcin Prokop prowadzi show z celebrytami',
            'view_count': 19876,
            'duration': '01:45:10'
        }
    ]
    
    # Utwórz pliki testowe
    test_files = [
        'report_PODCAST_2025-07-30.csv',
        'report_PODCAST_2025-07-31.csv'
    ]
    
    for filename in test_files:
        filepath = test_dir / filename
        df = pd.DataFrame(test_data)
        df.to_csv(filepath, index=False)
        print(f"   📄 Utworzono: {filepath}")


if __name__ == "__main__":
    main()