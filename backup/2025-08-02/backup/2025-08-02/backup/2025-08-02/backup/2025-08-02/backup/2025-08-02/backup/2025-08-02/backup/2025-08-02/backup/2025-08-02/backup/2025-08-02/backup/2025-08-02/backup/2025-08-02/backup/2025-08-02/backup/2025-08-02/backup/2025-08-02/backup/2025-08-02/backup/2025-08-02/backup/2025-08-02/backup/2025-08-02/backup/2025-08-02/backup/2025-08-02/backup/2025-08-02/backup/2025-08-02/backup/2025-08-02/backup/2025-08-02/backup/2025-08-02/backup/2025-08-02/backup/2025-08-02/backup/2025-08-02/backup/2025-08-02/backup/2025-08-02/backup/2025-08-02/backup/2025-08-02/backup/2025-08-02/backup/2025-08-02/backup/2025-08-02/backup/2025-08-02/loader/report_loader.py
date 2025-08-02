import json
import os
import pandas as pd
from pathlib import Path
from typing import Optional


def load_config() -> dict:
    """
    Wczytuje konfigurację z pliku config.json
    """
    config_path = Path('./config.json')
    if not config_path.exists():
        raise FileNotFoundError("Plik config.json nie został znaleziony")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_latest_report() -> pd.DataFrame:
    """
    Wczytuje najnowszy raport CSV z folderu raw_reports/
    
    Returns:
        pd.DataFrame: Wczytane dane z najnowszego raportu CSV
        
    Raises:
        FileNotFoundError: Jeśli nie znaleziono żadnych plików CSV
        ValueError: Jeśli brakuje wymaganych kolumn
    """
    # Wczytaj konfigurację
    config = load_config()
    reports_folder = Path(config['reports_folder'])
    
    # Sprawdź czy folder istnieje
    if not reports_folder.exists():
        raise FileNotFoundError(f"Folder raportów nie istnieje: {reports_folder}")
    
    # Znajdź wszystkie pliki CSV w folderze
    csv_files = list(reports_folder.glob('*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono żadnych plików CSV w folderze: {reports_folder}")
    
    # Wybierz najnowszy plik (sortuj po czasie modyfikacji)
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"Wczytuję najnowszy raport: {latest_file.name}")
    
    # Wczytaj CSV
    try:
        df = pd.read_csv(latest_file)
    except Exception as e:
        raise ValueError(f"Błąd podczas wczytywania pliku CSV {latest_file}: {str(e)}")
    
    # Sprawdź wymagane kolumny
    required_columns = ['title', 'description', 'tags', 'views', 'duration', 'video_type']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Brakujące wymagane kolumny w raporcie: {missing_columns}")
    
    print(f"Pomyślnie wczytano raport z {len(df)} wierszami")
    return df


if __name__ == "__main__":
    df = get_latest_report()
    print(df.head()) 