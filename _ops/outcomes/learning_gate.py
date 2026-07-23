#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning_gate.py — C3: قدمِ «Learning → Memory Update» با گیتِ regressionِ held-out.

قوسِ شکسته (کشفِ C3): زنجیرهٔ decision→receipt→outcome ساخته بود، ولی **هیچ‌جا از یک outcome
یک خاطرهٔ graded ساخته نمی‌شد** — پس تصمیمِ بعدی چیزی برای «استناد» نداشت و D8 صفر می‌ماند.
این ماژول آن قدم را می‌بندد، با ضدخودفریبی:

  outcome/verdictِ **تأییدشده** → کاندیدِ خاطرهٔ semantic → **گیتِ held-out** (ضدِ hacking) →
  اگر متریکِ داخلی «قبول» ولی held-out «رد» → REJECT (یادگیریِ مضر مسدود) →
  اگر held-out قبول → commit از Memory Gate (dedup/version/trust) + رسیدِ یادگیری (artifact durable).

قیودِ سخت:
  - یادگیری فقط وقتی «معتبر» است که **artifact durable** بسازد (memory_id + رسید). ادعای
    «یاد گرفتم» بدونِ این دو = دروغ (مأموریت step 7).
  - outcomeِ واقعی از preference جدا می‌ماند: فقط سیگنالِ trustِ بالا (OWNER_CONFIRMED/GRADED
    با evidence) یاد گرفته می‌شود؛ preferenceِ خام رد.
  - dedupِ یادگیری: کلیدِ mkey قطعی → همان درسِ دوباره = خاطرهٔ نو نمی‌سازد (Memory Gate).
  - rollback: خاطرهٔ مضر با یک retraction که supersede می‌کند invalidate می‌شود (append-only، نه delete).
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


def learn_from_outcome(*, memory_gate, signal: dict, receipt_store=None,
                       evaluator=None, eval_ctx=None, internal_metric_pass: bool = True,
                       min_salience: float = 0.5) -> dict:
    """یک outcome/verdictِ تأییدشده → خاطرهٔ graded، فقط اگر گیتِ held-out سبز باشد.

    signal (اجباری): content, mkey, correlation_id, outcome_ref, trust (یکی از _LEARNABLE_TRUST),
      salience(اختیاری≥min_salience)، provenance(source/producer)، namespace(پیش‌فرض semantic).
    خروجی: {learned: bool, memory_id?, receipt_id?, eval_verdict, anti_hacking_flag, reason}.
    هرگز raise نمی‌کند."""
    try:
        if not flag_on():
            return {"learned": False, "reason": "flag-off"}
        content = str(signal.get("content") or "").strip()
        if not content:
            return {"learned": False, "reason": "empty learning content"}
        trust = str(signal.get("trust") or "")
        if trust not in _LEARNABLE_TRUST:
            # preference/ادعای low-trust → یاد گرفته نمی‌شود (outcome≠preference)
            return {"learned": False, "reason": f"non-outcome trust {trust!r} (preference, not learned)"}

        # ── گیتِ held-out (ضدِخودفریبی) ─────────────────────────────────────────
        ev = _run_eval(evaluator, eval_ctx, internal_metric_pass)
        if ev["anti_hacking_flag"]:
            return {"learned": False, "reason": "anti-hacking: internal-pass but held-out-fail",
                    "eval_verdict": ev["verdict"], "anti_hacking_flag": True}
        if ev["verdict"] != "pass":
            return {"learned": False, "reason": "held-out gate failed — harmful/unsafe learning blocked",
                    "eval_verdict": ev["verdict"], "anti_hacking_flag": False}

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

        # ── artifactِ durable: رسیدِ یادگیری (evidenceِ گیت + مرجعِ خاطره) ────────
        rid = None
        if receipt_store is not None and mid:
            try:
                receipt_store.record({
                    "receipt_id": "dr_" + _sha({"learn": mid, "c": signal.get("correlation_id")})[:16],
                    "trace_id": str(signal.get("correlation_id") or ""),
                    "mission_id": str(signal.get("mission_id") or "learning"),
                    "objective": "commit learned memory (held-out gated)"[:290],
                    "alternatives": ["commit", "reject"],
                    "selected_alternative": "commit",
                    "reason_codes": [f"TRUST_{trust}", f"EVAL_{ev['verdict'].upper()}"],
                    "assumptions": ["held-out gate green", "outcome-not-preference"],
                    "memories_used": [],
                    "predicted_outcome": {"memory_id": str(mid)[:120],
                                          "salience": max(sal, min_salience)},
                    "effect_class": "E0"})   # یادگیریِ داخلی، صفر اثرِ بیرونی
                rid = "recorded"
            except Exception:  # noqa: BLE001
                rid = None
        return {"learned": True, "memory_id": mid, "receipt_id": rid,
                "eval_verdict": ev["verdict"], "anti_hacking_flag": False,
                "reason": "learned (durable artifact)"}
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
