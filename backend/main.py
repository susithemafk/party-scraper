from fastapi import FastAPI, HTTPException, Response
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
import httpx
import base64
import uuid
from instagrapi import Client
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
    from src.instagram_workflow import run_instagram_workflow
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


class IgLoginRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    session_id: Optional[str] = None
    verification_code: Optional[str] = None


class IgPostRequest(BaseModel):
    images_base64: List[str]
    caption: str
    location_name: Optional[str] = None


SESSION_PATH = "ig_session.json"
cl = Client()


def login_to_instagram(email=None, password=None, session_id=None, verification_code=None):
    """Přihlásí se k IG pomocí emailu/hesla, session_id nebo vyřeší challenge."""
    global cl
    print(f"[IG-DEBUG] Starting login process. Session_id: {bool(session_id)}, Code: {bool(verification_code)}")

    # 1. Challenge / 2FA (ponecháno beze změny)
    if verification_code:
        try:
            cl.challenge_resolve(verification_code)
            cl.dump_settings(SESSION_PATH)
            return "success"
        except Exception as e:
            if email and password:
                try:
                    cl.login(email, password, verification_code=verification_code)
                    cl.dump_settings(SESSION_PATH)
                    return "success"
                except Exception as e2:
                    return f"Verification failed: {e2}"
            return str(e)

    # 2. Login přes Session ID
    if session_id:
        try:
            from urllib.parse import unquote
            # Očištění session_id (odstranění uvozovek a URL kódování)
            session_id = unquote(session_id).strip('"').strip("'")

            # Reset klienta pro čistý start
            cl = Client()

            # Extrakce user_id ze session_id (formát: user_id:token:...)
            extracted_user_id = session_id.split(":")[0] if ":" in session_id else None

            if not extracted_user_id:
                return "Invalid Session ID format (missing user_id part)"

            # Nastavíme cookies manuálně - toto nevyvolává síťový požadavek
            cl.set_settings({}) # Inicializace prázdného nastavení
            cl.set_device({
                "app_version": "311.0.0.32.118", # Modernější verze
                "android_version": 29,
                "android_release": "10.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "Samsung",
                "device": "SM-G973F",
                "model": "beyond1",
                "cpu": "exynos9820",
                "version_code": "544155160",
            })

            # Vložíme session přímo do cookie jaru
            cl.login_by_sessionid(session_id)

            # Okamžitý test, zda nás IG vidí jako přihlášené
            try:
                cl.get_timeline_feed()
                print(f"[IG-DEBUG] Session ID login successful! User ID: {cl.user_id}")
                cl.dump_settings(SESSION_PATH)
                return "success"
            except Exception as e:
                print(f"[IG-DEBUG] Session validation failed: {e}")
                return "Session ID is expired or invalid"

        except Exception as e:
            print(f"[IG-DEBUG] SessionID Error: {type(e).__name__}: {e}")
            if "JSONDecodeError" in str(e) or "column 1" in str(e):
                return "Instagram blocked your IP or Session. Try refreshing Session ID in your browser."
            return str(e)

    # 3. Načtení ze souboru
    if os.path.exists(SESSION_PATH):
        try:
            cl.load_settings(SESSION_PATH)
            # Malý test validity
            cl.get_timeline_feed()
            return "success"
        except:
            if os.path.exists(SESSION_PATH): os.remove(SESSION_PATH)

    # 4. Email + Heslo
    if email and password:
        try:
            cl.login(email, password)
            cl.dump_settings(SESSION_PATH)
            return "success"
        except Exception as e:
            from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
            if isinstance(e, (ChallengeRequired, TwoFactorRequired)) or "checkpoint" in str(e).lower():
                return "challenge_required"
            return str(e)

    return "Missing credentials"


@app.get("/")
async def root():
    return {"message": "Party Scraper API is running."}


@app.post("/ig-login")
async def ig_login(request: IgLoginRequest):
    print(f"\n[API] Received /ig-login request")
    result = await asyncio.to_thread(
        login_to_instagram,
        email=request.email,
        password=request.password,
        session_id=request.session_id,
        verification_code=request.verification_code
    )

    if result == "success":
        try:
            account_info = cl.account_info()
            return {"status": "success", "message": "Logged in", "user": account_info.dict()}
        except Exception:
            return {"status": "success", "message": "Logged in (no info)", "user": {"email": request.email}}

    if result == "challenge_required":
        return {"status": "challenge", "message": "Instagram requested verification code. Please check your email/phone."}

    raise HTTPException(status_code=401, detail=f"Login failed: {result}")


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
                headless=False, # Pokud tě stále blokují, zkus False
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


@app.post("/ig-publish")
async def ig_publish(request: IgPostRequest):
    print(f"\n[API] Received /ig-publish request")

    # Create temp directory for images
    temp_dir = os.path.join(os.getcwd(), "temp_instagram_images")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    image_paths = []
    try:
        # Save base64 images to temporary files
        for i, img_b64 in enumerate(request.images_base64):
            # Strip metadata if present (e.g., "data:image/jpeg;base64,")
            if "," in img_b64:
                img_b64 = img_b64.split(",")[1]

            img_data = base64.b64decode(img_b64)
            file_name = f"upload_{uuid.uuid4()}_{i}.jpg"
            file_path = os.path.join(temp_dir, file_name)

            with open(file_path, "wb") as f:
                f.write(img_data)

            image_paths.append(file_path)

        print(f"Saved {len(image_paths)} images to {temp_dir}")

        # Run the playwright workflow
        # Note: This runs in the background or blocks until finished.
        # Since it's a long process, you might want to consider a task queue,
        # but for now we'll run it directly.
        await run_instagram_workflow(
            image_paths=image_paths,
            caption=request.caption,
            location=request.location_name
        )

        return {"status": "success", "message": "Post published successfully via browser automation"}

    except Exception as e:
        import traceback
        print(f"[IG-PUBLISH ERROR]: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary files
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Cleaned up: {path}")
            except Exception as e:
                print(f"Error cleaning up {path}: {e}")


if __name__ == "__main__":
    import uvicorn
    # --- 4. POZOR NA RELOAD NA WINDOWS ---
    # reload=True na Windows často rozbíjí Event Loop Policy pro Playwright.
    # Pro ladění scrapingu doporučuji reload=False.
    # Také se ujisti, že název souboru odpovídá (zde předpokládám backend-main.py)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
