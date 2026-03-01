"""Pipeline helpers and entry-point stages for the party scraper."""
from __future__ import annotations

import asyncio
import json
import random
import shutil
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .ai_scraper import process_all_events
from .config import get_config
from .event_parser import (
    get_venues,
    filter_today_only,
    parse_all_venues,
    save_fetched_events,
)
from .fetcher import fetch_all_venues
from .image_generator import generate_event_images
from .setup import run_setup

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _city_name() -> str:
    """Return the active city slug for directory isolation."""
    try:
        return get_config().name
    except RuntimeError:
        return "default"


# ── city-scoped paths ─────────────────────────────────────────────────────
# Each city gets its own subdirectory under temp/ and generated/ so that
# running two cities in parallel never conflicts.


def _get_temp_dir() -> Path:
    return PROJECT_ROOT / "temp" / _city_name()


def _get_fetched_events_path() -> Path:
    return _get_temp_dir() / "fetched-events.json"


def _get_processed_events_path() -> Path:
    return _get_temp_dir() / "processed-events.json"


def _get_generated_images_dir() -> Path:
    return PROJECT_ROOT / "generated" / _city_name() / "images"


def _get_post_dir() -> Path:
    return _get_temp_dir() / "post"


# Backwards-compatible module-level aliases (read lazily)
class _LazyPath:
    """Descriptor that calls a factory each time it's accessed."""
    def __init__(self, factory):
        self._factory = factory
    def __repr__(self):
        return str(self._factory())
    def __fspath__(self):
        return str(self._factory())
    def __str__(self):
        return str(self._factory())
    def __truediv__(self, other):
        return self._factory() / other
    @property
    def parent(self):
        return self._factory().parent
    def exists(self):
        return self._factory().exists()
    def mkdir(self, **kw):
        return self._factory().mkdir(**kw)
    def open(self, *a, **kw):
        return self._factory().open(*a, **kw)
    def iterdir(self):
        return self._factory().iterdir()
    def is_dir(self):
        return self._factory().is_dir()


TEMP_DIR = _LazyPath(_get_temp_dir)
FETCHED_EVENTS_PATH = _LazyPath(_get_fetched_events_path)
PROCESSED_EVENTS_PATH = _LazyPath(_get_processed_events_path)
GENERATED_IMAGES_DIR = _LazyPath(_get_generated_images_dir)
POST_DIR = _LazyPath(_get_post_dir)


def _ensure_temp_dir() -> None:
    _get_temp_dir().mkdir(parents=True, exist_ok=True)


def run_setup_step() -> bool:
    """Perform the prerequisite setup check."""
    return run_setup(PROJECT_ROOT)


async def fetch_and_parse_events(
    *, filter_past: bool = True, max_results: int = 4
) -> Dict[str, list[dict[str, Any]]]:
    """Fetch HTML from venues, parse the events, and save the JSON snapshot."""
    html_results = await fetch_all_venues(get_venues())
    fetched_events = parse_all_venues(
        html_results, filter_past=filter_past, max_results=max_results)

    _ensure_temp_dir()
    save_fetched_events(fetched_events, _get_fetched_events_path())
    return fetched_events


def load_fetched_events() -> Dict[str, list[dict[str, Any]]]:
    """Read the cached events produced by the fetching stage."""
    path = _get_fetched_events_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Missing fetched events file: {path}")

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_today_events(
    fetched_events: Optional[Dict[str, list[dict[str, Any]]]] = None,
    *,
    target_date: Optional[str] = None,
) -> Dict[str, list[dict[str, Any]]]:
    """Filter cached events down to *target_date* (defaults to tomorrow)."""
    if fetched_events is None:
        fetched_events = load_fetched_events()
    return filter_today_only(fetched_events, target_date=target_date)


async def process_today_events(
    today_events: Optional[Dict[str, list[dict[str, Any]]]] = None
) -> Dict[str, list[dict[str, Any]]]:
    """Run the AI extraction pass over today's events and save the results."""
    if today_events is None:
        today_events = build_today_events()

    _ensure_temp_dir()
    processed = await process_all_events(today_events, str(_get_processed_events_path()))
    return processed


