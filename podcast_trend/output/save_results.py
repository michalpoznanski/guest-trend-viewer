import os, json, datetime as dt, pandas as pd

OUT_DIR = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume") + "/guest_analysis"

def save_json(df:pd.DataFrame, report_date:str|None)->str:
    os.makedirs(OUT_DIR, exist_ok=True)
    data = {
        "date": report_date or dt.date.today().isoformat(),
        "top": [{"name": r["name"], "views": int(r["views"])} for _, r in df.head(50).iterrows()]
    }
    path = os.path.join(OUT_DIR, "guest_trend_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
