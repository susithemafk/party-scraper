"""
Instagram session generator.

Launches a persistent browser context, logs in (if needed), waits for the
session to be saved to disk, and exits.  No posting is performed.
"""
import asyncio
import os
import re
import random

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from typing import Optional

from .browser_utils import human_click, human_delay, human_type


headless = False


async def generate_ig_session(session_dir: str, email: str, password: str):
    """Log in to Instagram and persist the session to *session_dir*."""
    os.makedirs(session_dir, exist_ok=True)
    print(f"[IG Session] Session directory: {session_dir}")

    async with async_playwright() as p:
        context = None
        page = None
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=session_dir,
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--font-render-hinting=none",
                    "--disable-web-security",
                    "--lang=en-US",
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale="en-US",
                timezone_id="Europe/Prague",
            )

            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            print("[IG Session] Navigating to Instagram...")
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await human_delay(3000, 5000)

            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await human_delay(3000, 5000)

            is_logged_in = (
                await page.get_by_label("New post").is_visible()
                or await page.get_by_label("Home").is_visible()
                or await page.get_by_text("For you").is_visible()
            )

            if not is_logged_in:
                print("[IG Session] Not logged in. Proceeding to login page...")
                await page.goto("https://www.instagram.com/accounts/login/")
                await human_delay(2000, 4000)

                # Step 1: Cookies
                print("[IG Session] Step 1: Handling cookies...")
                try:
                    cookie_button = page.get_by_role("button", name=re.compile(
                        r"Allow all cookies|Povolit všechny soubory cookie|Accept All", re.IGNORECASE))
                    if await cookie_button.is_visible():
                        await human_click(page, cookie_button)
                        print("[IG Session] Cookies accepted.")
                        await human_delay(1000, 2000)
                except Exception:
                    print("[IG Session] Cookie banner not found or already accepted.")

                # Step 2: Find login form
                print("[IG Session] Step 2: Finding login form...")
                await page.wait_for_selector("#login_form", state="visible", timeout=10000)
                await human_delay(500, 1500)

                # Step 3: Fill credentials
                print("[IG Session] Step 3: Filling credentials...")
                await human_type(page, 'input[name="username"], input[name="email"]', email)
                await human_delay(400, 900)
                await human_type(page, 'input[name="pass"][type="password"]', password)
                await human_delay(800, 1500)

                # Step 4: Click Log in
                print("[IG Session] Step 4: Clicking Log in...")
                login_button = page.get_by_text("Log in", exact=True)
                await human_click(page, login_button)
            else:
                print("[IG Session] Already logged in via persistent session.")

            # Step 4.5: Handle "Continue" roadblock
            try:
                await human_delay(2000, 4000)
                continue_button = page.get_by_text("Continue", exact=True)
                if await continue_button.is_visible():
                    print("[IG Session] Step 4.5.1: 'Continue' button detected. Clicking...")
                    await human_click(page, continue_button)
                    await human_delay(2000, 3000)

                    print("[IG Session] Step 4.5.2: Re-filling password...")
                    await human_type(page, 'input[name="pass"][type="password"]', password)
                    await human_delay(1000, 2000)

                    print("[IG Session] Step 4.5.3: Clicking Log in again...")
                    re_login_button = page.get_by_role(
                        "button", name=re.compile(r"Log [iI]n", re.IGNORECASE))
                    if not await re_login_button.is_visible():
                        re_login_button = page.get_by_text("Log in", exact=True)
                    await human_click(page, re_login_button)
                    await human_delay(3000, 5000)
            except Exception as e:
                print(f"[IG Session] Info: No 'Continue' check needed or failed: {e}")

            # Step 5: Dismiss "Not now" prompt
            print("[IG Session] Step 5: Handling post-login prompts...")
            try:
                not_now_button = page.get_by_text("Not now", exact=True)
                if await not_now_button.is_visible():
                    await human_click(page, not_now_button)
                    print("[IG Session] Post-login prompt handled.")
            except Exception:
                print("[IG Session] Post-login prompt not found or already handled.")

            # Give the browser a moment to flush session data to disk
            await human_delay(2000, 4000)

            # Verify we are logged in
            final_check = (
                await page.get_by_label("New post").is_visible()
                or await page.get_by_label("Home").is_visible()
                or await page.get_by_text("For you").is_visible()
            )
            if final_check:
                print(f"[IG Session] SUCCESS — session saved to: {session_dir}")
            else:
                print("[IG Session] WARNING — login may have failed. Check the session directory.")
                if page is not None:
                    await page.screenshot(path="login_failed.png")
                    print("[IG Session] Screenshot saved to login_failed.png")

        finally:
            if context is not None:
                await context.close()
                print("[IG Session] Browser closed.")
