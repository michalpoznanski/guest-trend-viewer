#!/usr/bin/env python3
"""
Prosty skrypt do tworzenia backupu projektu podcast_trend
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

def main():
    print("🔄 TWORZENIE BACKUPU PROJEKTU PODCAST TREND")
    print("=" * 50)
    
    # Ścieżki
    source = Path(".")
    backup_dir = Path("backup/2025-08-02")
    
    # Utwórz folder backup
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Utworzono folder: {backup_dir}")
    
    # Foldery do skopiowania
    folders = ["data", "models", "output", "loader", "analyzer", 
               "active_learning", "training", "dispatcher", "tests"]
    
    # Pliki do skopiowania
    files = ["config.json", "requirements.txt", "main.py", "daily_runner.py"]
    
    # Kopiuj foldery
    for folder in folders:
        src = source / folder
        dst = backup_dir / folder
        if src.exists():
            try:
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"✅ {folder}/")
            except Exception as e:
                print(f"❌ {folder}/ - {e}")
        else:
            print(f"⚠️  {folder}/ - nie istnieje")
    
    # Kopiuj pliki
    for file in files:
        src = source / file
        dst = backup_dir / file
        if src.exists():
            try:
                shutil.copy2(src, dst)
                print(f"✅ {file}")
            except Exception as e:
                print(f"❌ {file} - {e}")
        else:
            print(f"⚠️  {file} - nie istnieje")
    
    # Plik informacyjny
    info_file = backup_dir / "backup_info.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"Backup projektu podcast_trend\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Lokalizacja: {backup_dir.absolute()}\n")
    
    print(f"\n🎉 BACKUP ZAKOŃCZONY!")
    print(f"📁 {backup_dir.absolute()}")

if __name__ == "__main__":
    main() 