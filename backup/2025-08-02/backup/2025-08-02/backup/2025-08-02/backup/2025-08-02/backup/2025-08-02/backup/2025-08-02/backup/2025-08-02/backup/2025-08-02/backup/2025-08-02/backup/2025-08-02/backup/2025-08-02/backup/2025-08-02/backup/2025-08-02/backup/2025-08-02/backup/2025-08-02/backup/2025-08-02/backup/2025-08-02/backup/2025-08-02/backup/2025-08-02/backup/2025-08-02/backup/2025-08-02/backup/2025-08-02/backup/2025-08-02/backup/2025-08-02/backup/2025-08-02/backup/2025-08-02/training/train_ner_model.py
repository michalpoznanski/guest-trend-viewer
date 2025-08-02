#!/usr/bin/env python3
"""
Moduł do trenowania modelu NER na podstawie danych z feedback.json
"""

import json
import spacy
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple
from spacy.tokens import DocBin
from spacy.training import Example
import warnings
warnings.filterwarnings("ignore")


def load_feedback_data(feedback_file: str = "data/feedback.json") -> List[Dict]:
    """
    Wczytuje dane z pliku feedback.json
    
    Args:
        feedback_file: Ścieżka do pliku z feedbackiem
        
    Returns:
        Lista feedbacków lub pusta lista w przypadku błędu
    """
    try:
        feedback_path = Path(feedback_file)
        if not feedback_path.exists():
            print(f"❌ Plik {feedback_file} nie istnieje!")
            return []
        
        with open(feedback_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"❌ Dane w pliku {feedback_file} nie są listą!")
            return []
        
        print(f"✅ Wczytano {len(data)} wpisów z {feedback_file}")
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Błąd parsowania JSON w pliku {feedback_file}: {e}")
        return []
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd podczas wczytywania {feedback_file}: {e}")
        return []


def group_by_labels(feedback_data: List[Dict]) -> Dict[str, List[str]]:
    """
    Grupuje frazy według etykiet
    
    Args:
        feedback_data: Lista feedbacków
        
    Returns:
        Słownik z frazami pogrupowanymi według etykiet
    """
    grouped = defaultdict(list)
    
    for item in feedback_data:
        phrase = item.get('phrase', '')
        label = item.get('label', 'UNKNOWN')
        
        if phrase.strip():  # Tylko niepuste frazy
            grouped[label].append(phrase.strip())
    
    return dict(grouped)


def display_data_statistics(grouped_data: Dict[str, List[str]]) -> None:
    """
    Wyświetla statystyki danych
    
    Args:
        grouped_data: Dane pogrupowane według etykiet
    """
    print(f"\n📊 STATYSTYKI DANYCH TRENINGOWYCH:")
    print("=" * 50)
    
    total_phrases = 0
    for label, phrases in sorted(grouped_data.items()):
        count = len(phrases)
        total_phrases += count
        
        # Ikony dla różnych etykiet
        icon = {
            'GUEST': '👥',
            'HOST': '🎤', 
            'OTHER': '❌',
            'MAYBE': '❓'
        }.get(label, '📝')
        
        print(f"{icon} {label:8s}: {count:4d} fraz")
        
        # Pokaż przykłady
        if count > 0:
            examples = phrases[:3]
            examples_str = ', '.join([f'"{ex}"' for ex in examples])
            if count > 3:
                examples_str += f" ... (+{count-3} więcej)"
            print(f"   Przykłady: {examples_str}")
    
    print(f"\n📊 ŁĄCZNIE: {total_phrases} fraz")


def prepare_training_data(grouped_data: Dict[str, List[str]]) -> List[Tuple[str, Dict]]:
    """
    Przygotowuje dane treningowe dla spaCy
    
    Args:
        grouped_data: Dane pogrupowane według etykiet
        
    Returns:
        Lista danych treningowych w formacie spaCy
    """
    training_data = []
    
    # Używamy tylko GUEST i HOST do treningu
    labels_to_use = ['GUEST', 'HOST']
    
    print(f"\n🔧 PRZYGOTOWANIE DANYCH TRENINGOWYCH:")
    print("=" * 50)
    
    for label in labels_to_use:
        if label not in grouped_data:
            print(f"⚠️  Brak danych dla etykiety {label}")
            continue
        
        phrases = grouped_data[label]
        print(f"✅ Przetwarzam {len(phrases)} fraz dla etykiety {label}")
        
        for phrase in phrases:
            # Tworzymy prosty przykład treningowy
            # Cała fraza jest oznaczona jako dana etykieta
            text = phrase
            start = 0
            end = len(text)
            
            entities = [(start, end, label)]
            
            training_data.append((text, {"entities": entities}))
    
    print(f"📊 Przygotowano {len(training_data)} przykładów treningowych")
    return training_data


def create_spacy_examples(nlp, training_data: List[Tuple[str, Dict]]) -> List[Example]:
    """
    Tworzy przykłady spaCy z danych treningowych
    
    Args:
        nlp: Model spaCy
        training_data: Dane treningowe
        
    Returns:
        Lista przykładów spaCy
    """
    examples = []
    
    for text, annotations in training_data:
        try:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)
        except Exception as e:
            print(f"⚠️  Błąd przy tworzeniu przykładu dla '{text}': {e}")
            continue
    
    return examples


