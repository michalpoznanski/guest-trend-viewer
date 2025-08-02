#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAYBE Similarity Engine - Generowanie podobnych kandydatów na podstawie fraz MAYBE

Funkcja generate_similar_candidates_from_maybe():
1. Wczytuje wszystkie frazy oznaczone jako "MAYBE" z feedback.json
2. Generuje embeddingi używając spaCy pl_core_news_sm
3. Szuka 5-10 najbardziej podobnych fraz z filtered_candidates.json  
4. Dopisuje je do feedback_candidates.json z flagą suggested_by_maybe: true

Autor: Guest Radar System
Data: 2025-08-03
"""

import json
import os
import spacy
import numpy as np
from typing import List, Dict, Tuple, Set
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity


class MaybeSimilarityEngine:
    """Silnik do generowania podobnych kandydatów na podstawie fraz MAYBE."""
    
    def __init__(self, 
                 feedback_file: str = "data/feedback.json",
                 candidates_file: str = "data/filtered_candidates.json", 
                 suggestions_file: str = "data/feedback_candidates.json"):
        """
        Inicjalizuje silnik podobieństwa.
        
        Args:
            feedback_file: Plik z feedback (źródło fraz MAYBE)
            candidates_file: Plik z kandydatami do przeszukania
            suggestions_file: Plik docelowy dla sugestii
        """
        self.feedback_file = feedback_file
        self.candidates_file = candidates_file
        self.suggestions_file = suggestions_file
        
        # Inicjalizacja modelu spaCy
        try:
            self.nlp = spacy.load("pl_core_news_sm")
            print("✅ Załadowano model spaCy pl_core_news_sm")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("⚠️ Używam modelu en_core_web_sm (brak pl_core_news_sm)")
            except OSError:
                raise Exception("❌ Brak dostępnych modeli spaCy!")
    
    def load_maybe_phrases(self) -> List[str]:
        """
        Wczytuje wszystkie frazy oznaczone jako MAYBE z feedback.json.
        
        Returns:
            Lista fraz MAYBE
        """
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
            
            maybe_phrases = []
            for item in feedback_data:
                if item.get('label') == 'MAYBE':
                    phrase = item.get('text') or item.get('phrase', '')
                    if phrase.strip():
                        maybe_phrases.append(phrase.strip())
            
            print(f"✅ Znaleziono {len(maybe_phrases)} fraz MAYBE")
            return maybe_phrases
            
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania fraz MAYBE: {e}")
            return []
    
    def load_candidates(self) -> List[Dict[str, str]]:
        """
        Wczytuje kandydatów z filtered_candidates.json.
        
        Returns:
            Lista kandydatów z metadanymi
        """
        try:
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                candidates_data = json.load(f)
            
            candidates = []
            for item in candidates_data:
                if isinstance(item, dict):
                    phrase = item.get('phrase', '')
                    source = item.get('source', 'unknown')
                    if phrase.strip():
                        candidates.append({
                            'phrase': phrase.strip(),
                            'source': source
                        })
                elif isinstance(item, str) and item.strip():
                    candidates.append({
                        'phrase': item.strip(),
                        'source': 'unknown'
                    })
            
            print(f"✅ Załadowano {len(candidates)} kandydatów")
            return candidates
            
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania kandydatów: {e}")
            return []
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generuje embedding dla tekstu używając spaCy.
        
        Args:
            text: Tekst do przetworzenia
            
        Returns:
            Wektor embedding
        """
        doc = self.nlp(text)
        
        if doc.has_vector:
            return doc.vector
        else:
            # Fallback: średnia z embeddingów tokenów
            vectors = [token.vector for token in doc if token.has_vector]
            if vectors:
                return np.mean(vectors, axis=0)
            else:
                # Ostatni fallback: wektor zerowy
                return np.zeros(self.nlp.vocab.vectors_length)
    
    def find_similar_candidates(self, maybe_phrases: List[str], 
                              candidates: List[Dict[str, str]], 
                              top_k: int = 8, 
                              threshold: float = 0.6) -> List[Tuple[Dict[str, str], float]]:
        """
        Znajduje kandydatów podobnych do fraz MAYBE.
        
        Args:
            maybe_phrases: Lista fraz MAYBE
            candidates: Lista kandydatów
            top_k: Maksymalna liczba wyników
            threshold: Minimalny próg podobieństwa
            
        Returns:
            Lista tupli (kandydat, podobieństwo)
        """
        if not maybe_phrases or not candidates:
            return []
        
        print(f"🔍 Generuję embeddingi dla {len(maybe_phrases)} fraz MAYBE...")
        
        # Generuj embeddingi dla fraz MAYBE
        maybe_embeddings = []
        for phrase in maybe_phrases:
            embedding = self.get_embedding(phrase)
            maybe_embeddings.append(embedding)
        
        if not maybe_embeddings:
            return []
        
        # Średni embedding MAYBE (reprezentuje "typ" fraz MAYBE)
        avg_maybe_embedding = np.mean(maybe_embeddings, axis=0).reshape(1, -1)
        
        print(f"🔍 Analizuję podobieństwo do {len(candidates)} kandydatów...")
        
        # Generuj embeddingi dla kandydatów i oblicz podobieństwa
        similarities = []
        for i, candidate in enumerate(candidates):
            try:
                candidate_embedding = self.get_embedding(candidate['phrase'])
                candidate_embedding = candidate_embedding.reshape(1, -1)
                
                # Oblicz cosine similarity
                similarity = cosine_similarity(avg_maybe_embedding, candidate_embedding)[0][0]
                
                if similarity >= threshold:
                    similarities.append((candidate, float(similarity)))
                    
            except Exception as e:
                print(f"⚠️ Błąd dla kandydata '{candidate['phrase']}': {e}")
                continue
        
        # Sortuj malejąco po podobieństwie
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"✅ Znaleziono {len(similarities)} kandydatów powyżej progu {threshold}")
        
        return similarities[:top_k]
    
    def save_suggestions(self, similar_candidates: List[Tuple[Dict[str, str], float]]) -> int:
        """
        Zapisuje sugestie do feedback_candidates.json.
        
        Args:
            similar_candidates: Lista podobnych kandydatów z similarity score
            
        Returns:
            Liczba nowo dodanych sugestii
        """
        try:
            # Wczytaj istniejące sugestie
            if os.path.exists(self.suggestions_file):
                with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                    suggestions = json.load(f)
            else:
                suggestions = []
            
            # Znajdź już istniejące frazy
            existing_phrases = set()
            for suggestion in suggestions:
                phrase = suggestion.get('phrase', '')
                if phrase:
                    existing_phrases.add(phrase)
            
            # Dodaj nowe sugestie
            new_suggestions_count = 0
            timestamp = datetime.now().isoformat()
            
            for candidate, similarity in similar_candidates:
                phrase = candidate['phrase']
                
                if phrase not in existing_phrases:
                    new_suggestion = {
                        "phrase": phrase,
                        "source": candidate['source'],
                        "suggested_by_maybe": True,
                        "similarity_score": similarity,
                        "timestamp": timestamp
                    }
                    
                    suggestions.append(new_suggestion)
                    existing_phrases.add(phrase)
                    new_suggestions_count += 1
            
            # Zapisz zaktualizowane sugestie
            if new_suggestions_count > 0:
                with open(self.suggestions_file, 'w', encoding='utf-8') as f:
                    json.dump(suggestions, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Dodano {new_suggestions_count} nowych sugestii do {self.suggestions_file}")
            else:
                print("ℹ️ Brak nowych sugestii do dodania (wszystkie już istnieją)")
            
            return new_suggestions_count
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania sugestii: {e}")
            return 0


def generate_similar_candidates_from_maybe() -> int:
    """
    Główna funkcja do generowania podobnych kandydatów na podstawie fraz MAYBE.
    
    Returns:
        Liczba wygenerowanych nowych sugestii
    """
    print("🚀 URUCHAMIAM GENERATOR PODOBNYCH KANDYDATÓW (MAYBE)")
    print("=" * 60)
    
    engine = MaybeSimilarityEngine()
    
    # 1. Wczytaj frazy MAYBE
    maybe_phrases = engine.load_maybe_phrases()
    if not maybe_phrases:
        print("❌ Brak fraz MAYBE do analizy")
        return 0
    
    # 2. Wczytaj kandydatów
    candidates = engine.load_candidates()
    if not candidates:
        print("❌ Brak kandydatów do przeszukania")
        return 0
    
    # 3. Znajdź podobnych kandydatów
    similar_candidates = engine.find_similar_candidates(maybe_phrases, candidates)
    
    if not similar_candidates:
        print("❌ Nie znaleziono podobnych kandydatów")
        return 0
    
    # 4. Zapisz sugestie
    new_count = engine.save_suggestions(similar_candidates)
    
    # 5. Pokaż przykłady
    print(f"\n🔮 PRZYKŁADY ZNALEZIONYCH SUGESTII:")
    print("-" * 50)
    for i, (candidate, similarity) in enumerate(similar_candidates[:5], 1):
        print(f"{i:2d}. \"{candidate['phrase']}\" (podobieństwo: {similarity:.3f})")
    
    print(f"\n✅ PROCES ZAKOŃCZONY: {new_count} nowych sugestii")
    return new_count


def test_maybe_similarity_engine():
    """Test funkcji generowania podobieństwa."""
    print("🧪 TEST MAYBE SIMILARITY ENGINE")
    print("=" * 50)
    
    count = generate_similar_candidates_from_maybe()
    print(f"\nTest zakończony: {count} sugestii")


if __name__ == "__main__":
    test_maybe_similarity_engine()