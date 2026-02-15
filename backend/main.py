from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import asyncio
import platform
import logging

# --- 1. KRITICKÁ ČÁST PRO WINDOWS ---
# Musí to být úplně nahoře, dříve než se vytvoří jakákoliv async smyčka
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Přidání cesty pro importy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importy s lepším ošetřením chyb
try:
    from src.scraper import process_event
    from crawl4ai import AsyncWebCrawler
except ImportError as e:
    print(f"FATAL: Import failed: {e}")
    sys.exit(1)

app = FastAPI(title="Party Scraper API")

# --- 2. CORS NASTAVENÍ (ponecháno, je správně) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    url: str
    date: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Party Scraper API is running."}


@app.post("/scrape")
async def scrape_url(request: ScrapeRequest):
    print(f"Starting scrape: {request.url}")

    # --- 3. FIX PRO CRAWL4AI UVNITŘ FASTAPI ---
    # Crawl4AI/Playwright vyžadují čisté prostředí.
    # Vytváříme crawler instance přímo v requestu, ale s ošetřením chyb.
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            # Důležité: timeout ošetři i zde, aby request nevisel věčně
            detail = await asyncio.wait_for(
                process_event(crawler, request.url, request.date or ""),
                timeout=60.0  # Max 60 sekund na jeden scrape
            )

            if not detail:
                raise HTTPException(
                    status_code=404, detail="Data extraction failed")

            return detail

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Scraping timed out")
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"SERVER ERROR:\n{error_msg}")
        # Vrácením 500 zajistíme, že prohlížeč dostane odpověď a nevyhodí CORS error
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    # --- 4. POZOR NA RELOAD NA WINDOWS ---
    # reload=True na Windows často rozbíjí Event Loop Policy pro Playwright.
    # Pro ladění scrapingu doporučuji reload=False.
    # Také se ujisti, že název souboru odpovídá (zde předpokládám backend-main.py)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
