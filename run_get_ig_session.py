"""Generate an Instagram session for a city.

Logs in to Instagram using the credentials from the city config,
saves the persistent browser session to the configured session_dir,
and exits without posting anything.

Usage:
    python run_get_ig_session.py --config configs/brno.yaml
"""

import argparse
import asyncio

from src.config import init_config
from src.ig_session import generate_ig_session


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Generate IG Session")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)
    print(f"Generating Instagram session for {cfg.display_name}...")

    email = cfg.instagram.email
    password = cfg.instagram.password
    if not email or not password:
        print("ERROR: Instagram credentials not set. Check your .env file.")
        return

    await generate_ig_session(
        session_dir=cfg.instagram.session_dir,
        email=email,
        password=password,
    )


if __name__ == "__main__":
    asyncio.run(main())
