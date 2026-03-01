"""Generate images from processed event data."""
import argparse

from src.config import init_config
from src.pipeline import (
    generate_images_from_processed,
    load_processed_events,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Generate Images")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print(f"\n[STEP 4] Generating images for {cfg.display_name}...\n")
    try:
        processed_events = load_processed_events()
    except FileNotFoundError as exc:
        print("[STEP 4] Cannot load processed events. Run run_process.py first.")
        print(exc)
        return

    print(f"[STEP 4] Using processed data for {cfg.display_name}")

    # omit the title initially; it will be generated later after approval
    generated_files = generate_images_from_processed(
        processed_events, generate_title=False
    )
    print(f"[STEP 4] Generated {len(generated_files)} image files")


if __name__ == "__main__":
    main()
