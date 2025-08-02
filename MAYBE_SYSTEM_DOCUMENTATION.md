# 🔮 DOKUMENTACJA SYSTEMU MAYBE

## Przegląd

System MAYBE to inteligentna logika dla przycisku `M` w interaktywnym systemie oznaczania danych treningowych. Implementuje zaawansowane uczenie aktywne oparte na embeddingach.

## Komponenty

### 1. MaybeEngine (`active_learning/maybe_engine.py`)

**Główne funkcje:**
- `add_maybe_example(phrase, source)` - Dodaje nowy przykład MAYBE
- `generate_similar_candidates()` - Generuje podobnych kandydatów co 10 kliknięć
- `get_maybe_stats()` - Zwraca statystyki systemu MAYBE
- `is_suggestion_from_maybe(phrase)` - Sprawdza czy fraza to sugestia z MAYBE

**Kluczowe cechy:**
- ✅ Używa polskiego modelu spaCy (`pl_core_news_sm`) do embeddingów
- ✅ Fallback na angielski model jeśli brak polskiego
- ✅ Trigger co 10 przykładów MAYBE automatycznie generuje sugestie
- ✅ Embeddingowy cosine similarity do znajdowania podobieństw
- ✅ Próg podobieństwa 0.7 dla filtrowania kandydatów
- ✅ Top-10 najbardziej podobnych kandydatów

### 2. InteractiveFeedbackHandler (zaktualizowany)

**Nowe funkcjonalności:**
- ✅ Integracja z MaybeEngine
- ✅ Automatyczne dodawanie przykładów MAYBE przy kliknięciu `M`
- ✅ Wyświetlanie symbolu `~M` dla sugestii z systemu MAYBE
- ✅ Statystyki MAYBE w podsumowaniu

### 3. Pliki danych

**`data/maybe_examples.json`** - Przechowuje przykłady MAYBE:
```json
[
  {
    "text": "Jakub Kowalski",
    "source": "title",
    "label": "M",
    "timestamp": "2025-08-02T10:01:22.123001"
  }
]
```

**`data/feedback_candidates.json`** - Rozszerzony o sugestie z MAYBE:
```json
[
  {
    "phrase": "Podobna Fraza",
    "source": "description",
    "suggested_by_maybe": true,
    "similarity_score": 0.889,
    "timestamp": "2025-08-02T10:01:29.784706"
  }
]
```

## Przepływ działania

1. **Użytkownik klika `M`** → Fraza zapisana do `maybe_examples.json`
2. **Co 10 przykładów MAYBE** → Automatyczny trigger generowania sugestii
3. **Generowanie embeddingów** → spaCy przetwarza wszystkie przykłady MAYBE
4. **Wyszukiwanie podobnych** → Cosine similarity z `filtered_candidates.json`
5. **Filtrowanie** → Próg 0.7, top-10 wyników
6. **Zapisanie sugestii** → Dodanie do `feedback_candidates.json` z flagą `suggested_by_maybe: true`
7. **Oznaczanie w GUI** → Symbol `~M` przy sugerowanych frazach

## Wymagania systemowe

**Biblioteki Python:**
```
pandas
spacy
scikit-learn
numpy
```

**Modele spaCy:**
- `pl_core_news_sm` (preferowany)
- `en_core_web_sm` (fallback)

## Konfiguracja

**MaybeEngine parameters:**
- `trigger_count: 10` - Co ile przykładów uruchamiać generator
- `threshold: 0.7` - Minimalny próg podobieństwa
- `top_k: 10` - Maksymalna liczba sugestii

## Testowanie

Uruchom test systemu:
```bash
python3 test_maybe_system.py
```

## Użytkowanie

1. **Uruchom feedback handler:**
   ```bash
   python3 active_learning/feedback_handler.py
   ```

2. **Oznaczaj frazy:**
   - `G` - GUEST
   - `H` - HOST  
   - `I` - OTHER
   - **`M` - MAYBE** (nowa inteligentna logika)
   - `Q` - QUIT

3. **Obserwuj sugestie:**
   - Po 10 kliknięciach `M` system automatycznie wygeneruje podobne kandydatów
   - Sugerowane frazy będą oznaczone symbolem `🔮 ~M`

## Monitorowanie

**Statystyki MAYBE:**
```
🔮 STATYSTYKI MAYBE ENGINE:
----------------------------------------
📝 Łącznie przykładów MAYBE: 10
🎯 Do następnego triggera: 0
📋 Ostatnie przykłady: Fraza A, Fraza B, Fraza C
📊 Źródła: {'title': 4, 'description': 3, 'tags': 3}
```

## Rozwiązywanie problemów

**Problem:** Brak modelu spaCy
**Rozwiązanie:** 
```bash
python3 -m spacy download pl_core_news_sm
```

**Problem:** Brak bibliotek
**Rozwiązanie:**
```bash
pip3 install -r requirements.txt
```

**Problem:** Brak sugestii
**Sprawdzenie:** System generuje sugestie dopiero po 10 przykładach MAYBE z podobieństwem >= 0.7

## Architektura danych

```
data/
├── maybe_examples.json          # Przykłady MAYBE + metadane
├── filtered_candidates.json     # Źródło kandydatów do podobieństwa  
├── feedback_candidates.json     # Sugestie + flagi suggested_by_maybe
└── feedback.json               # Finalne oznaczenia użytkownika
```

---
✅ **System MAYBE zaimplementowany i przetestowany - 2025-08-03**