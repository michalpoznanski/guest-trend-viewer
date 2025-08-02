#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAYBE Engine - Inteligentna logika dla etykiety MAYBE (M)

Ten moduł implementuje zaawansowaną logikę dla przycisku M:
1. Zapisuje frazy MAYBE do pliku maybe_examples.json
2. Co 10 kliknięć M generuje podobne kandydatów
3. Używa embeddingów do znajdowania podobieństw
4. Dodaje nowe sugestie do systemu

Autor: System Podcast Trend
Data: 2025-08-03
"""

import json
import os
from typing import List, Dict, Any, Tuple, Optional
import spacy
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MaybeEngine:
    """Silnik do obsługi inteligentnej logiki MAYBE."""
    
    def __init__(self, 
                 maybe_file: str = "data/maybe_examples.json",
                 candidates_file: str = "data/filtered_candidates.json",
                 suggestions_file: str = "data/feedback_candidates.json",
                 trigger_count: int = 10):
        """
        Inicjalizuje silnik MAYBE.
        
        Args:
            maybe_file: Ścieżka do pliku z przykładami MAYBE
            candidates_file: Ścieżka do pliku z kandydatami
            suggestions_file: Ścieżka do pliku z sugestiami
            trigger_count: Co ile kliknięć M uruchamiać generowanie sugestii
        """
        self.maybe_file = maybe_file
        self.candidates_file = candidates_file
        self.suggestions_file = suggestions_file
        self.trigger_count = trigger_count
        
        # Inicjalizacja modelu spaCy do embeddingów
        try:
            self.nlp = spacy.load("pl_core_news_sm")
            logger.info("✅ Załadowano model spaCy pl_core_news_sm")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("⚠️ Używam modelu en_core_web_sm (brak pl_core_news_sm)")
            except OSError:
                self.nlp = None
                logger.warning("❌ Brak dostępnych modeli spaCy dla embeddingów")
        
        # Tworzenie plików jeśli nie istnieją
        self._ensure_files_exist()
    
    def _ensure_files_exist(self) -> None:
        """Zapewnia, że wymagane pliki istnieją."""
        if not os.path.exists(self.maybe_file):
            with open(self.maybe_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Utworzono plik: {self.maybe_file}")
    
    def add_maybe_example(self, phrase: str, source: str) -> bool:
        """
        Dodaje nowy przykład MAYBE do pliku.
        
        Args:
            phrase: Fraza do dodania
            source: Źródło frazy (title, description, tags)
            
        Returns:
            True jeśli dodano, False jeśli już istnieje
        """
        try:
            # Wczytaj istniejące przykłady
            with open(self.maybe_file, 'r', encoding='utf-8') as f:
                maybe_examples = json.load(f)
            
            # Sprawdź czy już istnieje
            for example in maybe_examples:
                if example.get('text') == phrase:
                    logger.info(f"⚠️ Fraza już istnieje w MAYBE: {phrase}")
                    return False
            
            # Dodaj nowy przykład
            new_example = {
                "text": phrase,
                "source": source,
                "label": "M",
                "timestamp": self._get_timestamp()
            }
            
            maybe_examples.append(new_example)
            
            # Zapisz z powrotem
            with open(self.maybe_file, 'w', encoding='utf-8') as f:
                json.dump(maybe_examples, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Dodano do MAYBE: {phrase}")
            
            # Sprawdź czy należy wygenerować sugestie
            if len(maybe_examples) % self.trigger_count == 0:
                logger.info(f"🎯 Trigger! {len(maybe_examples)} przykładów MAYBE - generuję sugestie")
                self.generate_similar_candidates()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd przy dodawaniu MAYBE: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Zwraca aktualny timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_similar_candidates(self) -> int:
        """
        Generuje podobnych kandydatów na podstawie przykładów MAYBE.
        
        Returns:
            Liczba wygenerowanych sugestii
        """
        if not self.nlp:
            logger.warning("❌ Brak modelu spaCy - nie można generować sugestii")
            return 0
        
        try:
            # Wczytaj przykłady MAYBE
            with open(self.maybe_file, 'r', encoding='utf-8') as f:
                maybe_examples = json.load(f)
            
            if not maybe_examples:
                logger.info("ℹ️ Brak przykładów MAYBE")
                return 0
            
            # Wczytaj kandydatów
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                candidates = json.load(f)
            
            # Wczytaj istniejące sugestie
            if os.path.exists(self.suggestions_file):
                with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                    suggestions = json.load(f)
            else:
                suggestions = []
            
            # Przygotuj teksty MAYBE
            maybe_texts = [example['text'] for example in maybe_examples]
            candidate_texts = [candidate['phrase'] for candidate in candidates]
            
            # Znajdź podobnych kandydatów
            similar_candidates = self._find_similar_candidates(
                maybe_texts, candidate_texts, top_k=10
            )
            
            # Dodaj nowe sugestie
            new_suggestions_count = 0
            existing_phrases = {sugg.get('phrase', '') for sugg in suggestions}
            
            for candidate_idx, similarity in similar_candidates:
                candidate = candidates[candidate_idx]
                phrase = candidate['phrase']
                
                # Sprawdź czy już nie istnieje
                if phrase not in existing_phrases:
                    new_suggestion = {
                        "phrase": phrase,
                        "source": candidate['source'],
                        "suggested_by_maybe": True,
                        "similarity_score": float(similarity),
                        "timestamp": self._get_timestamp()
                    }
                    
                    suggestions.append(new_suggestion)
                    existing_phrases.add(phrase)
                    new_suggestions_count += 1
            
            # Zapisz sugestie
            if new_suggestions_count > 0:
                with open(self.suggestions_file, 'w', encoding='utf-8') as f:
                    json.dump(suggestions, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Wygenerowano {new_suggestions_count} nowych sugestii")
            else:
                logger.info("ℹ️ Brak nowych sugestii do dodania")
            
            return new_suggestions_count
            
        except Exception as e:
            logger.error(f"❌ Błąd przy generowaniu sugestii: {e}")
            return 0
    
    def _find_similar_candidates(self, maybe_texts: List[str], candidate_texts: List[str], 
                               top_k: int = 10, threshold: float = 0.7) -> List[Tuple[int, float]]:
        """
        Znajduje kandydatów podobnych do przykładów MAYBE.
        
        Args:
            maybe_texts: Lista tekstów MAYBE
            candidate_texts: Lista kandydatów
            top_k: Maksymalna liczba wyników
            threshold: Minimalny próg podobieństwa
            
        Returns:
            Lista tupli (indeks_kandydata, similarity_score)
        """
        if not maybe_texts or not candidate_texts:
            return []
        
        try:
            # Generuj embeddingi dla MAYBE
            maybe_embeddings = []
            for text in maybe_texts:
                doc = self.nlp(text)
                if doc.has_vector:
                    maybe_embeddings.append(doc.vector)
                else:
                    # Fallback: średnia z embeddingów tokenów
                    vectors = [token.vector for token in doc if token.has_vector]
                    if vectors:
                        maybe_embeddings.append(np.mean(vectors, axis=0))
            
            if not maybe_embeddings:
                logger.warning("❌ Brak embeddingów dla tekstów MAYBE")
                return []
            
            # Średni embedding MAYBE
            avg_maybe_embedding = np.mean(maybe_embeddings, axis=0).reshape(1, -1)
            
            # Generuj embeddingi dla kandydatów
            candidate_embeddings = []
            valid_indices = []
            
            for i, text in enumerate(candidate_texts):
                doc = self.nlp(text)
                if doc.has_vector:
                    candidate_embeddings.append(doc.vector)
                    valid_indices.append(i)
                else:
                    # Fallback: średnia z embeddingów tokenów
                    vectors = [token.vector for token in doc if token.has_vector]
                    if vectors:
                        candidate_embeddings.append(np.mean(vectors, axis=0))
                        valid_indices.append(i)
            
            if not candidate_embeddings:
                logger.warning("❌ Brak embeddingów dla kandydatów")
                return []
            
            # Oblicz podobieństwa
            candidate_matrix = np.array(candidate_embeddings)
            similarities = cosine_similarity(avg_maybe_embedding, candidate_matrix)[0]
            
            # Filtruj i sortuj
            similar_candidates = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    similar_candidates.append((valid_indices[i], similarity))
            
            # Sortuj malejąco po podobieństwie
            similar_candidates.sort(key=lambda x: x[1], reverse=True)
            
            return similar_candidates[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Błąd przy obliczaniu podobieństwa: {e}")
            return []
    
    def get_maybe_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki przykładów MAYBE.
        
        Returns:
            Słownik ze statystykami
        """
        try:
            with open(self.maybe_file, 'r', encoding='utf-8') as f:
                maybe_examples = json.load(f)
            
            if not maybe_examples:
                return {"total": 0, "sources": {}, "recent": []}
            
            # Statystyki źródeł
            sources = Counter(example.get('source', 'unknown') for example in maybe_examples)
            
            # Ostatnie 5 przykładów
            recent = maybe_examples[-5:] if len(maybe_examples) >= 5 else maybe_examples
            
            return {
                "total": len(maybe_examples),
                "sources": dict(sources),
                "recent": [ex.get('text', '') for ex in recent],
                "next_trigger": self.trigger_count - (len(maybe_examples) % self.trigger_count)
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd przy pobieraniu statystyk MAYBE: {e}")
            return {"total": 0, "sources": {}, "recent": [], "error": str(e)}
    
    def is_suggestion_from_maybe(self, phrase: str) -> bool:
        """
        Sprawdza czy fraza została zasugerowana przez system MAYBE.
        
        Args:
            phrase: Fraza do sprawdzenia
            
        Returns:
            True jeśli fraza została zasugerowana przez MAYBE
        """
        try:
            if not os.path.exists(self.suggestions_file):
                return False
            
            with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                suggestions = json.load(f)
            
            for suggestion in suggestions:
                if (suggestion.get('phrase') == phrase and 
                    suggestion.get('suggested_by_maybe', False)):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Błąd przy sprawdzaniu sugestii MAYBE: {e}")
            return False


def test_maybe_engine():
    """Test funkcji MaybeEngine."""
    print("🧪 TEST MAYBE ENGINE")
    print("=" * 50)
    
    # Inicjalizacja
    engine = MaybeEngine()
    
    # Test dodawania przykładu
    result = engine.add_maybe_example("Jakiś testowy gość", "title")
    print(f"✅ Dodano przykład: {result}")
    
    # Test statystyk
    stats = engine.get_maybe_stats()
    print(f"📊 Statystyki: {stats}")
    
    print("✅ Test zakończony")


if __name__ == "__main__":
    test_maybe_engine()