#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live4_harness.py — پرفلایت غیرزندهٔ LIVE-4 (حکم مالک 2026-08-19).
سه قطعه: ① اعتبارسنجی رکورد FX پین‌شدهٔ مالک ② داور کور + تصادفی‌سازی A/B
③ اعتبارسنج واجدیت ( coverage 100% + تفکیک confidence سیستمی از LLM )."""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = "live4-harness/1"
_HERE = Path(__file__).resolve().parent


# ── ۱) FX ────────────────────────────────────────────────────────────────
def fx_canonical_hash(rec: dict) -> str:
    body = {"fx_source_id": rec.get("fx_source_id"),
            "fx_timestamp_utc": rec.get("fx_timestamp_utc"),
            "fx_rate_usd_to_aud": rec.get("fx_rate_usd_to_aud")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def validate_fx(rec: dict, *, now: datetime | None = None) -> dict:
    """GO/NO-GO شرط ۱. رکورد باید ۵ فیلد داشته باشد، هش بخورد و ≤24h باشد."""
    now = now or datetime.now(timezone.utc)
    required = ("fx_source_id", "fx_timestamp_utc", "fx_rate_usd_to_aud", "fx_hash", "owner_pin_id")
    missing = [k for k in required if not str(rec.get(k) or "").strip()]
    if missing:
        return {"pass": False, "reason": f"missing:{','.join(missing)}", "paid_fallback": "BLOCKED"}
    try:
        rate = float(rec["fx_rate_usd_to_aud"])
        assert rate > 0
    except Exception:
        return {"pass": False, "reason": "malformed-rate", "paid_fallback": "BLOCKED"}
    if fx_canonical_hash(rec) != str(rec["fx_hash"]):
        return {"pass": False, "reason": "hash-mismatch", "paid_fallback": "BLOCKED"}
    try:
        ts = datetime.fromisoformat(str(rec["fx_timestamp_utc"]).replace("Z", "+00:00"))
    except Exception:
        return {"pass": False, "reason": "malformed-timestamp", "paid_fallback": "BLOCKED"}
    if now - ts > timedelta(hours=24):
        return {"pass": False, "reason": "expired(>24h)", "paid_fallback": "BLOCKED"}
    return {"pass": True, "rate": rate, "source": rec["fx_source_id"],
            "owner_pin_id": rec["owner_pin_id"], "paid_fallback": "ALLOWED"}


def load_fx(path: Path | None = None) -> dict:
    p = Path(path or (_HERE / "FX-RECORD.json"))
    if not p.exists():
        return {"pass": False, "reason": "no-fx-record(owner-pending)", "paid_fallback": "BLOCKED"}
    return validate_fx(json.loads(p.read_text(encoding="utf-8")))


# ── ۲) داور کور + A/B تصادفی ─────────────────────────────────────────────
JUDGE_PROMPT = ("Which proposal is more specific and testable for the question below? "
                "Respond with ONLY this JSON, nothing else: "
                '{"verdict":"A","rationale_hash":"<any short token or hash of your reason>"} '
                "Use A or B (TIE only if truly equal).\n"
                "Question: {q}\nA: {a}\nB: {b}")

# D-B/V3 (DEEPSEEK-AUTOMATIC-ROUTING-01): پیلودِ حداقلیِ تک‌کلیدی — دقیقاً {"choice":"A"|"B"|"TIE"}
# V3.1: دستورِ فرمت در انتها (اثرِ recency) + مثالِ صریح — چون حالتِ شکستِ مشاهده‌شده
# خروجیِ نثریِ ۷۰۰کاراکتری بود، نه حرفِ لخت.
JUDGE_PROMPT_V3 = ("Question: {q}\nA: {a}\nB: {b}\n\n"
                   "Which proposal (A or B) is more specific and testable? TIE only if truly equal.\n"
                   "Answer with ONLY one JSON object and absolutely nothing else. "
                   'Example of a valid answer: {"choice":"A"}')


def blind_pair(baseline: str, conditioned: str, *, seed: int, template: str | None = None) -> dict:
    """جایتصادفیِ قطعی با seed؛ خروجی: prompt داور + نگاشت موقعیت‌ها.
    template: JUDGE_PROMPT (پیش‌فرض/V2) یا JUDGE_PROMPT_V3 (D-B/V3)."""
    cond_is_a = random.Random(seed).random() < 0.5
    A, B = (conditioned, baseline) if cond_is_a else (baseline, conditioned)
    tpl = template or JUDGE_PROMPT
    return {"cond_position": "A" if cond_is_a else "B",
            "judge_prompt": (tpl.replace("{q}", "{TASK}")
                             .replace("{a}", A[:200]).replace("{b}", B[:200])),
            "baseline_sha": hashlib.sha256(baseline.encode("utf-8", "replace")).hexdigest(),
            "conditioned_sha": hashlib.sha256(conditioned.encode("utf-8", "replace")).hexdigest()}


def judge_contract(text: str, cond_position: str, *, judge_provider: str = "",
                  judge_model: str = "", trace_id: str = "") -> dict:
    """D-B: قرارداد ساخت‌یافته — A|B|TIE|UNREADABLE؛ ناخوانا هرگز برنده حدس نمی‌زند."""
    import hashlib as _h
    t = str(text or "").strip().upper()
    first = t.split()[0].strip(".,:")[:4] if t.split() else ""
    verdict = first if first in ("A", "B", "TIE") else "UNREADABLE"
    winner = None
    if verdict == "A": winner = "conditioned" if cond_position == "A" else "baseline"
    elif verdict == "B": winner = "conditioned" if cond_position == "B" else "baseline"
    return {"verdict": verdict, "winner": winner,
            "rationale_hash": _h.sha256(str(text).encode("utf-8", "replace")).hexdigest(),
            "judge_provider": judge_provider, "judge_model": judge_model,
            "trace_id": trace_id, "void": verdict == "UNREADABLE"}


def judge_json(text: str, cond_position: str, *, judge_provider: str = "",
               judge_model: str = "", trace_id: str = "") -> dict:
    """D-B/V2: قرارداد JSON سخت‌گیرانه — فقط اسکیمای دقیق
    {"verdict":"A|B|TIE","rationale_hash":"<64hex>"}؛ هر چیز دیگر = UNREADABLE/VOID."""
    import hashlib as _h
    import json as _j
    import re as _re
    raw = str(text or "")
    m = _re.search(r"\{[^{}]*\}", raw)
    verdict, rh = None, None
    if m:
        try:
            obj = _j.loads(m.group(0))
            if (isinstance(obj, dict) and set(obj) == {"verdict", "rationale_hash"}
                    and str(obj["verdict"]) in ("A", "B", "TIE")
                    and 0 < len(str(obj["rationale_hash"]).strip()) <= 200):
                verdict, rh = str(obj["verdict"]), str(obj["rationale_hash"]).lower()
        except Exception:  # noqa: BLE001
            verdict = None
    winner = None
    if verdict == "A": winner = "conditioned" if cond_position == "A" else "baseline"
    elif verdict == "B": winner = "conditioned" if cond_position == "B" else "baseline"
    ok = verdict is not None
    return {"verdict": verdict or "UNREADABLE", "winner": winner,
            "rationale_hash": rh or "",
            "raw_output_sha256": _h.sha256(raw.encode("utf-8", "replace")).hexdigest(),
            "judge_provider": judge_provider, "judge_model": judge_model,
            "trace_id": trace_id, "schema": "judge-json/1", "void": not ok}


def judge_choice_v3(text: str, cond_position: str, *, judge_provider: str = "",
                    judge_model: str = "", trace_id: str = "") -> dict:
    """D-B/V3 (DEEPSEEK-AUTOMATIC-ROUTING-01): پذیرشِ فقطِ اسکیمای حداقلی
    {"choice":"A"|"B"|"TIE"} — تک‌کلید، بدون rationale؛ هر چیز دیگر = UNREADABLE/VOID.
    ناخوانا هرگز برنده حدس نمی‌زند؛ winner فقط از نگاشت موقعیت می‌آید."""
    import hashlib as _h
    import json as _j
    import re as _re
    raw = str(text or "")
    m = _re.search(r"\{[^{}]*\}", raw)
    verdict = None
    if m:
        try:
            obj = _j.loads(m.group(0))
            if (isinstance(obj, dict) and set(obj) == {"choice"}
                    and str(obj["choice"]) in ("A", "B", "TIE")):
                verdict = str(obj["choice"])
        except Exception:  # noqa: BLE001
            verdict = None
    winner = None
    if verdict == "A": winner = "conditioned" if cond_position == "A" else "baseline"
    elif verdict == "B": winner = "conditioned" if cond_position == "B" else "baseline"
    return {"verdict": verdict or "UNREADABLE", "winner": winner,
            "raw_output_sha256": _h.sha256(raw.encode("utf-8", "replace")).hexdigest(),
            "judge_provider": judge_provider, "judge_model": judge_model,
            "trace_id": trace_id, "schema": "judge-choice-v3/1", "void": verdict is None}


def parse_judge(text: str, cond_position: str) -> str | None:
    """خروجی داور → 'conditioned' | 'baseline' | None(خوانا نیست)."""
    t = str(text or "").strip().upper()
    if t.startswith("A"):
        return "conditioned" if cond_position == "A" else "baseline"
    if t.startswith("B"):
        return "conditioned" if cond_position == "B" else "baseline"
    return None


# ── ۳) واجدیت رکوردها ───────────────────────────────────────────────────
REQUIRED_ROW = ("provenance_json", "created_at", "confidence", "valid_to")


def row_eligible(row: dict) -> tuple[bool, str]:
    for k in REQUIRED_ROW:
        v = row.get(k)
        if v is None or str(v).strip() == "":
            return False, f"missing:{k}"
    prov = str(row.get("provenance_json") or "")
    if "SYSTEM_DETERMINISTIC_RULE" in prov:
        # confidence سیستمی هرگز به‌عنوان confidence مدل امتیاز نمی‌خورد (حکم مالک)
        return True, "system-rule-excluded-from-llm-calibration"
    return True, "llm-confidence"


def coverage_report(rows: list[dict]) -> dict:
    elig = [row_eligible(r) for r in rows]
    ok = [e for e, _ in elig if e]
    return {"n": len(rows), "eligible": len(ok),
            "ineligible": len(rows) - len(ok),
            "llm_confidence_rows": sum(1 for _, w in elig if w == "llm-confidence"),
            "coverage_pct": round(100.0 * len(ok) / len(rows), 2) if rows else None,
            "rule": "eligible records must be 100%; ineligible are mechanically excluded"}


# ── smoke receipt (سنتزی، بدون شبکه) ────────────────────────────────────
def synthetic_smoke_receipt() -> dict:
    return {"schema": "live4-smoke/1", "kind": "SYNTHETIC_PREFLIGHT_SMOKE",
            "fx": load_fx(), "harness": SCHEMA,
            "note": "non-live preflight only; no provider call"}


# V4 (consent §1 + V4-FREEZE-PREP): fallback تک‌توکنی داور — پارسر جدا از JSON
SINGLE_TOKEN = '\n\nANSWER NOW with exactly ONE character: A or B or T. If truly equal, T. Nothing else.'

def parse_single_token(text: str, cond_position: str) -> dict:
    t = str(text or "").strip().upper()[:3]
    v = {"A": "A", "B": "B", "T": "TIE", "TI": "TIE", "TIE": "TIE"}.get(t)
    winner = None
    if v == "A": winner = "conditioned" if cond_position == "A" else "baseline"
    elif v == "B": winner = "conditioned" if cond_position == "B" else "baseline"
    return {"verdict": v or "UNREADABLE", "winner": winner,
            "schema": "judge-single-token/1", "void": v is None}
