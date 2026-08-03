"""Central config — load from .env once, expose typed settings everywhere."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    # Required
    anthropic_api_key: str = "<REDACTED-ANTHROPIC-KEY>"
    telegram_bot_token: str = "<REDACTED-TELEGRAM-TOKEN>"
    telegram_chat_id: str = "6150431610"
    tavily_api_key: str = "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"
    planning_alerts_api_key: str = "28eLkTbkY5tjy76vEp1t"

    # Optional
    openai_api_key: str = "<REDACTED-OPENAI-KEY>"
    serper_api_key: str = "fd778accd7b87d2349db21bda624da67225ce5cdbdd5db05be3a5ad8d78f5097"

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


settings = Settings()  # type: ignore[call-arg]

# Sanity warnings — early so user sees them at import time
import sys as _sys

_chat = str(settings.telegram_chat_id).strip()
if _chat.lower().endswith("_bot"):
    print(
        "⚠️  WARNING: TELEGRAM_CHAT_ID looks like a bot username "
        f"({_chat!r}). A bot cannot send messages to itself.\n"
        "    Set it to either your personal user id (an integer) or a "
        "channel/group username like @my_painting_leads where the bot is admin.\n"
        "    Get your personal id by sending /start to the bot, then visiting:\n"
        f"    https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates",
        file=_sys.stderr,
    )
