"""
HTML Fetcher - Uses Playwright with stealth to fetch HTML from venue websites.
Replicates the /fetch-html endpoint logic from the backend.
"""
import asyncio
import random
import platform
from typing import Optional
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def fetch_html(url: str, base_url: str = "") -> Optional[str]:
    """
    Fetch the HTML content of a URL using Playwright with stealth mode.

    Args:
        url: The target URL to fetch.
        base_url: The base URL of the website (visited first to appear natural).

    Returns:
        The HTML content as a string, or None on failure.
    """
    print(f"[Fetcher] Requesting HTML with Stealth for: {url}")
    try:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="cs-CZ"
            )
            page = await context.new_page()

            # Visit base URL first to appear natural
            if base_url:
                try:
                    print(f"[Fetcher] Visiting home page first: {base_url}")
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(random.uniform(1, 2))
                except Exception:
                    pass

            # Navigate to target
            print(f"[Fetcher] Navigating to target: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            if response and response.status == 403:
                print("[Fetcher] ALERT: 403 Forbidden detected!")
                await page.mouse.wheel(0, 500)
                await browser.close()
                return None

            # Scroll and wait for dynamic content
            await page.mouse.wheel(0, 511)
            await asyncio.sleep(2)

            html = await page.content()
            await browser.close()
            print(f"[Fetcher] Success: {len(html)} chars retrieved.")
            return html

    except Exception as e:
        print(f"[Fetcher] Critical Error: {str(e)}")
        return None


async def fetch_all_venues(venues: list) -> dict:
    """
    Fetch HTML for all venues sequentially.

    Args:
        venues: List of venue dicts with 'title', 'url', 'baseUrl', 'parser' keys.

    Returns:
        Dict mapping venue title to fetched HTML string.
    """
    results = {}
    for venue in venues:
        title = venue["title"]
        url = venue["url"]
        base_url = venue.get("baseUrl", "")

        print(f"\n{'='*40}")
        print(f"  Fetching: {title}")
        print(f"{'='*40}")

        html = await fetch_html(url, base_url)
        if html:
            results[title] = html
            print(f"[Fetcher] {title}: Got {len(html)} chars")
        else:
            print(f"[Fetcher] {title}: FAILED to fetch HTML")
            results[title] = None

    return results
