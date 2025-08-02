from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Dodaj katalog backend do ścieżki
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    from store import GuestStore
except ImportError:
    print("Błąd importu GuestStore")
    GuestStore = None

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Inicjalizacja GuestStore
guest_store = GuestStore() if GuestStore else None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Główna strona z listą gości."""
    try:
        if not guest_store:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "guests": [],
                "stats": {"total_guests": 0, "total_views": 0, "total_mentions": 0, "avg_strength": 0},
                "error": "Backend nie jest dostępny"
            })
        
        # Wczytaj dane gości
        guests = guest_store.load_guests()
        stats = guest_store.get_stats()
        top_guests = guest_store.get_top_guests(10)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "guests": top_guests,
            "stats": stats,
            "total_guests": len(guests)
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "guests": [],
            "stats": {"total_guests": 0, "total_views": 0, "total_mentions": 0, "avg_strength": 0},
            "error": str(e)
        })

@app.get("/api/guest-list")
async def get_guest_list():
    """API endpoint zwracający listę gości w formacie JSON."""
    try:
        if not guest_store:
            return JSONResponse({
                "success": False,
                "error": "Backend nie jest dostępny",
                "data": []
            })
        
        guests = guest_store.load_guests()
        return JSONResponse({
            "success": True,
            "data": guests,
            "total": len(guests)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "data": []
        })

@app.get("/api/stats")
async def get_stats():
    """API endpoint zwracający statystyki gości."""
    try:
        if not guest_store:
            return JSONResponse({
                "success": False,
                "error": "Backend nie jest dostępny"
            })
        
        stats = guest_store.get_stats()
        return JSONResponse({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }) 

import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port) 