def train_and_save_ner_model(feedback_file: str = "data/feedback.json", 
                             model_output_dir: str = "models/ner_model_2025_08_02",
                             n_iter: int = 30) -> bool:
    """
    Główna funkcja do trenowania i zapisywania modelu NER
    
    Args:
        feedback_file: Ścieżka do pliku z feedbackiem
        model_output_dir: Folder do zapisania modelu
        n_iter: Liczba iteracji treningu
        
    Returns:
        True jeśli trening się powiódł
    """
    print("🚀 ROZPOCZYNAM TRENING MODELU NER")
    print("=" * 60)
    
    # 1. Wczytaj dane
    feedback_data = load_feedback_data(feedback_file)
    if not feedback_data:
        return False
    
    # 2. Pogrupuj według etykiet
    grouped_data = group_by_labels(feedback_data)
    if not grouped_data:
        print("❌ Brak danych do grupowania!")
        return False
    
    # 3. Wyświetl statystyki
    display_data_statistics(grouped_data)
    
    # 4. Sprawdź czy mamy dane do treningu
    training_labels = ['GUEST', 'HOST']
    available_training_data = sum(len(grouped_data.get(label, [])) for label in training_labels)
    
    if available_training_data < 10:
        print(f"❌ Za mało danych treningowych! Potrzeba minimum 10, mamy {available_training_data}")
        return False
    
    print(f"✅ Będę trenować na {available_training_data} przykładach (GUEST + HOST)")
    
    # 5. Przygotuj dane treningowe
    training_data = prepare_training_data(grouped_data)
    if not training_data:
        print("❌ Nie udało się przygotować danych treningowych!")
        return False
    
    # 6. Inicjalizuj model spaCy
    print(f"\n🤖 INICJALIZACJA MODELU SPACY:")
    print("=" * 50)
    
    try:
        # Stwórz pusty model polski
        nlp = spacy.blank("pl")
        
        # Dodaj komponent NER
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        
        # Dodaj etykiety
        for label in training_labels:
            ner.add_label(label)
        
        print(f"✅ Zainicjalizowano model z etykietami: {training_labels}")
        
    except Exception as e:
        print(f"❌ Błąd podczas inicjalizacji modelu: {e}")
        return False
    
    # 7. Przygotuj przykłady treningowe
    print(f"\n📚 PRZYGOTOWANIE PRZYKŁADÓW:")
    print("=" * 50)
    
    try:
        examples = create_spacy_examples(nlp, training_data)
        if not examples:
            print("❌ Nie udało się utworzyć przykładów treningowych!")
            return False
        
        print(f"✅ Utworzono {len(examples)} przykładów treningowych")
        
        # Pomieszaj dane
        random.shuffle(examples)
        
    except Exception as e:
        print(f"❌ Błąd podczas przygotowania przykładów: {e}")
        return False
    
    # 8. Trenuj model
    print(f"\n🔥 TRENING MODELU:")
    print("=" * 50)
    
    try:
        # Inicjalizuj wagi
        nlp.initialize()
        
        # Trening
        print(f"🚀 Rozpoczynam trening ({n_iter} iteracji)...")
        
        losses = {}
        for iteration in range(n_iter):
            random.shuffle(examples)
            nlp.update(examples, losses=losses)
            
            if (iteration + 1) % 5 == 0:
                print(f"   Iteracja {iteration + 1:2d}/{n_iter}: loss = {losses.get('ner', 0.0):.4f}")
        
        print(f"✅ Trening zakończony! Końcowa strata: {losses.get('ner', 0.0):.4f}")
        
    except Exception as e:
        print(f"❌ Błąd podczas treningu: {e}")
        return False
    
    # 9. Zapisz model
    print(f"\n💾 ZAPISYWANIE MODELU:")
    print("=" * 50)
    
    try:
        output_path = Path(model_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        nlp.to_disk(output_path)
        
        print(f"✅ Model zapisany w: {output_path.absolute()}")
        
        # Zapisz też metadane
        metadata = {
            "training_date": "2025-08-02",
            "framework": "spaCy",
            "language": "pl",
            "labels": training_labels,
            "training_examples": len(examples),
            "iterations": n_iter,
            "final_loss": losses.get('ner', 0.0),
            "data_statistics": {label: len(grouped_data.get(label, [])) for label in grouped_data.keys()}
        }
        
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Metadane zapisane w: {metadata_file}")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania modelu: {e}")
        return False
    
    # 10. Test modelu
    print(f"\n🧪 TEST MODELU:")
    print("=" * 50)
    
    try:
        # Testowe frazy
        test_phrases = [
            "Rozmowa z Jakub Żulczyk",
            "Gość Piotr Pająk", 
            "Host Kuba Wojewódzki",
            "Wywiad z Prof. Paweł Kaczmarczyk"
        ]
        
        for test_phrase in test_phrases:
            doc = nlp(test_phrase)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            if entities:
                entities_str = ", ".join([f'"{text}" ({label})' for text, label in entities])
                print(f"   '{test_phrase}' → {entities_str}")
            else:
                print(f"   '{test_phrase}' → (brak wykrytych nazwisk)")
        
    except Exception as e:
        print(f"⚠️  Błąd podczas testowania: {e}")
    
    # 11. Podsumowanie
    print(f"\n🎉 TRENING ZAKOŃCZONY POMYŚLNIE!")
    print("=" * 60)
    print(f"📊 Dane treningowe: {len(examples)} przykładów")
    print(f"🎯 Etykiety: {', '.join(training_labels)}")
    print(f"🔥 Iteracje: {n_iter}")
    print(f"📁 Model zapisany w: {output_path.absolute()}")
    print(f"📋 Użyj modelu: nlp = spacy.load('{output_path.absolute()}')")
    
    return True


def main():
    """
    Główna funkcja uruchamiająca trening
    """
    success = train_and_save_ner_model()
    
    if success:
        print(f"\n✅ SUKCES! Model NER został wytrenowany i zapisany.")
    else:
        print(f"\n❌ BŁĄD! Nie udało się wytrenować modelu.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())