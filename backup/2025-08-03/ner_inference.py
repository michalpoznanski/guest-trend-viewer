#!/usr/bin/env python3
"""
Moduł do wczytywania i używania wytrenowanego modelu NER
"""

import spacy
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import json


def load_trained_ner_model(model_dir: str) -> Optional[spacy.language.Language]:
    """
    Wczytuje wytrenowany model spaCy NER z podanej ścieżki
    
    Args:
        model_dir: Ścieżka do folderu z modelem (np. 'models/ner_model_2025_08_02/')
        
    Returns:
        Obiekt spaCy nlp lub None w przypadku błędu
        
    Raises:
        FileNotFoundError: Jeśli folder modelu nie istnieje
        OSError: Jeśli model jest uszkodzony lub niekompletny
        ValueError: Jeśli ścieżka jest nieprawidłowa
    """
    try:
        # Sprawdź czy ścieżka istnieje
        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(f"Folder modelu nie istnieje: {model_dir}")
        
        if not model_path.is_dir():
            raise ValueError(f"Ścieżka nie jest folderem: {model_dir}")
        
        # Sprawdź czy model ma wymagane pliki
        required_files = ['config.cfg', 'meta.json']
        missing_files = [f for f in required_files if not (model_path / f).exists()]
        
        if missing_files:
            raise OSError(f"Model niekompletny - brakuje plików: {missing_files}")
        
        # Sprawdź czy istnieje komponent NER
        config_file = model_path / 'config.cfg'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
                if 'ner' not in config_content:
                    print("⚠️  Ostrzeżenie: Model może nie zawierać komponentu NER")
        
        # Wczytaj model
        print(f"🔄 Wczytywanie modelu NER z: {model_path.absolute()}")
        nlp = spacy.load(str(model_path))
        
        # Sprawdź czy model ma komponent NER
        if "ner" not in nlp.pipe_names:
            print("⚠️  Ostrzeżenie: Wczytany model nie zawiera komponentu NER")
        else:
            ner_labels = nlp.get_pipe("ner").labels
            print(f"✅ Model wczytany pomyślnie!")
            print(f"   🎯 Etykiety NER: {list(ner_labels)}")
            print(f"   🔧 Pipeline: {nlp.pipe_names}")
        
        return nlp
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        print(f"💡 Sprawdź czy folder '{model_dir}' istnieje")
        return None
        
    except OSError as e:
        print(f"❌ Błąd systemowy: {e}")
        print(f"💡 Model może być uszkodzony lub niekompletny")
        return None
        
    except ValueError as e:
        print(f"❌ Błąd wartości: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd podczas wczytywania modelu: {e}")
        return None


def test_model_loading(model_dir: str) -> bool:
    """
    Testuje wczytywanie modelu i wykonuje prosty test
    
    Args:
        model_dir: Ścieżka do modelu
        
    Returns:
        True jeśli test przeszedł pomyślnie
    """
    print(f"🧪 TEST WCZYTYWANIA MODELU")
    print("=" * 50)
    
    # Wczytaj model
    nlp = load_trained_ner_model(model_dir)
    if nlp is None:
        print("❌ Test nie przeszedł - nie udało się wczytać modelu")
        return False
    
    # Testowe frazy
    test_phrases = [
        "Rozmowa z Jakub Żulczyk o nowej książce",
        "Gość Piotr Pająk opowiada o podróżach",
        "Host Kuba Wojewódzki prowadzi wywiad",
        "Prof. Paweł Kaczmarczyk wyjaśnia ekonomię"
    ]
    
    print(f"\n🔍 TEST ROZPOZNAWANIA NAZWISK:")
    print("-" * 40)
    
    success_count = 0
    for i, phrase in enumerate(test_phrases, 1):
        try:
            doc = nlp(phrase)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            if entities:
                entities_str = ", ".join([f'"{text}" ({label})' for text, label in entities])
                print(f"✅ {i}. '{phrase}' → {entities_str}")
                success_count += 1
            else:
                print(f"⚠️  {i}. '{phrase}' → (brak wykrytych nazwisk)")
                
        except Exception as e:
            print(f"❌ {i}. '{phrase}' → Błąd: {e}")
    
    print(f"\n📊 WYNIKI TESTU:")
    print(f"   Przeszło: {success_count}/{len(test_phrases)} testów")
    
    if success_count > 0:
        print("✅ Model działa poprawnie!")
        return True
    else:
        print("❌ Model nie wykrywa nazwisk - może wymagać ponownego treningu")
        return False


def get_model_info(model_dir: str) -> Optional[Dict]:
    """
    Pobiera informacje o modelu
    
    Args:
        model_dir: Ścieżka do modelu
        
    Returns:
        Słownik z informacjami o modelu lub None
    """
    try:
        model_path = Path(model_dir)
        
        # Podstawowe informacje
        info = {
            "model_path": str(model_path.absolute()),
            "exists": model_path.exists(),
            "is_directory": model_path.is_dir() if model_path.exists() else False
        }
        
        if not model_path.exists():
            return info
        
        # Sprawdź pliki
        files = list(model_path.glob("*"))
        info["files"] = [f.name for f in files if f.is_file()]
        info["directories"] = [f.name for f in files if f.is_dir()]
        
        # Sprawdź metadane
        meta_file = model_path / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                info["metadata"] = meta
            except:
                info["metadata"] = "Błąd wczytywania"
        
        # Sprawdź dodatkowe metadane treningu
        training_meta = model_path / "metadata.json"
        if training_meta.exists():
            try:
                with open(training_meta, 'r', encoding='utf-8') as f:
                    training_info = json.load(f)
                info["training_info"] = training_info
            except:
                info["training_info"] = "Błąd wczytywania"
        
        return info
        
    except Exception as e:
        print(f"❌ Błąd podczas pobierania informacji o modelu: {e}")
        return None


def main():
    """
    Główna funkcja do testowania modułu
    """
    print("🤖 MODUŁ NER INFERENCE - TEST")
    print("=" * 50)
    
    # Test z przykładowym modelem
    model_dir = "models/ner_model_2025_08_02"
    
    # Pokaż informacje o modelu
    print(f"\n📋 INFORMACJE O MODELU:")
    print("-" * 30)
    info = get_model_info(model_dir)
    if info:
        print(f"Ścieżka: {info['model_path']}")
        print(f"Istnieje: {info['exists']}")
        if info['exists']:
            print(f"Pliki: {len(info.get('files', []))}")
            print(f"Foldery: {len(info.get('directories', []))}")
            
            if 'training_info' in info:
                training = info['training_info']
                print(f"Data treningu: {training.get('training_date', 'nieznana')}")
                print(f"Etykiety: {training.get('labels', [])}")
                print(f"Przykłady: {training.get('training_examples', 0)}")
    else:
        print("❌ Nie udało się pobrać informacji o modelu")
    
    # Test wczytywania
    print(f"\n🧪 TEST WCZYTYWANIA:")
    print("-" * 30)
    success = test_model_loading(model_dir)
    
    if success:
        print(f"\n✅ MODUŁ DZIAŁA POPRAWNIE!")
    else:
        print(f"\n❌ MODUŁ WYMAGA POPRAWEK!")


if __name__ == "__main__":
    main() 