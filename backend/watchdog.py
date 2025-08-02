import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from datetime import datetime

# Import naszych modułów
from .analyze import GuestAnalyzer
from .store import GuestStore

class ReportHandler(FileSystemEventHandler):
    """Handler do obsługi zdarzeń w folderze raportów."""
    
    def __init__(self, reports_dir: str = "/mnt/volume/reports"):
        self.reports_dir = Path(reports_dir)
        self.analyzer = GuestAnalyzer(reports_dir)
        self.store = GuestStore()
        self.processed_files = set()
        
        # Konfiguracja logowania
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('watchdog.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        """Obsługuje zdarzenie utworzenia nowego pliku."""
        if not event.is_directory and event.src_path.endswith('.csv'):
            self.logger.info(f"Wykryto nowy plik: {event.src_path}")
            self.process_new_file(event.src_path)
    
    def on_moved(self, event):
        """Obsługuje zdarzenie przeniesienia pliku."""
        if not event.is_directory and event.dest_path.endswith('.csv'):
            self.logger.info(f"Wykryto przeniesiony plik: {event.dest_path}")
            self.process_new_file(event.dest_path)
    
    def process_new_file(self, file_path: str):
        """Przetwarza nowy plik CSV."""
        try:
            # Sprawdź czy plik nie był już przetwarzany
            if file_path in self.processed_files:
                self.logger.info(f"Plik {file_path} już był przetwarzany")
                return
            
            # Dodaj do listy przetworzonych
            self.processed_files.add(file_path)
            
            # Poczekaj chwilę, żeby plik został w pełni zapisany
            time.sleep(2)
            
            # Sprawdź czy plik nadal istnieje
            if not os.path.exists(file_path):
                self.logger.warning(f"Plik {file_path} nie istnieje po oczekiwaniu")
                return
            
            self.logger.info(f"Rozpoczynam analizę pliku: {file_path}")
            
            # Wygeneruj nowy ranking
            success = self.analyzer.generate_ranking()
            
            if success:
                self.logger.info("Analiza zakończona pomyślnie")
                
                # Wczytaj i wyświetl statystyki
                guests = self.store.load_guests()
                stats = self.store.get_stats()
                
                self.logger.info(f"Statystyki: {stats['total_guests']} gości, "
                               f"{stats['total_views']} wyświetleń, "
                               f"{stats['total_mentions']} wzmianek")
                
                # Wyświetl top 3 gości
                top_guests = self.store.get_top_guests(3)
                self.logger.info("Top 3 goście:")
                for i, guest in enumerate(top_guests, 1):
                    self.logger.info(f"{i}. {guest['name']} - {guest['total_strength']} strength")
            else:
                self.logger.error("Błąd podczas analizy pliku")
                
        except Exception as e:
            self.logger.error(f"Błąd podczas przetwarzania pliku {file_path}: {e}")

def start_watcher(reports_dir: str = "/mnt/volume/reports"):
    """Uruchamia monitorowanie folderu raportów."""
    reports_path = Path(reports_dir)
    
    # Sprawdź czy katalog istnieje
    if not reports_path.exists():
        print(f"Katalog {reports_path} nie istnieje!")
        print("Tworzę katalog...")
        reports_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Rozpoczynam monitorowanie katalogu: {reports_path}")
    print("Naciśnij Ctrl+C aby zatrzymać...")
    
    # Utwórz handler i observer
    event_handler = ReportHandler(reports_dir)
    observer = Observer()
    observer.schedule(event_handler, str(reports_path), recursive=False)
    
    try:
        # Uruchom observer
        observer.start()
        
        # Wykonaj początkową analizę
        print("Wykonuję początkową analizę...")
        event_handler.analyzer.generate_ranking()
        
        # Monitoruj w pętli
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nZatrzymuję monitorowanie...")
        observer.stop()
    
    observer.join()
    print("Monitorowanie zatrzymane.")

def run_initial_analysis(reports_dir: str = "/mnt/volume/reports"):
    """Uruchamia początkową analizę wszystkich plików."""
    print("Uruchamiam początkową analizę...")
    
    analyzer = GuestAnalyzer(reports_dir)
    success = analyzer.generate_ranking()
    
    if success:
        store = GuestStore()
        guests = store.load_guests()
        stats = store.get_stats()
        
        print(f"Analiza zakończona!")
        print(f"Znaleziono {stats['total_guests']} gości")
        print(f"Łącznie {stats['total_views']} wyświetleń")
        print(f"Łącznie {stats['total_mentions']} wzmianek")
        
        # Wyświetl top 5
        top_guests = store.get_top_guests(5)
        print("\nTop 5 gości:")
        for i, guest in enumerate(top_guests, 1):
            print(f"{i}. {guest['name']} - {guest['total_strength']} strength")
    else:
        print("Błąd podczas analizy!")

# Przykład użycia
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        reports_dir = sys.argv[1]
    else:
        reports_dir = "/mnt/volume/reports"
    
    print(f"Używam katalogu raportów: {reports_dir}")
    
    # Sprawdź czy katalog istnieje
    if not Path(reports_dir).exists():
        print(f"Katalog {reports_dir} nie istnieje!")
        print("Uruchamiam z przykładowymi danymi...")
        
        # Utwórz przykładowe dane
        from .analyze import GuestAnalyzer
        analyzer = GuestAnalyzer()
        analyzer.generate_ranking()  # To utworzy przykładowe dane
    
    # Uruchom początkową analizę
    run_initial_analysis(reports_dir)
    
    # Uruchom monitorowanie
    start_watcher(reports_dir) 