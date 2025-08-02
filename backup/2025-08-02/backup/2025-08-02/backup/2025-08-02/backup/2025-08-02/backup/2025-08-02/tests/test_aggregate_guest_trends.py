#!/usr/bin/env python3
"""
Testy dla modułu aggregate_guest_trends
"""

import json
import tempfile
import shutil
from pathlib import Path
import sys
import unittest

# Dodaj ścieżkę do modułów
sys.path.append(str(Path(__file__).parent.parent))

from analyzer.aggregate_guest_trends import aggregate_guest_trends, get_aggregated_stats


class TestAggregateGuestTrends(unittest.TestCase):
    """Testy dla funkcji agregacji danych gości"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        # Utwórz tymczasowy folder
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_folder = Path(self.temp_dir) / "test_analysis_results"
        self.test_input_folder.mkdir()
        
        # Przykładowe dane testowe
        self.test_data_1 = {
            "data_date": "2025-07-30",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 100.0, "total_views": 1000, "mentions": 2},
                {"name": "Anna Nowak", "strength": 200.0, "total_views": 2000, "mentions": 3}
            ]
        }
        
        self.test_data_2 = {
            "data_date": "2025-07-31",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 150.0, "total_views": 1500, "mentions": 1},
                {"name": "Piotr Wiśniewski", "strength": 300.0, "total_views": 3000, "mentions": 4}
            ]
        }
        
        self.test_data_3 = {
            "data_date": "2025-08-01",
            "guest_ranking": [
                {"name": "Jan Kowalski", "strength": 75.0, "total_views": 750, "mentions": 1},
                {"name": "Anna Nowak", "strength": 125.0, "total_views": 1250, "mentions": 2}
            ]
        }
        
        # Utwórz pliki testowe
        self.create_test_files()
    
    def create_test_files(self):
        """Tworzy pliki testowe"""
        test_files = [
            ("guest_summary_2025-07-30.json", self.test_data_1),
            ("guest_summary_2025-07-31.json", self.test_data_2),
            ("guest_summary_2025-08-01.json", self.test_data_3)
        ]
        
        for filename, data in test_files:
            file_path = self.test_input_folder / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    
    def tearDown(self):
        """Czyszczenie po testach"""
        shutil.rmtree(self.temp_dir)
    
    def test_aggregate_guest_trends_basic(self):
        """Test podstawowej agregacji danych"""
        output_file = Path(self.temp_dir) / "aggregated" / "guest_trend_summary.json"
        
        # Uruchom agregację
        aggregate_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Sprawdź czy plik został utworzony
        self.assertTrue(output_file.exists(), "Plik wynikowy nie został utworzony")
        
        # Wczytaj wynik
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Sprawdź strukturę wyniku
        self.assertIsInstance(result, list, "Wynik powinien być listą")
        self.assertGreater(len(result), 0, "Wynik nie powinien być pusty")
        
        # Sprawdź czy wszystkie wymagane pola są obecne
        required_fields = ['name', 'total_strength', 'total_views', 'total_mentions', 'active_days']
        for guest in result:
            for field in required_fields:
                self.assertIn(field, guest, f"Brak pola {field} w wyniku")
    
    def test_aggregate_guest_trends_calculations(self):
        """Test poprawności obliczeń"""
        output_file = Path(self.temp_dir) / "aggregated" / "guest_trend_summary.json"
        
        # Uruchom agregację
        aggregate_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Wczytaj wynik
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Znajdź Jan Kowalski w wynikach
        jan_kowalski = None
        for guest in result:
            if guest['name'] == 'Jan Kowalski':
                jan_kowalski = guest
                break
        
        self.assertIsNotNone(jan_kowalski, "Jan Kowalski powinien być w wynikach")
        
        # Sprawdź obliczenia dla Jan Kowalski
        # Dni: 3 (występuje we wszystkich 3 plikach)
        # Siła: 100.0 + 150.0 + 75.0 = 325.0
        # Wyświetlenia: 1000 + 1500 + 750 = 3250
        # Wystąpienia: 2 + 1 + 1 = 4
        
        self.assertEqual(jan_kowalski['active_days'], 3, "Nieprawidłowa liczba aktywnych dni")
        self.assertEqual(jan_kowalski['total_strength'], 325.0, "Nieprawidłowa suma siły")
        self.assertEqual(jan_kowalski['total_views'], 3250, "Nieprawidłowa suma wyświetleń")
        self.assertEqual(jan_kowalski['total_mentions'], 4, "Nieprawidłowa suma wystąpień")
    
    def test_aggregate_guest_trends_sorting(self):
        """Test sortowania malejąco po total_strength"""
        output_file = Path(self.temp_dir) / "aggregated" / "guest_trend_summary.json"
        
        # Uruchom agregację
        aggregate_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Wczytaj wynik
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Sprawdź czy wyniki są posortowane malejąco
        for i in range(len(result) - 1):
            self.assertGreaterEqual(
                result[i]['total_strength'], 
                result[i + 1]['total_strength'],
                "Wyniki nie są posortowane malejąco po total_strength"
            )
    
    def test_aggregate_guest_trends_empty_folder(self):
        """Test obsługi pustego folderu"""
        empty_folder = Path(self.temp_dir) / "empty_folder"
        empty_folder.mkdir()
        
        output_file = Path(self.temp_dir) / "aggregated" / "empty_result.json"
        
        # Uruchom agregację na pustym folderze
        aggregate_guest_trends(str(empty_folder), str(output_file))
        
        # Sprawdź czy plik nie został utworzony (bo nie ma danych)
        self.assertFalse(output_file.exists(), "Plik nie powinien zostać utworzony dla pustego folderu")
    
    def test_aggregate_guest_trends_invalid_file(self):
        """Test obsługi niepoprawnego pliku"""
        # Utwórz niepoprawny plik JSON
        invalid_file = self.test_input_folder / "guest_summary_invalid.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": "json"')
        
        output_file = Path(self.temp_dir) / "aggregated" / "invalid_test.json"
        
        # Uruchom agregację (powinna pominąć niepoprawny plik)
        aggregate_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Sprawdź czy plik wynikowy został utworzony (z pozostałymi danymi)
        self.assertTrue(output_file.exists(), "Plik wynikowy powinien zostać utworzony")
    
    def test_get_aggregated_stats(self):
        """Test funkcji get_aggregated_stats"""
        output_file = Path(self.temp_dir) / "aggregated" / "stats_test.json"
        
        # Uruchom agregację
        aggregate_guest_trends(str(self.test_input_folder), str(output_file))
        
        # Pobierz statystyki
        stats = get_aggregated_stats(str(output_file))
        
        # Sprawdź czy statystyki są poprawne
        self.assertIn('total_guests', stats, "Brak total_guests w statystykach")
        self.assertIn('total_strength', stats, "Brak total_strength w statystykach")
        self.assertIn('total_views', stats, "Brak total_views w statystykach")
        self.assertIn('total_mentions', stats, "Brak total_mentions w statystykach")
        self.assertIn('avg_active_days', stats, "Brak avg_active_days w statystykach")
        
        # Sprawdź czy wartości są rozsądne
        self.assertGreater(stats['total_guests'], 0, "Liczba gości powinna być większa od 0")
        self.assertGreater(stats['total_strength'], 0, "Łączna siła powinna być większa od 0")
        self.assertGreater(stats['avg_active_days'], 0, "Średnia liczba dni powinna być większa od 0")


if __name__ == '__main__':
    # Uruchom testy
    unittest.main(verbosity=2) 