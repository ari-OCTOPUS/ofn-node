#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning_gate.py — C3: قدمِ «Learning → Memory Update»، outcome-bound و held-out-gated.

قوسِ شکسته (کشفِ C3): زنجیرهٔ decision→receipt→outcome ساخته بود، ولی **هیچ‌جا از یک outcome
یک خاطرهٔ graded ساخته نمی‌شد** — پس تصمیمِ بعدی چیزی برای «استناد» نداشت و D8 صفر می‌ماند.
این ماژول آن قدم را می‌بندد.

**دو گاردِ ضدخودفریبی (صادقانه دربارهٔ حدودشان):**
  ۱) **outcome-binding (گاردِ محتوایی):** trustِ ادعایی (OWNER_CONFIRMED/…) فقط وقتی پذیرفته
     می‌شود که `outcome_ref` به یک outcomeِ **واقعیِ durable** در outcomes.db با event_typeِ
     سازگار اشاره کند (verify_outcome). بدونِ آن، trust فقط یک رشتهٔ جعل‌پذیر بود (red-team P1).
     → «یاد نمی‌گیریم مگر یک outcomeِ ثبت‌شده پشتش باشد» = گاردِ اصلیِ preference≠outcome.
  ۲) **held-out (گاردِ ایمنیِ سیستمی، نه اوراکلِ محتوا):** پیش از commit، اگر سیستم در پنجرهٔ
     regressionِ ایمنی باشد (canaryهای ثابت قرمز / زنجیرهٔ ledger شکسته / anti-hacking)، یادگیری
     مسدود می‌شود. **این گیت صحتِ *محتوایِ* درس را نمی‌سنجد** (نوشتنِ خاطره روی آن تست‌ها اثر
     ندارد)؛ circuit-breaker است: «وقتی سیستم ناسالم است یاد نگیر». سنجشِ صحتِ پیش‌بینیِ هر
     خاطره روی held-set برچسب‌دار = کارِ آینده (dataset لازم دارد).

قیودِ سخت:
  - یادگیری فقط با **artifact durable** (memory_id + رسید) معتبر است (step 7).
  - preference≠outcome: فقط trustِ بالا **که با outcomeِ verify‌شده پشتیبانی شده** یاد گرفته می‌شود.
  - dedup (Memory Gate) · rollback با supersede که TTL را هم کوتاه می‌کند (red-team P1 fix).
  - صفر شبکه/پول/effector. fail-soft.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "memory")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_MEMORY_GATE"        # یادگیری پشتِ همان فلگِ Memory Gate (نویسندهٔ خاطره)
# فقط این trustها «outcomeِ واقعی»اند؛ بقیه preference/ادعا → یاد گرفته نمی‌شوند.
_LEARNABLE_TRUST = ("OWNER_CONFIRMED", "DETERMINISTIC", "GRADED")


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def fast_ledger_eval(*, internal_metric_pass: bool = True, **kw) -> dict:
    """گیتِ سبکِ hot-path (مسیرِ زندهٔ رأیِ مالک): فقط زنجیرهٔ hash لجر را verify می‌کند
    (~۱ ثانیه)، نه سوئیتِ ۵-تستیِ subprocess (~۳۰s که pollerِ تلگرام را بلاک می‌کند).
    سوئیتِ کاملِ canary جای دیگر periodically اجرا می‌شود. content-relevant به ایمنی:
    اگر لجر شکسته باشد یاد نمی‌گیریم."""
    try:
        import held_out_evaluator as _he  # noqa: WPS433
        ch = _he.verify_ledger_chain()
        valid = ch.get("valid")
        return {"overall_verdict": "pass" if valid in (True, None) else "fail",
                "anti_hacking_flag": bool(internal_metric_pass and valid is False)}
    except Exception:  # noqa: BLE001 — fail-closed
        return {"overall_verdict": "fail", "anti_hacking_flag": False}


def _retract(memory_gate, ns, mkey, content, memory_id, reason) -> None:
    """compensating retraction: خاطرهٔ admittedِ بی‌رسید را supersede/invalidate کن (append-only)."""
    try:
        if memory_id:
            memory_gate.submit({"namespace": ns, "mkey": mkey,
                                "content": f"[RETRACTED:{str(reason)[:24]}] {content}"[:400],
                                "salience": 0.9, "confidence": 0.9, "privacy": "scrubbed",
                                "source": "learning_gate", "producer": "retract",
                                "supersedes": memory_id})
    except Exception:  # noqa: BLE001
        pass


