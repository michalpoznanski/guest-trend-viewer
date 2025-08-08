from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from loader.report_loader import load_latest
from analyzer.name_counter import build_ranking
from output.save_results import save_json
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="podcast_trend/templates")

@app.get("/health")
def health(): 
    return {"status":"ok"}

@app.get("/podcast-trend/run")
def run_analysis():
    df = load_latest()
    if df is None: 
        return JSONResponse({"error":"no report found"}, status_code=404)
    rank = build_ranking(df)
    # spróbuj wziąć datę z kolumny Date_of_Publishing jeśli istnieje
    report_date = None
    if "Date_of_Publishing" in df.columns and not df.empty:
        report_date = str(df["Date_of_Publishing"].max())
    path = save_json(rank, report_date)
    return {"saved": path, "count": int(len(rank))}

@app.get("/podcast-trend", response_class=HTMLResponse)
def dashboard(request: Request):
    import json, os
    path = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume") + "/guest_analysis/guest_trend_summary.json"
    data = {"top":[]}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return templates.TemplateResponse("podcast_dashboard.html", {"request": request, "data": data})
