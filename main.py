#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

from database import init_db, get_recommended_guests
from utils import load_guest_recommendations

# Inicjalizacja FastAPI
app = FastAPI(
    title="Podcast Guest Recommendations",
    description="System rekomendacji gości podcastów",
    version="1.0.0"
)

# Konfiguracja szablonów
templates = Jinja2Templates(directory="templates")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicjalizacja bazy danych przy starcie
@app.on_event("startup")
async def startup_event():
    """Inicjalizacja aplikacji przy starcie."""
    init_db()
    print("✅ Baza danych zainicjalizowana")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Główna strona z listą polecanych gości."""
    try:
        # Wczytaj dane z pliku CSV
        recommendations = load_guest_recommendations()
        
        # Pobierz dane z bazy danych (opcjonalnie)
        db_guests = get_recommended_guests()
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "recommendations": recommendations,
                "total_guests": len(recommendations),
                "top_guests": recommendations[:10] if recommendations else []
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": f"Błąd wczytywania danych: {str(e)}",
                "recommendations": [],
                "total_guests": 0,
                "top_guests": []
            }
        )

@app.get("/api/recommendations")
async def api_recommendations():
    """API endpoint zwracający rekomendacje w formacie JSON."""
    try:
        recommendations = load_guest_recommendations()
        return {
            "success": True,
            "data": recommendations,
            "total": len(recommendations)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@app.get("/health")
async def health_check():
    """Endpoint sprawdzający stan aplikacji."""
    return {
        "status": "healthy",
        "service": "podcast-guest-recommendations",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Uruchomienie serwera
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 