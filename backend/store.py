import json
import os
from typing import List, Dict, Optional
from pathlib import Path

class GuestStore:
    """Klasa do zarządzania danymi gości z pliku JSON."""
    
    def __init__(self, data_file: str = "guest_trend_summary.json"):
        self.data_file = data_file
        self.data_dir = Path("data")
        self.data_path = self.data_dir / data_file
        
        # Utwórz katalog data jeśli nie istnieje
        self.data_dir.mkdir(exist_ok=True)
    
    def load_guests(self) -> List[Dict]:
        """Wczytuje dane gości z pliku JSON."""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            else:
                print(f"Plik {self.data_path} nie istnieje. Zwracam pustą listę.")
                return []
        except Exception as e:
            print(f"Błąd podczas wczytywania danych: {e}")
            return []
    
    def save_guests(self, guests: List[Dict]) -> bool:
        """Zapisuje dane gości do pliku JSON."""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(guests, f, ensure_ascii=False, indent=2)
            print(f"Dane zapisane do {self.data_path}")
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania danych: {e}")
            return False
    
    def get_top_guests(self, limit: int = 10) -> List[Dict]:
        """Zwraca top N gości posortowanych po total_strength."""
        guests = self.load_guests()
        return sorted(guests, key=lambda x: x.get('total_strength', 0), reverse=True)[:limit]
    
    def get_guest_by_name(self, name: str) -> Optional[Dict]:
        """Znajduje gościa po nazwie."""
        guests = self.load_guests()
        for guest in guests:
            if guest.get('name', '').lower() == name.lower():
                return guest
        return None
    
    def get_stats(self) -> Dict:
        """Zwraca statystyki gości."""
        guests = self.load_guests()
        if not guests:
            return {
                'total_guests': 0,
                'total_views': 0,
                'total_mentions': 0,
                'avg_strength': 0
            }
        
        total_views = sum(guest.get('total_views', 0) for guest in guests)
        total_mentions = sum(guest.get('total_mentions', 0) for guest in guests)
        avg_strength = sum(guest.get('total_strength', 0) for guest in guests) / len(guests)
        
        return {
            'total_guests': len(guests),
            'total_views': total_views,
            'total_mentions': total_mentions,
            'avg_strength': round(avg_strength, 2)
        }

# Przykład użycia
if __name__ == "__main__":
    store = GuestStore()
    
    # Przykładowe dane
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
        }
    ]
    
    # Zapisz przykładowe dane
    store.save_guests(sample_guests)
    
    # Wczytaj i wyświetl dane
    guests = store.load_guests()
    print(f"Wczytano {len(guests)} gości:")
    for guest in guests:
        print(f"- {guest['name']}: {guest['total_strength']} strength")
    
    # Wyświetl statystyki
    stats = store.get_stats()
    print(f"\nStatystyki: {stats}") 