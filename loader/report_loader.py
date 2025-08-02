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


def load_latest_podcast_report(report_dir: str) -> pd.DataFrame:
    """
    Wczytuje najnowszy plik report_PODCAST_YYYY-MM-DD.csv z folderu report_dir
    i zwraca jako DataFrame
    
    Args:
        report_dir (str): Ścieżka do folderu z raportami
        
    Returns:
        pd.DataFrame: Wczytane dane z najnowszego raportu CSV
        
    Raises:
        FileNotFoundError: Jeśli nie znaleziono żadnych plików pasujących do wzorca
        ValueError: Jeśli wystąpił błąd podczas wczytywania pliku
    """
    import glob
    import re
    from datetime import datetime
    
    # Sprawdź czy folder istnieje
    if not os.path.exists(report_dir):
        raise FileNotFoundError(f"Folder raportów nie istnieje: {report_dir}")
    
    # Wyszukaj pliki pasujące do wzorca report_PODCAST_*.csv
    pattern = os.path.join(report_dir, "report_PODCAST_*.csv")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        raise FileNotFoundError(f"Nie znaleziono żadnych plików report_PODCAST_*.csv w folderze: {report_dir}")
    
    # Funkcja do wyciągnięcia daty z nazwy pliku
    def extract_date_from_filename(filename):
        # Wyciągnij datę z nazwy pliku report_PODCAST_YYYY-MM-DD.csv
        match = re.search(r'report_PODCAST_(\d{4}-\d{2}-\d{2})\.csv', os.path.basename(filename))
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d')
        return datetime.min  # Domyślna data dla plików bez daty
    
    # Posortuj pliki malejąco po dacie w nazwie
    sorted_files = sorted(matching_files, key=extract_date_from_filename, reverse=True)
    
    # Wybierz najnowszy plik
    latest_file = sorted_files[0]
    print(f"Wczytuję najnowszy raport podcast: {os.path.basename(latest_file)}")
    
    # Wczytaj CSV jako pandas.DataFrame
    try:
        df = pd.read_csv(latest_file)
        print(f"Pomyślnie wczytano raport z {len(df)} wierszami")
        return df
    except Exception as e:
        raise ValueError(f"Błąd podczas wczytywania pliku CSV {latest_file}: {str(e)}")


if __name__ == "__main__":
    # Przykład użycia nowej funkcji
    try:
        # Użyj domyślnego folderu /mnt/volume/reports/
        df = load_latest_podcast_report("/mnt/volume/reports/")
        print("Najnowszy raport podcast:")
        print(df.head())
    except FileNotFoundError as e:
        print(f"Błąd: {e}")
    except ValueError as e:
        print(f"Błąd: {e}")
    
    # Oryginalna funkcja
    try:
        df = get_latest_report()
        print("\nNajnowszy raport (oryginalna funkcja):")
        print(df.head())
    except Exception as e:
        print(f"Błąd: {e}") 