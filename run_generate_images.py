"""Generate images from processed event data."""
from src.pipeline import (
    GENERATED_IMAGES_DIR,
    PROCESSED_EVENTS_PATH,
    generate_images_from_processed,
    load_processed_events,
)


def main() -> None:
    print("\n[STEP 4] Generating images from processed events...\n")
    try:
        processed_events = load_processed_events()
    except FileNotFoundError as exc:
        print("[STEP 4] Cannot load processed events. Run run_process.py first.")
        print(exc)
        return

    print(f"[STEP 4] Using processed snapshot: {PROCESSED_EVENTS_PATH}")

    # omit the title initially; it will be generated later after approval
    generated_files = generate_images_from_processed(
        processed_events, GENERATED_IMAGES_DIR, generate_title=False
    )
    print(f"[STEP 4] Generated {len(generated_files)} image files")
    print(f"[STEP 4] Images written to: {GENERATED_IMAGES_DIR}")


if __name__ == "__main__":
    main()