def _run_eval(evaluator, eval_ctx, internal_metric_pass) -> dict:
    """گیتِ held-out. evaluator تزریق‌پذیر است (تولید: held_out_evaluator.evaluate_held_out؛
    تست: stub سریع). خروجیِ نرمال: {verdict, anti_hacking_flag, raw}."""
    try:
        if evaluator is None:
            import held_out_evaluator as _he  # noqa: WPS433
            raw = _he.evaluate_held_out(internal_metric_pass=internal_metric_pass,
                                        **(eval_ctx or {}))
        else:
            raw = evaluator(internal_metric_pass=internal_metric_pass, **(eval_ctx or {}))
        return {"verdict": raw.get("overall_verdict", "fail"),
                "anti_hacking_flag": bool(raw.get("anti_hacking_flag")), "raw": raw}
    except Exception as e:  # noqa: BLE001 — گیت هرگز خودش را نمی‌کشد؛ خطا = fail-closed
        return {"verdict": "fail", "anti_hacking_flag": False,
                "raw": {"error": type(e).__name__}}


def _verify_outcome(outcome_store, outcome_ref: str, trust: str) -> "tuple[bool, str]":
    """گاردِ محتوایی (red-team P1 fix): outcome_refِ ادعایی باید یک ردیفِ **واقعیِ** outcomes.db
    باشد و event_typeاش با trust سازگار. OWNER_CONFIRMED → فقط accepted-measurement. بدونِ این،
    trust یک رشتهٔ جعل‌پذیر است. fail-closed."""
    if outcome_store is None:
        return (False, "no-outcome-store")   # نمی‌توان verify کرد → یاد نگیر (fail-closed)
    ref = str(outcome_ref or "").strip()
    if not ref:
        return (False, "no-outcome-ref")
    try:
        row = outcome_store._conn.execute(   # noqa: SLF001 — read-only verify
            "SELECT event_type FROM outcomes WHERE idempotency_key=?", (ref,)).fetchone()
    except Exception:  # noqa: BLE001
        return (False, "outcome-query-error")
    if not row:
        return (False, "outcome-ref not found (forged trust)")
    et = str(row[0] or "")
    ok = (et == "accepted-measurement") if trust == "OWNER_CONFIRMED" else (et in (
        "accepted-measurement", "delivered", "outcome-recorded", "decided"))
    return (ok, f"outcome event_type={et}")


