"""
config.py — بارگذاری و اعتبارسنجیِ متغیرهای محیطی (تنها نقطه‌ی ورودِ env).

.env فقط key=value است. هیچ کدِ پایتونی در .env نباید باشد.
کلیدها هرگز در لاگ چاپ نمی‌شوند.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _int(v, default):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return default


def _clean(v):
    """فاصله و گیومه‌ی اضافی و کامای انتهایی را پاک می‌کند (محافظ در برابر .envِ شلخته)."""
    if v is None:
        return None
    s = str(v).strip().strip(",").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1]
    return s or None


@dataclass
class Config:
    bot_token: str | None
    owner_id: str | None
    claude_key: str | None
    chatbox_api_key: str | None
    chatbox_base_url: str | None
    brain_model: str
    brain_provider: str          # auto | anthropic | chatbox | offline
    self_reflect: bool
    ping_hour: int
    # researcher / web search
    search_provider: str         # auto | brave | serpapi | offline
    brave_api_key: str | None
    serpapi_key: str | None


def _first(*keys):
    """اولین متغیرِ موجود از بینِ نام‌های مترادف (alias) را برمی‌گرداند."""
    for k in keys:
        v = _clean(os.environ.get(k))
        if v:
            return v
    return None


def load_config() -> Config:
    return Config(
        # نام‌های مترادف هم پشتیبانی می‌شوند تا .envهای مختلف کار کنند
        bot_token=_first("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
        owner_id=_first("OWNER_ID", "OWNER_CHAT_ID"),
        claude_key=_first("CLAUDE_KEY", "ANTHROPIC_API_KEY"),
        chatbox_api_key=_first("CHATBOX_API_KEY", "OPENAI_KEY", "OPENAI_API_KEY"),
        chatbox_base_url=_first("CHATBOX_BASE_URL", "OPENAI_BASE_URL"),
        brain_model=_first("BRAIN_MODEL", "OPENAI_MODEL") or "deepseek-reasoner",
        brain_provider=(_first("BRAIN_PROVIDER") or "auto").lower(),
        self_reflect=_bool(os.environ.get("BRAIN_SELF_REFLECT", "false")),
        ping_hour=_int(os.environ.get("LANGAR_PING_HOUR", "8"), 8),
        search_provider=(_first("SEARCH_PROVIDER") or "auto").lower(),
        brave_api_key=_first("BRAVE_API_KEY"),
        serpapi_key=_first("SERPAPI_KEY", "SERPAPI_API_KEY"),
    )


# بودجه و capabilities (خارج از dataclass تا ساده بماند)
def ailab_daily_budget() -> float:
    try:
        return float(os.environ.get("AILAB_DAILY_BUDGET_USD", "1") or "1")
    except ValueError:
        return 1.0


def ailab_monthly_budget() -> float:
    try:
        return float(os.environ.get("AILAB_MONTHLY_BUDGET_USD", "30") or "30")
    except ValueError:
        return 30.0


def cap(name: str, default=True) -> bool:
    v = os.environ.get(name)
    return default if v is None else _bool(v)


def validate(cfg: Config) -> list[str]:
    """فهرستِ مشکلاتِ بحرانی (خالی = همه‌چیز خوب)."""
    problems = []
    if not cfg.bot_token:
        problems.append("BOT_TOKEN تنظیم نشده.")
    if not cfg.owner_id:
        problems.append("OWNER_ID تنظیم نشده.")
    return problems


CONFIG = load_config()
