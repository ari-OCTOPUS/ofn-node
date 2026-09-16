"""novelty.py — موتور تازگی و عدم تکرار.

بند ۸: قبل از اعلام کشف، بررسی کن آیا اختاپوس قبلاً آن را می‌دانسته.
چهار نوع نوآوری: fact / relation / strategic / action.

قانون:
  خلاصه‌کردن یک مقاله = کشف نیست.
  ترکیب چند شاهد برای ساخت فرضیهٔ ابطال‌پذیر = می‌تواند کشف باشد.

منابع امن برای novelty scan (فقط‌خواندنی):
- GOALS-OCTOPUS.md, research-latest.json, synthesis-latest.json, reports.
- هرگز: secret, wallet, seed, credential, .env, memory.db.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .contracts import (
    NOVELTY_ACTION,
    NOVELTY_FACT,
    NOVELTY_RELATION,
    NOVELTY_STRATEGIC,
    NoveltyReceipt,
)

_OPS_ROOT = Path(__file__).resolve().parent.parent

# مسیرهای امن برای novelty scan (read-only)
NOVELTY_SCAN_PATHS = [
    _OPS_ROOT / "GOALS-OCTOPUS.md",
    _OPS_ROOT / "state" / "pulse" / "research-latest.json",
    _OPS_ROOT / "state" / "cortex" / "synthesis-latest.json",
    Path(__file__).resolve().parent / "reports",
]

# مسیرهای ممنوع برای scan (هرگز باز نشوند)
FORBIDDEN_SCAN = (
    ".env", "secret", "wallet", "seed", "credential", "token",
    "memory.db", ".key", "mnemonic",
)

# آستانهٔ overlap برای "known"
KNOWN_THRESHOLD = 0.7
PARTIALLY_THRESHOLD = 0.35


@dataclass
class _MemoryCorpus:
    """جمع‌آوری متن امن از حافظهٔ اختاپوس برای مقایسه."""

    chunks: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, paths: Optional[list[Path]] = None) -> "_MemoryCorpus":
        paths = paths or NOVELTY_SCAN_PATHS
        chunks: list[str] = []
        for p in paths:
            cls._scan_one(p, chunks)
        return cls(chunks=chunks)

    @staticmethod
    def _scan_one(p: Path, chunks: list[str]) -> None:
        if not p.exists():
            return
        # deny access to forbidden paths
        name_low = p.name.lower()
        if any(f in name_low for f in FORBIDDEN_SCAN):
            return
        try:
            if p.is_file():
                if p.suffix.lower() == ".json":
                    _MemoryCorpus._scan_json(p, chunks)
                else:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                    # به قطعات کوچک بشکن (پاراگراف/بخش)
                    for para in re.split(r"\n\s*\n", txt):
                        para = para.strip()
                        if len(para) > 40:
                            chunks.append(para[:1500])
            elif p.is_dir():
                for child in sorted(p.iterdir()):
                    _MemoryCorpus._scan_one(child, chunks)
        except OSError:
            return

    @staticmethod
    def _scan_json(p: Path, chunks: list[str]) -> None:
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            return
        # استخراج متن از ساختار JSON (findings, proposals, topics, ...)
        for key in ("findings", "proposals", "topics", "hypotheses", "items", "goals"):
            vals = data.get(key) if isinstance(data, dict) else None
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, dict):
                        for k in ("title", "snippet", "why", "claim", "first_step", "text"):
                            t = v.get(k)
                            if isinstance(t, str) and len(t) > 20:
                                chunks.append(t[:1500])
                    elif isinstance(v, str) and len(v) > 20:
                        chunks.append(v[:1500])


def _tokenize(text: str) -> set[str]:
    """tokenization ساده برای overlap (lowercase، حذف stopword پرتکرار)."""
    low = (text or "").lower()
    toks = re.findall(r"[a-z0-9\u0600-\u06FF]{3,}", low)
    # stopword پرتکرار انگلیسی
    stop = {
        "the", "and", "for", "that", "this", "with", "from", "are", "was",
        "were", "has", "have", "will", "can", "not", "but", "all", "any",
        "its", "our", "you", "your", "they", "them", "their", "http", "https",
        "www", "com", "org",
    }
    return {t for t in toks if t not in stop}


def _overlap(a_tokens: set[str], b_tokens: set[str]) -> float:
    """Jaccard-like overlap."""
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return inter / union if union else 0.0


def assess_novelty(
    claim: str,
    *,
    corpus: Optional[_MemoryCorpus] = None,
    searched_scopes: Optional[list[str]] = None,
    novelty_kinds: Optional[Iterable[str]] = None,
) -> NoveltyReceipt:
    """ساخت یک novelty receipt برای یک claim."""
    corpus = corpus or _MemoryCorpus.load()
    claim_toks = _tokenize(claim)

    nearest: list[tuple[float, str]] = []
    for chunk in corpus.chunks:
        score = _overlap(claim_toks, _tokenize(chunk))
        if score > 0.05:
            nearest.append((score, chunk[:120]))
    nearest.sort(reverse=True)
    top = nearest[:5]

    best = top[0][0] if top else 0.0

    # decision
    if best >= KNOWN_THRESHOLD:
        decision = "known"
    elif best >= PARTIALLY_THRESHOLD:
        decision = "partially-novel"
    elif best > 0.0:
        decision = "novel"
    else:
        # best == 0.0: هیچ چیز مشابه در حافظه نیست → احتمالا novel.
        # اما اگر corpus خالی بود → نمی‌توان قضاوت کرد → unknown.
        if len(corpus.chunks) == 0:
            decision = "unknown"
        else:
            decision = "novel"

    kinds = list(novelty_kinds) if novelty_kinds else _infer_kinds(claim)

    return NoveltyReceipt(
        searched_scopes=[str(p) for p in (searched_scopes or NOVELTY_SCAN_PATHS)],
        nearest_existing_items=[t for _, t in top],
        overlap_score=round(best, 3),
        novel_parts=[claim] if decision in ("novel", "partially-novel") else [],
        not_novel_parts=[t for s, t in top if s >= PARTIALLY_THRESHOLD],
        novelty_kinds=kinds,
        decision=decision,
        method="jaccard-token-overlap vs octopus-memory-corpus",
    )


def _infer_kinds(claim: str) -> list[str]:
    """حدس نوع نوآوری از ادعا."""
    low = (claim or "").lower()
    kinds = []
    # relation: اگر نشانه‌های اتصال دارد
    if any(k in low for k in ("because", "leads to", "causes", "relationship",
                               "connects", " link ", "ties", "correlat",
                               "بنابراین", "منجر", "ربط")):
        kinds.append(NOVELTY_RELATION)
    # strategic: اگر رقابتی/مزیت
    if any(k in low for k in ("advantage", "weakness", "competitor", "moat",
                               "asymmetry", "opportunity", "threat",
                               "مزیت", "ضعف", "رقیب", "فرصت", "تهدید")):
        kinds.append(NOVELTY_STRATEGIC)
    # action: اگر آزمایش/اقدام
    if any(k in low for k in ("experiment", "test", "try", "measure", "deploy",
                               "build", "implement", "launch",
                               "آزمون", "آزمایش", "سنجش", "اجرا", "ساخت")):
        kinds.append(NOVELTY_ACTION)
    # fact: اگر واقعیت جدید
    if not kinds:
        kinds.append(NOVELTY_FACT)
    return kinds


def novelty_receipt_dict(claim: str, **kwargs) -> dict:
    return assess_novelty(claim, **kwargs).as_dict()
