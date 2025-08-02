import json
from pathlib import Path
import pandas as pd
from datetime import datetime

# Ścieżka do pliku
path = Path("trends/guest_trends.json")
if not path.exists():
    print("❌ Nie znaleziono pliku trends/guest_trends.json")
    exit(1)

# Załaduj dane
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ustal 3 ostatnie daty
all_dates = set()
for guest in data.values():
    all_dates.update(guest.get("daily_counts", {}).keys())

last_dates = sorted(all_dates)[-3:]

# Zbierz wyniki
results = []
for name, guest_data in data.items():
    counts = guest_data.get("daily_counts", {})
    total = sum(counts.get(day, 0) for day in last_dates)
    if total > 0:
        results.append({
            "name": name,
            "last_3_days_total": total,
            "last_dates": ", ".join(f"{d}: {counts.get(d, 0)}" for d in last_dates)
        })

# Posortuj i pokaż
df = pd.DataFrame(results)
df = df.sort_values("last_3_days_total", ascending=False)

print("\n📊 RANKING NAZWISK Z OSTATNICH 3 DNI\n")
print(df.to_string(index=False))