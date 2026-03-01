"""Shared browser-automation utilities for human-like interaction."""

import asyncio
import random

from playwright.async_api import Page


async def human_delay(min_ms: int = 500, max_ms: int = 1500) -> None:
    """Wait for a random amount of time to simulate human behavior."""
    delay = random.uniform(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def human_type(page: Page, selector: str, text: str) -> None:
    """Type text like a human with random delays between keys."""
    await page.wait_for_selector(selector)
    await page.focus(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(50, 200))
        if random.random() < 0.1:  # 10% chance of a longer pause
            await human_delay(300, 700)


async def human_click(page: Page, selector_or_locator) -> None:
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
