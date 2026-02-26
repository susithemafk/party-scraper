"""Discord-based image review using native polls.

Exposes ``run_review(images_dir, temp_dir)`` which launches a Discord bot,
posts the generated images, creates a native Discord poll for approval,
waits for the reviewer to finish, and **returns** the list of approved
image paths so the caller can act on the results.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

import discord
from dotenv import load_dotenv

# ── constants ─────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_POLL_ANSWERS = 10  # Discord hard limit


# ── config ────────────────────────────────────────────────────────────────────


def _load_config() -> dict:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    channel_str = os.getenv("REVIEW_CHANNEL_ID") or os.getenv("TARGET_CHANNEL_ID")
    reviewer_str = os.getenv("REVIEWER_USER_ID")
    timeout = int(os.getenv("REVIEW_TIMEOUT", "600"))

    if not token:
        raise SystemExit("DISCORD_TOKEN is missing from the .env file.")
    if not channel_str:
        raise SystemExit(
            "REVIEW_CHANNEL_ID or TARGET_CHANNEL_ID is required in .env."
        )

    return {
        "token": token,
        "channel_id": int(channel_str),
        "reviewer_id": int(reviewer_str) if reviewer_str else None,
        "timeout": max(timeout, 10),
    }


# ── helpers ───────────────────────────────────────────────────────────────────


def _collect_images(images_dir: Path) -> list[Path]:
    """Return all generated image files sorted alphabetically.

    Excludes ``title-post.*`` because the title image is generated *after*
    the poll based on which venues were approved.
    """
    if not images_dir.exists():
        return []
    return sorted(
        p
        for p in images_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
        and not p.stem.startswith("title-post")
    )


def _relative(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def _short_label(text: str, limit: int = 55) -> str:
    """Truncate to fit Discord's poll-answer character limit."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _persist(
    approved: list[str],
    timed_out: bool,
    config: dict,
    temp_dir: Path,
    started_at: datetime,
    finished_at: datetime,
) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    out = temp_dir / "image-review.json"
    record = {
        "approved_images": approved,
        "started_at": started_at.isoformat() + "Z",
        "finished_at": finished_at.isoformat() + "Z",
        "channel_id": config["channel_id"],
        "reviewer_id": config["reviewer_id"],
        "timed_out": timed_out,
    }
    out.write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


# ── core poll logic ───────────────────────────────────────────────────────────


async def _run_poll(
    client: discord.Client,
    config: dict,
    images_dir: Path,
    temp_dir: Path,
) -> list[str]:
    """Post images, create a native Discord poll, wait, return approved paths."""

    channel = client.get_channel(config["channel_id"])
    if channel is None:
        channel = await client.fetch_channel(config["channel_id"])
    if not isinstance(channel, discord.TextChannel):
        print(f"[Review] Channel {config['channel_id']} is not a text channel.")
        return []

    images = _collect_images(images_dir)
    if not images:
        print(f"[Review] No images found under {images_dir}.")
        return []

    total = len(images)
    start_time = datetime.utcnow()

    # 1. Post each image so the reviewer can see them ─────────────────────────
    for idx, path in enumerate(images, 1):
        rel = _relative(path, images_dir)
        await channel.send(
            f"**Image {idx}/{total}** — {rel}",
            file=discord.File(str(path), filename=path.name),
        )

    # 2. Build and send the native Discord poll ───────────────────────────────
    #    Poll duration must be ≥ 1 hour; we end it early via poll.end().
    poll = discord.Poll(
        question="Select images to approve",
        duration=timedelta(hours=1),
        multiple=True,
    )
    for idx, path in enumerate(images, 1):
        rel = _relative(path, images_dir)
        poll.add_answer(text=_short_label(f"{idx}. {rel}"))

    poll_msg = await channel.send(
        "**Image Approval Poll**\n"
        f"Vote for the images you want to keep.\n"
        f"React ✅ on the message below to finish early, "
        f"otherwise the poll will be collected in **{config['timeout']}s**.",
        poll=poll,
    )

    # 3. Separate control message for early-close ─────────────────────────────
    control_msg = await channel.send("React ✅ here to close the poll early.")
    await control_msg.add_reaction("✅")

    # 4. Wait for either the timeout or a ✅ on the control message ───────────
    timed_out = False
    try:
        await client.wait_for(
            "reaction_add",
            timeout=config["timeout"],
            check=lambda r, u: (
                r.message.id == control_msg.id
                and str(r.emoji)
                in {"✅", ":white_check_mark:", "white_check_mark"}
                and u.id != client.user.id
                and (
                    not config["reviewer_id"]
                    or u.id == config["reviewer_id"]
                )
            ),
        )
    except asyncio.TimeoutError:
        timed_out = True

    # 5. End the poll and read results ────────────────────────────────────────
    try:
        poll_msg = await channel.fetch_message(poll_msg.id)
        ended_poll = await poll_msg.poll.end()
    except Exception:
        # poll may have already ended naturally
        poll_msg = await channel.fetch_message(poll_msg.id)
        ended_poll = poll_msg.poll

    approved: list[str] = []
    for i, answer in enumerate(ended_poll.answers):
        if answer.vote_count and answer.vote_count > 0 and i < len(images):
            approved.append(_relative(images[i], images_dir))

    finish_time = datetime.utcnow()

    # 6. Persist & announce ───────────────────────────────────────────────────
    record_path = _persist(
        approved, timed_out, config, temp_dir, start_time, finish_time
    )
    summary = (
        f"Approved {len(approved)}/{total} images."
        if approved
        else "No images were approved."
    )
    await channel.send(
        f"**Poll complete** — {summary}\n"
        f"Record saved to `{record_path}`."
    )

    return approved


# ── public entry point ────────────────────────────────────────────────────────


async def run_review(images_dir: Path, temp_dir: Path) -> list[str]:
    """Launch the Discord bot, run the approval poll, return approved paths.

    This is a coroutine so it can be awaited from an already-running event
    loop (e.g. ``ensure_main_flow``).  It uses ``client.start()`` /
    ``client.close()`` instead of ``client.run()`` to avoid nesting
    ``asyncio.run()``.

    Each returned path is relative to *images_dir*
    (e.g. ``"Bobyhall/event-slug.png"``).
    """
    config = _load_config()
    result: list[str] = []
    ready_event = asyncio.Event()

    intents = discord.Intents(
        guilds=True,
        messages=True,
        reactions=True,
        message_content=True,
    )
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        nonlocal result
        try:
            result = await _run_poll(client, config, images_dir, temp_dir)
        finally:
            await client.close()
            ready_event.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        raise SystemExit(
            "Discord rejected the token. Check DISCORD_TOKEN in .env."
        )

    # wait until on_ready has finished and the client has closed
    await ready_event.wait()
    return result
