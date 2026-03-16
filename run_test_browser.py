import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from src.discord_utils import send_discord_file, send_discord_message
from src.browser_settings import launch_browser_context

async def test_browser():
    user_data_dir = "./ig_session"
    screenshot_path = Path("./temp/test-browser-screenshot.png")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await launch_browser_context(user_data_dir=user_data_dir, headless=True)

        page = await browser.new_page()
        try:
            print("Navigating to Instagram...")
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Wait for 5 seconds

            print("Taking screenshot...")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Screenshot saved to {screenshot_path}")

            print("Sending screenshot to Discord...")
            await send_discord_message("🖥️ **Test Browser Screenshot**")
            await send_discord_file(screenshot_path, "🖼️ **Screenshot from test browser session:**")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_browser())