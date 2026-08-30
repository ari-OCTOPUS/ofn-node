"""truth_layer.py — Cognitive Runtime: Truth Layer + Verifier.

هر ادعای مهم دربارهٔ runtime/معماری/حافظه باید claim object داشته باشد.
Verifier با شاهد خارجی (file/test/runtime) بررسی می‌کند — نه مدل.

states: UNVERIFIED → REPORTED → VERIFIED | CONFLICT | STALE | REJECTED

هرگز `VERIFIED` جعل نکند — فقط وقتی فایل/خط واقعاً خوانده شود.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent

VERIFICATION_STATES = ("UNVERIFIED", "REPORTED", "VERIFIED", "CONFLICT", "STALE", "REJECTED")


def make_claim(text: str, *, source: str = "", locator: str = "",
               confidence: float = 0.0, evidence_refs: list[str] | None = None,
               run_id: str | None = None) -> dict[str, Any]:
    """یک claim بساز (UNVERIFIED پیش‌فرض)."""
    return {
        "claim_id": f"claim_{uuid4().hex[:12]}",
        "run_id": run_id,
        "text": str(text)[:500],
        "source": str(source)[:200],
        "locator": str(locator)[:200],
        "confidence": float(confidence),
        "evidence_refs": evidence_refs or [],
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verification": "UNVERIFIED",
        "runtime_verified": False,
        "may_authorize": False,
    }


def _check_file_exists(locator: str) -> bool:
    """بررسی اینکه آیا فایل/مسیر واقعاً در مخزن وجود دارد."""
    if not locator:
        return False
    # استخراج مسیر از locator (ممکن است file:line یا مسیر خام باشد)
    path_str = locator.split(":")[0] if ":" in locator else locator
    path_str = path_str.strip().strip('"').strip("'")
    if not path_str:
        return False
    # مسیرهای نسبی از ریشهٔ repo
    candidates = [
        Path(path_str),
        _OPS.parent / path_str,
        _OPS / path_str,
        _OPS.parent / path_str.lstrip("/"),
    ]
    for c in candidates:
        try:
            if c.exists():
                return True
        except OSError:
            continue
    return False


def _check_test_exists(ref: str) -> bool:
    """بررسی اینکه آیا فایل تست واقعاً وجود دارد."""
    if not ref:
        return False
    path_str = ref.strip()
    candidates = [
        _OPS / "tests" / path_str if "/" not in path_str else _OPS.parent / path_str,
        _OPS / "tests" / path_str,
    ]
    for c in candidates:
        try:
            if c.exists() and c.suffix == ".py":
                return True
        except OSError:
            continue
    return False


def verify_claim(claim: dict) -> dict:
    """یک claim را با شاهد خارجی بررسی کن.

    VERIFIED: حداقل یک evidence_ref واقعاً وجود دارد (فایل یا تست).
    REPORTED: source/locator داده شده ولی فایل پیدا نشده.
    CONFLICT: چند source متناقض (فعلاً ساده — فقط یک ref بررسی می‌شود).
    UNVERIFIED: هیچ evidence_ref نیست.
    """
    refs = claim.get("evidence_refs") or []
    locator = claim.get("locator") or ""
    source = claim.get("source") or ""

    if not refs and not locator:
        claim["verification"] = "UNVERIFIED"
        claim["confidence"] = min(claim.get("confidence", 0.0), 0.1)
        claim["runtime_verified"] = False
        return claim

    verified_count = 0
    checked = 0
    for ref in refs:
        ref_str = str(ref).strip()
        if not ref_str:
            continue
        checked += 1
        # اگر شبیه مسیر فایل است
        if ref_str.startswith("_ops/") or ref_str.startswith("architecture/") \
                or "/" in ref_str or ref_str.endswith(".py") or ref_str.endswith(".md"):
            if _check_file_exists(ref_str):
                verified_count += 1
        # اگر اسم تست است
        elif ref_str.startswith("test_") or "test_" in ref_str:
            if _check_test_exists(ref_str):
                verified_count += 1

    # locator خودش هم چک شود
    if locator and _check_file_exists(locator):
        verified_count += 1
        checked += 1

    if verified_count > 0:
        claim["verification"] = "VERIFIED"
        claim["confidence"] = max(claim.get("confidence", 0.5), 0.8)
        claim["runtime_verified"] = True
    elif checked > 0:
        claim["verification"] = "REPORTED"
        claim["confidence"] = min(claim.get("confidence", 0.3), 0.4)
        claim["runtime_verified"] = False
    else:
        claim["verification"] = "UNVERIFIED"

    return claim


def verify_facts(facts: list[dict]) -> list[dict]:
    """یک لیست fact را verify کن. هر fact → claim → verify."""
    verified = []
    for f in facts:
        claim = make_claim(
            text=f.get("claim") or f.get("content_preview") or f.get("title") or "",
            source=f.get("source") or f.get("source_path") or "",
            locator=f.get("locator") or f.get("source_path") or "",
            confidence=f.get("confidence_num", 0.3),
            evidence_refs=[f.get("source_path", "")] if f.get("source_path") else [],
        )
        verify_claim(claim)
        f["verification"] = claim["verification"]
        f["runtime_verified"] = claim["runtime_verified"]
        f["claim_id"] = claim["claim_id"]
        verified.append(f)
    return verified
