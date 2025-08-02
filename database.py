#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import json


class DatabaseManager:
    """Klasa do zarządzania bazą danych SQLite."""
    
    def __init__(self, db_path: str = "data.db"):
        self.db_path = db_path
        self.conn = None
    
    def get_connection(self):
        """Zwraca połączenie z bazą danych."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close_connection(self):
        """Zamyka połączenie z bazą danych."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_database(self):
        """Inicjalizuje bazę danych i tworzy tabele."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela gości
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                total_count INTEGER DEFAULT 0,
                spike BOOLEAN DEFAULT FALSE,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela trendów dziennych
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (guest_id) REFERENCES guests (id),
                UNIQUE(guest_id, date)
            )
        ''')
        
        # Indeksy dla lepszej wydajności
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_score ON guests(score DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_spike ON guests(spike)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trends_date ON daily_trends(date)')
        
        conn.commit()
        print("✅ Baza danych zainicjalizowana")
    
    def insert_or_update_guest(self, name: str, total_count: int, spike: bool, score: int):
        """Dodaje lub aktualizuje gościa w bazie danych."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO guests (name, total_count, spike, score, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, total_count, spike, score))
        
        conn.commit()
    
    def get_recommended_guests(self, limit: int = 50) -> List[Dict]:
        """Pobiera listę polecanych gości z bazy danych."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, total_count, spike, score
            FROM guests
            ORDER BY score DESC, total_count DESC
            LIMIT ?
        ''', (limit,))
        
        guests = []
        for row in cursor.fetchall():
            guests.append({
                'guest': row['name'],
                'total_count': row['total_count'],
                'spike': bool(row['spike']),
                'score': row['score']
            })
        
        return guests
    
    def get_guest_stats(self) -> Dict:
        """Pobiera statystyki gości z bazy danych."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Łączna liczba gości
        cursor.execute('SELECT COUNT(*) as total FROM guests')
        total_guests = cursor.fetchone()['total']
        
        # Goście ze skokami
        cursor.execute('SELECT COUNT(*) as spike_count FROM guests WHERE spike = 1')
        spike_guests = cursor.fetchone()['spike_count']
        
        # Goście z wysoką punktacją
        cursor.execute('SELECT COUNT(*) as high_score FROM guests WHERE score >= 2')
        high_score_guests = cursor.fetchone()['high_score']
        
        # Średnia punktacja
        cursor.execute('SELECT AVG(score) as avg_score FROM guests')
        avg_score = cursor.fetchone()['avg_score'] or 0
        
        return {
            'total_guests': total_guests,
            'spike_guests': spike_guests,
            'high_score_guests': high_score_guests,
            'avg_score': round(avg_score, 2)
        }
    
    def sync_from_csv(self, csv_path: str):
        """Synchronizuje bazę danych z plikiem CSV."""
        try:
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                self.insert_or_update_guest(
                    name=row['guest'],
                    total_count=row['total_count'],
                    spike=row['spike'],
                    score=row['score']
                )
            
            print(f"✅ Zsynchronizowano {len(df)} gości z pliku {csv_path}")
            
        except Exception as e:
            print(f"❌ Błąd synchronizacji: {e}")


# Globalna instancja menedżera bazy danych
db_manager = DatabaseManager()


def init_db():
    """Inicjalizuje bazę danych."""
    db_manager.init_database()


def get_recommended_guests(limit: int = 50) -> List[Dict]:
    """Pobiera listę polecanych gości."""
    return db_manager.get_recommended_guests(limit)


def get_guest_stats() -> Dict:
    """Pobiera statystyki gości."""
    return db_manager.get_guest_stats()


def sync_recommendations_from_csv():
    """Synchronizuje rekomendacje z pliku CSV."""
    csv_path = Path("trends/guest_recommendations.csv")
    if csv_path.exists():
        db_manager.sync_from_csv(str(csv_path))
    else:
        print("⚠️  Plik guest_recommendations.csv nie istnieje")


if __name__ == "__main__":
    # Test bazy danych
    init_db()
    sync_recommendations_from_csv()
    
    stats = get_guest_stats()
    print(f"Statystyki: {stats}")
    
    guests = get_recommended_guests(5)
    print(f"Top 5 gości: {guests}") 