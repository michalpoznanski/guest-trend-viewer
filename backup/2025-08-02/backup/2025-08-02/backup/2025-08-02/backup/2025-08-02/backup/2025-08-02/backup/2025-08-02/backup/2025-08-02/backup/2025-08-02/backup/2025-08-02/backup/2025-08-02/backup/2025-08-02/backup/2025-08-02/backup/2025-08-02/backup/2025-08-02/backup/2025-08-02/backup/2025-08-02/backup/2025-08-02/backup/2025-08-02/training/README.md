# 🎯 TRENING MODELU SPACY NER - PODCAST TREND

## 📋 Wymagania

Przed rozpoczęciem treningu upewnij się, że masz zainstalowane:
- Python 3.7+
- spaCy
- pandas

```bash
pip install -r requirements.txt
```

## 🚀 Instrukcja treningu

### Krok 1: Przygotowanie danych treningowych
```bash
python analyzer/prepare_training_data.py
```
- Otworzy interfejs do ręcznego oznaczania fragmentów tekstu
- Oznacz fragmenty jako: GUEST, HOST, OTHER
- Dane zostaną zapisane w `data/training_data.jsonl`

### Krok 2: Konwersja danych do formatu spaCy
```bash
python training/convert_data.py
```
- Wczyta dane z `data/training_data.jsonl`
- Podzieli dane na train (80%) i dev (20%)
- Utworzy pliki `training/train.spacy` i `training/dev.spacy`

### Krok 3: Trening modelu
```bash
bash training/train.sh
```
- Uruchomi trening modelu spaCy
- Model zostanie zapisany w `models/podcast_ner_v2`

## 📁 Struktura plików

```
training/
├── convert_data.py    # Konwersja danych do formatu spaCy
├── config.cfg         # Konfiguracja spaCy (język polski, NER)
├── train.sh           # Skrypt do uruchomienia treningu
├── train.spacy        # Dane treningowe (generowane)
├── dev.spacy          # Dane walidacyjne (generowane)
└── README.md          # Ten plik
```

## 🧪 Testowanie modelu

Po zakończeniu treningu możesz przetestować model:

```python
import spacy

# Wczytaj wytrenowany model
nlp = spacy.load('models/podcast_ner_v2')

# Przetestuj na przykładowym tekście
text = "Podcast z Janem Kowalskim | Prowadzący: Kuba Wojewódzki"
doc = nlp(text)

# Wyświetl znalezione encje
for ent in doc.ents:
    print(f"{ent.text} -> {ent.label_}")
```

## ⚙️ Konfiguracja

Plik `config.cfg` zawiera:
- Język: polski (pl)
- Pipeline: NER (Named Entity Recognition)
- Optymalizacja: efficiency (CPU)
- Brak transformerów (dla kompatybilności)

## 📊 Statystyki treningu

Podczas treningu spaCy wyświetli:
- Loss na zbiorze treningowym
- Metryki na zbiorze walidacyjnym
- F1-score dla każdej etykiety
- Wykresy w TensorBoard (jeśli dostępne)

## 🔧 Rozwiązywanie problemów

### Brak plików treningowych
```bash
# Sprawdź czy dane zostały przygotowane
ls data/training_data.jsonl
```

### Błąd konwersji
```bash
# Sprawdź format danych
head -5 data/training_data.jsonl
```

### Błąd treningu
```bash
# Sprawdź czy spaCy jest zainstalowane
python -c "import spacy; print(spacy.__version__)"
``` 