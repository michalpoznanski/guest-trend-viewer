#!/bin/bash

echo "🚀 ROZPOCZYNAM TRENING MODELU SPACY NER"
echo "========================================"

# Sprawdź czy pliki treningowe istnieją
if [ ! -f "training/train.spacy" ]; then
    echo "❌ Brak pliku training/train.spacy"
    echo "Najpierw uruchom: python training/convert_data.py"
    exit 1
fi

if [ ! -f "training/dev.spacy" ]; then
    echo "❌ Brak pliku training/dev.spacy"
    echo "Najpierw uruchom: python training/convert_data.py"
    exit 1
fi

if [ ! -f "training/config.cfg" ]; then
    echo "❌ Brak pliku training/config.cfg"
    exit 1
fi

echo "✅ Wszystkie pliki treningowe znalezione"
echo "📊 Rozpoczynam trening..."

# Uruchom trening
python3 -m spacy train training/config.cfg \
    --output models/podcast_ner_v2 \
    --paths.train training/train.spacy \
    --paths.dev training/dev.spacy

echo ""
echo "🎉 TRENING ZAKOŃCZONY!"
echo "📁 Model zapisany w: models/podcast_ner_v2"
echo ""
echo "Aby przetestować model:"
echo "python -c \"import spacy; nlp = spacy.load('models/podcast_ner_v2'); doc = nlp('Tekst do testu'); print([(ent.text, ent.label_) for ent in doc.ents])\"" 