def load_processed_events() -> Dict[str, list[dict[str, Any]]]:
    """Load the JSON that contains AI-processed events."""
    path = _get_processed_events_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Missing processed events file: {path}")

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def generate_images_from_processed(
    processed_events: Optional[Dict[str, list[dict[str, Any]]]] = None,
    images_dir: Optional[Path] = None,
    *,
    generate_title: bool = False,
) -> list[str]:
    """Render Instagram-style images for the processed events.

    ``generate_title`` controls whether a title-post image should be produced
    along with the individual event images.  In typical pipeline runs the
    Discord review script will regenerate the title after polling, so we
    default this parameter to ``False`` and only set it to ``True`` when the
    caller explicitly needs the title ahead of time (e.g. during testing or
    manual image generation).
    """
    if processed_events is None:
        processed_events = load_processed_events()

    if images_dir is None:
        images_dir = _get_generated_images_dir()

    images_dir.mkdir(parents=True, exist_ok=True)
    return generate_event_images(processed_events, str(images_dir), generate_title=generate_title)


def generate_title_from_venues(
    venues: Iterable[str], images_dir: Optional[Path] = None
) -> Optional[str]:
    """Create or overwrite a title-post.png containing only the given venues.

    Called by the Discord review script after the approval poll completes.
    Picks a random background from existing PNGs in the approved venue folders.
    Returns the path to the title image or ``None`` on failure.
    """
    from .image_generator import build_title_html, render_html_with_playwright

    if images_dir is None:
        images_dir = _get_generated_images_dir()

    images_dir.mkdir(parents=True, exist_ok=True)
    html_dir = images_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    venues_list = list(venues)
    venues_str = " | ".join(venues_list)

    tomorrow = datetime.now() + timedelta(days=1)
    date_display = f"{tomorrow.day:02d}. {tomorrow.month:02d}."

    # pick a random existing PNG from the approved venues as backdrop
    background_candidates: list[str] = []
    for v in venues_list:
        venue_path = images_dir / v
        if venue_path.is_dir():
            for p in venue_path.glob("*.png"):
                background_candidates.append(str(p.as_posix()))

    cfg = get_config()
    background_html = ""
    if background_candidates:
        chosen = random.choice(background_candidates)
        background_html = (
            f'<img src="{chosen}" class="background-image" alt="{cfg.title_alt}" />'
        )

    title_html = build_title_html(venues_str, date_display, background_html,
                                  title_text=cfg.title_text)
    title_path = images_dir / "title-post.png"
    title_html_path = html_dir / "title-post.html"

    try:
        success, error = render_html_with_playwright(
            title_html, title_html_path, title_path)
        if success:
            print(f"[Pipeline] Generated title image: {title_path}")
            return str(title_path)
        else:
            print(f"[Pipeline] ERROR generating title image: {error}")
            return None
    except Exception as exc:
        print(f"[Pipeline] ERROR generating title image: {exc}")
        return None


def _finalize_post(approved_images: list[str]) -> None:
    """Copy approved images + title to temp/post and clean up generated/.

    - Moves ``generated/images/html/`` to ``temp/html/`` for archival.
    - Copies each approved image into ``temp/post/``.
    - Copies ``title-post.png`` into ``temp/post/`` (placed first).
    - Removes the entire ``generated/`` directory.
    """
    post_dir = _get_post_dir()
    images_dir = _get_generated_images_dir()

    # clean previous post dir
    if post_dir.exists():
        shutil.rmtree(post_dir)
    post_dir.mkdir(parents=True, exist_ok=True)

    # remove generated html (not needed in output)
    src_html = images_dir / "html"
    if src_html.exists():
        shutil.rmtree(src_html)
        print("[Pipeline] Deleted generated HTML")

    # copy title-post first
    title_src = images_dir / "title-post.png"
    if title_src.exists():
        shutil.copy2(str(title_src), str(post_dir / "title-post.png"))
        print(f"[Pipeline] Copied title-post.png to {post_dir}")

    # copy approved event images
    for rel_path in approved_images:
        src = images_dir / rel_path
        if src.exists():
            dest = post_dir / Path(rel_path).name
            shutil.copy2(str(src), str(dest))

    # remove generated/ entirely
    generated_root = images_dir.parent  # generated/<city>/
    if generated_root.exists():
        shutil.rmtree(generated_root)
        print(f"[Pipeline] Cleaned up {generated_root}")

    count = len(list(post_dir.iterdir()))
    print(f"[Pipeline] {count} file(s) ready in {post_dir}")


