import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Dodaj ścieżkę do loader
sys.path.append(str(Path(__file__).parent.parent))
from loader.report_loader import get_latest_report


def get_text_combination(row) -> str:
    """
    Łączy tytuł, opis i tagi w jeden tekst
    """
    title = str(row.get('title', ''))
    description = str(row.get('description', ''))
    tags = str(row.get('tags', ''))
    
    return f"{title} | {description} | {tags}".strip()


def find_text_positions(text: str, fragment: str) -> List[Tuple[int, int]]:
    """
    Znajduje pozycje fragmentu w tekście (start, end)
    """
    positions = []
    start = 0
    while True:
        pos = text.find(fragment, start)
        if pos == -1:
            break
        positions.append((pos, pos + len(fragment)))
        start = pos + 1
    return positions


def validate_entity(text: str, fragment: str, start: int, end: int) -> bool:
    """
    Sprawdza czy fragment rzeczywiście znajduje się na danej pozycji
    """
    return text[start:end] == fragment


def prepare_training_data():
    """
    Główna funkcja do przygotowania danych treningowych
    """
    print("🎯 PRZYGOTOWANIE DANYCH TRENINGOWYCH DLA MODELU NER")
    print("=" * 60)
    
    # Wczytaj dane
    try:
        df = get_latest_report()
        print(f"✅ Wczytano {len(df)} rekordów z raportu")
    except Exception as e:
        print(f"❌ Błąd podczas wczytywania raportu: {e}")
        return
    
    # Wybierz losowo 30 rekordów
    if len(df) < 30:
        print(f"⚠️  Dostępnych tylko {len(df)} rekordów, używam wszystkich")
        selected_records = df
    else:
        selected_records = df.sample(n=30, random_state=42)
    
    training_data = []
    
    for i, (idx, row) in enumerate(selected_records.iterrows(), 1):
        print(f"\n{'='*60}")
        print(f"📝 Tekst #{i} z {len(selected_records)}:")
        print(f"{'='*60}")
        
        # Przygotuj tekst
        text = get_text_combination(row)
        print(f"Tekst: {text}")
        print()
        
        entities = []
        
        while True:
            print("Wpisz fragment tekstu oraz etykietę (GUEST/HOST/OTHER).")
            print("Jeśli nie ma więcej fragmentów, wpisz 'dalej'.")
            print()
            
            fragment = input("Fragment: ").strip()
            
            if fragment.lower() == 'dalej':
                break
            
            if not fragment:
                print("⚠️  Fragment nie może być pusty!")
                continue
            
            # Sprawdź czy fragment istnieje w tekście
            if fragment not in text:
                print(f"⚠️  Fragment '{fragment}' nie został znaleziony w tekście!")
                continue
            
            # Pobierz etykietę
            while True:
                label = input("Etykieta (GUEST/HOST/OTHER): ").strip().upper()
                if label in ['GUEST', 'HOST', 'OTHER']:
                    break
                else:
                    print("⚠️  Nieprawidłowa etykieta! Użyj: GUEST, HOST lub OTHER")
            
            # Znajdź pozycje fragmentu
            positions = find_text_positions(text, fragment)
            
            if len(positions) > 1:
                print(f"⚠️  Fragment '{fragment}' występuje {len(positions)} razy!")
                for j, (start, end) in enumerate(positions):
                    print(f"  {j+1}. Pozycja {start}-{end}: '{text[start:end]}'")
                
                while True:
                    try:
                        choice = int(input("Wybierz numer pozycji: ")) - 1
                        if 0 <= choice < len(positions):
                            start, end = positions[choice]
                            break
                        else:
                            print("⚠️  Nieprawidłowy numer!")
                    except ValueError:
                        print("⚠️  Wpisz liczbę!")
            else:
                start, end = positions[0]
            
            # Sprawdź czy pozycja nie koliduje z już oznaczonymi
            conflict = False
            for existing_start, existing_end, existing_label in entities:
                if (start < existing_end and end > existing_start):
                    print(f"⚠️  Konflikt z już oznaczonym fragmentem '{text[existing_start:existing_end]}' ({existing_label})!")
                    conflict = True
                    break
            
            if conflict:
                continue
            
            # Dodaj encję
            entities.append([start, end, label])
            print(f"✅ Dodano: '{fragment}' jako {label} (pozycja {start}-{end})")
            print()
        
        # Dodaj do danych treningowych
        training_data.append({
            "text": text,
            "entities": entities
        })
        
        print(f"✅ Zakończono oznaczanie tekstu #{i}")
    
    # Zapisz dane treningowe
    output_file = Path("data/training_data.jsonl")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n🎉 ZAPISANO DANE TRENINGOWE!")
    print(f"📁 Plik: {output_file}")
    print(f"📊 Liczba oznaczonych tekstów: {len(training_data)}")
    
    # Statystyki
    total_entities = sum(len(item['entities']) for item in training_data)
    print(f"🏷️  Łączna liczba oznaczonych encji: {total_entities}")
    
    if total_entities > 0:
        label_counts = {}
        for item in training_data:
            for _, _, label in item['entities']:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        print("📈 Rozkład etykiet:")
        for label, count in label_counts.items():
            print(f"  {label}: {count}")


if __name__ == "__main__":
    prepare_training_data() 