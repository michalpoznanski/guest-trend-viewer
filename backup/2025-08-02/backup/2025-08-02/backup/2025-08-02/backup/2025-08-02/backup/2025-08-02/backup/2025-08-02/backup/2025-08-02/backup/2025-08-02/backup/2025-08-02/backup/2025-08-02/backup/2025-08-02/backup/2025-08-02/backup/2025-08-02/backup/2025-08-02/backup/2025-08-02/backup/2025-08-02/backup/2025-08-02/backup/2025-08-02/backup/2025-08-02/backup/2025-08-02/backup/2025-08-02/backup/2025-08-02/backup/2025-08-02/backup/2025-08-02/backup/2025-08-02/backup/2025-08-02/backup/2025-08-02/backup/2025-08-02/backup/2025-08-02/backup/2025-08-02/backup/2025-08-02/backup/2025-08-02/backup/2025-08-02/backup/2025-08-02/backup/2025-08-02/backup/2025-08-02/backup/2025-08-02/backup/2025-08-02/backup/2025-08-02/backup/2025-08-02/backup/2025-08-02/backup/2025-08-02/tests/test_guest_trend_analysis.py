#!/usr/bin/env python3
"""
Testy dla modułu guest_trend_analysis
"""

import json
import tempfile
import shutil
from pathlib import Path
import sys
import unittest

# Dodaj ścieżkę do modułów
sys.path.append(str(Path(__file__).parent.parent))

from analyzer.guest_trend_analysis import (
    load_guest_summary_files, 
    build_guest_trends, 
    analyze_guest_trends,
    get_trend_statistics
)


