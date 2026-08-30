#!/usr/bin/env python3
"""review_bus.py — قرارداد تحویل بین‌فازی (Handoff Contract).

طبق Blueprint بخش A: خروجی هر فاز ساختار ثابت دارد تا ایجنت/فاز بعدی
مطمئن مصرفش کند.

Review types: AUDIT_REPORT, ROADMAP, PHASE_RESULT
هر review: JSON append-only در state_dir/reviews/
verdict انسانی: "approved" | "rejected" | "needs-revision"

طراحی: stdlib-only، $0.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

VALID_REVIEW_TYPES = ("AUDIT_REPORT", "ROADMAP", "PHASE_RESULT")
VALID_VERDICTS = ("approved", "rejected", "needs-revision")

_REVIEWS_DIR = "reviews"


def _reviews_dir(state_dir: Path) -> Path:
    d = state_dir / _REVIEWS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def submit_review(phase_id: str, review_type: str,
                  payload: dict, state_dir: Path | str | None = None) -> str:
    """ذخیرهٔ review طبق قرارداد تحویل.

    review_type: AUDIT_REPORT | ROADMAP | PHASE_RESULT
    payload: dict طبق ساختار قرارداد (top5_gaps, phases, metrics...)
    خروجی: مسیر فایل ذخیره‌شده."""
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"invalid review_type: {review_type}")

    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    rdir = _reviews_dir(state_dir)
    ts = time.strftime("%Y%m%dT%H%M%S")
    fname = f"{phase_id}-{review_type}-{ts}.json"
    fpath = rdir / fname

    doc = {
        "phase_id": phase_id,
        "review_type": review_type,
        "ts": ts,
        "payload": payload,
        "verdict": None,   # منتظر انسان
    }
    fpath.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
    return str(fpath)


def get_review(phase_id: str, review_type: str,
               state_dir: Path | str | None = None) -> dict | None:
    """آخرین review از این نوع برای این فاز."""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    rdir = state_dir / _REVIEWS_DIR
    if not rdir.is_dir():
        return None

    prefix = f"{phase_id}-{review_type}-"
    matches = sorted(rdir.glob(f"{prefix}*.json"), reverse=True)
    if not matches:
        return None

    try:
        return json.loads(matches[0].read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_all_reviews(phase_id: str,
                    state_dir: Path | str | None = None) -> list[dict]:
    """همه reviewهای یک فاز."""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    rdir = state_dir / _REVIEWS_DIR
    if not rdir.is_dir():
        return []

    results = []
    for f in sorted(rdir.glob(f"{phase_id}-*.json")):
        try:
            doc = json.loads(f.read_text("utf-8"))
            doc["_file"] = f.name
            results.append(doc)
        except (json.JSONDecodeError, OSError):
            continue
    return results


def verify_handoff(from_phase: str, to_phase: str,
                    state_dir: Path | str | None = None) -> dict:
    """آیا خروجیهای لازم برای handoff از from_phase به to_phase وجود دارند؟

    برای فاز ۰: PHASE_RESULT لازم است.
    برای فاز ۱+: AUDIT_REPORT + ROADMAP + PHASE_RESULT (از فاز قبل) لازم است.
    """
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    missing: list[str] = []
    found: list[str] = []

    # فاز ۰ فقط PHASE_RESULT نیاز دارد
    if from_phase == "phase-0":
        required = ("PHASE_RESULT",)
    else:
        required = ("AUDIT_REPORT", "ROADMAP", "PHASE_RESULT")

    for rtype in required:
        review = get_review(from_phase, rtype, state_dir)
        if review is not None:
            found.append(rtype)
        else:
            missing.append(rtype)

    return {
        "complete": len(missing) == 0,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "found": found,
        "missing": missing,
    }


def mark_human_verdict(phase_id: str, verdict: str, note: str = "",
                       state_dir: Path | str | None = None) -> dict:
    """ثبت verdict انسانی روی آخرین reviewهای فاز.

    این تابع را فقط انسان صدا می‌زند (از طریق dashboard یا Telegram).
    هر review بدون verdict_approved → فاز بعدی باز نمی‌شود."""
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"invalid verdict: {verdict}")

    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    reviews = get_all_reviews(phase_id, state_dir)
    updated = 0
    rdir = _reviews_dir(state_dir)

    for review in reviews:
        if review.get("verdict") is not None:
            continue
        fpath = rdir / review["_file"]
        review["verdict"] = verdict
        review["verdict_ts"] = time.strftime("%Y%m%dT%H%M%S")
        review["verdict_note"] = note[:500]
        fpath.write_text(json.dumps(review, ensure_ascii=False, indent=2), "utf-8")
        updated += 1

    return {"updated": updated, "verdict": verdict, "phase_id": phase_id}


def handoff_ready(from_phase: str, state_dir: Path | str | None = None) -> dict:
    """آیا همه reviewهای فاز verdict human دارند؟"""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    reviews = get_all_reviews(from_phase, state_dir)
    if not reviews:
        return {"ready": False, "reason": "no-reviews"}

    unreviewed = [r for r in reviews if r.get("verdict") is None]
    rejected = [r for r in reviews if r.get("verdict") == "rejected"]

    return {
        "ready": len(unreviewed) == 0 and len(rejected) == 0,
        "total_reviews": len(reviews),
        "unreviewed": len(unreviewed),
        "rejected": len(rejected),
    }
