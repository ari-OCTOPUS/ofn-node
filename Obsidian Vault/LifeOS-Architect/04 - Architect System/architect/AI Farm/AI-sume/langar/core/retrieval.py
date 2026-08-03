"""
retrieval.py — بازیابیِ ترکیبی (hybrid retrieval) — محلی و بدونِ API.

طبقِ چشم‌اندازِ Unified Agent Prompt (بخش ۵): retrieval = dense + sparse + fusion.
چون اصلِ پروژه local-first/privacy است، این پیاده‌سازی **هیچ embedding یا کلیدِ بیرونی**
لازم ندارد:

  • sparse  → BM25 (Okapi) روی توکن‌های کلیدواژه‌ای.
  • dense   → TF-IDF cosine (نزدیک‌ترین چیز به معناییِ بدونِ شبکه).
  • fusion  → min-max normalize هر امتیاز، سپس میانگینِ وزن‌دار.

فارسی‌آگاه: نرمال‌سازیِ ي/ك عربی و حذفِ اعراب (همسو با core/constitution.py).
خالص (pure-python، بدونِ numpy) تا روی هر سروری بدونِ وابستگی اجرا شود و تست‌پذیر بماند.

این یک جایگزینِ کاملِ vector-DB نیست؛ یک بازیابیِ سبک و قابلِ‌اعتماد برای حجمِ
داده‌ی شخصی (هزاران رکورد) است. مسیرِ ارتقا: همان رابط، با backend برداری در آینده.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

# --- نرمال‌سازیِ متن (همسو با constitution._norm) ---
_DIACRITICS = re.compile(r"[ً-ْـ]")
_TOKEN = re.compile(r"[0-9A-Za-z؀-ۿ]+")

# توقف‌واژه‌های پرتکرارِ فارسی/انگلیسی (کوتاه و محافظه‌کارانه)
_STOP = {
    "و", "در", "به", "از", "که", "را", "با", "این", "آن", "است", "بود", "می",
    "هم", "تا", "یک", "بر", "یا", "اگر", "ولی", "اما", "برای", "هر", "همه",
    "the", "a", "an", "is", "are", "of", "to", "in", "and", "or", "for", "on",
}


def normalize(s: str) -> str:
    s = (s or "").translate({0x064A: 0x06CC, 0x0643: 0x06A9})  # ي→ی ، ك→ک
    return _DIACRITICS.sub("", s).lower()


def tokenize(s: str) -> list[str]:
    return [t for t in _TOKEN.findall(normalize(s)) if t not in _STOP and len(t) > 1]


def _minmax(scores: list[float]) -> list[float]:
    if not scores:
        return scores
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-12:
        return [0.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


@dataclass
class Doc:
    id: object
    text: str
    meta: dict = field(default_factory=dict)
    tokens: list[str] = field(default_factory=list)


@dataclass
class Hit:
    id: object
    score: float
    text: str
    meta: dict


class HybridRetriever:
    """
    BM25 (sparse) + TF-IDF cosine (dense) با ترکیبِ min-max نرمال‌شده.

    استفاده:
        r = HybridRetriever()
        r.add(id, text, meta); ... ; r.build()
        hits = r.search("سؤال", k=3)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, alpha: float = 0.5):
        self.k1 = k1            # اشباعِ فراوانیِ BM25
        self.b = b             # نرمال‌سازیِ طول
        self.alpha = alpha     # وزنِ dense در fusion (1-alpha برای sparse)
        self.docs: list[Doc] = []
        self._df: Counter = Counter()
        self._idf: dict[str, float] = {}
        self._avg_len: float = 0.0
        self._built = False

    # --- ساخت ---
    def add(self, doc_id, text: str, meta: dict | None = None) -> None:
        toks = tokenize(text)
        if not toks:
            return
        self.docs.append(Doc(doc_id, text, dict(meta or {}), toks))
        self._built = False

    def build(self) -> "HybridRetriever":
        n = len(self.docs)
        self._df.clear()
        for d in self.docs:
            for term in set(d.tokens):
                self._df[term] += 1
        # idf هموارشده (همیشه مثبت) برای TF-IDF/cosine
        self._idf = {t: math.log(1 + n / (1 + df)) for t, df in self._df.items()}
        self._avg_len = (sum(len(d.tokens) for d in self.docs) / n) if n else 0.0
        self._built = True
        return self

    # --- امتیازها ---
    def _bm25(self, q_tokens: list[str], d: Doc) -> float:
        n = len(self.docs)
        tf = Counter(d.tokens)
        dl = len(d.tokens)
        score = 0.0
        for term in q_tokens:
            f = tf.get(term, 0)
            if not f:
                continue
            df = self._df.get(term, 0)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))  # BM25 idf
            denom = f + self.k1 * (1 - self.b + self.b * dl / (self._avg_len or 1))
            score += idf * (f * (self.k1 + 1)) / (denom or 1)
        return score

    def _tfidf_vec(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        vec = {t: (c / len(tokens)) * self._idf.get(t, 0.0) for t, c in tf.items()}
        return vec

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    # --- جستجو ---
    def search(self, query: str, k: int = 3) -> list[Hit]:
        if not self._built:
            self.build()
        q_tokens = tokenize(query)
        if not q_tokens or not self.docs:
            return []
        q_vec = self._tfidf_vec(q_tokens)

        sparse = [self._bm25(q_tokens, d) for d in self.docs]
        dense = [self._cosine(q_vec, self._tfidf_vec(d.tokens)) for d in self.docs]
        sN, dN = _minmax(sparse), _minmax(dense)

        fused = []
        for i, d in enumerate(self.docs):
            s = self.alpha * dN[i] + (1 - self.alpha) * sN[i]
            if s > 0:
                fused.append(Hit(d.id, round(s, 6), d.text, d.meta))
        fused.sort(key=lambda h: h.score, reverse=True)
        return fused[:k]
