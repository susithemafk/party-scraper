"""
City configuration loader for the party scraper.

Each city has its own YAML config file under ``configs/``.
All scripts accept a ``--config <path>`` argument to select the active city.

Secrets (API keys, passwords, tokens) stay in ``.env`` and are referenced
by environment-variable name from the YAML config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Parser registry – maps a string name from YAML to the actual parser function
# ---------------------------------------------------------------------------

_PARSER_REGISTRY: Dict[str, Callable] = {}


def _ensure_parsers_registered() -> None:
    """Lazily populate the parser registry on first use."""
    if _PARSER_REGISTRY:
        return

    from .parsers.artbar import artbar_parser
    from .parsers.bobyhall import bobyhall_parser
    from .parsers.fleda import fleda_parser
    from .parsers.kabinet import kabinet_parser
    from .parsers.metro import metro_parser
    from .parsers.patro import patro_parser
    from .parsers.perpetuum import perpetuum_parser
    from .parsers.ra import ra_parser
    from .parsers.sono import sono_parser

    _PARSER_REGISTRY.update({
        "artbar": artbar_parser,
        "bobyhall": bobyhall_parser,
        "fleda": fleda_parser,
        "kabinet": kabinet_parser,
        "metro": metro_parser,
        "patro": patro_parser,
        "perpetuum": perpetuum_parser,
        "ra": ra_parser,
        "sono": sono_parser,
    })


def get_parser(name: str) -> Callable:
    """Return the parser function for *name*.  Raises ``KeyError`` if unknown."""
    _ensure_parsers_registered()
    if name not in _PARSER_REGISTRY:
        available = ", ".join(sorted(_PARSER_REGISTRY))
        raise KeyError(
            f"Unknown parser '{name}'. Available parsers: {available}"
        )
    return _PARSER_REGISTRY[name]


def register_parser(name: str, func: Callable) -> None:
    """Register an additional parser at runtime (e.g. from a plugin)."""
    _PARSER_REGISTRY[name] = func


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class VenueConfig:
    title: str
    url: str
    base_url: str
    parser: str  # name into _PARSER_REGISTRY

    def get_parser_func(self) -> Callable:
        return get_parser(self.parser)

    def to_legacy_dict(self) -> dict:
        """Return the dict format expected by the fetcher / event_parser."""
        return {
            "title": self.title,
            "url": self.url,
            "baseUrl": self.base_url,
            "parser": self.get_parser_func(),
        }


@dataclass
class InstagramConfig:
    caption_template: str = "Events in {city} {date}"
    location: str = ""
    session_dir: str = "ig_session"  # per-city browser profile directory
    email_env: str = "INSTAGRAM_EMAIL"
    password_env: str = "INSTAGRAM_PASSWORD"

    @property
    def email(self) -> str:
        return os.getenv(self.email_env, "")

    @property
    def password(self) -> str:
        return os.getenv(self.password_env, "")


@dataclass
class DiscordConfig:
    token_env: str = "DISCORD_TOKEN"
    channel_id_env: str = "TARGET_CHANNEL_ID"
    review_channel_id_env: str = "REVIEW_CHANNEL_ID"
    reviewer_user_id_env: str = "REVIEWER_USER_ID"
    review_timeout: int = 600

    @property
    def token(self) -> str:
        return os.getenv(self.token_env, "")

    @property
    def channel_id(self) -> int:
        val = os.getenv(self.review_channel_id_env) or os.getenv(self.channel_id_env) or "0"
        return int(val)

    @property
    def reviewer_user_id(self) -> Optional[int]:
        val = os.getenv(self.reviewer_user_id_env)
        return int(val) if val else None


@dataclass
class CityConfig:
    """Complete configuration for a single city deployment."""

    # ── identity ──────────────────────────────────────────────────────────
    name: str                           # e.g. "brno"
    display_name: str                   # e.g. "Brno"
    country: str = "Czech Republic"

    # ── title image ───────────────────────────────────────────────────────
    title_text: str = ""                # e.g. "AKCE V BRNĚ"
    title_alt: str = ""                 # e.g. "Akce v Brně"

    # ── venues ────────────────────────────────────────────────────────────
    venues: List[VenueConfig] = field(default_factory=list)

    # ── instagram ─────────────────────────────────────────────────────────
    instagram: InstagramConfig = field(default_factory=InstagramConfig)

    # ── discord ───────────────────────────────────────────────────────────
    discord: DiscordConfig = field(default_factory=DiscordConfig)

    # ── derived helpers ───────────────────────────────────────────────────

    def venues_as_legacy_list(self) -> List[dict]:
        """Return venues in the dict-list format used by fetcher / event_parser."""
        return [v.to_legacy_dict() for v in self.venues]

    @property
    def fallback_location_label(self) -> str:
        """Fallback label used in image generation when venue/place is empty."""
        return self.display_name or self.name.title()

    def format_caption(self, date_str: str) -> str:
        """Render the Instagram caption with ``{city}`` and ``{date}`` placeholders."""
        return self.instagram.caption_template.format(
            city=self.display_name,
            date=date_str,
        )


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------

def _build_venues(raw: list) -> List[VenueConfig]:
    venues = []
    for v in raw:
        venues.append(VenueConfig(
            title=v["title"],
            url=v["url"],
            base_url=v.get("base_url", v.get("baseUrl", "")),
            parser=v["parser"],
        ))
    return venues


def load_config(path: str | Path) -> CityConfig:
    """Parse a YAML city-config file and return a ``CityConfig``."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw: Dict[str, Any] = yaml.safe_load(fh)

    # ── load the city-specific .env file ──────────────────────────────
    # The YAML may specify  env_file: .env.brno  (relative to project root).
    # Falls back to  .env.<city_name>  and then  .env .
    project_root = path.parent.parent
    env_file = raw.get("env_file", "")
    if env_file:
        env_path = project_root / env_file
    else:
        city_name = raw.get("city", {}).get("name", "")
        candidate = project_root / f".env.{city_name}" if city_name else None
        if candidate and candidate.exists():
            env_path = candidate
        else:
            env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"[Config] Loaded env file: {env_path}")
    else:
        # ultimate fallback – cwd/.env
        load_dotenv()

    city_raw = raw.get("city", {})
    ig_raw = raw.get("instagram", {})
    dc_raw = raw.get("discord", {})
    venues_raw = raw.get("venues", [])

    instagram = InstagramConfig(
        caption_template=ig_raw.get("caption_template", InstagramConfig.caption_template),
        location=ig_raw.get("location", ""),
        session_dir=ig_raw.get("session_dir", f"ig_sessions/{city_raw.get('name', 'default')}"),
        email_env=ig_raw.get("email_env", "INSTAGRAM_EMAIL"),
        password_env=ig_raw.get("password_env", "INSTAGRAM_PASSWORD"),
    )

    discord_cfg = DiscordConfig(
        token_env=dc_raw.get("token_env", "DISCORD_TOKEN"),
        channel_id_env=dc_raw.get("channel_id_env", "TARGET_CHANNEL_ID"),
        review_channel_id_env=dc_raw.get("review_channel_id_env", "REVIEW_CHANNEL_ID"),
        reviewer_user_id_env=dc_raw.get("reviewer_user_id_env", "REVIEWER_USER_ID"),
        review_timeout=dc_raw.get("review_timeout", 600),
    )

    return CityConfig(
        name=city_raw.get("name", "default"),
        display_name=city_raw.get("display_name", city_raw.get("name", "Default")),
        country=city_raw.get("country", "Czech Republic"),
        title_text=city_raw.get("title_text", ""),
        title_alt=city_raw.get("title_alt", ""),
        venues=_build_venues(venues_raw),
        instagram=instagram,
        discord=discord_cfg,
    )


# ---------------------------------------------------------------------------
# Global singleton – set once at startup via ``init_config()``
# ---------------------------------------------------------------------------

_active_config: Optional[CityConfig] = None


def init_config(path: str | Path) -> CityConfig:
    """Load the config from *path* and store it as the global active config."""
    global _active_config
    _active_config = load_config(path)
    print(f"[Config] Loaded city config: {_active_config.display_name} ({path})")
    return _active_config


def get_config() -> CityConfig:
    """Return the active config, raising if ``init_config`` hasn't been called."""
    if _active_config is None:
        raise RuntimeError(
            "City config not loaded. Call init_config(path) or pass --config <path> "
            "to the runner script."
        )
    return _active_config
