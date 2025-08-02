import json
import random
from pathlib import Path
from typing import List, Dict, Any
import spacy
from spacy.tokens import DocBin


def load_training_data(jsonl_path: str) -> List[Dict[str, Any]]:
    """
    Wczytuje dane treningowe z pliku JSON Lines
    """
    data = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def convert_to_spacy_format(data: List[Dict[str, Any]], nlp) -> List[Dict[str, Any]]:
    """
    Konwertuje dane do formatu spaCy
    """
    spacy_data = []
    
    for item in data:
        text = item['text']
        entities = item['entities']
        
        # Utwórz dokument spaCy
        doc = nlp.make_doc(text)
        
        # Dodaj encje
        ents = []
        for start, end, label in entities:
            # Sprawdź czy pozycje są poprawne
            if start < len(text) and end <= len(text) and start < end:
                span = doc.char_span(start, end, label=label)
                if span is not None:
                    ents.append(span)
        
        doc.ents = ents
        spacy_data.append(doc)
    
    return spacy_data


def split_data(data: List, train_ratio: float = 0.8, random_seed: int = 42) -> tuple:
    """
    Dzieli dane na zbiór treningowy i walidacyjny
    """
    random.seed(random_seed)
    random.shuffle(data)
    
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    dev_data = data[split_idx:]
    
    return train_data, dev_data


def save_spacy_data(data: List, output_path: str):
    """
    Zapisuje dane w formacie binarnym spaCy
    """
    doc_bin = DocBin()
    for doc in data:
        doc_bin.add(doc)
    
    with open(output_path, 'wb') as f:
        f.write(doc_bin.to_bytes())


def main():
    """
    Główna funkcja konwersji danych
    """
    print("🔄 KONWERSJA DANYCH TRENINGOWYCH DO FORMATU SPACY")
    print("=" * 50)
    
    # Ścieżki
    input_file = Path("data/training_data.jsonl")
    train_output = Path("training/train.spacy")
    dev_output = Path("training/dev.spacy")
    
    # Sprawdź czy plik wejściowy istnieje
    if not input_file.exists():
        print(f"❌ Plik {input_file} nie istnieje!")
        print("Najpierw uruchom: python analyzer/prepare_training_data.py")
        return
    
    # Wczytaj dane
    print(f"📖 Wczytywanie danych z {input_file}...")
    data = load_training_data(input_file)
    print(f"✅ Wczytano {len(data)} rekordów")
    
    if len(data) == 0:
        print("❌ Brak danych do konwersji!")
        return
    
    # Inicjalizuj spaCy (pusty model)
    print("🔧 Inicjalizacja spaCy...")
    nlp = spacy.blank("pl")
    
    # Konwertuj do formatu spaCy
    print("🔄 Konwersja do formatu spaCy...")
    spacy_data = convert_to_spacy_format(data, nlp)
    print(f"✅ Skonwertowano {len(spacy_data)} dokumentów")
    
    # Podziel dane
    print("📊 Dzielenie danych (80% train / 20% dev)...")
    train_data, dev_data = split_data(spacy_data)
    print(f"✅ Train: {len(train_data)} dokumentów")
    print(f"✅ Dev: {len(dev_data)} dokumentów")
    
    # Zapisz pliki
    print("💾 Zapisuję pliki...")
    save_spacy_data(train_data, train_output)
    save_spacy_data(dev_data, dev_output)
    
    print(f"✅ Zapisano: {train_output}")
    print(f"✅ Zapisano: {dev_output}")
    
    # Statystyki
    total_entities = sum(len(doc.ents) for doc in spacy_data)
    print(f"\n📈 Statystyki:")
    print(f"   Łączna liczba encji: {total_entities}")
    
    if total_entities > 0:
        label_counts = {}
        for doc in spacy_data:
            for ent in doc.ents:
                label_counts[ent.label_] = label_counts.get(ent.label_, 0) + 1
        
        print("   Rozkład etykiet:")
        for label, count in label_counts.items():
            print(f"     {label}: {count}")
    
    print(f"\n🎉 KONWERSJA ZAKOŃCZONA!")
    print(f"Możesz teraz uruchomić trening: bash training/train.sh")


if __name__ == "__main__":
    main() 