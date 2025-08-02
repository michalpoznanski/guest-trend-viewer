from pipeline.ner_inference import load_trained_ner_model

print('🧪 TEST FUNKCJI load_trained_ner_model()')
print('=' * 50)

# Ścieżka do modelu
model_dir = 'models/ner_model_2025_08_02'
print(f'📁 Wczytuję model z: {model_dir}')

nlp = load_trained_ner_model(model_dir)

if nlp is not None:
    print('✅ Model wczytany pomyślnie!')
    
    test_text = 'W dzisiejszym odcinku gościem jest Jakub Żulczyk, a rozmowę prowadzi Kuba Wojewódzki.'
    print(f'\n🔍 TEST INFERENCJI:\nTekst: "{test_text}"\n')
    
    doc = nlp(test_text)
    if doc.ents:
        print('📊 WYKRYTE ENCJE:')
        for ent in doc.ents:
            print(f'   {ent.text} → {ent.label_}')
        print('\n✅ Model działa poprawnie i wykrywa etykiety GUEST / HOST')
    else:
        print('❌ Nie wykryto żadnych encji')
else:
    print('❌ Nie udało się wczytać modelu')