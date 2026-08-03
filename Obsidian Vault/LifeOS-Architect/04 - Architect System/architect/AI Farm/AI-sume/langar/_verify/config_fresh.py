from __future__ import annotations
import os
from dataclasses import dataclass
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _bool(v):
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _int(v, default):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return default


def _clean(v):
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
    brain_provider: str
    self_reflect: bool
    ping_hour: int


def _first(*keys):
    for k in keys:
        v = _clean(os.environ.get(k))
        if v:
            return v
    return None


def load_config() -> Config:
    return Config(
        bot_token=_first("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
        owner_id=_first("OWNER_ID", "OWNER_CHAT_ID"),
        claude_key=_first("CLAUDE_KEY", "ANTHROPIC_API_KEY"),
        chatbox_api_key=_first("CHATBOX_API_KEY", "OPENAI_KEY", "OPENAI_API_KEY"),
        chatbox_base_url=_first("CHATBOX_BASE_URL", "OPENAI_BASE_URL"),
        brain_model=_first("BRAIN_MODEL", "OPENAI_MODEL") or "deepseek-reasoner",
        brain_provider=(_first("BRAIN_PROVIDER") or "auto").lower(),
        self_reflect=_bool(os.environ.get("BRAIN_SELF_REFLECT", "false")),
        ping_hour=_int(os.environ.get("LANGAR_PING_HOUR", "8"), 8),
    )


def validate(cfg) -> list:
    problems = []
    if not cfg.bot_token:
        problems.append("BOT_TOKEN تنظیم نشده.")
    if not cfg.owner_id:
        problems.append("OWNER_ID تنظیم نشده.")
    return problems
