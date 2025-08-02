import pandas as pd
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import os

class GuestAnalyzer:
    """Parser CSV/JSON do analizy danych gości i generowania rankingu."""
    
    def __init__(self, reports_dir: str = "/mnt/volume/reports"):
        self.reports_dir = Path(reports_dir)
        self.guest_store = None  # Będzie zainicjalizowany z zewnątrz
    
    def extract_guest_names(self, text: str) -> List[str]:
        """Wyciąga potencjalne nazwiska gości z tekstu."""
        if not text or pd.isna(text):
            return []
        
        # Proste wyciąganie nazwisk - można rozszerzyć o bardziej zaawansowane metody
        # Szukamy wzorców typu "Imię Nazwisko" lub "Nazwisko"
        words = str(text).split()
        names = []
        
        for i, word in enumerate(words):
            # Sprawdź czy słowo wygląda jak nazwisko (duże litery, minimum 3 znaki)
            if len(word) >= 3 and word[0].isupper() and word.isalpha():
                # Jeśli to pierwsze słowo lub poprzednie też wygląda jak imię
                if i == 0 or (i > 0 and len(words[i-1]) >= 2 and words[i-1][0].isupper()):
                    if i > 0:
                        names.append(f"{words[i-1]} {word}")
                    else:
                        names.append(word)
        
        return list(set(names))  # Usuń duplikaty
    
    def calculate_guest_strength(self, guest_name: str, row: pd.Series) -> float:
        """Oblicza siłę gościa na podstawie różnych czynników."""
        strength = 0.0
        
        # Sprawdź wystąpienia w różnych polach
        title = str(row.get('title', '')).lower()
        description = str(row.get('description', '')).lower()
        tags = str(row.get('tags', '')).lower()
        
        guest_lower = guest_name.lower()
        
        # Wagi dla różnych pól
        if guest_lower in title:
            strength += 1.5
        if guest_lower in description:
            strength += 1.0
        if guest_lower in tags:
            strength += 0.5
        
        # Mnożnik dla typu filmu
        video_type = str(row.get('video_type', '')).lower()
        if 'short' in video_type:
            strength *= 0.5
        elif 'long' in video_type:
            strength *= 1.0
        
        # Mnożnik dla wyświetleń
        views = row.get('views', 0)
        if views > 0:
            strength *= (views / 1000)  # Normalizacja wyświetleń
        
        return round(strength, 2)
    
    def analyze_csv_file(self, file_path: Path) -> List[Dict]:
        """Analizuje pojedynczy plik CSV i zwraca dane gości."""
        try:
            df = pd.read_csv(file_path)
            print(f"Analizuję plik: {file_path}")
            
            guest_data = {}
            
            for _, row in df.iterrows():
                # Wyciągnij nazwiska z różnych pól
                title_names = self.extract_guest_names(row.get('title', ''))
                desc_names = self.extract_guest_names(row.get('description', ''))
                tags_names = self.extract_guest_names(row.get('tags', ''))
                
                all_names = title_names + desc_names + tags_names
                
                for name in all_names:
                    if name not in guest_data:
                        guest_data[name] = {
                            'name': name,
                            'total_strength': 0,
                            'total_views': 0,
                            'total_mentions': 0,
                            'active_days': 1
                        }
                    
                    # Oblicz siłę dla tego wystąpienia
                    strength = self.calculate_guest_strength(name, row)
                    guest_data[name]['total_strength'] += strength
                    guest_data[name]['total_views'] += row.get('views', 0)
                    guest_data[name]['total_mentions'] += 1
            
            return list(guest_data.values())
            
        except Exception as e:
            print(f"Błąd podczas analizy pliku {file_path}: {e}")
            return []
    
    def analyze_all_reports(self) -> List[Dict]:
        """Analizuje wszystkie pliki CSV w katalogu raportów."""
        if not self.reports_dir.exists():
            print(f"Katalog {self.reports_dir} nie istnieje!")
            return []
        
        all_guests = {}
        
        # Znajdź wszystkie pliki CSV
        csv_files = list(self.reports_dir.glob("*.csv"))
        print(f"Znaleziono {len(csv_files)} plików CSV do analizy")
        
        for csv_file in csv_files:
            file_guests = self.analyze_csv_file(csv_file)
            
            # Agreguj dane z wszystkich plików
            for guest in file_guests:
                name = guest['name']
                if name not in all_guests:
                    all_guests[name] = guest
                else:
                    all_guests[name]['total_strength'] += guest['total_strength']
                    all_guests[name]['total_views'] += guest['total_views']
                    all_guests[name]['total_mentions'] += guest['total_mentions']
                    all_guests[name]['active_days'] += 1
        
        # Konwertuj na listę i posortuj
        guests_list = list(all_guests.values())
        guests_list.sort(key=lambda x: x['total_strength'], reverse=True)
        
        # Zaokrąglij wartości
        for guest in guests_list:
            guest['total_strength'] = round(guest['total_strength'], 2)
            guest['total_views'] = int(guest['total_views'])
            guest['total_mentions'] = int(guest['total_mentions'])
            guest['active_days'] = int(guest['active_days'])
        
        return guests_list
    
    def generate_ranking(self) -> bool:
        """Generuje ranking gości i zapisuje do JSON."""
        try:
            print("Rozpoczynam analizę raportów...")
            guests = self.analyze_all_reports()
            
            if not guests:
                print("Nie znaleziono danych gości!")
                return False
            
            print(f"Znaleziono {len(guests)} unikalnych gości")
            
            # Zapisz do pliku JSON
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            output_file = data_dir / "guest_trend_summary.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(guests, f, ensure_ascii=False, indent=2)
            
            print(f"Ranking zapisany do {output_file}")
            print(f"Top 5 gości:")
            for i, guest in enumerate(guests[:5], 1):
                print(f"{i}. {guest['name']} - {guest['total_strength']} strength")
            
            return True
            
        except Exception as e:
            print(f"Błąd podczas generowania rankingu: {e}")
            return False

# Przykład użycia
if __name__ == "__main__":
    analyzer = GuestAnalyzer()
    
    # Sprawdź czy katalog raportów istnieje
    if analyzer.reports_dir.exists():
        analyzer.generate_ranking()
    else:
        print(f"Katalog {analyzer.reports_dir} nie istnieje!")
        print("Uruchom z przykładowymi danymi...")
        
        # Utwórz przykładowe dane
        sample_guests = [
            {
                "name": "Jan Kowalski",
                "total_strength": 123456.78,
                "total_views": 98765,
                "total_mentions": 12,
                "active_days": 3
            },
            {
                "name": "Anna Nowak",
                "total_strength": 98765.43,
                "total_views": 54321,
                "total_mentions": 8,
                "active_days": 2
            },
            {
                "name": "Piotr Wiśniewski",
                "total_strength": 65432.10,
                "total_views": 32109,
                "total_mentions": 5,
                "active_days": 1
            }
        ]
        
        # Zapisz przykładowe dane
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        output_file = data_dir / "guest_trend_summary.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_guests, f, ensure_ascii=False, indent=2)
        
        print(f"Przykładowe dane zapisane do {output_file}") 