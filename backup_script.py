#!/usr/bin/env python3
"""
Skrypt do tworzenia backupu projektu podcast_trend
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

def create_backup():
    """
    Tworzy backup całego projektu do folderu backup/2025-08-02/
    """
    print("🔄 ROZPOCZYNAM TWORZENIE BACKUPU PROJEKTU")
    print("=" * 50)
    
    # Określ ścieżki
    source_dir = Path(".")
    backup_dir = Path("backup/2025-08-02")
    
    # Utwórz folder backup
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Utworzono folder backup: {backup_dir.absolute()}")
    
    # Lista folderów do skopiowania
    folders_to_backup = [
        "data", "models", "output", 
        "loader", "analyzer", "active_learning", 
        "training", "dispatcher", "tests"
    ]
    
    # Lista plików do skopiowania
    files_to_backup = [
        "config.json", "requirements.txt", 
        "main.py", "daily_runner.py"
    ]
    
    # Kopiuj foldery
    for folder in folders_to_backup:
        source_folder = source_dir / folder
        if source_folder.exists():
            dest_folder = backup_dir / folder
            try:
                if dest_folder.exists():
                    shutil.rmtree(dest_folder)
                shutil.copytree(source_folder, dest_folder)
                print(f"✅ Skopiowano folder: {folder}")
            except Exception as e:
                print(f"❌ Błąd przy kopiowaniu {folder}: {e}")
        else:
            print(f"⚠️  Folder nie istnieje: {folder}")
    
    # Kopiuj pliki
    for file in files_to_backup:
        source_file = source_dir / file
        if source_file.exists():
            dest_file = backup_dir / file
            try:
                shutil.copy2(source_file, dest_file)
                print(f"✅ Skopiowano plik: {file}")
            except Exception as e:
                print(f"❌ Błąd przy kopiowaniu {file}: {e}")
        else:
            print(f"⚠️  Plik nie istnieje: {file}")
    
    # Stwórz plik informacyjny o backupie
    backup_info = backup_dir / "backup_info.txt"
    with open(backup_info, 'w', encoding='utf-8') as f:
        f.write("🗂️  BACKUP PROJEKTU PODCAST TREND\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Data utworzenia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Źródło: {source_dir.absolute()}\n")
        f.write(f"Backup: {backup_dir.absolute()}\n\n")
        f.write("Zawartość backupu:\n")
        for folder in folders_to_backup:
            if (source_dir / folder).exists():
                f.write(f"  📁 {folder}/\n")
        for file in files_to_backup:
            if (source_dir / file).exists():
                f.write(f"  📄 {file}\n")
    
    print(f"📋 Utworzono plik informacyjny: backup_info.txt")
    
    print(f"\n🎉 BACKUP ZAKOŃCZONY POMYŚLNIE!")
    print(f"📁 Lokalizacja: {backup_dir.absolute()}")
    
    return True

if __name__ == "__main__":
    try:
        create_backup()
        print("\n✅ SUKCES! Backup projektu został utworzony.")
    except Exception as e:
        print(f"\n❌ BŁĄD podczas tworzenia backupu: {e}")