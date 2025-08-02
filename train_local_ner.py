#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trening lokalnego modelu NER na bazie danych z feedback.json

Pipeline:
1. Wczytuje dane z data/feedback.json
2. Przygotowuje dane treningowe (GUEST + MAYBE → PERSON)
3. Tworzy pipeline spaCy z EntityRuler + trenowalnym NER
4. Trenuje model na przygotowanych danych
5. Zapisuje model do ner_model/

Autor: Guest Radar System
Data: 2025-08-03
"""

import json
import spacy
import random
from pathlib import Path
from spacy.tokens import DocBin
from spacy.training import Example
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")


class LocalNERTrainer:
    """Klasa do trenowania lokalnego modelu NER."""
    
    def __init__(self, 
                 feedback_file: str = "data/feedback.json",
                 model_output_dir: str = "ner_model"):
        """
        Inicjalizuje trainer NER.
        
        Args:
            feedback_file: Plik z danymi feedback
            model_output_dir: Katalog wyjściowy dla modelu
        """
        self.feedback_file = feedback_file
        self.model_output_dir = Path(model_output_dir)
        self.training_data = []
        
    def load_feedback_data(self) -> List[Dict]:
        """
        Wczytuje dane z pliku feedback.json.
        
        Returns:
            Lista rekordów feedback
        """
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Wczytano {len(data)} rekordów z {self.feedback_file}")
            return data
            
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania danych: {e}")
            return []
    
    def prepare_training_data(self, feedback_data: List[Dict]) -> List[Tuple[str, Dict]]:
        """
        Przygotowuje dane treningowe z feedback.
        
        Args:
            feedback_data: Lista rekordów feedback
            
        Returns:
            Lista danych treningowych w formacie spaCy
        """
        training_data = []
        
        print(f"\n🧠 PRZYGOTOWANIE DANYCH TRENINGOWYCH:")
        print("=" * 50)
        
        guest_count = 0
        maybe_count = 0
        
        for item in feedback_data:
            label = item.get('label', '')
            text = item.get('text') or item.get('phrase', '')
            
            # Używamy tylko GUEST i MAYBE
            if label in ['GUEST', 'MAYBE'] and text.strip():
                text = text.strip()
                
                # Cała fraza jako jedna encja PERSON
                entities = [(0, len(text), 'PERSON')]
                
                training_example = (text, {"entities": entities})
                training_data.append(training_example)
                
                if label == 'GUEST':
                    guest_count += 1
                elif label == 'MAYBE':
                    maybe_count += 1
        
        print(f"✅ Przygotowano {len(training_data)} przykładów treningowych:")
        print(f"   • GUEST → PERSON: {guest_count}")
        print(f"   • MAYBE → PERSON: {maybe_count}")
        
        # Pokaż przykłady
        print(f"\n📋 PRZYKŁADY DANYCH TRENINGOWYCH:")
        for i, (text, annotations) in enumerate(training_data[:5], 1):
            entities = annotations['entities']
            print(f"   {i}. \"{text}\" → {entities}")
        
        return training_data
    
    def create_spacy_model(self) -> spacy.Language:
        """
        Tworzy pusty model spaCy z komponentem NER.
        
        Returns:
            Model spaCy
        """
        print(f"\n🤖 TWORZENIE MODELU SPACY:")
        print("=" * 50)
        
        # Utwórz pusty model polski
        nlp = spacy.blank("pl")
        
        # Dodaj komponent NER
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        
        # Dodaj etykietę PERSON
        ner.add_label("PERSON")
        
        print(f"✅ Utworzono model z komponentami: {nlp.pipe_names}")
        print(f"✅ Etykiety NER: ['PERSON']")
        
        return nlp
    
    def train_model(self, nlp: spacy.Language, training_data: List[Tuple[str, Dict]], 
                   n_iter: int = 30) -> spacy.Language:
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
                print(f"⚠️ Błąd dla przykładu '{text}': {e}")
                continue
        
        print(f"✅ Przygotowano {len(examples)} przykładów do treningu")
        
        # Inicjalizuj model
        nlp.initialize(lambda: examples)
        
        # Trening
        print(f"🚀 Rozpoczynam trening ({n_iter} iteracji)...")
        
        losses = {}
        for iteration in range(n_iter):
            random.shuffle(examples)
            nlp.update(examples, losses=losses)
            
            # Wyświetl postęp co 5 iteracji
            if (iteration + 1) % 5 == 0:
                loss = losses.get('ner', 0)
                print(f"   Iteracja {iteration + 1:2d}/{n_iter}: loss = {loss:.4f}")
        
        final_loss = losses.get('ner', 0)
        print(f"✅ Trening zakończony! Końcowa strata: {final_loss:.4f}")
        
        return nlp
    
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
    
    def test_model(self, nlp: spacy.Language) -> None:
        """
        Testuje wytrenowany model na przykładowych tekstach.
        
        Args:
            nlp: Wytrenowany model
        """
        print(f"\n🧪 TEST MODELU:")
        print("=" * 50)
        
        test_texts = [
            "W podcaście gościem jest Jakub Żulczyk",
            "Rozmowa z Krzysztofem Stanowskim",
            "Adam Małysz opowiada o skokach",
            "Wywiad z Anną Kowalską i Piotrem Nowak",
            "Program prowadzi Kuba Wojewódzki"
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
    
    def run_training(self) -> bool:
        """
        Uruchamia pełny proces treningu.
        
        Returns:
            True jeśli trening się powiódł
        """
        print("🚀 ROZPOCZYNAM TRENING LOKALNEGO MODELU NER")
        print("=" * 60)
        
        # 1. Wczytaj dane
        feedback_data = self.load_feedback_data()
        if not feedback_data:
            print("❌ Brak danych do treningu")
            return False
        
        # 2. Przygotuj dane treningowe
        training_data = self.prepare_training_data(feedback_data)
        if not training_data:
            print("❌ Nie udało się przygotować danych treningowych")
            return False
        
        # 3. Utwórz model
        nlp = self.create_spacy_model()
        
        # 4. Trenuj model
        nlp = self.train_model(nlp, training_data)
        
        # 5. Zapisz model
        if not self.save_model(nlp):
            print("❌ Nie udało się zapisać modelu")
            return False
        
        # 6. Testuj model
        self.test_model(nlp)
        
        print(f"\n🎉 TRENING ZAKOŃCZONY POMYŚLNIE!")
        print(f"📁 Model zapisany w: {self.model_output_dir}")
        
        return True


def main():
    """Główna funkcja."""
    trainer = LocalNERTrainer()
    success = trainer.run_training()
    
    if success:
        print("\n✅ Model NER został pomyślnie wytrenowany i zapisany!")
    else:
        print("\n❌ Trening nieudany!")


if __name__ == "__main__":
    main()