#!/usr/bin/env python3
"""Read-only truth snapshot: self, direction, heart, cortex, goal-cycle and guidance.

No runtime imports and no writes. Every component is labelled AUTHORITATIVE, ADVISORY_SHADOW,
STALE, MISSING or BLOCKED. A fresh shadow is never promoted to authority.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import contracts

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "_ops"
STATE = OPS / "state"


def _json(path: Path) -> dict:
    try:
        d = json.loads(path.read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                out.append(d)
    except OSError:
        pass
    return out


def _age(path: Path, now: float) -> float | None:
    try:
        return max(0.0, now - path.stat().st_mtime)
    except OSError:
        return None


def _state(path: Path, *, now: float, sla_s: float, shadow=False) -> dict:
    d = _json(path)
    age = _age(path, now)
    if not d or age is None:
        auth = "MISSING"
    elif age > sla_s:
        auth = "STALE"
    elif shadow:
        auth = "ADVISORY_SHADOW"
    else:
        auth = "AUTHORITATIVE"
    # مسیرِ نمایشی fail-soft است: `relative_to` روی هر مسیرِ بیرون از `OPS`
    # استثنا می‌دهد. در تولید همیشه داخلِ `_ops` صدا زده می‌شود، ولی همان
    # استثنا باعث شده بود این تابعِ **خالص** بیرون از آن یک مسیر اصلاً
    # قابلِ‌سنجش نباشد — و دقیقاً به همین دلیل دو محافظتِ کهنگی تست نداشتند
    # (هر دو جهششان سبز ماند). یک نامِ نمایشی هرگز نباید سنجه را بکشد.
    try:
        shown = path.relative_to(OPS).as_posix()
    except ValueError:
        shown = path.name
    return {"path": shown, "age_s": age,
            "sla_s": float(sla_s), "authority": auth, "data": d}


def _goals() -> list[str]:
    try:
        return [ln[2:].strip() for ln in (OPS / "GOALS-OCTOPUS.md").read_text("utf-8").splitlines()
                if ln.startswith("- ") and ln[2:].strip()]
    except OSError:
        return []


def _genome_missions() -> dict:
    """دنیای دومِ mission (Genome ِ تلگرام) با واژگانِ canonical — آشتیِ
    VQ-MISSION-RECONCILE-001 قدمِ ۱: یک خواننده، یک زبان. read-only و fail-soft."""
    out = {"counts": {}, "awaiting_owner": 0, "total": 0}
    try:
        import sys as _sys
        if str(OPS) not in _sys.path:
            _sys.path.insert(0, str(OPS))
        import mission_contract as _mc
        d = _json(STATE / "telegram" / "missions" / "missions.json")
        for m in (d.get("missions") or []):
            if not isinstance(m, dict):
                continue
            canon = _mc.genome_to_canonical(m.get("state"))
            out["counts"][canon] = out["counts"].get(canon, 0) + 1
            out["total"] += 1
            if canon == "needs_approval":
                out["awaiting_owner"] += 1
    except Exception:  # noqa: BLE001 — دنیای دوم هرگز snapshot را نمی‌کشد
        pass
    return out


def build(*, now: float | None = None) -> dict:
    now = float(now if now is not None else time.time())
    self_model = _state(STATE / "cortex" / "self-model.json", now=now, sla_s=7200)
    cortex = _state(STATE / "cortex" / "cortex-state.json", now=now, sla_s=1800)
    heart = _state(STATE / "pulse" / "heart-shadow-latest.json", now=now,
                   sla_s=1800, shadow=True)
    heartstate = _state(STATE / "pulse" / "heartstate-latest.json", now=now,
                        sla_s=1800, shadow=True)
    innervation = _state(STATE / "cortex" / "innervation-latest.json", now=now, sla_s=1800)
    work = _state(STATE / "pulse" / "work-plan.json", now=now, sla_s=7 * 86400)
    preregs = _jsonl(STATE / "test_cycle" / "prereg.jsonl")
    cycles = _jsonl(STATE / "test_cycle" / "journal.jsonl")
    verdicts = _jsonl(STATE / "test_cycle" / "verdicts.jsonl")
    guidance = _jsonl(STATE / "cortex" / "owner-guidance.jsonl")

    hd = heart["data"]
    production = hd.get("production_wire") or {}
    heart["production_open"] = bool(production.get("open"))
    heart["production_reasons"] = list(production.get("reasons") or [])
    # Even if the file is fresh, it remains advisory until production_wire.open.
    if heart["authority"] == "ADVISORY_SHADOW" and heart["production_open"]:
        heart["authority"] = "AUTHORITATIVE"

    latest_pre = preregs[-1] if preregs else {}
    # پیوندِ exact-row (۰۷-۳۱): ردیفِ journal/verdict ِ نمایش‌داده‌شده باید مالِ
    # همان چرخهٔ آخرین پیش‌ثبت باشد — سه «آخرین» ِ مستقل می‌توانند سه چرخهٔ
    # متفاوت باشند و link_graph آن‌وقت حکمِ چرخهٔ کهنه را در ردِ چرخهٔ نو
    # نشان می‌دهد. کلیدِ اتصال: prereg_id (اگر ردیف حمل کند)، وگرنه cycle_id.
    _pid = str(latest_pre.get("prereg_id") or "")
    _cid = str(latest_pre.get("cycle_id") or "")

    def _same_cycle(rows: list) -> dict:
        for r in reversed(rows):
            rp = str(r.get("prereg_id") or "")
            if rp and _pid:
                if rp == _pid:
                    return r
                continue
            if _cid and str(r.get("cycle_id") or "") == _cid:
                return r
        return {}

    latest_cycle = _same_cycle(cycles) if latest_pre else {}
    latest_verdict = _same_cycle(verdicts) if latest_pre else {}
    dead = list((innervation["data"] or {}).get("dead_spots") or [])
    coverage = (innervation["data"] or {}).get("coverage_pct")

    blockers = []
    if self_model["authority"] != "AUTHORITATIVE":
        blockers.append("self-model-not-fresh")
    if not heart["production_open"]:
        blockers.append("heart-production-wire-closed")
    if isinstance(coverage, (int, float)) and coverage < 100:
        blockers.append(f"innervation-{coverage:g}-pct")
    if not latest_pre:
        blockers.append("no-preregistered-goal")
    # سلامتِ حلقه = «آیا ارزیاب تا حالا حکمی داده؟» — نه «حکمِ همین چرخه»؛
    # حکمِ چرخهٔ جاری همیشه بعد از deadline می‌آید و نبودش بازدارنده نیست.
    if not verdicts:
        blockers.append("no-independent-verdict-yet")

    return {
        "schema": contracts.SNAPSHOT_SCHEMA,
        "created_epoch": now,
        "self_model": self_model,
        "directions": _goals(),
        "cortex": cortex,
        "heart": heart,
        "heartstate": heartstate,
        "innervation": {**innervation, "coverage_pct": coverage, "dead_spots": dead},
        "work_plan": work,
        "goal_cycle": {"prereg": latest_pre, "journal": latest_cycle,
                       "verdict": latest_verdict,
                       "link_basis": ("prereg_id" if _pid else
                                      ("cycle_id" if _cid else None)),
                       "counts": {
                           "prereg": len(preregs), "cycles": len(cycles),
                           "verdicts": len(verdicts)}},
        "owner_guidance": {"latest": guidance[-1] if guidance else None,
                           "count": len(guidance)},
        "genome_missions": _genome_missions(),
        "blockers": blockers,
        "fully_integrated": not blockers,
    }
