import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Optional
import re

# Dodaj ścieżkę do innych modułów
sys.path.append(str(Path(__file__).parent))
from normalizer import NameNormalizer
sys.path.append(str(Path(__file__).parent.parent))
from active_learning.feedback_handler import FeedbackHandler


class NameStrengthCalculator:
    """
    Klasa do obliczania siły nazwisk na podstawie różnych czynników
    """
    
    def __init__(self, df: pd.DataFrame, normalizer: NameNormalizer, 
                 feedback_handler: Optional[FeedbackHandler] = None):
        """
        Inicjalizacja NameStrengthCalculator
        
        Args:
            df: DataFrame z danymi raportu
            normalizer: Instancja NameNormalizer
            feedback_handler: Instancja FeedbackHandler (opcjonalnie)
        """
        self.df = df.copy()
        self.normalizer = normalizer
        self.feedback_handler = feedback_handler
        
        # Wagi dla różnych pól
        self.field_weights = {
            'title': 1.5,
            'description': 1.0,
            'tags': 0.5
        }
        
        # Wagi dla typów filmów
        self.video_type_weights = {
            'shorts': 0.5,
            'longs': 1.0
        }
    
    def _count_mentions_in_text(self, text: str, name: str) -> int:
        """
        Liczy wystąpienia nazwiska w tekście (case-insensitive)
        
        Args:
            text: Tekst do przeszukania
            name: Nazwisko do znalezienia
            
        Returns:
            Liczba wystąpień
        """
        if pd.isna(text) or not text:
            return 0
        
        text = str(text).lower()
        name = name.lower()
        
        # Użyj regex do znalezienia całych słów
        pattern = r'\b' + re.escape(name) + r'\b'
        matches = re.findall(pattern, text)
        
        return len(matches)
    
    def _get_video_type_weight(self, video_type: str) -> float:
        """
        Zwraca wagę dla typu filmu
        
        Args:
            video_type: Typ filmu
            
        Returns:
            Waga typu filmu
        """
        if pd.isna(video_type):
            return 1.0
        
        video_type = str(video_type).lower().strip()
        return self.video_type_weights.get(video_type, 1.0)
    
    def _should_skip_name(self, name: str) -> bool:
        """
        Sprawdza czy nazwisko powinno być pominięte (oznaczone jako OTHER)
        
        Args:
            name: Nazwisko do sprawdzenia
            
        Returns:
            True jeśli nazwisko powinno być pominięte
        """
        if not self.feedback_handler:
            return False
        
        # Sprawdź czy nazwisko ma feedback jako OTHER
        if self.feedback_handler.has_feedback(name):
            label = self.feedback_handler.get_label(name)
            return label == "OTHER"
        
        return False
    
    def calculate_strength(self, names: List[str]) -> Dict[str, Dict]:
        """
        Oblicza siłę dla każdego nazwiska
        
        Args:
            names: Lista nazwisk do analizy
            
        Returns:
            Dict z wynikami dla każdego nazwiska
        """
        results = {}
        
        for name in names:
            # Sprawdź czy nazwisko powinno być pominięte
            if self._should_skip_name(name):
                continue
            
            # Normalizuj nazwisko
            normalized_name = self.normalizer.normalize(name)
            if not normalized_name:
                continue
            
            # Inicjalizuj liczniki
            total_strength = 0.0
            total_views = 0
            total_mentions = 0
            
            # Przeanalizuj każdy wiersz (film)
            for _, row in self.df.iterrows():
                # Sprawdź wystąpienia w różnych polach
                title_mentions = self._count_mentions_in_text(row.get('title', ''), normalized_name)
                description_mentions = self._count_mentions_in_text(row.get('description', ''), normalized_name)
                tags_mentions = self._count_mentions_in_text(row.get('tags', ''), normalized_name)
                
                # Oblicz łączną liczbę wystąpień w tym filmie
                film_mentions = title_mentions + description_mentions + tags_mentions
                
                if film_mentions > 0:
                    # Oblicz siłę dla tego filmu
                    views = int(row.get('views', 0)) if pd.notna(row.get('views')) else 0
                    video_type_weight = self._get_video_type_weight(row.get('video_type', ''))
                    
                    # Wzór: (title_mentions * 1.5 + description_mentions * 1.0 + tag_mentions * 0.5) * video_type_weight * views
                    film_strength = (
                        title_mentions * self.field_weights['title'] +
                        description_mentions * self.field_weights['description'] +
                        tags_mentions * self.field_weights['tags']
                    ) * video_type_weight * views
                    
                    total_strength += film_strength
                    total_views += views
                    total_mentions += film_mentions
            
            # Zapisz wyniki
            if total_mentions > 0:
                results[normalized_name] = {
                    'strength': total_strength,
                    'total_views': total_views,
                    'mentions': total_mentions,
                    'original_name': name
                }
        
        return results
    
    def get_ranked(self, names: List[str]) -> List[Dict]:
        """
        Zwraca posortowaną listę nazwisk według siły
        
        Args:
            names: Lista nazwisk do analizy
            
        Returns:
            Lista słowników posortowana malejąco po strength
        """
        strength_data = self.calculate_strength(names)
        
        # Konwertuj na listę słowników
        ranked_list = []
        for name, data in strength_data.items():
            ranked_list.append({
                'name': name,
                'strength': data['strength'],
                'total_views': data['total_views'],
                'mentions': data['mentions'],
                'original_name': data['original_name']
            })
        
        # Sortuj malejąco po strength
        ranked_list.sort(key=lambda x: x['strength'], reverse=True)
        
        return ranked_list
    
    def get_top_names(self, names: List[str], top_n: int = 10) -> List[Dict]:
        """
        Zwraca top N nazwisk według siły
        
        Args:
            names: Lista nazwisk do analizy
            top_n: Liczba najlepszych nazwisk do zwrócenia
            
        Returns:
            Lista top N nazwisk
        """
        ranked = self.get_ranked(names)
        return ranked[:top_n]


