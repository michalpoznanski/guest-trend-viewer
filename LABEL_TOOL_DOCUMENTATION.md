# 🏷️ DOKUMENTACJA NARZĘDZIA LABEL.PY

## Przegląd

`label.py` to narzędzie CLI do ręcznego oznaczania fraz z pliku `data/filtered_candidates.json`. Umożliwia efektywne tworzenie danych treningowych dla modelu NER poprzez interaktywne oznaczanie kandydatów.

## Funkcje

### ✅ **Podstawowe funkcje:**
- ✅ Wczytuje kandydatów z `data/filtered_candidates.json`
- ✅ Pozwala oznaczać frazy jako: **G**=GUEST, **H**=HOST, **I**=IGNORE, **M**=MAYBE
- ✅ Zapisuje wyniki do `data/feedback.json`
- ✅ Pomija frazy już oznaczone wcześniej
- ✅ Działa w terminalu z prostym interfejsem

### ✅ **Zaawansowane funkcje:**
- ✅ **Obsługa błędów** - graceful handling braków plików, złych formatów
- ✅ **Auto-tworzenie plików** - tworzy pusty `feedback.json` jeśli nie istnieje
- ✅ **Unikanie duplikatów** - filtruje już oznaczone frazy
- ✅ **Statystyki** - pokazuje podsumowanie na końcu
- ✅ **Interruption handling** - obsługuje Ctrl+C i Ctrl+D
- ✅ **Progress tracking** - pokazuje postęp [X/Y]

## Użytkowanie

### Podstawowe użycie:
```bash
python3 label.py
```

### Pomoc:
```bash
python3 label.py --help
```

### Uruchomienie jako executable:
```bash
chmod +x label.py
./label.py
```

## Interfejs użytkownika

### Klawisze sterujące:
- **G/g** - GUEST (👥 gość podcastu)
- **H/h** - HOST (🎤 prowadzący)
- **I/i** - IGNORE (❌ ignoruj, nieistotne)
- **M/m** - MAYBE (❓ może być nazwiskiem)
- **S/s** - SKIP (⏭️ pomiń na razie)
- **Q/q** - QUIT (💾 zapisz i wyjdź)

### Przykład sesji:
```
============================================================
🏷️  NARZĘDZIE DO OZNACZANIA FRAZ
============================================================
Instrukcje:
  G = GUEST     (gość podcastu)
  H = HOST      (prowadzący)
  I = IGNORE    (ignoruj, nieistotne)
  M = MAYBE     (może być nazwiskiem)
  S = SKIP      (pomiń na razie)
  Q = QUIT      (zapisz i wyjdź)
============================================================

[1/1929]
Fraza: "Krzysztof Stanowski"
Wybór [G/H/I/M/S/Q]: G
✅ Oznaczono jako: 👥 Gość
💾 Zapisano

[2/1929]
Fraza: "Kuba Wojewódzki"
Wybór [G/H/I/M/S/Q]: H
✅ Oznaczono jako: 🎤 Host/Prowadzący
💾 Zapisano
```

## Format danych

### Wejście (`data/filtered_candidates.json`):
```json
[
  {
    "phrase": "Nazwa kandydata",
    "source": "title"
  },
  {
    "phrase": "Inna fraza",
    "source": "description"  
  }
]
```

### Wyjście (`data/feedback.json`):
```json
[
  {
    "text": "Nazwa kandydata",
    "label": "GUEST", 
    "source": "manual_cli"
  },
  {
    "text": "Inna fraza",
    "label": "IGNORE",
    "source": "manual_cli"
  }
]
```

## Statystyki i podsumowanie

Po zakończeniu sesji narzędzie wyświetla szczegółowe statystyki:

```
==================================================
📊 STATYSTYKI OZNACZANIA:
--------------------------------------------------
👥 GUEST   :  15 ( 45.5%)
🎤 HOST    :   3 (  9.1%)
❌ IGNORE  :  12 ( 36.4%)
❓ MAYBE   :   3 (  9.1%)

📊 ŁĄCZNIE OZNACZONO: 33
==================================================
```

## Obsługa błędów

### ✅ **Zabezpieczenia:**
- **Brak plików** - automatycznie tworzy pusty `feedback.json`
- **Złe formaty JSON** - graceful error handling z komunikatami
- **Przerwania** - Ctrl+C i Ctrl+D są bezpiecznie obsługiwane
- **Nieprawidłowe klawisze** - prosi o ponowne wprowadzenie
- **Błędy zapisu** - informuje o problemach z plikami

### **Komunikaty błędów:**
```
❌ Plik data/filtered_candidates.json nie istnieje!
❌ Błąd parsowania JSON w data/feedback.json: ...
❌ Błąd podczas zapisywania: ...
⚠️  Nieprawidłowy klawisz. Użyj: G, H, I, M, S, Q
⚠️  Przerwano przez użytkownika (Ctrl+C)
```

## Integracja z systemem

### **Kompatybilność z istniejącymi plikami:**
- ✅ Rozpoznaje różne klucze: `text`, `phrase`
- ✅ Kompatybilne z `feedback_handler.py`
- ✅ Źródło oznaczane jako `manual_cli`
- ✅ Zachowuje istniejące dane

### **Workflow:**
1. **Przygotowanie** - `training_set_builder.py` → `filtered_candidates.json`
2. **Oznaczanie** - `label.py` → `feedback.json`
3. **Trening** - `train_ner_model.py` używa `feedback.json`

## Wydajność

### **Aktualne statystyki:**
- ✅ **Łącznie kandydatów**: 2691
- ✅ **Już oznaczonych**: 969 (różne źródła)
- ✅ **Do oznaczenia**: 1929 
- ✅ **Prędkość**: ~1 fraza/sekundę (zależnie od użytkownika)

### **Szacowany czas:**
- **1929 fraz** × 2 sekundy = **~64 minuty** pełnego oznaczania
- **Można robić w transzach** dzięki funkcji SKIP i QUIT

## Najlepsze praktyki

### **Rekomendacje oznaczania:**
1. **GUEST** - jasne nazwiska gości (Janusz Kowalski, Anna Nowak)
2. **HOST** - prowadzący, gospodarze (Kuba Wojewódzki)
3. **MAYBE** - niepewne przypadki, mogą być nazwiskami 
4. **IGNORE** - frazy opisowe, nie-nazwiska (duże miasto, w programie)
5. **SKIP** - gdy się nie decydujesz, możesz wrócić później

### **Workflow:**
1. **Rozpocznij** sesję 10-20 minut
2. **Oznacz** oczywiste przypadki szybko
3. **SKIP** trudne przypadki
4. **QUIT** i wróć później do trudnych

### **Quality control:**
- Sprawdzaj czy fraza to rzeczywiście nazwisko
- W razie wątpliwości wybieraj MAYBE zamiast GUEST
- IGNORE dla fragmentów zdań i opisów

## Rozwiązywanie problemów

### **Problem:** Brak uprawnień do zapisu
**Rozwiązanie:** 
```bash
chmod 664 data/feedback.json
```

### **Problem:** Przerwane sesje
**Rozwiązanie:** Restartuj narzędzie - automatycznie pominie oznaczone

### **Problem:** Zbyt dużo kandydatów
**Rozwiązanie:** Używaj funkcji SKIP dla trudnych przypadków

---
✅ **Narzędzie gotowe do użycia - 2025-08-03**