#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agregacja trendów nazwisk gości z wielu plików CSV (Guest Radar)

Użycie:
    python3 aggregate_guest_trends.py --input-dir ner_podcast_improved --output trends/guest_trends.json

Autor: Guest Radar System
Data: 2025-08-03
"""

import os
import argparse
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict, Counter
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("aggregate_guest_trends")

def extract_date_from_filename(filename: str) -> str:
    """Wyciąga datę z nazwy pliku typu ner_output_2025-07-29_improved.csv"""
    match = re.search(r'ner_output_(\d{4}-\d{2}-\d{2})_improved\.csv', filename)
    if match:
        return match.group(1)
    return "unknown"

def aggregate_trends(input_dir: str, output_file: str):
    input_path = Path(input_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    guest_stats = defaultdict(lambda: {"total_count": 0, "daily_counts": defaultdict(int)})

    files = sorted(input_path.glob("ner_output_*_improved.csv"))
    logger.info(f"🔍 Znaleziono {len(files)} plików do agregacji w {input_dir}")

    for file in files:
        date = extract_date_from_filename(file.name)
        if date == "unknown":
            logger.warning(f"⚠️  Nie rozpoznano daty w pliku: {file.name}")
            continue

        df = pd.read_csv(file)
        for _, row in df.iterrows():
            detected = row.get("detected_names", "")
            if not isinstance(detected, str) or not detected.strip():
                continue
            names = [name.strip() for name in detected.split(",") if name.strip()]
            for name in names:
                guest_stats[name]["total_count"] += 1
                guest_stats[name]["daily_counts"][date] += 1

    # Konwersja defaultdict do zwykłego dict
    guest_stats = {
        name: {
            "total_count": stats["total_count"],
            "daily_counts": dict(stats["daily_counts"])
        }
        for name, stats in guest_stats.items()
    }

    # Sortowanie po total_count malejąco
    guest_stats_sorted = dict(sorted(guest_stats.items(), key=lambda x: x[1]["total_count"], reverse=True))

    # Zapisz do pliku JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(guest_stats_sorted, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ Zapisano wynik do: {output_path.absolute()}")
    logger.info(f"📊 Liczba unikalnych nazwisk: {len(guest_stats_sorted)}")

    # Top 5 nazwisk
    logger.info("\n🏆 TOP 5 NAZWISK:")
    for i, (name, stats) in enumerate(list(guest_stats_sorted.items())[:5], 1):
        logger.info(f"  {i}. {name} ({stats['total_count']} wystąpień, dni: {len(stats['daily_counts'])})")

def main():
    parser = argparse.ArgumentParser(description="Agregacja trendów nazwisk gości z wielu plików CSV")
    parser.add_argument("--input-dir", default="ner_podcast_improved", help="Katalog z plikami CSV (default: ner_podcast_improved)")
    parser.add_argument("--output", default="trends/guest_trends.json", help="Plik wyjściowy JSON (default: trends/guest_trends.json)")
    args = parser.parse_args()

    aggregate_trends(args.input_dir, args.output)

if __name__ == "__main__":
    main()