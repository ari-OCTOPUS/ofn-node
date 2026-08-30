"""config.py — تنظیماتِ بک‌اندِ LANGAR Pro (فقط از env)."""

import os


class Settings:
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://langar:changeme@db:5432/langar")
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    owner_telegram_id = os.environ.get("OWNER_ID", "")
    # کلیدهای LLM/سرچ (همان نام‌های باتِ فعلی، برای سازگاری)
    claude_key = os.environ.get("CLAUDE_KEY") or None
    openai_key = os.environ.get("OPENAI_KEY") or None
    openai_base_url = os.environ.get("OPENAI_BASE_URL") or None
    brave_api_key = os.environ.get("BRAVE_API_KEY") or None
    serpapi_key = os.environ.get("SERPAPI_KEY") or None
    search_provider = (os.environ.get("SEARCH_PROVIDER") or "auto").lower()


settings = Settings()
