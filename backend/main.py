from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os
import asyncio
import platform
import logging
import json

# --- 1. KRITICKÁ ČÁST PRO WINDOWS ---
# Musí to být úplně nahoře, dříve než se vytvoří jakákoliv async smyčka
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Přidání cesty pro importy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importy s lepším ošetřením chyb
try:
    from src.scraper import process_event, process_batch
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
    # ... ponecháno pro kompatibilitu ...
    print(f"Starting scrape: {request.url}")
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            detail = await asyncio.wait_for(
                process_event(crawler, request.url, request.date or ""),
                timeout=60.0
            )
            if not detail:
                raise HTTPException(status_code=404, detail="Data extraction failed")
            return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape-batch")
async def scrape_batch(request: dict):
    """
    Spustí hromadné zpracování pomocí jedné instance crawleru (process_batch).
    """
    print(f"Starting batch scrape for {len(request)} venues")
    try:
        results = await process_batch(request)
        return results
    except Exception as e:
        import traceback
        print(f"BATCH ERROR:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape-batch-stream")
async def scrape_batch_stream(request: dict):
    """
    Groups events by venue. Streams result-by-result.
    Format of chunk: { "VenueName": [event] }
    """
    async def event_generator():
        async with AsyncWebCrawler(verbose=True) as crawler:
            for venue, events in request.items():
                for event in events:
                    url = event.get("url")
                    date = event.get("date")
                    if not url:
                        continue

                    print(f"Processing stream item: {url}")
                    try:
                        detail = await asyncio.wait_for(
                            process_event(crawler, url, date or ""),
                            timeout=60.0
                        )
                        if detail:
                            res = detail.model_dump()
                            # Wrap in venue key for grouped format
                            yield json.dumps({venue: [res]}) + "\n"
                        else:
                            yield json.dumps({venue: [{"url": url, "error": "Extraction failed"}]}) + "\n"
                    except Exception as e:
                        yield json.dumps({venue: [{"url": url, "error": str(e)}]}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


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
