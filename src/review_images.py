"""Discord-based image review using native polls.

Two-phase workflow
------------------
1. **Morning** – ``send_poll(images_dir, temp_dir)`` posts the generated
   images and a native Discord poll, then exits immediately.  The poll
   message ID is persisted to ``temp/poll-state.json`` so the second phase
   can find it.

2. **Post** – ``collect_poll_results(images_dir, temp_dir)`` reconnects to
   Discord, ends the poll, reads the votes, and returns the list of approved
   image paths.  If nobody voted, *all* images are treated as approved.

Legacy single-shot entry point ``run_review`` is kept for backwards compat.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import discord
from dotenv import load_dotenv

# ── constants ─────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_POLL_ANSWERS = 10  # Discord hard limit
POLL_STATE_FILE = "poll-state.json"
SKIP_UPLOAD_LABEL = "❌ Don't upload this post"


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


def _save_poll_state(
    temp_dir: Path,
    *,
    channel_id: int,
    poll_message_id: int,
    image_paths: list[str],
    sent_at: str,
) -> Path:
    """Persist poll metadata so the second script can find the poll."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    out = temp_dir / POLL_STATE_FILE
    state = {
        "channel_id": channel_id,
        "poll_message_id": poll_message_id,
        "image_paths": image_paths,
        "sent_at": sent_at,
    }
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _load_poll_state(temp_dir: Path) -> dict:
    path = temp_dir / POLL_STATE_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"No poll state found at {path}. Did you run the morning script first?"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _persist_results(
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


# ── phase 1: send poll (morning) ─────────────────────────────────────────────


async def _do_send_poll(
    client: discord.Client,
    config: dict,
    images_dir: Path,
    temp_dir: Path,
) -> None:
    """Post images + Discord poll, save state, and return immediately."""
    channel = client.get_channel(config["channel_id"])
    if channel is None:
        channel = await client.fetch_channel(config["channel_id"])
    if not isinstance(channel, discord.TextChannel):
        print(f"[Review] Channel {config['channel_id']} is not a text channel.")
        return

    images = _collect_images(images_dir)
    if not images:
        print(f"[Review] No images found under {images_dir}.")
        return

    total = len(images)

    # 1. Post each image ──────────────────────────────────────────────────────
    for idx, path in enumerate(images, 1):
        rel = _relative(path, images_dir)
        await channel.send(
            f"**Image {idx}/{total}** — {rel}",
            file=discord.File(str(path), filename=path.name),
        )

    # 2. Build and send native Discord poll ───────────────────────────────────
    poll = discord.Poll(
        question="Select images to approve",
        duration=timedelta(hours=24),
        multiple=True,
    )
    for idx, path in enumerate(images, 1):
        rel = _relative(path, images_dir)
        poll.add_answer(text=_short_label(f"{idx}. {rel}"))

    # Last option: skip the upload entirely
    poll.add_answer(text=SKIP_UPLOAD_LABEL)

    poll_msg = await channel.send(
        "**Image Approval Poll**\n"
        "Vote for the images you want to keep.\n"
        "Vote **\"" + SKIP_UPLOAD_LABEL + "\"** to cancel the post entirely.\n"
        "The poll will be collected automatically tomorrow at 00:01.\n"
        "If nobody votes, **all images** will be approved.",
        poll=poll,
    )

    # 3. Save state for the post script ───────────────────────────────────────
    rel_paths = [_relative(p, images_dir) for p in images]
    state_path = _save_poll_state(
        temp_dir,
        channel_id=config["channel_id"],
        poll_message_id=poll_msg.id,
        image_paths=rel_paths,
        sent_at=datetime.utcnow().isoformat() + "Z",
    )
    print(f"[Review] Poll sent ({total} images). State saved to {state_path}")


async def send_poll(images_dir: Path, temp_dir: Path) -> None:
    """Public entry point for the morning script."""
    config = _load_config()
    done = asyncio.Event()

    intents = discord.Intents(guilds=True, messages=True, message_content=True)
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            await _do_send_poll(client, config, images_dir, temp_dir)
        finally:
            await client.close()
            done.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Check DISCORD_TOKEN in .env.")

    await done.wait()


# ── phase 2: collect results (post script at 00:01) ─────────────────────────


async def _do_collect_results(
    client: discord.Client,
    config: dict,
    images_dir: Path,
    temp_dir: Path,
) -> list[str] | None:
    """End the poll, read votes, return approved paths or None to skip upload."""
    state = _load_poll_state(temp_dir)

    channel = client.get_channel(state["channel_id"])
    if channel is None:
        channel = await client.fetch_channel(state["channel_id"])
    if not isinstance(channel, discord.TextChannel):
        print(f"[Review] Channel {state['channel_id']} is not a text channel.")
        return []

    image_paths: list[str] = state["image_paths"]

    # Fetch the poll message and end it ────────────────────────────────────────
    poll_msg = await channel.fetch_message(state["poll_message_id"])
    try:
        ended_poll = await poll_msg.poll.end()
    except Exception:
        # poll may have already ended naturally (24h limit)
        poll_msg = await channel.fetch_message(state["poll_message_id"])
        ended_poll = poll_msg.poll

    # Read votes ──────────────────────────────────────────────────────────────
    answers_list = list(ended_poll.answers)
    # The last answer is the "Don't upload" option
    skip_answer = answers_list[-1] if answers_list else None
    skip_upload = (
        skip_answer is not None
        and skip_answer.vote_count
        and skip_answer.vote_count > 0
    )

    approved: list[str] = []
    any_votes = False
    for i, answer in enumerate(answers_list[:-1]):  # exclude skip option
        if answer.vote_count and answer.vote_count > 0:
            any_votes = True
            if i < len(image_paths):
                approved.append(image_paths[i])

    # If nobody voted at all (and didn't vote skip), approve everything
    if not any_votes and not skip_upload:
        print("[Review] No votes cast — approving all images.")
        approved = list(image_paths)

    total = len(image_paths)
    finish_time = datetime.utcnow()
    start_time = datetime.fromisoformat(state["sent_at"].rstrip("Z"))

    # Persist & announce ──────────────────────────────────────────────────────
    record_path = _persist_results(
        approved, False, config, temp_dir, start_time, finish_time
    )

    if skip_upload:
        summary = "Upload cancelled via poll."
    elif approved:
        summary = f"Approved {len(approved)}/{total} images."
    else:
        summary = "No images were approved."

    await channel.send(
        f"**Poll complete** — {summary}\n"
        f"Record saved to `{record_path}`."
    )

    # Return None to signal "don't upload at all"
    if skip_upload:
        print("[Review] Upload skipped by poll vote.")
        return None

    return approved


async def collect_poll_results(images_dir: Path, temp_dir: Path) -> list[str] | None:
    """Public entry point for the post script (00:01).

    Returns a list of approved relative paths, or ``None`` if the
    \"Don't upload\" option was voted.
    """
    config = _load_config()
    result: list[str] | None = []
    done = asyncio.Event()

    intents = discord.Intents(guilds=True, messages=True, message_content=True)
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        nonlocal result
        try:
            result = await _do_collect_results(client, config, images_dir, temp_dir)
        finally:
            await client.close()
            done.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Check DISCORD_TOKEN in .env.")

    await done.wait()
    return result


# ── legacy single-shot entry point ───────────────────────────────────────────


async def run_review(images_dir: Path, temp_dir: Path) -> list[str]:
    """Send poll, wait for timeout / early close, return approved paths.

    Kept for backwards compatibility with the monolithic ``ensure_main_flow``.
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
            result = await _run_poll_legacy(client, config, images_dir, temp_dir)
        finally:
            await client.close()
            ready_event.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Check DISCORD_TOKEN in .env.")

    await ready_event.wait()
    return result


async def _run_poll_legacy(
    client: discord.Client,
    config: dict,
    images_dir: Path,
    temp_dir: Path,
) -> list[str]:
    """Original single-shot poll: post, wait, end, return."""
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

    for idx, path in enumerate(images, 1):
        rel = _relative(path, images_dir)
        await channel.send(
            f"**Image {idx}/{total}** — {rel}",
            file=discord.File(str(path), filename=path.name),
        )

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

    control_msg = await channel.send("React ✅ here to close the poll early.")
    await control_msg.add_reaction("✅")

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

    try:
        poll_msg = await channel.fetch_message(poll_msg.id)
        ended_poll = await poll_msg.poll.end()
    except Exception:
        poll_msg = await channel.fetch_message(poll_msg.id)
        ended_poll = poll_msg.poll

    approved: list[str] = []
    for i, answer in enumerate(ended_poll.answers):
        if answer.vote_count and answer.vote_count > 0 and i < len(images):
            approved.append(_relative(images[i], images_dir))

    finish_time = datetime.utcnow()

    record_path = _persist_results(
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


# ── utility: send a one-off message to the review channel ────────────────────


async def send_discord_message(text: str) -> None:
    """Connect to Discord, send a single message to the review channel, disconnect.

    Used by the pipeline to post status updates (e.g. Instagram upload result).
    """
    config = _load_config()
    done = asyncio.Event()

    intents = discord.Intents(guilds=True, messages=True)
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            channel = client.get_channel(config["channel_id"])
            if channel is None:
                channel = await client.fetch_channel(config["channel_id"])
            if isinstance(channel, discord.TextChannel):
                await channel.send(text)
        finally:
            await client.close()
            done.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        print("[Discord] Could not send message — login failed.")
        return

    await done.wait()
