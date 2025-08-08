import os, re, pandas as pd

REPORT_DIR = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume") + "/reports"

def latest_podcast_report()->str|None:
    if not os.path.isdir(REPORT_DIR):
        return None
    files = [f for f in os.listdir(REPORT_DIR) if re.match(r"report_PODCAST_\d{4}-\d{2}-\d{2}.csv", f)]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(REPORT_DIR, files[0])

def load_latest()->pd.DataFrame|None:
    path = latest_podcast_report()
    if not path:
        return None
    return pd.read_csv(path)
