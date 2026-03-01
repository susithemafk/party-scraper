import asyncio
import os
import re
import random
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional

# Load environment variables from .env in the project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

headless = True


async def human_delay(min_ms=500, max_ms=1500):
    """Wait for a random amount of time to simulate human behavior."""
    delay = random.uniform(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def human_type(page: Page, selector: str, text: str):
    """Type text like a human with random delays between keys."""
    await page.wait_for_selector(selector)
    await page.focus(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(50, 200))
        if random.random() < 0.1:  # 10% chance of a longer pause
            await human_delay(300, 700)


async def human_click(page: Page, selector_or_locator):
    """Move mouse to element and click with a slight offset."""
    if isinstance(selector_or_locator, str):
        locator = page.locator(selector_or_locator)
    else:
        locator = selector_or_locator

    await locator.wait_for(state="visible")
    box = await locator.bounding_box()
    if box:
        # Calculate random point within the button
        x = box['x'] + box['width'] * random.uniform(0.2, 0.8)
        y = box['y'] + box['height'] * random.uniform(0.2, 0.8)

        # Move mouse realistically
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await human_delay(100, 300)
        await page.mouse.click(x, y)
    else:
        await locator.click()


async def run_instagram_workflow(image_paths: Optional[List[str]] = None, caption: Optional[str] = None, location: Optional[str] = None):
    # Prefer config-driven credentials; fall back to raw env vars
    try:
        from .config import get_config
        cfg = get_config()
        INSTAGRAM_EMAIL = cfg.instagram.email or os.getenv("INSTAGRAM_EMAIL", "your_username")
        INSTAGRAM_PASSWORD = cfg.instagram.password or os.getenv("INSTAGRAM_PASSWORD", "your_password")
        user_data_dir = cfg.instagram.session_dir
    except Exception:
        INSTAGRAM_EMAIL = os.getenv("INSTAGRAM_EMAIL", "your_username")
        INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "your_password")
        user_data_dir = "./ig_session"

    # Ensure the session directory exists
    os.makedirs(user_data_dir, exist_ok=True)

    async with async_playwright() as p:
        context = None
        page = None
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                # Tady jsou klíčové parametry pro stabilitu na Linuxu
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",     # Využije /tmp místo sdílené paměti
                    # Vypne GPU akceleraci (nutné na VPS)
                    "--disable-gpu",
                    "--font-render-hinting=none",  # Fix pro renderování textu
                    "--disable-web-security",
                    "--lang=en-US",
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale="en-US",
                timezone_id="Europe/Prague"
            )

            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            print("Navigating to Instagram...")
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await human_delay(3000, 5000)

            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await human_delay(3000, 5000)
            # Zkontrolujeme, zda vidíme tlačítko pro nový post nebo vyhledávání
            is_logged_in = await page.get_by_label("New post").is_visible() or await page.get_by_label("Home").is_visible() or await page.get_by_text("For you").is_visible()

            if not is_logged_in:
                print("Not logged in. Proceeding to login page...")
                await page.goto("https://www.instagram.com/accounts/login/")
                await human_delay(2000, 4000)

                # Step 1: Cookies
                print("Step 1: Handling cookies...")
                try:
                    cookie_button = page.get_by_role("button", name=re.compile(
                        r"Allow all cookies|Povolit všechny soubory cookie|Accept All", re.IGNORECASE))
                    if await cookie_button.is_visible():
                        await human_click(page, cookie_button)
                        print("Cookies accepted.")
                        await human_delay(1000, 2000)
                except Exception:
                    print("Cookie banner not found or already accepted.")

                # step 2: find form with id "login_form"
                print("Step 2: Finding login form...")
                await page.wait_for_selector("#login_form", state="visible", timeout=10000)
                await human_delay(500, 1500)

                # step 3: find inputs and fill
                print("Step 3: Filling credentials...")
                await human_type(page, 'input[name="username"], input[name="email"]', INSTAGRAM_EMAIL)
                await human_delay(400, 900)
                await human_type(page, 'input[name="pass"][type="password"]', INSTAGRAM_PASSWORD)
                await human_delay(800, 1500)

                # step 4: click log in
                print("Step 4: Clicking Log in...")
                login_button = page.get_by_text("Log in", exact=True)
                await human_click(page, login_button)

            else:
                print("Already logged in via persistent session. Skipping login steps.")

            # step 4.5: handle "Continue" roadblock if it appears
            try:
                # Wait a few seconds for potential redirects or popups
                await human_delay(2000, 4000)
                continue_button = page.get_by_text("Continue", exact=True)

                if await continue_button.is_visible():
                    print(
                        "Step 4.5.1: 'Continue' button detected. Clicking it...")
                    await human_click(page, continue_button)
                    await human_delay(2000, 3000)

                    # step 4.5.2: find password input and fill it
                    print("Step 4.5.2: Re-filling password...")
                    await human_type(page, 'input[name="pass"][type="password"]', INSTAGRAM_PASSWORD)
                    await human_delay(1000, 2000)

                    # step 4.5.3: click "Log in" again
                    print("Step 4.5.3: Clicking Log in again...")
                    # Try to find the button again as it might have changed
                    re_login_button = page.get_by_role(
                        "button", name=re.compile(r"Log [iI]n", re.IGNORECASE))
                    if not await re_login_button.is_visible():
                        re_login_button = page.get_by_text(
                            "Log in", exact=True)

                    await human_click(page, re_login_button)
                    print("Log in attempt after Continue done.")
                    await human_delay(3000, 5000)
            except Exception as e:
                print(f"Info: No 'Continue' check needed or failed: {e}")

            # step 5: click "Not now" for notifications if it appears
            print("Step 5: Handling post-login prompts...")
            try:
                not_now_button = page.get_by_text("Not now", exact=True)
                if await not_now_button.is_visible():
                    await human_click(page, not_now_button)
                    print("Post-login prompt handled.")
            except Exception:
                print("Post-login prompt not found or already handled.")

            # step 6: click "New post"
            print("Step 6: Clicking 'New post' button...")
            try:
                # Instagram's "New post" button is an SVG with aria-label="New post"
                new_post_button = page.get_by_label("New post", exact=True)
                await new_post_button.wait_for(state="visible", timeout=15000)
                await human_click(page, new_post_button)
                print("Clicked 'New post'.")
            except Exception as e:
                print(f"Could not find 'New post' button: {e}")

            # step 7 & 8: upload file using FileChooser
            print("Step 7 & 8: Uploading images...")
            try:
                if not image_paths:
                    # Fallback to local images if none provided
                    img_dir = Path(__file__).parent.parent / \
                        "instagram_images"
                    extensions = ["*.jpg", "*.jpeg", "*.png",
                                  "*.avif", "*.heic", "*.heif"]
                    images = []
                    for ext in extensions:
                        images.extend(img_dir.glob(ext))
                    if images:
                        image_paths = [str(images[0].absolute())]

                if not image_paths:
                    print(f"ERROR: No images provided for upload.")
                else:
                    print(f"Files to upload: {image_paths}")

                    # Start waiting for the file chooser before clicking the select button
                    async with page.expect_file_chooser() as fc_info:
                        # Click the "Select from computer" button that appears in the dialog
                        await page.get_by_role("button", name=re.compile(r"Select from computer|Vybrat z počítače", re.IGNORECASE)).click()

                    file_chooser = await fc_info.value
                    await file_chooser.set_files(image_paths)
                    print("File successfully uploaded.")
                    await human_delay(3000, 5000)
            except Exception as e:
                print(f"Upload failed: {e}")

            # step 9 & 10: Navigate through editing screens
            print("Step 9 & 10: Clicking through 'Next' buttons...")
            try:
                # First Next (Image adjustments)
                next_button = page.get_by_role(
                    "button", name=re.compile(r"Next|Další", re.IGNORECASE))
                await human_click(page, next_button)
                await human_delay(1500, 2500)

                # Second Next (Filters)
                await human_click(page, next_button)
                await human_delay(2000, 4000)
            except Exception as e:
                print(f"Could not navigate through 'Next' steps: {e}")

            # step 11 & 12: Add caption
            print("Step 11 & 12: Adding caption...")
            try:
                final_caption = caption or "Testing automated post from Brno! \ud83c\udde8\ud83c\uddff #brno #party"
                # The caption box is a div with role="textbox"
                caption_box = page.get_by_role("textbox", name=re.compile(
                    r"Write a caption|Napište popisek", re.IGNORECASE))
                if not await caption_box.is_visible():
                    caption_box = page.locator('div[role="textbox"]')

                await human_click(page, caption_box)
                await human_type(page, 'div[role="textbox"]', final_caption)
                await human_delay(1000, 2000)
            except Exception as e:
                print(f"Error adding caption: {e}")

            # step 13: Add location
            if location:
                print(f"Step 13: Adding location: {location}...")
                try:
                    location_input = page.get_by_placeholder(re.compile(
                        r"Add location|Přidat lokalitu", re.IGNORECASE))
                    await human_click(page, location_input)
                    await human_type(page, 'input[placeholder="Add location"], input[placeholder="Přidat lokalitu"]', location)
                    print("Location selected.")
                    await human_delay(1000, 2000)
                except Exception as e:
                    print(f"Could not add location: {e}")

            # step 14: Final Share
            print("Step 14: Clicking 'Share' button...")
            try:
                share_button = page.get_by_role(
                    "button", name=re.compile(r"Share|Sdílet", re.IGNORECASE))
                await human_click(page, share_button)
                print("Post shared successfully!")
                await human_delay(5000, 8000)
            except Exception as e:
                print(f"Could not find Share button: {e}")

            print("Workflow completed.")
            await human_delay(30000, 35000)
        except Exception as exc:
            # Save a debug screenshot before re-raising
            screenshot_path = Path(
                __file__).parent.parent / "temp" / "debug-screenshot.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if page is not None:
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    print(
                        f"[Instagram] Debug screenshot saved to {screenshot_path}")
            except Exception:
                print("[Instagram] Could not save debug screenshot.")
            raise exc
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception as close_exc:
                    print(f"[Instagram] Failed to close browser context cleanly: {close_exc}")


if __name__ == "__main__":
    # Ensure policy for Windows if needed (as seen in backend/main.py)
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(run_instagram_workflow())
