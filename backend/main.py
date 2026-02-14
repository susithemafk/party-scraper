from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add the parent directory to the path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
try:
    from src.scraper import process_event
    from src.models import EventDetail
    from crawl4ai import AsyncWebCrawler
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback if imports fail during initialization
    pass

app = FastAPI(title="Party Scraper API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
