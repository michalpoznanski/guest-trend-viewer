#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_guest_recommendations() -> List[Dict]:
    """
    Wczytuje rekomendacje gości z pliku CSV.
    
    Returns:
        Lista słowników z danymi gości
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
        Exception: Inne błędy wczytywania
    """
    csv_path = Path("trends/guest_recommendations.csv")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Plik {csv_path} nie istnieje!")
    
    try:
        df = pd.read_csv(csv_path)
        
        # Konwertuj DataFrame na listę słowników
        recommendations = []
        for _, row in df.iterrows():
            recommendations.append({
                'guest': row['guest'],
                'total_count': int(row['total_count']),
                'spike': bool(row['spike']),
                'score': int(row['score'])
            })
        
        # Sortuj po punktacji i liczbie wystąpień
        recommendations.sort(key=lambda x: (x['score'], x['total_count']), reverse=True)
        
        logger.info(f"Wczytano {len(recommendations)} rekomendacji gości")
        return recommendations
        
    except Exception as e:
        logger.error(f"Błąd wczytywania rekomendacji: {e}")
        raise


def load_guest_trends() -> Dict:
    """
    Wczytuje trendy gości z pliku JSON.
    
    Returns:
        Słownik z trendami gości
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
        json.JSONDecodeError: Jeśli plik ma nieprawidłowy format JSON
    """
    json_path = Path("trends/guest_trends_filtered.json")
    
    if not json_path.exists():
        raise FileNotFoundError(f"Plik {json_path} nie istnieje!")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            trends = json.load(f)
        
        logger.info(f"Wczytano trendy dla {len(trends)} gości")
        return trends
        
    except json.JSONDecodeError as e:
        logger.error(f"Błąd parsowania JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Błąd wczytywania trendów: {e}")
        raise


def load_guest_spikes() -> List[Dict]:
    """
    Wczytuje dane skoków gości z pliku CSV.
    
    Returns:
        Lista słowników z danymi skoków
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
    """
    csv_path = Path("trends/guest_spikes.csv")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Plik {csv_path} nie istnieje!")
    
    try:
        df = pd.read_csv(csv_path)
        
        spikes = []
        for _, row in df.iterrows():
            spikes.append({
                'guest': row['guest'],
                'count_last3': int(row['count_last3']),
                'count_prev3': int(row['count_prev3']),
                'growth_abs': int(row['growth_abs']),
                'growth_pct': float(row['growth_pct']),
                'spike': bool(row['spike'])
            })
        
        logger.info(f"Wczytano dane skoków dla {len(spikes)} gości")
        return spikes
        
    except Exception as e:
        logger.error(f"Błąd wczytywania skoków: {e}")
        raise


def get_trends_file_info() -> Dict:
    """
    Zwraca informacje o plikach w folderze trends.
    
    Returns:
        Słownik z informacjami o plikach
    """
    trends_dir = Path("trends")
    
    if not trends_dir.exists():
        return {"error": "Folder trends nie istnieje"}
    
    files_info = {}
    
    # Sprawdź pliki CSV
    csv_files = list(trends_dir.glob("*.csv"))
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            files_info[csv_file.name] = {
                "type": "CSV",
                "rows": len(df),
                "columns": list(df.columns),
                "size_kb": round(csv_file.stat().st_size / 1024, 2)
            }
        except Exception as e:
            files_info[csv_file.name] = {
                "type": "CSV",
                "error": str(e)
            }
    
    # Sprawdź pliki JSON
    json_files = list(trends_dir.glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                files_info[json_file.name] = {
                    "type": "JSON",
                    "keys": len(data),
                    "size_kb": round(json_file.stat().st_size / 1024, 2)
                }
            elif isinstance(data, list):
                files_info[json_file.name] = {
                    "type": "JSON",
                    "items": len(data),
                    "size_kb": round(json_file.stat().st_size / 1024, 2)
                }
        except Exception as e:
            files_info[json_file.name] = {
                "type": "JSON",
                "error": str(e)
            }
    
    return files_info


def validate_data_integrity() -> Dict:
    """
    Sprawdza integralność danych w folderze trends.
    
    Returns:
        Słownik z wynikami walidacji
    """
    validation_results = {
        "status": "ok",
        "errors": [],
        "warnings": [],
        "files_checked": 0
    }
    
    try:
        # Sprawdź rekomendacje
        recommendations = load_guest_recommendations()
        validation_results["files_checked"] += 1
        
        if len(recommendations) == 0:
            validation_results["warnings"].append("Plik rekomendacji jest pusty")
        
        # Sprawdź trendy
        trends = load_guest_trends()
        validation_results["files_checked"] += 1
        
        if len(trends) == 0:
            validation_results["warnings"].append("Plik trendów jest pusty")
        
        # Sprawdź skoki
        spikes = load_guest_spikes()
        validation_results["files_checked"] += 1
        
        if len(spikes) == 0:
            validation_results["warnings"].append("Plik skoków jest pusty")
        
        # Sprawdź spójność danych
        recommendation_guests = {r['guest'] for r in recommendations}
        trend_guests = set(trends.keys())
        spike_guests = {s['guest'] for s in spikes}
        
        # Goście w rekomendacjach ale nie w trendach
        missing_in_trends = recommendation_guests - trend_guests
        if missing_in_trends:
            validation_results["warnings"].append(f"Goście w rekomendacjach ale nie w trendach: {len(missing_in_trends)}")
        
        # Goście w skokach ale nie w rekomendacjach
        missing_in_recommendations = spike_guests - recommendation_guests
        if missing_in_recommendations:
            validation_results["warnings"].append(f"Goście w skokach ale nie w rekomendacjach: {len(missing_in_recommendations)}")
        
        if validation_results["errors"]:
            validation_results["status"] = "error"
        elif validation_results["warnings"]:
            validation_results["status"] = "warning"
        
    except Exception as e:
        validation_results["status"] = "error"
        validation_results["errors"].append(f"Błąd walidacji: {str(e)}")
    
    return validation_results


if __name__ == "__main__":
    # Test funkcji pomocniczych
    try:
        print("🔍 Testowanie funkcji pomocniczych...")
        
        # Test wczytywania rekomendacji
        recommendations = load_guest_recommendations()
        print(f"✅ Wczytano {len(recommendations)} rekomendacji")
        
        # Test wczytywania trendów
        trends = load_guest_trends()
        print(f"✅ Wczytano trendy dla {len(trends)} gości")
        
        # Test wczytywania skoków
        spikes = load_guest_spikes()
        print(f"✅ Wczytano skoki dla {len(spikes)} gości")
        
        # Test informacji o plikach
        files_info = get_trends_file_info()
        print(f"✅ Informacje o plikach: {len(files_info)} plików")
        
        # Test walidacji
        validation = validate_data_integrity()
        print(f"✅ Walidacja: {validation['status']}")
        
    except Exception as e:
        print(f"❌ Błąd testowania: {e}") 