class TestGuestTrendAnalysis(unittest.TestCase):
    """Testy dla funkcji analizy trendów gości"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        # Utwórz tymczasowy folder
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_folder = Path(self.temp_dir) / "test_analysis_results"
        self.test_input_folder.mkdir()
        
        # Przykładowe dane testowe z trendami
        self.test_data_1 = {
            "data_date": "2025-07-28",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 100.0, "total_views": 1000, "mentions": 2},
                {"name": "Anna Nowak", "strength": 200.0, "total_views": 2000, "mentions": 3}
            ]
        }
        
        self.test_data_2 = {
            "data_date": "2025-07-30",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 150.0, "total_views": 1500, "mentions": 1},
                {"name": "Anna Nowak", "strength": 180.0, "total_views": 1800, "mentions": 2},
                {"name": "Piotr Wiśniewski", "strength": 300.0, "total_views": 3000, "mentions": 4}
            ]
        }
        
        self.test_data_3 = {
            "data_date": "2025-08-01",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 250.0, "total_views": 2500, "mentions": 3},
                {"name": "Anna Nowak", "strength": 120.0, "total_views": 1200, "mentions": 1}
            ]
        }
        
        # Utwórz pliki testowe
        self.create_test_files()
    
    def create_test_files(self):
        """Tworzy pliki testowe"""
        test_files = [
            ("guest_summary_2025-07-28.json", self.test_data_1),
            ("guest_summary_2025-07-30.json", self.test_data_2),
            ("guest_summary_2025-08-01.json", self.test_data_3)
        ]
        
        for filename, data in test_files:
            file_path = self.test_input_folder / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    
    def tearDown(self):
        """Czyszczenie po testach"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_guest_summary_files(self):
        """Test wczytywania plików guest_summary"""
        loaded_data = load_guest_summary_files(str(self.test_input_folder))
        
        self.assertEqual(len(loaded_data), 3, "Powinno wczytać 3 pliki")
        
        # Sprawdź czy wszystkie wymagane daty są obecne
        dates = [data['data_date'] for data in loaded_data]
        expected_dates = ['2025-07-28', '2025-07-30', '2025-08-01']
        for expected_date in expected_dates:
            self.assertIn(expected_date, dates, f"Brak daty {expected_date} w wynikach")
    
    def test_build_guest_trends(self):
        """Test budowania trendów gości"""
        loaded_data = load_guest_summary_files(str(self.test_input_folder))
        trends = build_guest_trends(loaded_data)
        
        self.assertEqual(len(trends), 3, "Powinno być 3 gości")
        
        # Znajdź Jan Kowalski
        jan_kowalski = next((guest for guest in trends if guest['name'] == 'Jan Kowalski'), None)
        self.assertIsNotNone(jan_kowalski, "Jan Kowalski powinien być w wynikach")
        
        # Sprawdź dane dla Jan Kowalski
        self.assertEqual(jan_kowalski['days_active'], 3, "Jan Kowalski powinien być aktywny 3 dni")
        self.assertEqual(jan_kowalski['total_change'], 150.0, "Zmiana powinna być 150.0 (250-100)")
        
        # Sprawdź daily_strength
        expected_strength = {
            "2025-07-28": 100.0,
            "2025-07-30": 150.0,
            "2025-08-01": 250.0
        }
        self.assertEqual(jan_kowalski['daily_strength'], expected_strength)
    
    def test_build_guest_trends_sorting(self):
        """Test sortowania trendów malejąco po total_change"""
        loaded_data = load_guest_summary_files(str(self.test_input_folder))
        trends = build_guest_trends(loaded_data)
        
        # Sprawdź czy wyniki są posortowane malejąco po total_change
        for i in range(len(trends) - 1):
            self.assertGreaterEqual(
                trends[i]['total_change'], 
                trends[i + 1]['total_change'],
                "Wyniki nie są posortowane malejąco po total_change"
            )
    
    def test_analyze_guest_trends(self):
        """Test głównej funkcji analizy trendów"""
        output_file = Path(self.temp_dir) / "aggregated" / "test_trend_evolution.json"
        
        # Uruchom analizę
        analyze_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Sprawdź czy plik został utworzony
        self.assertTrue(output_file.exists(), "Plik wynikowy nie został utworzony")
        
        # Wczytaj wynik
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Sprawdź strukturę wyniku
        self.assertIsInstance(result, list, "Wynik powinien być listą")
        self.assertEqual(len(result), 3, "Powinno być 3 gości")
        
        # Sprawdź czy wszystkie wymagane pola są obecne
        required_fields = ['name', 'daily_strength', 'total_change', 'days_active']
        for guest in result:
            for field in required_fields:
                self.assertIn(field, guest, f"Brak pola {field} w wyniku")
    
    def test_get_trend_statistics(self):
        """Test funkcji get_trend_statistics"""
        output_file = Path(self.temp_dir) / "aggregated" / "test_trend_evolution.json"
        
        # Uruchom analizę
        analyze_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Pobierz statystyki
        stats = get_trend_statistics(str(output_file))
        
        # Sprawdź czy statystyki są poprawne
        self.assertIn('total_guests', stats, "Brak total_guests w statystykach")
        self.assertIn('total_change', stats, "Brak total_change w statystykach")
        self.assertIn('avg_days_active', stats, "Brak avg_days_active w statystykach")
        self.assertIn('max_increase', stats, "Brak max_increase w statystykach")
        self.assertIn('max_decrease', stats, "Brak max_decrease w statystykach")
        
        # Sprawdź czy wartości są rozsądne
        self.assertEqual(stats['total_guests'], 3, "Powinno być 3 gości")
        self.assertGreater(stats['avg_days_active'], 0, "Średnia liczba dni powinna być większa od 0")
    
    def test_empty_folder(self):
        """Test obsługi pustego folderu"""
        empty_folder = Path(self.temp_dir) / "empty_folder"
        empty_folder.mkdir()
        
        loaded_data = load_guest_summary_files(str(empty_folder))
        self.assertEqual(len(loaded_data), 0, "Powinno zwrócić pustą listę dla pustego folderu")
    
    def test_invalid_file(self):
        """Test obsługi niepoprawnego pliku"""
        # Utwórz niepoprawny plik JSON
        invalid_file = self.test_input_folder / "guest_summary_invalid.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": "json"')
        
        loaded_data = load_guest_summary_files(str(self.test_input_folder))
        
        # Powinno wczytać tylko poprawne pliki
        self.assertEqual(len(loaded_data), 3, "Powinno wczytać tylko poprawne pliki")


if __name__ == '__main__':
    # Uruchom testy
    unittest.main(verbosity=2) 