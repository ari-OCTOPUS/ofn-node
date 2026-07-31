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
_OWNER_ATTEST_KEY = "owner_verdict_raw"
_OWNER_ATTEST_VERDICT = "measurement"
_UNATTESTED_SOURCE = "unattested_owner_claim"


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


def _owner_attested(row) -> bool:
    """فقط ردیفِ واقعیِ رأی مالک گواهی می‌دهد: event_type=accepted-measurement،
    verdict=measurement، و payload دارای owner_verdict_raw غیرخالی. هرگز رشتهٔ source."""
    try:
        et = str(row[0] or "") if row else ""
        verdict = str(row[1] or "") if row and len(row) > 1 else ""
        payload = {}
        if row and len(row) > 2:
            try:
                payload = json.loads(row[2] or "{}")
            except Exception:
                payload = {}
        return (et == "accepted-measurement" and verdict == _OWNER_ATTEST_VERDICT
                and bool(str(payload.get(_OWNER_ATTEST_KEY) or "").strip()))
    except Exception:  # noqa: BLE001
        return False


def _verify_outcome(outcome_store, outcome_ref: str, trust: str) -> "tuple[bool, bool, str]":
    """گاردِ محتوایی (red-team P1 fix): outcome_refِ ادعایی باید یک ردیفِ **واقعیِ** outcomes.db
    باشد و event_typeاش با trust سازگار. خروجی: (ok, owner_attested, why). fail-closed."""
    if outcome_store is None:
        return (False, False, "no-outcome-store")
    ref = str(outcome_ref or "").strip()
    if not ref:
        return (False, False, "no-outcome-ref")
    try:
        row = outcome_store._conn.execute(   # noqa: SLF001 — read-only verify
            "SELECT event_type, verdict, payload_json FROM outcomes WHERE idempotency_key=?",
            (ref,)).fetchone()
    except Exception:  # noqa: BLE001
        return (False, False, "outcome-query-error")
    if not row:
        return (False, False, "outcome-ref not found (forged trust)")
    et = str(row[0] or "")
    attested = _owner_attested(row)
    if trust == "OWNER_CONFIRMED":
        ok = (et == "accepted-measurement")
    else:
        # «rejected» (۰۷-۳۱): ردِ مالک هم یک outcomeِ واقعیِ durable است و هدفِ
        # اعلام‌شدهٔ verdict_recorder «یادگیری از پذیرش/رد» بود — ولی این فهرست
        # ردش می‌کرد ⇒ درسِ رد ساختاراً هرگز ثبت نمی‌شد. ضدجعل سرِ جاست: ردیف
        # باید واقعاً وجود داشته باشد و trust هرگز از GRADED بالاتر نمی‌رود.
        ok = (et in ("accepted-measurement", "rejected", "delivered",
                     "outcome-recorded", "decided"))
    return (ok, attested, f"outcome event_type={et}")


def learn_from_outcome(*, memory_gate, signal: dict, receipt_store=None, outcome_store=None,
                       evaluator=None, eval_ctx=None, internal_metric_pass: bool = True,
                       min_salience: float = 0.5, pending_admission: bool = False) -> dict:
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
        declared_trust = str(signal.get("trust") or "")
        if declared_trust not in _LEARNABLE_TRUST:
            return {"learned": False, "reason": f"non-outcome trust {declared_trust!r} (preference, not learned)"}
        # ── گاردِ ۱: outcome-binding (trust باید با یک outcomeِ واقعی پشتیبانی شود) ──
        ok, owner_attested, why = _verify_outcome(outcome_store, signal.get("outcome_ref"), declared_trust)
        if not ok:
            return {"learned": False, "reason": f"unverified outcome — {why} (trust not bound to reality)"}
        owner_claim_unattested = False
        trust = declared_trust
        source = str(signal.get("source", "learning_gate"))
        if declared_trust == "OWNER_CONFIRMED" and not owner_attested:
            trust = "GRADED"
            owner_claim_unattested = True
        if source == "owner" and not owner_attested:
            source = _UNATTESTED_SOURCE
            owner_claim_unattested = True
        ns = str(signal.get("namespace") or "semantic")
        if ns == "owner_fact" and not owner_attested:
            return {"learned": False, "reason": "owner_fact requires attested owner verdict",
                    "trust": trust, "trust_declared": declared_trust,
                    "owner_claim_unattested": owner_claim_unattested}

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
        sal = signal.get("salience")
        try:
            sal = float(sal)
        except (TypeError, ValueError):
            sal = min_salience
        candidate = {"namespace": ns, "mkey": signal.get("mkey"),
                     "content": content, "salience": max(sal, min_salience),
                     "confidence": signal.get("confidence", 0.7),
                     "privacy": signal.get("privacy", "scrubbed"),
                     "source": source,
                     "producer": signal.get("producer", "learning_gate"),
                     "supersedes": signal.get("supersedes"),
                     "admission_state": "PENDING" if pending_admission else "ADMITTED"}
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
                "reason_codes": [f"TRUST_{trust}", f"DECLARED_{declared_trust}",
                                 f"EVAL_{ev['verdict'].upper()}"],
                "assumptions": ["held-out gate green", "outcome-not-preference"],
                "memories_used": [],
                "predicted_outcome": {"memory_id": str(mid)[:120], "salience": max(sal, min_salience)},
                "effect_class": "E0"})   # یادگیریِ داخلی، صفر اثرِ بیرونی
        except Exception:  # noqa: BLE001
            rid = None
        if not rid:
            # رسید نساخت → خاطرهٔ بی‌رسید نمی‌گذاریم. Pending admission can be
            # retracted directly (it was never visible); legacy stores use supersede.
            direct = False
            try:
                direct = bool(memory_gate.retract(mid))
            except Exception:
                direct = False
            if not direct:
                _retract(memory_gate, ns, signal.get("mkey"), content, mid, "receipt-failed")
            return {"learned": False, "memory_id": None, "receipt_id": None,
                    "eval_verdict": ev["verdict"],
                    "reason": "receipt write failed — memory retracted (no uncited admission)"}
        return {"learned": not pending_admission, "staged": bool(pending_admission),
                "memory_id": mid, "receipt_id": rid,
                "eval_verdict": ev["verdict"], "anti_hacking_flag": False,
                "trust": trust, "trust_declared": declared_trust,
                "owner_claim_unattested": owner_claim_unattested,
                "reason": ("staged (PENDING; invisible until final durable ledger)"
                           if pending_admission else
                           "learned (durable artifact: memory + receipt)")}
    except Exception as e:  # noqa: BLE001 — یادگیری هرگز مسیرِ اصلی را نمی‌کشد
        return {"learned": False, "reason": f"failsoft:{type(e).__name__}"}


def finalize_pending_learning(*, memory_gate, memory_id: str, admit: bool) -> dict:
    """Finish a two-phase memory admission idempotently.

    PENDING memories are excluded by MemoryStore.get/search. Only a successful final
    research ledger commit may call admit=True. Any failure calls admit=False.
    """
    try:
        cur = memory_gate.admission_state(memory_id)
        if admit and cur == "ADMITTED":
            return {"ok": True, "state": cur, "idempotent": True}
        if not admit and cur == "RETRACTED":
            return {"ok": True, "state": cur, "idempotent": True}
        ok = memory_gate.promote(memory_id) if admit else memory_gate.retract(memory_id)
        return {"ok": bool(ok), "state": "ADMITTED" if admit and ok else
                ("RETRACTED" if ok else cur), "idempotent": False}
    except Exception as e:
        return {"ok": False, "state": None, "reason": f"failsoft:{type(e).__name__}"}


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
