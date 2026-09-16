"""Central config — load from .env once, expose typed settings everywhere.

SECURITY RULE: NO secrets in this file, ever. All keys live only in `.env`
(gitignored). If a required key is missing the bot refuses to start with a
clear message — better than half-working with silent failures.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Values that mean "not configured yet" (placeholders left in .env)
_PLACEHOLDER_MARKERS = ("<", "xxxx", "rotate-me", "change-me", "your-", "...")


def _is_placeholder(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v:
        return True
    return any(m in v for m in _PLACEHOLDER_MARKERS)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    # --- Secrets (REQUIRED — only via .env, never hardcode here) ---
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    tavily_api_key: str = ""
    planning_alerts_api_key: str = ""

    # --- Secrets (optional) ---
    openai_api_key: str = ""
    serper_api_key: str = ""

    # Operator
    operator_name: str = "Armin"
    operator_business: str = "Sydney Painting"
    operator_suburbs: str = "Sydney CBD,North Shore,Eastern Suburbs,Inner West,Inner South,Northern Beaches"
    operator_min_value_aud: int = 20_000
    operator_max_value_aud: int = 2_000_000
    operator_categories: str = "gov,commercial,strata,residential-premium"

    # Behavior
    hunter_run_every_hours: int = 6
    harvester_run_every_minutes: int = 15
    digest_hour_local: int = 8
    timezone: str = "Australia/Sydney"
    llm_model: str = "claude-sonnet-4-6"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Paths
    @property
    def data_dir(self) -> Path:
        d = ROOT / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def db_path(self) -> Path:
        return self.data_dir / "leads.db"

    @property
    def hunter_memory_path(self) -> Path:
        return self.data_dir / "hunter_memory.md"

    @property
    def suburbs_list(self) -> list[str]:
        return [s.strip() for s in self.operator_suburbs.split(",") if s.strip()]

    @property
    def categories_list(self) -> list[str]:
        return [c.strip() for c in self.operator_categories.split(",") if c.strip()]

    @property
    def chat_id_for_telegram(self) -> int | str:
        """Return chat_id in the form python-telegram-bot expects.

        - Numeric string -> int (personal DM or group/supergroup numeric id)
        - String starting with '@' -> channel/supergroup username, kept as str
        """
        raw = str(self.telegram_chat_id).strip()
        if raw.startswith("@"):
            return raw
        try:
            return int(raw)
        except ValueError:
            return raw  # let telegram surface the error

    # --- Validation -------------------------------------------------------

    REQUIRED_KEYS: tuple[str, ...] = (
        "anthropic_api_key",
        "telegram_bot_token",
        "telegram_chat_id",
        "tavily_api_key",
        "planning_alerts_api_key",
    )

    def missing_required(self) -> list[str]:
        """Names of required settings that are empty or still placeholders."""
        return [k for k in self.REQUIRED_KEYS if _is_placeholder(getattr(self, k))]


def _fail_fast(missing: list[str]) -> None:
    names = ", ".join(m.upper() for m in missing)
    print(
        "\n"
        "❌ CONFIG ERROR — required keys missing or still placeholders in .env:\n"
        f"   {names}\n\n"
        f"   .env location: {ROOT / '.env'}\n"
        "   1) copy .env.example to .env if you haven't\n"
        "   2) fill in real values (see ../05_راهنمای_API_keys.md)\n"
        "   3) if a key was leaked/rotated, generate a NEW one in the provider console\n",
        file=sys.stderr,
    )
    raise SystemExit(1)


settings = Settings()  # type: ignore[call-arg]

# Fail fast at import time so every entrypoint (main/diagnose/tests) gets a
# clear error instead of a confusing 401 later. Tests can bypass by setting
# the env vars to dummy values.
_missing = settings.missing_required()
if _missing:
    _fail_fast(_missing)

# Sanity warnings — early so user sees them at import time
_chat = str(settings.telegram_chat_id).strip()
if _chat.lower().endswith("_bot"):
    print(
        "⚠️  WARNING: TELEGRAM_CHAT_ID looks like a bot username "
        f"({_chat!r}). A bot cannot send messages to itself.\n"
        "    Set it to either your personal user id (an integer) or a "
        "channel/group username like @my_painting_leads where the bot is admin.\n"
        "    Get your personal id by sending /start to the bot, then checking\n"
        "    the getUpdates endpoint for your bot token.",
        file=sys.stderr,
    )
