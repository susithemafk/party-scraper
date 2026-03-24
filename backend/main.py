from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os
import asyncio
import platform
import logging
import json
import httpx
import base64
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import random

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STUDIO_DATA_DIR = PROJECT_ROOT / "studio_data"
STUDIO_DATA_DIR.mkdir(exist_ok=True)
STUDIO_IMAGES_DIR = STUDIO_DATA_DIR / "generated_images"
STUDIO_IMAGES_DIR.mkdir(exist_ok=True)
STUDIO_DATA_EXPORT_DIR = PROJECT_ROOT / "studio_data_export"
STUDIO_DATA_EXPORT_DIR.mkdir(exist_ok=True)

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


class StudioSaveRequest(BaseModel):
    data: Dict[str, List[dict]]


class StudioGeneratedImageRequest(BaseModel):
    image_base64: str
    filename_hint: Optional[str] = None


class StudioExportImageItem(BaseModel):
    date: str
    order: int
    image_path: str


class StudioExportImagesRequest(BaseModel):
    items: List[StudioExportImageItem]

@app.get("/")
async def root():
    return {"message": "Party Scraper API is running."}


def _latest_studio_file() -> Optional[Path]:
    files = sorted(STUDIO_DATA_DIR.glob("final-events-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    return files[0]


@app.get("/studio/latest")
async def studio_latest():
    latest = _latest_studio_file()
    if not latest:
        raise HTTPException(status_code=404, detail="No saved studio JSON found")

    try:
        with latest.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "filename": latest.name,
            "updated_at": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load studio JSON: {str(e)}")


@app.post("/studio/save")
async def studio_save(request: StudioSaveRequest):
    timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
    target = STUDIO_DATA_DIR / f"final-events-{timestamp}.json"

    try:
        with target.open("w", encoding="utf-8") as f:
            json.dump(request.data, f, ensure_ascii=False, indent=2)
        return {"saved": True, "filename": target.name, "path": str(target)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save studio JSON: {str(e)}")


@app.get("/studio/local-image")
async def studio_local_image(path: str):
    if not path:
        raise HTTPException(status_code=400, detail="Image path is required")

    requested = Path(path)
    candidate = requested if requested.is_absolute() else (PROJECT_ROOT / requested)

    try:
        resolved = candidate.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image path")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}
    if resolved.suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    try:
        return FileResponse(str(resolved))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read image: {str(e)}")


@app.post("/studio/save-generated-image")
async def studio_save_generated_image(request: StudioGeneratedImageRequest):
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")

    try:
        payload = request.image_base64
        if "," in payload:
            payload = payload.split(",", 1)[1]

        image_bytes = base64.b64decode(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image payload")

    safe_hint = (request.filename_hint or "event").strip().replace(" ", "-")
    safe_hint = "".join(ch for ch in safe_hint if ch.isalnum() or ch in ("-", "_"))[:40] or "event"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    filename = f"{safe_hint}-{timestamp}.jpg"
    target = STUDIO_IMAGES_DIR / filename

    try:
        with target.open("wb") as f:
            f.write(image_bytes)

        relative_path = str(target.relative_to(PROJECT_ROOT)).replace("\\", "/")
        return {
            "saved": True,
            "filename": filename,
            "path": relative_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save generated image: {str(e)}")


def _resolve_export_source_path(image_path: str) -> Path:
    if not image_path:
        raise HTTPException(status_code=400, detail="image_path is required")

    trimmed = image_path.strip()
    if trimmed.startswith("data:") or trimmed.startswith("http://") or trimmed.startswith("https://"):
        raise HTTPException(status_code=400, detail="Only local image paths are supported for export")

    requested = Path(trimmed)
    candidate = requested if requested.is_absolute() else (PROJECT_ROOT / requested)

    try:
        resolved = candidate.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid local image path")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"Image file not found: {trimmed}")

    return resolved


@app.post("/studio/export-images")
async def studio_export_images(request: StudioExportImagesRequest):
    if not request.items:
        raise HTTPException(status_code=400, detail="No export items provided")

    saved_files: List[str] = []

    for item in request.items:
        date_folder = (item.date or "unknown-day").strip()
        safe_date_folder = "".join(ch for ch in date_folder if ch.isalnum() or ch in ("-", "_")) or "unknown-day"
        order_number = item.order if item.order > 0 else 1

        day_dir = STUDIO_DATA_EXPORT_DIR / safe_date_folder
        day_dir.mkdir(parents=True, exist_ok=True)

        target_file = day_dir / f"{order_number}.jpg"
        source_file = _resolve_export_source_path(item.image_path)

        try:
            shutil.copy2(source_file, target_file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save JPG for {item.date}/{order_number}: {str(e)}")

        saved_files.append(str(target_file.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    return {
        "saved": True,
        "saved_count": len(saved_files),
        "folder": str(STUDIO_DATA_EXPORT_DIR.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "files": saved_files,
    }

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
                            res["url"] = url
                            res["date"] = date
                            # Wrap in venue key for grouped format
                            yield json.dumps({venue: [res]}) + "\n"
                        else:
                            yield json.dumps({venue: [{"url": url, "error": "Extraction failed"}]}) + "\n"
                    except Exception as e:
                        yield json.dumps({venue: [{"url": url, "error": str(e)}]}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.get("/proxy-image")
async def proxy_image(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={"Access-Control-Allow-Origin": "*"}
            )
    except Exception as e:
        print(f"[Proxy] Error fetching image at {url}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching image")


@app.post("/fetch-html")
async def fetch_html(request: dict):
    url = request.get("url")
    base_url = request.get("base_url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    print(f"[Fetcher] Requesting HTML with Recommended Stealth for: {url}")

    try:
        # 1. Použití doporučeného Stealth wrapperu podle dokumentace
        async with Stealth().use_async(async_playwright()) as p:
            # Spustíme prohlížeč
            browser = await p.chromium.launch(
                headless=True, # Pokud tě stále blokují, zkus False
                args=["--no-sandbox"]
            )

            # 2. Vytvoření kontextu s reálnými parametry
            # Je důležité, aby User-Agent odpovídal tomu, co Stealth emuluje
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="cs-CZ"
            )

            page = await context.new_page()

            # 3. Předstíráme lidské chování - návštěva hlavní stránky (Referer)
            # DataDome často blokuje přímé skoky na hluboké URL
            try:
                print(f"[Fetcher] Visiting home page first: {base_url}")
                await page.goto(base_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(random.uniform(1, 2))
            except:
                pass # Ignorujeme chyby na home page

            # 4. Samotný skok na cílovou URL
            print(f"[Fetcher] Navigating to target: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            # Kontrola statusu (DataDome vrací 403 při detekci)
            if response.status == 403:
                print("[Fetcher] ALERT: DataDome 403 Forbidden detected!")
                # Tady můžeš zkusit malý scroll, aby se aktivovaly eventy
                await page.mouse.wheel(0, 500)
                raise HTTPException(status_code=403, detail="Blocked by DataDome")

            await page.mouse.wheel(0, 511)

            # Extra pauza pro doběhnutí JavaScriptu
            await asyncio.sleep(2)

            html = await page.content()
            await browser.close()

            print(f"[Fetcher] Success: {len(html)} chars retrieved.")
            return {"html": html}

    except Exception as e:
        print(f"[Fetcher] Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # --- 4. POZOR NA RELOAD NA WINDOWS ---
    # reload=True na Windows často rozbíjí Event Loop Policy pro Playwright.
    # Pro ladění scrapingu doporučuji reload=False.
    # Spouštíme přímo app objekt, aby se vždy načetla tato instance se všemi /studio routami.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