def learn_from_outcome(*, memory_gate, signal: dict, receipt_store=None, outcome_store=None,
                       evaluator=None, eval_ctx=None, internal_metric_pass: bool = True,
                       min_salience: float = 0.5) -> dict:
    """یک outcomeِ verify‌شده → خاطرهٔ graded، پشتِ دو گارد (outcome-binding + held-out).

    signal (اجباری): content, mkey, correlation_id, **outcome_ref** (باید در outcomes.db باشد),
      trust (یکی از _LEARNABLE_TRUST)، salience، provenance، namespace(پیش‌فرض semantic).
    outcome_store: برای بایندِ trust به outcomeِ واقعی (اگر None → fail-closed، یاد نمی‌گیرد).
    خروجی: {learned, memory_id?, receipt_id?, eval_verdict, anti_hacking_flag, reason}. هرگز raise."""
    try:
        if not flag_on():
            return {"learned": False, "reason": "flag-off"}
        content = str(signal.get("content") or "").strip()
        if not content:
            return {"learned": False, "reason": "empty learning content"}
        trust = str(signal.get("trust") or "")
        if trust not in _LEARNABLE_TRUST:
            return {"learned": False, "reason": f"non-outcome trust {trust!r} (preference, not learned)"}
        # ── گاردِ ۱: outcome-binding (trust باید با یک outcomeِ واقعی پشتیبانی شود) ──
        ok, why = _verify_outcome(outcome_store, signal.get("outcome_ref"), trust)
        if not ok:
            return {"learned": False, "reason": f"unverified outcome — {why} (trust not bound to reality)"}

        # ── گیتِ held-out (ضدِخودفریبی) ─────────────────────────────────────────
        ev = _run_eval(evaluator, eval_ctx, internal_metric_pass)
        if ev["anti_hacking_flag"]:
            return {"learned": False, "reason": "anti-hacking: internal-pass but held-out-fail",
                    "eval_verdict": ev["verdict"], "anti_hacking_flag": True}
        if ev["verdict"] != "pass":
            return {"learned": False, "reason": "held-out gate failed — harmful/unsafe learning blocked",
                    "eval_verdict": ev["verdict"], "anti_hacking_flag": False}

        # ── C7-S2 (audit #3): بدونِ receipt_store اصلاً خاطره نمی‌سازیم (no admission without receipt)
        if receipt_store is None:
            return {"learned": False, "memory_id": None, "receipt_id": None,
                    "eval_verdict": ev["verdict"],
                    "reason": "receipt_store required — no admitted memory without a receipt"}
        # ── commit خاطره از Memory Gate (dedup/version/trust یک‌جا) ──────────────
        ns = str(signal.get("namespace") or "semantic")
        sal = signal.get("salience")
        try:
            sal = float(sal)
        except (TypeError, ValueError):
            sal = min_salience
        candidate = {"namespace": ns, "mkey": signal.get("mkey"),
                     "content": content, "salience": max(sal, min_salience),
                     "confidence": signal.get("confidence", 0.7),
                     "privacy": signal.get("privacy", "scrubbed"),
                     "source": signal.get("source", "learning_gate"),
                     "producer": signal.get("producer", "learning_gate"),
                     "supersedes": signal.get("supersedes")}
        if signal.get("grade_receipt"):
            candidate["grade_receipt"] = signal["grade_receipt"]
        res = memory_gate.submit(candidate)
        if res.get("verb") == "commit":
            mid = res.get("memory_id")
        elif res.get("verb") == "skip":
            # dedup: همان درس قبلاً یاد گرفته شده → یادگیریِ تکراری صفر (نه artifactِ نو)
            return {"learned": False, "reason": "duplicate learning (already learned)",
                    "eval_verdict": ev["verdict"], "memory_id": None, "dedup": True}
        else:
            return {"learned": False, "reason": f"gate {res.get('verb')}: {res.get('reason')}",
                    "eval_verdict": ev["verdict"]}

        # ── C7-S2 (audit finding #3): memory + receipt **اتمیک** — هیچ خاطرهٔ admittedِ بی‌رسید.
        # ناوردی: learned=True ⟺ هم memory_id هم receipt_idِ واقعی. اگر رسید ننشیند → خاطره
        # retract (supersede→invalidate) و learned=False (no uncited admission).
        rid = None
        try:
            rid = receipt_store.record({
                "receipt_id": "dr_" + _sha({"learn": mid, "c": signal.get("correlation_id")})[:16],
                "trace_id": str(signal.get("correlation_id") or ""),
                "mission_id": str(signal.get("mission_id") or "learning"),
                "objective": "commit learned memory (held-out gated)"[:290],
                "alternatives": ["commit", "reject"], "selected_alternative": "commit",
                "reason_codes": [f"TRUST_{trust}", f"EVAL_{ev['verdict'].upper()}"],
                "assumptions": ["held-out gate green", "outcome-not-preference"],
                "memories_used": [],
                "predicted_outcome": {"memory_id": str(mid)[:120], "salience": max(sal, min_salience)},
                "effect_class": "E0"})   # یادگیریِ داخلی، صفر اثرِ بیرونی
        except Exception:  # noqa: BLE001
            rid = None
        if not rid:
            # رسید نساخت → خاطرهٔ بی‌رسید نمی‌گذاریم: compensating retraction
            _retract(memory_gate, ns, signal.get("mkey"), content, mid, "receipt-failed")
            return {"learned": False, "memory_id": None, "receipt_id": None,
                    "eval_verdict": ev["verdict"],
                    "reason": "receipt write failed — memory retracted (no uncited admission)"}
        return {"learned": True, "memory_id": mid, "receipt_id": rid,
                "eval_verdict": ev["verdict"], "anti_hacking_flag": False,
                "reason": "learned (durable artifact: memory + receipt)"}
    except Exception as e:  # noqa: BLE001 — یادگیری هرگز مسیرِ اصلی را نمی‌کشد
        return {"learned": False, "reason": f"failsoft:{type(e).__name__}"}


def rollback_learning(*, memory_gate, memory_id: str, content: str,
                      mkey: str, namespace: str = "semantic", reason: str = "regression") -> dict:
    """rollbackِ یک خاطرهٔ مضر (append-only): یک retraction که خاطرهٔ قبلی را supersede
    (invalidate: valid_to=now) می‌کند — هرگز delete فیزیکی. خروجی {rolled_back, memory_id?}."""
    try:
        if not flag_on():
            return {"rolled_back": False, "reason": "flag-off"}
        res = memory_gate.submit({
            "namespace": namespace, "mkey": mkey,
            "content": f"[RETRACTED:{reason[:32]}] {content}"[:400],
            "salience": 0.9, "confidence": 0.9, "privacy": "scrubbed",
            "source": "learning_gate", "producer": "rollback",
            "supersedes": memory_id})
        return {"rolled_back": res.get("verb") == "commit",
                "retraction_id": res.get("memory_id"), "superseded": memory_id,
                "reason": res.get("reason")}
    except Exception as e:  # noqa: BLE001
        return {"rolled_back": False, "reason": f"failsoft:{type(e).__name__}"}
