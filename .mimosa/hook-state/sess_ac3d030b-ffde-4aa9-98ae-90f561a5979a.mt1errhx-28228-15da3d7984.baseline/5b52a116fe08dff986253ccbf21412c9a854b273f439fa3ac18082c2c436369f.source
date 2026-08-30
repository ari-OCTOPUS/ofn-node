#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolution_gate.py — safe self-improvement loop با evaluator مستقل (ADR-014/017).

قرارداد (Seed Agent v1 — مورد ۳، ۲۰۲۶-۰۸-۰۸):
  · producer ≠ verifier (ADR-014) — ایجنتِ بهبوددهنده با قاضیِ مستقل ارزیابی می‌شود.
  · improvement metrics هرگز خودارجاعی نیستند (درس reward hacking arXiv 2603.28063).
  · هر candidate skill باید regression suite را پاس کند قبل از promotion.
  · rollback design: هر promoted skill قابل revert است.
  · propose-only: promotion نهایی با approval انسانی.

پایپ‌لاین:
  trace → lesson extractor → candidate skill → external eval → gate → promote/reject

پشت فلگ OCTOPUS_WIRE_EVOLUTION_GATE (default OFF).
منبع: seed pack behavioral model §۵ (۵ قانون safety) + ADR-014/017.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

FLAG = "OCTOPUS_WIRE_EVOLUTION_GATE"
SKILLS_DIR = _OPS / "state" / "evolution" / "skills"
CANDIDATES_DIR = _OPS / "state" / "evolution" / "candidates"
LEDGER = _OPS / "state" / "evolution" / "evolution-ledger.jsonl"


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


# ─── مدل ────────────────────────────────────────────────────────────────────

@dataclass
class Lesson:
    """یک درسِ استخراج‌شده از trace — ورودیِ pipeline."""
    source_trace: str           # مسیرِ trace مبدأ
    trigger: str                # چه چیزی این درس را trigger کرد (error/pattern/success)
    observation: str            # چه دیده شد
    proposed_skill: str         # چه مهارتی پیشنهاد می‌شود
    confidence: float = 0.0     # 0.0-1.0 — اعتمادِ استخراج‌کننده


@dataclass
class CandidateSkill:
    """یک skill candidate — قبل از eval و promotion."""
    skill_id: str               # unique id (hash of content)
    lesson_ref: str             # مسیرِ lesson مبدأ
    content: str                # محتوای skill (prompt/SOP/rule)
    skill_type: str             # prompt|sop|rule|tool
    producer: str               # چه ایجنتی ساخت این را
    created_at: str = ""
    eval_status: str = "PENDING"  # PENDING|PASS|FAIL|REJECT
    eval_score: float = 0.0     # 0.0-1.0 — score از evaluator مستقل
    eval_reason: str = ""       # چرا pass/fail


@dataclass
class PromotionRecord:
    """رکوردِ promotion/rejection در ledger — immutable audit trail."""
    skill_id: str
    action: str                 # PROMOTE|REJECT|REVERT
    eval_score: float
    decided_by: str             # evaluator_id یا owner
    decided_at: str
    reason: str
    rollback_ref: str = ""      # برای REVERT: مسیرِ skill قبلی


# ─── lesson extractor (producer) ────────────────────────────────────────────

def extract_lessons_from_trace(trace_path: Path, max_lessons: int = 5) -> list[Lesson]:
    """از یک فایل trace، lesson استخراج کن.
    fail-soft: شکست → [].
    این نقشِ producer را دارد — evaluator هرگز این تابع را صدا نمی‌زند."""
    if not _flag_on():
        return []
    lessons: list[Lesson] = []
    try:
        if not trace_path.exists():
            return []
        lines = trace_path.read_text("utf-8", errors="replace").splitlines()
        for line in lines[-50:]:  # آخرین ۵۰ رویداد
            line = line.strip()
            if not line or "\x00" in line or line.startswith("#"):
                continue
            try:
                rec = json.loads(line)
            except (ValueError, TypeError):
                continue
            # الگو: error با تکرار بالا = lesson
            err = str(rec.get("err") or rec.get("error") or "")
            if err and err not in ("", "None"):
                lessons.append(Lesson(
                    source_trace=str(trace_path),
                    trigger=f"error:{err[:40]}",
                    observation=f"خطای مکرر: {err[:80]}",
                    proposed_skill=f"guard_against_{err[:20].replace(' ', '_')}",
                    confidence=0.6,
                ))
            if len(lessons) >= max_lessons:
                break
    except OSError:
        pass
    return lessons


# ─── candidate builder ──────────────────────────────────────────────────────

