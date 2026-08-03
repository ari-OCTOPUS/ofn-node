"""
memory.py — سیستمِ حافظه‌ی سه‌لایه.

  لایه ۱ — Short-term: dictِ درون‌حافظه، محدود به session.
  لایه ۲ — Long-term structured: روی جدول‌های SQLite (از db).
  لایه ۳ — Semantic/Vector: فعلاً غیرفعال (نیاز به embeddings/کلید). hook آماده است.

db تزریق می‌شود تا تست‌پذیر بماند.
"""

from __future__ import annotations


class MemorySystem:
    def __init__(self, db):
        self.db = db
        self._short = {}  # لایه ۱

    # --- لایه ۱ ---
    def load_short_term(self) -> dict:
        return dict(self._short)

    def store_short_term(self, key: str, value) -> None:
        self._short[key] = value

    # --- لایه ۲ ---
    def load_long_term(self, period_days: int = 7) -> dict:
        out = {"logs": [], "reflections": []}
        try:
            out["logs"] = [dict(r) for r in self.db.recent_logs(period_days)]
        except Exception:
            pass
        try:
            out["reflections"] = [dict(r) for r in self.db.recent_reflections(5)]
        except Exception:
            pass
        return out

    def store_long_term(self, *a, **k) -> None:
        # داده‌ها از طریقِ /log و /reflect در db ذخیره می‌شوند؛ این passthrough است.
        return None

    # --- لایه ۳ (غیرفعال) ---
    SEMANTIC_ENABLED = False

    def search_semantic(self, query: str, k: int = 3) -> list:
        # نیاز به embeddings دارد؛ در این نسخه غیرفعال است.
        return []

    def store_semantic(self, text: str, metadata: dict | None = None) -> None:
        return None
