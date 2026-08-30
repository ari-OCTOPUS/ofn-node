"""memory_formation.py — Cognitive Runtime: Memory Formation Pipeline.

هر پیام مستقیماً memory نمی‌شود. مسیر درست:
    message → candidate_extraction → importance_scoring →
    conflict_detection → provenance_binding → owner_approval_if_required → commit

سه نوع حافظه:
    1. Session memory: موقت، مجاز (session_memory.py موجود)
    2. Episodic candidate: proposal، may_authorize=false
    3. Semantic/core: write خودکار ممنوع، نیازمند رأی مالک

این ماژول فقط #2 را مدیریت می‌کند. commit از MemoryGate موجود با رأی.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

_OPS = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
CANDIDATES_FILE = STATE_DIR / "cognitive" / "memory-candidates.jsonl"

IMPORTANCE_HIGH = "HIGH"
IMPORTANCE_MEDIUM = "MEDIUM"
IMPORTANCE_LOW = "LOW"

# کلمات کلیدی برای importance scoring
_HIGH_SIGNALS = frozenset({
    "تصمیم", "هدف", "اولویت", "رأی", "موافقم", "مخالفم", "تغییر",
    "decision", "goal", "priority", "vote", "approve",
})
_MEDIUM_SIGNALS = frozenset({
    "یادت", "بماند", "به خاطر", "این مهم", "فراموش",
    "remember", "important", "note",
})


def extract_candidates(text: str, intent: str = "chat") -> list[dict[str, Any]]:
    """از یک پیام مالک، memory candidate استخراج کن."""
    t = str(text or "").strip()
    if not t or len(t) < 10:
        return []
    candidates = []
    # کل پیام به‌عنوان یک candidate
    c_id = f"cand_{uuid4().hex[:12]}"
    text_digest = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
    candidates.append({
        "candidate_id": c_id,
        "text_digest": text_digest,
        "text_preview": t[:200],
        "intent": str(intent)[:50],
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "conversation",
    })
    return candidates


def score_importance(candidate: dict, text: str = "") -> str:
    """اهمیت یک candidate را بسنج."""
    t = str(text or candidate.get("text_preview") or "").lower()
    if any(s in t for s in _HIGH_SIGNALS):
        return IMPORTANCE_HIGH
    if any(s in t for s in _MEDIUM_SIGNALS):
        return IMPORTANCE_MEDIUM
    return IMPORTANCE_LOW


def detect_conflict(candidate: dict, existing: list[dict] | None = None) -> dict[str, Any]:
    """آیا candidate با حافظهٔ موجود تناقض دارد؟ (ساده: تطبیق digest)."""
    if not existing:
        return {"has_conflict": False, "conflicting_ids": []}
    digest = candidate.get("text_digest")
    conflicts = []
    for e in existing:
        if e.get("text_digest") == digest and e.get("candidate_id") != candidate.get("candidate_id"):
            conflicts.append(e.get("candidate_id"))
    return {"has_conflict": bool(conflicts), "conflicting_ids": conflicts}


def propose_memory(text: str, intent: str = "chat",
                   run_id: str | None = None) -> dict[str, Any]:
    """یک memory candidate کامل بساز و در فایل ثبت کن.

    این commit نیست — فقط candidate. may_authorize همیشه false.
    semantic write خودکار ممنوع است.
    """
    candidates = extract_candidates(text, intent)
    if not candidates:
        return {
            "ok": False,
            "reason": "no_candidates",
            "may_authorize": False,
        }
    cand = candidates[0]
    importance = score_importance(cand, text)

    # read existing برای conflict detection
    existing = _read_candidates()
    conflict = detect_conflict(cand, existing)

    proposal = {
        "candidate_id": cand["candidate_id"],
        "run_id": run_id,
        "text_digest": cand["text_digest"],
        "text_preview": cand["text_preview"],
        "intent": cand["intent"],
        "importance": importance,
        "conflict": conflict,
        "provenance": {
            "source": "conversation",
            "producer": "memory_formation",
            "extracted_at": cand["extracted_at"],
        },
        "status": "CANDIDATE",
        "may_authorize": False,
        "committed": False,
        "note": "semantic write mungkin hanya dengan râi mâlek (owner approval).",
    }

    # ثبت در فایل (fail-soft)
    try:
        CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CANDIDATES_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(proposal, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return {
        "ok": True,
        "proposal": proposal,
        "candidate_id": cand["candidate_id"],
        "importance": importance,
        "has_conflict": conflict["has_conflict"],
        "status": "CANDIDATE_NOT_COMMITTED",
        "may_authorize": False,
        "message": (
            "یک پیشنهاد حافظه ساختم؛ هنوز در حافظهٔ دائمی ننوشتم. "
            "semantic write خودکار ممنوع است — نیازمند رأی شما."
        ),
    }


def list_candidates(limit: int = 20) -> list[dict]:
    """آخرین candidateها را بخوان."""
    return _read_candidates(limit)


def _read_candidates(limit: int = 100) -> list[dict]:
    try:
        if not CANDIDATES_FILE.is_file():
            return []
        lines = CANDIDATES_FILE.read_text("utf-8", errors="replace").splitlines()
        out = []
        for line in lines:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out[-limit:]
    except OSError:
        return []