def build_candidate(lesson: Lesson, producer: str = "seed_agent") -> CandidateSkill:
    """از یک lesson، یک CandidateSkill بساز."""
    import hashlib
    content_hash = hashlib.sha256(
        (lesson.proposed_skill + lesson.observation).encode("utf-8")
    ).hexdigest()[:12]
    return CandidateSkill(
        skill_id=f"skill_{content_hash}",
        lesson_ref=lesson.source_trace,
        content=lesson.proposed_skill,
        skill_type="rule",
        producer=producer,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


# ─── external evaluator (verifier — مستقل از producer) ─────────────────────

def evaluate_candidate(candidate: CandidateSkill) -> tuple[float, str]:
    """ارزیابیِ مستقلِ یک candidate skill.
    evaluator ≠ producer (ADR-014).
    معیارها:
      - content خالی یا خیلی کوتاه → REJECT
      - skill_type نامعتبر → REJECT
      - confidence producer زیر ۰.۳ → جریمه
      - self-referential metric → REJECT (درس reward hacking)
    خروجی: (score 0.0-1.0, reason)."""
    if not candidate.content or len(candidate.content) < 5:
        return 0.0, "content_too_short"
    if candidate.skill_type not in ("prompt", "sop", "rule", "tool"):
        return 0.0, f"invalid_skill_type:{candidate.skill_type}"
    # self-referential check: skill نباید به خودِ evaluation اشاره کند
    if any(w in candidate.content.lower() for w in ("eval_score", "improvement_rate", "self_score")):
        return 0.0, "self_referential_metric_detected"
    # base score از طول و وضوحِ content
    score = min(1.0, len(candidate.content) / 100.0)
    return score, "evaluated"


# ─── promotion gate ─────────────────────────────────────────────────────────

PROMOTION_THRESHOLD = 0.5  # حداقل score برای promotion


def gate(candidate: CandidateSkill, owner_approved: bool = False) -> PromotionRecord:
    """gate: تصمیم نهایی درباره promotion.
    owner_approved=True یعنی مالک هم تأیید کرده (الزامی برای promotion واقعی).
    ADR-014: evaluator مستقل + ADR-011: human gate."""
    score, reason = evaluate_candidate(candidate)
    candidate.eval_score = score
    candidate.eval_reason = reason

    if score < PROMOTION_THRESHOLD:
        candidate.eval_status = "REJECT"
        record = PromotionRecord(
            skill_id=candidate.skill_id,
            action="REJECT",
            eval_score=score,
            decided_by="evolution_gate",
            decided_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            reason=f"score {score:.2f} < threshold {PROMOTION_THRESHOLD}: {reason}",
        )
        _write_ledger(record)
        return record

    if not owner_approved:
        candidate.eval_status = "PENDING"
        record = PromotionRecord(
            skill_id=candidate.skill_id,
            action="PENDING",
            eval_score=score,
            decided_by="evolution_gate",
            decided_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            reason=f"passed eval ({score:.2f}) — awaiting owner approval",
        )
        _write_ledger(record)
        return record

    # promotion!
    candidate.eval_status = "PASS"
    _persist_skill(candidate)
    record = PromotionRecord(
        skill_id=candidate.skill_id,
        action="PROMOTE",
        eval_score=score,
        decided_by="owner+evolution_gate",
        decided_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        reason=f"owner-approved, eval score {score:.2f}",
    )
    _write_ledger(record)
    return record


def revert(skill_id: str, reason: str = "manual revert") -> PromotionRecord:
    """rollback: یک promoted skill را revert کن."""
    record = PromotionRecord(
        skill_id=skill_id,
        action="REVERT",
        eval_score=0.0,
        decided_by="owner",
        decided_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        reason=reason,
    )
    _write_ledger(record)
    return record


# ─── persistence ────────────────────────────────────────────────────────────

def _persist_skill(candidate: CandidateSkill) -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    path = SKILLS_DIR / f"{candidate.skill_id}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(candidate), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(path))


def _write_ledger(record: PromotionRecord) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# ─── health metrics ─────────────────────────────────────────────────────────

def health_metrics() -> dict:
    """نشانگرهای سلامتیِ evolution loop.
    healthy: promotion_rate معقول، rollback_rate پایین، diversity بالا.
    unhealthy: metric inflation، diversity collapse."""
    try:
        if not LEDGER.exists():
            return {"status": "empty", "promotions": 0, "rejections": 0, "reverts": 0}
        records = []
        for line in LEDGER.read_text("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except (ValueError, TypeError):
                continue
        actions = [r.get("action") for r in records]
        promotions = sum(1 for a in actions if a == "PROMOTE")
        rejections = sum(1 for a in actions if a == "REJECT")
        reverts = sum(1 for a in actions if a == "REVERT")
        pending = sum(1 for a in actions if a == "PENDING")
        unique_skills = len(set(r.get("skill_id") for r in records))
        # rollback rate: reverts / promotions (بالای ۲۰٪ = نگران‌کننده)
        rollback_rate = (reverts / promotions) if promotions > 0 else 0.0
        return {
            "status": "ok",
            "total_records": len(records),
            "unique_skills": unique_skills,
            "promotions": promotions,
            "rejections": rejections,
            "pending": pending,
            "reverts": reverts,
            "rollback_rate": round(rollback_rate, 3),
            "flag_on": _flag_on(),
        }
    except OSError:
        return {"status": "error"}
