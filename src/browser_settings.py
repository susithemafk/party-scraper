from playwright.async_api import BrowserContext, async_playwright
from typing import Optional

default_args = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--font-render-hinting=none",
    "--disable-web-security",
    "--lang=en-US",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
]

default_viewport = {'width': 1280, 'height': 720}

default_locale = "en-US"
default_timezone = "Europe/Prague"

default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

async def launch_browser_context(user_data_dir: Optional[str] = None, headless: bool = True) -> BrowserContext:
    """Launch a Playwright browser context with standardized settings."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            args=default_args,
            viewport=default_viewport,
            locale=default_locale,
            timezone_id=default_timezone,
            user_agent=default_user_agent,
        )
        return context