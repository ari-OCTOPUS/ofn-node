"""provenance.py — autonomy_provenance.jsonl + طبقه‌بندیِ self-initiation (ADR-039 C2).

ستون‌فقراتِ provenanceِ ADR-039 §2. هر یالِ DAG با prev_hash زنجیر می‌خورد.
`classify_initiation` صادقانه می‌گوید آیا یک run خودآغاز بوده یا با دخالتِ
انسان — تجسیدِ «شواهد-نه-ادعا»: یالِ پس از start با human_prompt_id ⇒ دیگر
شاهدِ self-initiation نیست.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .canonical import (
    ChainVerification,
    append_chained,
    last_chain_hash,
    verify_hash_chain,
)
from .schemas import Initiator, ProvenanceEdge

DEFAULT_PROVENANCE = Path("_ops/epistemics/autonomy_provenance.jsonl")
_ALLOWED_ROOTS = (Path("_ops/epistemics"), Path("outputs/epistemics"))


def _check_confined(path: Path) -> None:
    p = Path(path).resolve()
    for root in _ALLOWED_ROOTS:
        try:
            p.relative_to(root.resolve())
            return
        except ValueError:
            continue
    raise RuntimeError(
        f"provenance path {path} outside allowed roots (ADR-039 §7.3 / §11 #10)"
    )


class ProvenanceWriter:
    """نویسندهٔ append-only برای یال‌های DAG خودمختاری."""

    def __init__(self, path=DEFAULT_PROVENANCE, *, confine: bool = True):
        self.path = Path(path)
        if confine:
            _check_confined(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def tip(self) -> str:
        return last_chain_hash(self.path)

    def append_edge(self, edge: ProvenanceEdge) -> dict:
        """یک یالِ provenance را به زنجیره بچسبان."""
        return append_chained(self.path, edge.model_dump(mode="json"))

    def verify(self) -> ChainVerification:
        return verify_hash_chain(self.path)


def load_edges(path) -> List[dict]:
    """همهٔ یال‌های provenance را از فایل بخوان (به ترتیبِ append)."""
    p = Path(path)
    if not p.exists():
        return []
    out: List[dict] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def classify_initiation(edges: List[dict]) -> str:
    """ADR-039 §2: آیا run خودآغاز بود؟

    - «self_initiated»: هیچ یالِ human_prompt_id / initiator==HUMAN نیست.
    - «human_prompted»: همگی human.
    - «mixed»: هم self هم human.
    - «system_only»: فقط system.
    - «unknown»: خالی.

    این تابع صرفاً برچسب می‌زند — هرگز ادعا را به شاهد تبدیل نمی‌کند.
    """
    if not edges:
        return "unknown"
    has_human = any(
        e.get("human_prompt_id") or e.get("initiator") == Initiator.HUMAN.value
        for e in edges
    )
    has_self = any(e.get("initiator") == Initiator.SELF.value for e in edges)
    if has_human and has_self:
        return "mixed"
    if has_human:
        return "human_prompted"
    if has_self:
        return "self_initiated"
    return "system_only"


def verify_provenance(path) -> ChainVerification:
    """زنجیرهٔ provenance را بازبینی کن (همان منطقِ receipt chain)."""
    return verify_hash_chain(path)
