#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ulepszona wersja treningu modelu NER z lepszą precyzją

Główne ulepszenia:
1. Inteligentne wykrywanie granic nazwisk w frazach
2. Generowanie sztucznych kontekstów
3. Lepsze dane treningowe z EntityRuler
4. Pattern matching dla typowych formatów nazwisk

Autor: Guest Radar System  
Data: 2025-08-03
"""

import json
import spacy
import random
import re
from pathlib import Path
from spacy.training import Example
from spacy.lang.pl import Polish
from typing import List, Dict, Tuple, Set
import warnings
warnings.filterwarnings("ignore")


class ImprovedNERTrainer:
    """Ulepszona klasa do trenowania modelu NER."""
    
    def __init__(self, 
                 feedback_file: str = "data/feedback.json",
                 model_output_dir: str = "ner_model_improved"):
        """
        Inicjalizuje ulepszonego trainer'a NER.
        
        Args:
            feedback_file: Plik z danymi feedback
            model_output_dir: Katalog wyjściowy dla modelu
        """
        self.feedback_file = feedback_file
        self.model_output_dir = Path(model_output_dir)
        
        # Wzorce do wykrywania nazwisk
        self.name_patterns = [
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b',  # Imię Nazwisko
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Standardowe nazwiska
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ]{2,}\s+[A-ZĄĆĘŁŃÓŚŹŻ]{2,}\b',  # CAPS NAZWISKA
        ]
        
        # Typowe konteksty dla nazwisk
        self.name_contexts = [
            "gościem jest {name}",
            "rozmowa z {name}",
            "wywiad z {name}", 
            "prowadzi {name}",
            "autor {name}",
            "{name} opowiada",
            "{name} w studiu",
            "razem z {name}",
            "{name} i jego",
            "według {name}"
        ]
    
    def extract_names_from_phrase(self, phrase: str) -> List[Tuple[int, int, str]]:
        """
        Wydobywa prawdopodobne nazwiska z frazy.
        
        Args:
            phrase: Fraza do analizy
            
        Returns:
            Lista tupli (start, end, text) dla znalezionych nazwisk
        """
        names = []
        
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, phrase)
            for match in matches:
                start, end = match.span()
                name_text = match.group().strip()
                
                # Filtruj oczywiste false positive
                if self._is_likely_name(name_text):
                    names.append((start, end, name_text))
        
        return names
    
    def _is_likely_name(self, text: str) -> bool:
        """
        Sprawdza czy tekst prawdopodobnie jest nazwiskiem.
        
        Args:
            text: Tekst do sprawdzenia
            
        Returns:
            True jeśli prawdopodobnie nazwisko
        """
        # Podstawowe filtry
        if len(text) < 4 or len(text) > 50:
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 3:
            return False
        
        # Sprawdź czy słowa wyglądają jak nazwiska
        for word in words:
            if len(word) < 2:
                return False
            # Pierwsza litera powinna być wielka
            if not word[0].isupper():
                return False
            # Pozostałe litery powinny być małe (z wyjątkiem CAPS)
            if not (word[1:].islower() or word.isupper()):
                return False
        
        # Odrzuć typowe false positive
        false_positives = {
            'CHCESZ NAS', 'TEN MATERIAŁ', 'GODNY TWOJEJ', 'MOŻESZ POPRZEZ',
            'W PODCAŚCIE', 'NA KANAŁ', 'LINK W', 'DISCORD LINK'
        }
        
        if text.upper() in false_positives:
            return False
        
        return True
    
    def load_and_process_feedback(self) -> List[Tuple[str, Dict]]:
        """
        Wczytuje i przetwarza dane feedback do formatu treningowego.
        
        Returns:
            Lista danych treningowych
        """
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Wczytano {len(data)} rekordów z {self.feedback_file}")
            
            training_data = []
            processed_names = set()
            
            print(f"\n🧠 PRZETWARZANIE DANYCH:")
            print("=" * 50)
            
            guest_count = 0
            maybe_count = 0
            extracted_names = 0
            
            for item in data:
                label = item.get('label', '')
                text = item.get('text') or item.get('phrase', '')
                
                if label in ['GUEST', 'MAYBE'] and text.strip():
                    text = text.strip()
                    
                    # Spróbuj wydobyć konkretne nazwiska
                    names = self.extract_names_from_phrase(text)
                    
                    if names:
                        # Użyj wydobytych nazwisk
                        entities = []
                        for start, end, name_text in names:
                            entities.append((start, end, 'PERSON'))
                            processed_names.add(name_text)
                            extracted_names += 1
                        
                        training_data.append((text, {"entities": entities}))
                    else:
                        # Jeśli brak wydobytych nazwisk, użyj całej frazy (fallback)
                        entities = [(0, len(text), 'PERSON')]
                        training_data.append((text, {"entities": entities}))
                    
                    if label == 'GUEST':
                        guest_count += 1
                    elif label == 'MAYBE':
                        maybe_count += 1
            
            print(f"✅ Przygotowano {len(training_data)} przykładów treningowych:")
            print(f"   • GUEST: {guest_count}")
            print(f"   • MAYBE: {maybe_count}")
            print(f"   • Wydobyte konkretne nazwiska: {extracted_names}")
            print(f"   • Unikalne nazwiska: {len(processed_names)}")
            
            # Generuj dodatkowe konteksty
            additional_data = self._generate_additional_contexts(processed_names)
            training_data.extend(additional_data)
            
            print(f"✅ Dodano {len(additional_data)} sztucznych kontekstów")
            print(f"📊 Łącznie danych treningowych: {len(training_data)}")
            
            return training_data
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania danych: {e}")
            return []
    
    def _generate_additional_contexts(self, names: Set[str]) -> List[Tuple[str, Dict]]:
        """
        Generuje dodatkowe konteksty dla nazwisk.
        
        Args:
            names: Zbiór nazwisk
            
        Returns:
            Lista dodatkowych przykładów treningowych
        """
        additional_data = []
        
        # Wybierz najlepsze nazwiska (krótsze, bardziej prawdopodobne)
        good_names = []
        for name in names:
            if len(name.split()) == 2 and len(name) < 25 and self._is_likely_name(name):
                good_names.append(name)
        
        # Ogranicz do 20 najlepszych nazwisk
        selected_names = random.sample(good_names, min(20, len(good_names)))
        
        for name in selected_names:
            for context_template in self.name_contexts[:5]:  # Użyj 5 kontekstów
                # Stwórz kontekst
                full_text = context_template.format(name=name)
                
                # Znajdź pozycję nazwiska w kontekście
                name_start = full_text.find(name)
                name_end = name_start + len(name)
                
                entities = [(name_start, name_end, 'PERSON')]
                additional_data.append((full_text, {"entities": entities}))
        
        return additional_data
    
    def create_spacy_model(self) -> spacy.Language:
        """
        Tworzy model spaCy z EntityRuler i NER.
        
        Returns:
            Model spaCy
        """
        print(f"\n🤖 TWORZENIE MODELU SPACY:")
        print("=" * 50)
        
        # Utwórz pusty model polski
        nlp = spacy.blank("pl")
        
        # Dodaj komponent NER najpierw
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        
        # Dodaj EntityRuler przed NER
        if "entity_ruler" not in nlp.pipe_names:
            ruler = nlp.add_pipe("entity_ruler", before="ner")
        
        # Dodaj etykietę PERSON
        ner.add_label("PERSON")
        
        # Dodaj wzorce do EntityRuler
        patterns = [
            {"label": "PERSON", "pattern": [
                {"SHAPE": "Xxxxx"}, {"SHAPE": "Xxxxx"}
            ]},
            {"label": "PERSON", "pattern": [
                {"IS_TITLE": True}, {"IS_TITLE": True}
            ]}
        ]
        
        ruler.add_patterns(patterns)
        
        print(f"✅ Utworzono model z komponentami: {nlp.pipe_names}")
        print(f"✅ Etykiety NER: ['PERSON']")
        print(f"✅ Wzorce EntityRuler: {len(patterns)}")
        
        return nlp
    
    def train_model(self, nlp: spacy.Language, training_data: List[Tuple[str, Dict]], 
                   n_iter: int = 20) -> spacy.Language:
        """
        Trenuje model NER.
        
        Args:
            nlp: Model spaCy
            training_data: Dane treningowe
            n_iter: Liczba iteracji treningu
            
        Returns:
            Wytrenowany model
        """
        print(f"\n🔥 TRENING MODELU:")
        print("=" * 50)
        
        # Przygotuj przykłady treningowe
        examples = []
        for text, annotations in training_data:
            try:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)
            except Exception as e:
                print(f"⚠️ Błąd dla przykładu '{text[:30]}...': {e}")
                continue
        
        print(f"✅ Przygotowano {len(examples)} przykładów do treningu")
        
        # Inicjalizuj tylko NER (EntityRuler jest już gotowy)
        nlp.initialize(lambda: examples)
        
        # Wyłącz EntityRuler podczas treningu NER
        with nlp.disable_pipes("entity_ruler"):
            print(f"🚀 Rozpoczynam trening NER ({n_iter} iteracji)...")
            
            losses = {}
            for iteration in range(n_iter):
                random.shuffle(examples)
                nlp.update(examples, losses=losses)
                
                # Wyświetl postęp co 4 iteracje
                if (iteration + 1) % 4 == 0:
                    loss = losses.get('ner', 0)
                    print(f"   Iteracja {iteration + 1:2d}/{n_iter}: loss = {loss:.4f}")
        
        final_loss = losses.get('ner', 0)
        print(f"✅ Trening zakończony! Końcowa strata: {final_loss:.4f}")
        
        return nlp
    
    def test_model(self, nlp: spacy.Language) -> None:
        """
        Testuje wytrenowany model.
        
        Args:
            nlp: Wytrenowany model
        """
        print(f"\n🧪 TEST MODELU:")
        print("=" * 50)
        
        test_texts = [
            "W podcaście gościem jest Jakub Żulczyk",
            "Rozmowa z Krzysztofem Stanowskim i Anną Kowalską",
            "Adam Małysz opowiada o skokach narciarskich",
            "Program prowadzi Kuba Wojewódzki wraz z Marcinem Prokopem",
            "Wywiad z prezesem, Janem Nowakiem",
            "Piotr Pająk premiera nowej książki"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n{i}. Tekst: \"{text}\"")
            doc = nlp(text)
            
            if doc.ents:
                print("   Wykryte encje:")
                for ent in doc.ents:
                    print(f"     • \"{ent.text}\" → {ent.label_}")
            else:
                print("   ❌ Brak wykrytych encji")
    
    def save_model(self, nlp: spacy.Language) -> bool:
        """
        Zapisuje wytrenowany model.
        
        Args:
            nlp: Wytrenowany model
            
        Returns:
            True jeśli udało się zapisać
        """
        print(f"\n💾 ZAPISYWANIE MODELU:")
        print("=" * 50)
        
        try:
            # Utwórz katalog jeśli nie istnieje
            self.model_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Zapisz model
            nlp.to_disk(self.model_output_dir)
            
            print(f"✅ Model zapisany w: {self.model_output_dir.absolute()}")
            
            # Wyświetl zawartość katalogu
            files = list(self.model_output_dir.iterdir())
            print(f"📁 Pliki modelu: {[f.name for f in files]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania modelu: {e}")
            return False
    
    def run_training(self) -> bool:
        """
        Uruchamia pełny proces treningu.
        
        Returns:
            True jeśli trening się powiódł
        """
        print("🚀 ROZPOCZYNAM TRENING ULEPSZONEGO MODELU NER")
        print("=" * 60)
        
        # 1. Wczytaj i przetwórz dane
        training_data = self.load_and_process_feedback()
        if not training_data:
            print("❌ Brak danych do treningu")
            return False
        
        # 2. Utwórz model
        nlp = self.create_spacy_model()
        
        # 3. Trenuj model
        nlp = self.train_model(nlp, training_data)
        
        # 4. Zapisz model
        if not self.save_model(nlp):
            print("❌ Nie udało się zapisać modelu")
            return False
        
        # 5. Testuj model
        self.test_model(nlp)
        
        print(f"\n🎉 TRENING ZAKOŃCZONY POMYŚLNIE!")
        print(f"📁 Model zapisany w: {self.model_output_dir}")
        
        return True


def main():
    """Główna funkcja."""
    trainer = ImprovedNERTrainer()
    success = trainer.run_training()
    
    if success:
        print("\n✅ Ulepszoný model NER został pomyślnie wytrenowany!")
    else:
        print("\n❌ Trening nieudany!")


if __name__ == "__main__":
    main()