if __name__ == "__main__":
    # Testowanie klasy
    print("🧪 TESTOWANIE OBLICZANIA SIŁY NAZWISK")
    print("=" * 50)
    
    # Wczytaj najnowszy raport
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from loader.report_loader import get_latest_report
        
        df = get_latest_report()
        print(f"✅ Wczytano raport z {len(df)} rekordami")
        
        # Sprawdź czy są dane
        if len(df) == 0:
            print("⚠️  Brak danych w raporcie. Tworzę przykładowe dane...")
            # Utwórz przykładowe dane
            df = pd.DataFrame({
                'title': ['Podcast z Janem Kowalskim', 'Rozmowa z Kuba Wojewódzki', 'Gość: Piotr Polo'],
                'description': ['Wspaniała rozmowa z Janem Kowalskim', 'Kuba Wojewódzki opowiada', 'Piotr Polo w studio'],
                'tags': ['Jan Kowalski', 'Wojewódzki', 'Polo'],
                'views': [1000, 5000, 2000],
                'video_type': ['longs', 'shorts', 'longs']
            })
        
    except Exception as e:
        print(f"❌ Błąd podczas wczytywania raportu: {e}")
        print("Używam przykładowych danych...")
        
        # Przykładowe dane
        df = pd.DataFrame({
            'title': ['Podcast z Janem Kowalskim', 'Rozmowa z Kuba Wojewódzki', 'Gość: Piotr Polo'],
            'description': ['Wspaniała rozmowa z Janem Kowalskim', 'Kuba Wojewódzki opowiada', 'Piotr Polo w studio'],
            'tags': ['Jan Kowalski', 'Wojewódzki', 'Polo'],
            'views': [1000, 5000, 2000],
            'video_type': ['longs', 'shorts', 'longs']
        })
    
    # Inicjalizuj komponenty
    normalizer = NameNormalizer()
    
    # Przykładowa lista nazwisk do testowania
    test_names = [
        "Jan Kowalski",
        "Kuba Wojewódzki", 
        "Piotr Polo",
        "Piotr Przywarski",
        "Klaudia Lewandowska",
        "gość",  # powinno być pominięte
        "Marek Kaczyński"
    ]
    
    print(f"\n📝 Testowane nazwiska: {test_names}")
    
    # Normalizuj nazwiska
    normalized_names = normalizer.normalize_all(test_names)
    print(f"✅ Znormalizowane nazwiska: {normalized_names}")
    
    # Oblicz ranking
    calculator = NameStrengthCalculator(df, normalizer)
    ranked_results = calculator.get_ranked(test_names)
    
    print(f"\n🏆 TOP 5 NAZWISK WEDŁUG SIŁY:")
    print("-" * 60)
    
    for i, result in enumerate(ranked_results[:5], 1):
        print(f"{i}. {result['name']}")
        print(f"   Siła: {result['strength']:.2f}")
        print(f"   Wyświetlenia: {result['total_views']:,}")
        print(f"   Wystąpienia: {result['mentions']}")
        print(f"   Oryginalna nazwa: {result['original_name']}")
        print()
    
    print(f"📊 Łącznie przeanalizowano {len(ranked_results)} nazwisk") 