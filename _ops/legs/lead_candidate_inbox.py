#!/usr/bin/env python3
"""lead_candidate_inbox.py — Trust-Engine P0: آداپترِ canonicalِ ورودیِ لید (submit_candidate).

تنها نقطهٔ ورودِ کاندیدِ لید به ارگانیسم. جای‌گزینِ همگرا برای دو inboxِ متناقضِ قدیمی
(`lead_leg_inbox` freeze می‌شود؛ `lead_sense` مکانیکِ ذخیره/چرخهٔ عمرش canonical می‌ماند).
قرارداد: `Trust-Engine-v1.1/PHASE-B-CONTRACTS/` (02 اسکیما · 07a مرز · 09a مهاجرت).

خطِ لولهٔ قطعی (هر گام fail-closed):
  halt-check → validate → normalize(v1.1) → classify+consent-firewall → dedup(idempotency)
  → receipt(append-only) → routing بر candidate_type.

نامتغیرها (هم‌راستا با اصلاحاتِ راستی‌آزماییِ متخاصمِ فاز B):
  · **market_signal فایلِ کاندیدِ lead_sense نمی‌سازد** (B2): وارد قوسِ draftِ consent-نابینا
    نمی‌شود؛ به `signals/` می‌رود (سطحِ digest). فقط consented_inbound/public_b2b فایلِ
    top-levelِ قابل‌مصرفِ scorer/draft می‌سازند.
  · **در halt، تنها نوشته = receiptِ append-only** (audit)، صفر جهشِ دیگرِ state (B2).
  · `external_send_allowed` را producer/inbox هرگز True نمی‌کند — فقط رأیِ مالک→LANGAR→
    EffectorGate. synthetic_test علاوه‌براین نشانِ سختِ synthetic می‌گیرد (بلاکِ نوعی در گیت).
  · هرگز چیزی نمی‌فرستد/خرج نمی‌کند. stdlib-only. flag خاموش = no-op.

Flag: OCTOPUS_WIRE_LEAD_CANDIDATES (پیش‌فرض OFF).
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib          # noqa: E402
import consent_firewall as cf   # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_CANDIDATES"
SCHEMA_VERSION = "1.1"

_VALID_CHANNELS = frozenset({
    "telegram_manual", "website_form", "missed_call", "meta_lead_ad", "facebook_group",
    "nsw_da", "domain_listing", "synthetic_test", "other",
})


def enabled() -> bool:
    """flag خاموش (پیش‌فرض) = no-op مطلق."""
    return os.environ.get(FLAG) == "1"


# ── مسیرها (call-time تا OPS_DIR تستی اثر کند) ────────────────────────────────────
def _inbox() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox"


def _events() -> Path:
    return _inbox() / "events.jsonl"          # receiptهای append-only (نه *.json → از glob امن)


def _quarantine() -> Path:
    return _inbox() / "quarantine"            # بدنه‌های نامعتبر (هرگز حذف)


def _signals() -> Path:
    return _inbox() / "signals"               # market_signalها (سطحِ digest، نه کارتِ per-candidate)


def _idem_index() -> Path:
    return _inbox() / "processed" / "_idem.json"   # زیرِ processed/ (نه top-level → از glob امن)


# ── receipt (append-only؛ envelope مطابقِ 03_EVENT_CONTRACT) ─────────────────────
def _receipt(event_type: str, correlation_id: str, payload: dict) -> str:
    ev_id = uuid.uuid4().hex
    rec = {
        "event_id": ev_id,
        "event_type": event_type,
        "occurred_at": opslib.now_iso(),
        "correlation_id": correlation_id,
        "source_component": "LeadInboxLeg",
        "schema_version": "1.0",
        "payload": payload,
    }
    try:
        opslib.append_jsonl(_events(), rec)
    except Exception:  # noqa: BLE001 — receipt نباید مسیر را بکشد
        pass
    return ev_id


def _load_idem() -> dict:
    try:
        return json.loads(_idem_index().read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save_idem(idx: dict) -> None:
    try:
        _idem_index().parent.mkdir(parents=True, exist_ok=True)
        tmp = _idem_index().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, _idem_index())
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: dedupِ ضعیف‌تر، نه کرش


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    os.replace(tmp, path)


def _validate(candidate: dict) -> str | None:
    """اعتبارسنجیِ ساختاریِ سبک (pure-python، بی‌وابستگیِ jsonschema). خطا→پیام، معتبر→None.

    قیدهای حیاتیِ اسکیمای 02 که اینجا enforce می‌شوند (بقیه در فاز C کامل‌تر)."""
    if not isinstance(candidate, dict):
        return "candidate باید dict باشد"
    src = candidate.get("source")
    if not isinstance(src, dict):
        return "source.{} غایب/نامعتبر"
    channel = str(src.get("channel") or "").strip()
    if channel not in _VALID_CHANNELS:
        return f"source.channel نامعتبر: «{channel}»"
    req = candidate.get("request") or {}
    scope = str((req.get("scope_text") or candidate.get("description") or "")).strip()
    if not scope:
        return "request.scope_text (یا description) الزامی و غیرخالی است"
    return None


def _to_lead_sense_file(lead_id: str, candidate: dict, verdict: dict) -> dict:
    """آینهٔ سازگار با lead_sense.read_inbox (dict با description ناخالی) + پاکتِ کاملِ v1.1.
    کلیدهای top-level آینهٔ writer-enforced از پاکتِ v1.1‌اند؛ مصرف‌کنندهٔ قدیمی دست‌نخورده."""
    req = candidate.get("request") or {}
    prop = candidate.get("property") or {}
    src = candidate.get("source") or {}
    contact = candidate.get("contact") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "lead_id": lead_id,
        "description": str(req.get("scope_text") or candidate.get("description") or "").strip(),
        "address": prop.get("address"),
        "suburb": prop.get("suburb"),
        "source": src.get("channel"),
        "applicant": contact.get("organisation") or contact.get("name"),
        "day": str(src.get("received_at") or opslib.now_iso())[:10],
        "candidate": {
            "candidate_type": verdict["candidate_type"],
            "consent": {
                "basis": verdict["consent_basis"],
                "outreach_allowed": verdict["outreach_allowed"],
                "retention_class": verdict["retention_class"],
                "compliance_reason": verdict["compliance_reason"],
            },
            "request": req,
            "workflow": {
                "status": "received",
                "owner_action_required": True,
                "external_send_allowed": False,   # هرگز از producer/inbox؛ فقط verdict→LANGAR→gate
                "next_action": "qualify",
            },
            "synthetic": (src.get("channel") == "synthetic_test"),
        },
    }


def submit_candidate(candidate: dict, source_id: str = "unknown") -> dict:
    """تنها نقطهٔ ورودِ کاندید. همیشه dict با کلیدِ `ok` برمی‌گرداند؛ هرگز استثنا.

    خروجی: {ok, status, lead_id?, reason?, receipt_event_id?, candidate_type?, outreach_allowed?}
    statusها: accepted | signal_recorded | duplicate | quarantined | halted | gate_off
    """
    if not enabled():
        return {"ok": False, "status": "gate_off", "reason": "flag off"}

    # ۱) halt اول: در halt تنها receipt نوشته می‌شود، صفر جهشِ دیگرِ state (B2).
    kill = opslib.master_halted() or opslib.halted() or (
        "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None) or (
        "FREEZE" if opslib.frozen() else None)
    if kill:
        rid = _receipt("lead.candidate.rejected", source_id,
                       {"outcome": "halted_refused", "reason": kill})
        return {"ok": False, "status": "halted", "reason": kill, "receipt_event_id": rid}

    # ۲) validate → نامعتبر: quarantine (هرگز حذف) + سایدکارِ دلیل + alert + receipt.
    err = _validate(candidate)
    if err:
        try:
            _quarantine().mkdir(parents=True, exist_ok=True)
            body = json.dumps(candidate, ensure_ascii=False, default=str).encode("utf-8")
            h = uuid.uuid4().hex[:12]
            (_quarantine() / f"{h}.json").write_bytes(body)
            (_quarantine() / f"{h}.reason.json").write_text(
                json.dumps({"error": err, "source_id": source_id,
                            "received_at": opslib.now_iso()}, ensure_ascii=False), "utf-8")
        except Exception:  # noqa: BLE001
            pass
        try:
            opslib.alert([f"lead-inbox quarantine: {err} (src={source_id})"])
        except Exception:  # noqa: BLE001
            pass
        rid = _receipt("lead.candidate.rejected", source_id,
                       {"outcome": "quarantined", "reason": err})
        return {"ok": False, "status": "quarantined", "reason": err, "receipt_event_id": rid}

    # ۳) idempotency: source_id:external_id — تکراری هیچ لیدِ دومی نمی‌سازد.
    ext = str(((candidate.get("source") or {}).get("external_id") or "")).strip()
    idem_key = f"{source_id}:{ext}" if ext else None
    idx = _load_idem()
    if idem_key and idem_key in idx:
        rid = _receipt("lead.duplicate.detected", idx[idem_key],
                       {"idempotency_key": idem_key})
        return {"ok": True, "status": "duplicate", "lead_id": idx[idem_key],
                "reason": "idempotency_key seen", "receipt_event_id": rid}

    # ۴) classify + consent firewall (fail-closed).
    lead_id = uuid.uuid4().hex
    verdict = cf.evaluate(candidate)
    ctype = verdict["candidate_type"]

    # ۵) receipt پذیرش (append-only).
    rid = _receipt("lead.candidate.received", lead_id, {
        "source_id": source_id, "idempotency_key": idem_key,
        "candidate_type": ctype, "outreach_allowed": verdict["outreach_allowed"],
    })

    # ۶) routing بر candidate_type (اصلاحِ B2).
    if ctype == "market_signal":
        # سیگنال فایلِ کاندیدِ top-level نمی‌سازد → وارد قوسِ draft نمی‌شود؛ فقط digest.
        try:
            _atomic_write(_signals() / f"{lead_id}.json",
                          {"lead_id": lead_id, "source_id": source_id,
                           "candidate": candidate, "verdict": verdict,
                           "recorded_at": opslib.now_iso()})
        except Exception:  # noqa: BLE001
            pass
        status = "signal_recorded"
    else:
        # consented_inbound / public_b2b → فایلِ سازگار با lead_sense (قوسِ موجود مصرف می‌کند).
        try:
            _atomic_write(_inbox() / f"{lead_id}.json",
                          _to_lead_sense_file(lead_id, candidate, verdict))
        except Exception:  # noqa: BLE001
            rid2 = _receipt("lead.candidate.rejected", lead_id, {"outcome": "write_failed"})
            return {"ok": False, "status": "quarantined", "reason": "write_failed",
                    "receipt_event_id": rid2}
        status = "accepted"

    # ثبتِ idempotency پس از موفقیت.
    if idem_key:
        idx[idem_key] = lead_id
        _save_idem(idx)

    return {"ok": True, "status": status, "lead_id": lead_id,
            "candidate_type": ctype, "outreach_allowed": verdict["outreach_allowed"],
            "receipt_event_id": rid}


if __name__ == "__main__":
    os.environ.setdefault(FLAG, "0")   # عمداً OFF: اجرای مستقیم چیزی نمی‌نویسد
    print(json.dumps({"enabled": enabled(),
                      "note": "برای دمو FLAG را در env روشن کن + STATE_DIR را tmp کن"},
                     ensure_ascii=False))