async def morning_flow() -> None:
    """Morning script: fetch, parse, process, generate images, send Discord poll.

    The poll stays open until the post script collects it (next day at 00:01).
    """
    # 1. Setup
    run_setup_step()

    # 2. Fetch + parse
    await fetch_and_parse_events()

    # 3. Filter tomorrow's events + AI-process
    build_today_events()
    await process_today_events()

    # 4. Clean previous generated images so only today's run is in the poll
    gen_dir = _get_generated_images_dir()
    if gen_dir.exists():
        shutil.rmtree(gen_dir)
        print("[Pipeline] Cleaned previous generated images.")

    # 5. Generate event images only (sync Playwright — run outside async loop)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, partial(generate_images_from_processed, generate_title=False)
    )

    # 5. Send Discord poll (exits immediately, poll stays open)
    from .review_images import send_poll

    print("\n[Pipeline] Sending Discord review poll...")
    await send_poll(_get_generated_images_dir(), _get_temp_dir())
    print("[Pipeline] Morning flow complete. Poll is open for voting.")


async def post_flow() -> None:
    """Post script (00:01): collect poll results, generate title, finalize, upload.

    If nobody voted on the poll, all images are approved automatically.
    """
    # 6. Collect poll results from Discord
    from .review_images import collect_poll_results

    print("\n[Pipeline] Collecting Discord poll results...")
    approved_images = await collect_poll_results(_get_generated_images_dir(), _get_temp_dir())

    if approved_images is None:
        print("[Pipeline] Upload was cancelled via Discord poll. Exiting.")
        return

    # 7. Generate title from approved venues only
    print("\n[Pipeline] Generating title image from approved venues...")
    if approved_images:
        approved_venues = {
            Path(p).parts[0] for p in approved_images if "/" in p
        }
        if approved_venues:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                partial(generate_title_from_venues, approved_venues),
            )
            print(
                f"[Pipeline] Title generated for: "
                f"{', '.join(sorted(approved_venues))}"
            )
        else:
            print("[Pipeline] No venue-specific images approved; skipping title.")
    else:
        print("[Pipeline] No images approved; skipping title generation.")

    # 8. Copy approved images + title to temp/post, clean up generated/
    print("\n[Pipeline] Finalizing post with approved images...")
    _finalize_post(approved_images)

    # 9. Post to Instagram
    from .instagram_workflow import run_instagram_workflow
    from .discord_utils import send_discord_message, send_discord_file

    post_dir = _get_post_dir()
    post_images: list[str] = []
    if post_dir.exists():
        title_post = post_dir / "title-post.png"
        if title_post.exists():
            post_images.append(str(title_post))
        for f in sorted(post_dir.iterdir()):
            if f.suffix.lower() in {".png", ".jpg", ".jpeg"} and f.name != "title-post.png":
                post_images.append(str(f))

    if post_images:
        cfg = get_config()
        today = datetime.now()
        formatted_date = f"{today.day}. {today.month}. {today.year}"
        caption = cfg.format_caption(formatted_date)

        print(f"\n[Pipeline] Uploading {len(post_images)} image(s) to Instagram...")
        await send_discord_message(
            f"⏳ **Uploading {len(post_images)} image(s) to Instagram...**"
        )

        try:
            await run_instagram_workflow(
                image_paths=post_images,
                caption=caption,
                location=cfg.instagram.location,
            )
            print("[Pipeline] Instagram upload completed.")
            await send_discord_message(
                f"✅ **Instagram upload completed!** ({len(post_images)} images)"
            )
        except Exception as exc:
            print(f"[Pipeline] Instagram upload FAILED: {exc}")
            await send_discord_message(
                f"❌ **Instagram upload failed:** {exc}"
            )
            # Send debug screenshot if one was captured
            screenshot = _get_temp_dir() / "debug-screenshot.png"
            if screenshot.exists():
                await send_discord_file(
                    screenshot, "🖥️ **Debug screenshot at time of failure:**"
                )
    else:
        print("[Pipeline] No images in post folder; skipping Instagram upload.")
        await send_discord_message(
            "⚠️ **No images in post folder** — skipping Instagram upload."
        )


async def ensure_main_flow() -> None:
    """Run the full pipeline end-to-end (legacy, kept for backwards compat)."""
    await morning_flow()
    await post_flow()
