from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import asyncio
import platform

# Playwright/Crawl4AI require ProactorEventLoop on Windows for subprocess support
# This MUST be set before the loop is created/started
if platform.system() == 'Windows':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as e:
        print(f"Error setting loop policy: {e}")

# Add the parent directory to the path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
try:
    from src.scraper import process_event
    from src.models import EventDetail
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback if imports fail during initialization
    pass

app = FastAPI(title="Party Scraper API")

# Enable CORS for frontend development
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


@app.post("/scrape")
async def scrape_url(request: ScrapeRequest):
    async with AsyncWebCrawler(verbose=True) as crawler:
        try:
            detail = await process_event(crawler, request.url, request.date)
            if not detail:
                raise HTTPException(
                    status_code=404, detail="Failed to extract event data")
            return detail
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-html")
async def fetch_html(request: ScrapeRequest):
    async with AsyncWebCrawler(verbose=True) as crawler:
        try:
            # Bypass cache to get fresh HTML using the correct config pattern
            config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            result = await crawler.arun(url=request.url, config=config)
            return {"html": result.html}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
