"""Shared Discord utilities — config loading, one-off messages & file sends."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import discord
from dotenv import load_dotenv


# ── config ────────────────────────────────────────────────────────────────────


def load_discord_config() -> dict:
    """Build the Discord config dict.

    Prefers values from the city config (if loaded), falling back to raw
    environment variables for backwards compatibility.
    """
    load_dotenv()

    # Try city config first
    try:
        from .config import get_config
        cfg = get_config()
        token = cfg.discord.token or os.getenv("DISCORD_TOKEN")
        channel_id = cfg.discord.channel_id or int(
            os.getenv("REVIEW_CHANNEL_ID") or os.getenv("TARGET_CHANNEL_ID") or "0"
        )
        reviewer_id = cfg.discord.reviewer_user_id
        timeout = cfg.discord.review_timeout
    except Exception:
        token = os.getenv("DISCORD_TOKEN")
        channel_str = os.getenv("REVIEW_CHANNEL_ID") or os.getenv("TARGET_CHANNEL_ID")
        reviewer_str = os.getenv("REVIEWER_USER_ID")
        timeout = int(os.getenv("REVIEW_TIMEOUT", "600"))
        channel_id = int(channel_str) if channel_str else 0
        reviewer_id = int(reviewer_str) if reviewer_str else None

    if not token:
        raise SystemExit("DISCORD_TOKEN is missing from the .env file.")
    if not channel_id:
        raise SystemExit(
            "REVIEW_CHANNEL_ID or TARGET_CHANNEL_ID is required in .env."
        )

    return {
        "token": token,
        "channel_id": channel_id,
        "reviewer_id": reviewer_id,
        "timeout": max(timeout, 10),
    }


# ── one-off messaging ────────────────────────────────────────────────────────


async def send_discord_message(text: str) -> None:
    """Connect to Discord, send a single message to the review channel, disconnect.

    Used by the pipeline to post status updates (e.g. Instagram upload result).
    """
    config = load_discord_config()
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


async def send_discord_file(file_path: str | Path, message: str = "") -> None:
    """Connect to Discord, send a file (with optional text) to the review channel."""
    path = Path(file_path)
    if not path.exists():
        print(f"[Discord] File not found, skipping: {path}")
        return

    config = load_discord_config()
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
                await channel.send(
                    message,
                    file=discord.File(str(path), filename=path.name),
                )
        finally:
            await client.close()
            done.set()

    try:
        await client.start(config["token"])
    except discord.LoginFailure:
        print("[Discord] Could not send file — login failed.")
        return

    await done.wait()
