"""
memory.py — سیستمِ حافظه‌ی سه‌لایه.

  لایه ۱ — Short-term: dictِ درون‌حافظه، محدود به session.
  لایه ۲ — Long-term structured: روی جدول‌های SQLite (از db).
  لایه ۳ — Semantic/Retrieval: بازیابیِ ترکیبیِ محلی (BM25 + TF-IDF) بدونِ API/کلید.
            از reflectionها و logهای db یک corpus می‌سازد و hybrid retrieval می‌زند.

db تزریق می‌شود تا تست‌پذیر بماند.
"""

from __future__ import annotations


class MemorySystem:
    def __init__(self, db):
        self.db = db
        self._short = {}  # لایه ۱
        self._retriever = None
        self._retriever_n = -1  # چند سند هنگامِ آخرین build

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

    # --- لایه ۳ (بازیابیِ ترکیبیِ محلی، بدونِ API) ---
    SEMANTIC_ENABLED = True
    CORPUS_LIMIT = 2000  # سقفِ رکوردهای واردِ corpus (کنترلِ هزینه/حافظه)

    def _build_corpus(self):
        """corpus را از reflectionها و logهای db می‌سازد. در صورتِ نبودِ ماژول، None."""
        try:
            from .retrieval import HybridRetriever
        except Exception:
            return None
        r = HybridRetriever()
        try:
            for row in (self.db.recent_reflections(self.CORPUS_LIMIT) or []):
                d = dict(row)
                text = " ".join(str(d.get(k, "")) for k in ("question", "answer", "domain"))
                r.add(("reflection", d.get("id")), text,
                      {"kind": "reflection", "domain": d.get("domain"), "ts": d.get("ts")})
        except Exception:
            pass
        try:
            for row in (self.db.recent_logs(self.CORPUS_LIMIT) or []):
                d = dict(row)
                note = d.get("note") or ""
                if note.strip():
                    r.add(("log", d.get("id")), note,
                          {"kind": "log", "ts": d.get("ts")})
        except Exception:
            pass
        return r.build()

    def _ensure_retriever(self):
        # rebuild ساده وقتی تعدادِ reflectionها عوض شده (کش‌ کردنِ ارزان).
        try:
            n = len(self.db.recent_reflections(self.CORPUS_LIMIT) or [])
        except Exception:
            n = 0
        if self._retriever is None or n != self._retriever_n:
            self._retriever = self._build_corpus()
            self._retriever_n = n
        return self._retriever

    def search_semantic(self, query: str, k: int = 3) -> list:
        """top-k رکوردِ مرتبط (hits با id/score/text/meta). محلی و آفلاین."""
        if not self.SEMANTIC_ENABLED:
            return []
        r = self._ensure_retriever()
        if r is None:
            return []
        return r.search(query, k=k)

    def store_semantic(self, text: str, metadata: dict | None = None) -> None:
        # corpus از db ساخته می‌شود؛ ذخیره از مسیرِ /log و /reflect انجام می‌شود.
        # invalidate تا دفعه‌ی بعد دوباره build شود.
        self._retriever_n = -1
        return None
