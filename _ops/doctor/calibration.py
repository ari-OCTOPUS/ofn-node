#!/usr/bin/env python3
"""calibration.py — Doctor feedback loop + attention-budget (ضدِ agreement-spiral).

دو سازوکار که دکتر را آرام‌تر و هدفمندتر می‌کنند، نه پرحرف‌تر:

۱. **Feedback loop (verdict_history):** هر RFC را با verdict نهایی (merged/rejected/ignored)
   و اثرِ پایین‌دست (آیا metric بهتر شد؟) ثبت می‌کند. mine() از این می‌آموزد:
   «RFCهای گلوگاهِ X سه‌بار رد شده → دیگر پیشنهاد نده» یا «Y merge شد و σ بهتر شد».

۲. **Attention-budget (confidence tax):** هرچه RFCهای pending انسان بیشتر باشند، میلهٔ
   افزودنِ RFC جدید بالاتر می‌رود. این throttleِ خودِ دکتر روی خودش = anti-self-preservation.

هر دو در chrono.db ذخیره می‌شوند (اگر db وصل باشد) یا در memory (تست). additive؛ stdlib-only.
⚠ بدونِ wiring واقعی، این فقط مکانیزم است — در runtime دادهٔ verdict واقعی نمی‌آید تا یاد بگیرد.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

# آستانه‌های attention-budget
PENDING_SOFT_CAP = 3     # تا ۳ RFC pending → عادی
PENDING_HARD_CAP = 5     # ۵+ pending → دکتر فقط critical می‌دهد
REJECT_FORGET_N = 3      # ۳ reject روی همان bottleneck → دیگر پیشنهاد نده


def record_verdict(db, rfc_id: str, verdict: str, bottleneck_key: str = "",
                   effect: dict | None = None) -> bool:
    """ثبتِ verdict یک RFC. verdict ∈ {merged, rejected, ignored}.
    bottleneck_key = کلیدِ گلوگاه (مثلاً 'error-rate-high') برای فیلترِ آینده.
    effect = آیا metric بهتر شد؟ {before, after}.
    در chrono.db (جدولِ duration_marker، additive) یا memory dict."""
    if db is None:
        return False
    try:
        eid = f"verdict-{rfc_id[:16]}"
        payload = {"rfc_id": rfc_id, "verdict": verdict,
                   "bottleneck_key": bottleneck_key,
                   "effect": effect or {}, "ts": int(time.time() * 1000)}
        db.ex(
            "INSERT OR REPLACE INTO duration_marker(event_id, hlc_phys, hlc_logical, "
            "wall_ts, label) VALUES (?,?,?,?,?)",
            (eid, 0, 0, int(time.time() * 1000), json.dumps(payload, ensure_ascii=False)))
        return True
    except Exception:  # noqa: BLE001
        return False


def get_verdict_history(db, bottleneck_key: str | None = None) -> list[dict]:
    """تاریخچهٔ verdict‌ها از chrono.db. فیلتر بر bottleneck_key."""
    if db is None:
        return []
    try:
        rows = db.q("SELECT label FROM duration_marker WHERE event_id LIKE 'verdict-%'")
        out = []
        for (label,) in rows:
            try:
                d = json.loads(label)
                if bottleneck_key and d.get("bottleneck_key") != bottleneck_key:
                    continue
                out.append(d)
            except (json.JSONDecodeError, TypeError):
                continue
        return out
    except Exception:  # noqa: BLE001
        return []


def should_skip_bottleneck(db, bottleneck_key: str) -> tuple[bool, str]:
    """آیا این bottleneck قبلاً به اندازهٔ کافی رد شده؟ (ضدِ تکرارِ نویز).
    خروجی: (skip, reason). REJECT_FORGET_N reject → skip."""
    history = get_verdict_history(db, bottleneck_key)
    rejects = sum(1 for h in history if h.get("verdict") == "rejected")
    if rejects >= REJECT_FORGET_N:
        return True, f"already rejected {rejects}× on '{bottleneck_key}' — skip (ضدِ نویز)"
    return False, ""


def attention_gate(db, pending_count: int, severity: str) -> tuple[bool, str]:
    """attention-budget: آیا دکتر اجازه دارد RFC جدید بدهد؟
    اگر pending زیاد باشد، فقط critical می‌گذرد.
    خروجی: (allow, reason)."""
    if pending_count >= PENDING_HARD_CAP and severity != "critical":
        return False, (f"attention-budget: {pending_count} pending ≥ {PENDING_HARD_CAP} "
                       f"hard-cap → فقط critical مجاز (severity={severity})")
    if pending_count >= PENDING_SOFT_CAP and severity not in ("critical", "high"):
        return False, (f"attention-budget: {pending_count} pending ≥ {PENDING_SOFT_CAP} "
                       f"soft-cap → فقط critical/high مجاز (severity={severity})")
    return True, ""


def count_pending_rfc(doctor) -> int:
    """تعدادِ RFCهای pending در registryِ دکتر."""
    try:
        return sum(1 for r in doctor._rfcs.values()
                   if r.status in ("drafted", "sandboxed", "submitted", "submitted-no-channel"))
    except Exception:  # noqa: BLE001
        return 0



def draft_epistemic_uncertainty(snapshot: dict | None = None) -> dict | None:
    """Smallest doctor->epistemics wire (ADR-039 C1 + claim draft).

    Loads fail-closed policy (C1) and builds a propose-only claim via
    claim_builder.draft_from_telemetry. Never executes tests, never sets
    may_execute True. Fail-soft: any import/policy error -> None.
    """
    try:
        import sys as _sys
        _ops = str(Path(__file__).resolve().parents[1])
        if _ops not in _sys.path:
            _sys.path.insert(0, _ops)
        from epistemics.policy import load_policy
        from epistemics.claim_builder import draft_from_telemetry, is_runnable_draft
        cfg = load_policy()
        snap = dict(snapshot or {})
        if not any(k in snap for k in ("coherence", "discovery_rate",
                                       "convergence", "pain")):
            snap.setdefault("coherence", 0.5)
        draft = draft_from_telemetry(snap)
        if not draft or not is_runnable_draft(draft):
            return None
        chain_ok, chain_n = None, None
        try:
            from epistemics.receipt_store import ReceiptStore
            chain = ReceiptStore().verify()
            chain_ok, chain_n = bool(chain.ok), int(chain.n_records)
        except Exception:  # noqa: BLE001
            pass
        return {
            "wired": True,
            "policy_schema_version": cfg.schema_version,
            "max_authority": cfg.max_authority,
            "sandbox_profile": cfg.sandbox_profile,
            "default_off": cfg.default_off,
            "may_execute": False,
            "receipt_chain_ok": chain_ok,
            "receipt_chain_n": chain_n,
            "draft": draft,
        }
    except Exception:  # noqa: BLE001
        return None


def effective_mine(doctor, trace: dict | None = None,
                   db=None) -> dict | None:
    """mine() + calibration: bottleneck پیدا کن، ولی skip کن اگر قبلاً رد شده،
    و attention-gate کن اگر pending زیاد است. خروجی = mine() یا None (با reason در dict).
    این wrapper است — mine() خودش دست‌نخورده."""
    bn = doctor.mine(trace=trace)
    if bn is None:
        return None
    # calibration ۱: skip bottleneck‌های رد‌شده (chrono.db — شمارشی)
    key = (bn.get("evidence") or {}).get("key", "")
    if key and db is not None:
        skip, reason = should_skip_bottleneck(db, key)
        if skip:
            return None   # سکوت — نویز نده
    # calibration ۱b (۲۰۲۶-۰۸-۰۸): skip bottleneck‌هایی که RULE ِ فعالِ انسانی
    # دارند (rules_store — declare-only، مکملِ نه رقیبِ should_skip_bottleneck).
    # should_skip_bottleneck می‌گوید «۳بار رد شد»؛ rules_store می‌گوید «مالک صریح
    # گفت هرگز دوباره». دو سازوکارِ متفاوت، هر دو می‌بندند. پشتِ OCTOPUS_WIRE_RULES
    # (همان فلگِ record_occurrence در doctor.py) — خاموش = no-op، صفر تغییرِ رفتار.
    if key and os.environ.get("OCTOPUS_WIRE_RULES") == "1":
        try:
            import sys as _rs_sys
            _here = str(Path(__file__).resolve().parent)
            if _here not in _rs_sys.path:
                _rs_sys.path.insert(0, _here)
            import rules_store as _rs
            _cls = _rs._norm_class(key)
            if any(_rs._norm_class(r.get("error_class", "")) == _cls
                   for r in _rs.list_active()):
                return None   # سکوت — مالک صریح هرگزگفته
        except Exception:  # noqa: BLE001 — rules_store نباید mine را بکشد
            pass
    # calibration ۲: attention-budget
    pending = count_pending_rfc(doctor)
    allow, reason = attention_gate(db, pending, bn.get("severity", "high"))
    if not allow:
        return {"bottleneck": bn["bottleneck"], "evidence": bn.get("evidence", {}),
                "severity": bn.get("severity", "high"),
                "_suppressed_by_attention_budget": reason}
    try:
        ev = bn.get("evidence") or {}
        score = ev.get("score", ev.get("value", 0.5))
        epi = draft_epistemic_uncertainty({
            "coherence": float(score) if isinstance(score, (int, float)) else 0.5,
            "bottleneck": bn.get("bottleneck"),
        })
        if epi is not None:
            bn = dict(bn)
            bn["_epistemic"] = epi
    except Exception:  # noqa: BLE001
        pass
    return bn
