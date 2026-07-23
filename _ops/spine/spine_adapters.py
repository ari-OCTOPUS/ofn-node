#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spine_adapters.py — آداپتورهای رویدادِ canonical برای Event Spine (LIMITED MULTI-DOMAIN SHADOW).

پنج نامِ canonical (مصوب): mission-created · decision-recorded · proposal-issued ·
owner-verdict-recorded · outcome-recorded. این ماژول **تنها لایهٔ نازکِ ورود** است:
producerهای دامنه‌ای (lead/doctor/ziman/…) به‌جای ساختنِ envelope خام، این توابع را صدا
می‌زنند تا نام/trust/idempotency/بهداشتِ payload یک‌جا و یکسان enforce شود.

قیود (هم‌قراردادِ event_spine):
  - پشتِ OCTOPUS_WIRE_SPINE (پیش‌فرض خاموش) → خاموش = صفر I/O (هیچ spine.db ساخته نمی‌شود).
  - fail-soft: هیچ استثنایی به caller نمی‌رسد؛ خروجی همیشه {published, reason}.
  - idempotent: کلیدِ قطعی per-event → replay/دوباره‌صدا = suppressed (published=False, duplicate).
  - PII/raw-text ممنوع: payload از صافیِ whitelist می‌گذرد — فقط اسکالرهای کوتاه؛ کلیدهای
    متن‌خام (body/description/prompt/…) ساختاراً حذف می‌شوند.
  - صفر شبکه/پول/effector — فقط sqliteِ محلیِ spine (stdlib).

Sol-T4 (verdict_recorder → measurement dual-write) سرِ جای خودش می‌ماند؛
owner_verdict_recorded این‌جا لایهٔ نامِ canonical با کلیدِ idempotencyِ جدا است
(صفر تصادم/تکرار با Sol-T4) — برای Worker A/coordinator که نباید envelope دستی بسازند.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import event_spine  # noqa: E402

CANONICAL_EVENTS = ("mission-created", "decision-recorded", "proposal-issued",
                    "owner-verdict-recorded", "outcome-recorded")
_MEASUREMENT_VERDICTS = ("accepted-measurement", "rejected", "deferred")

# ── بهداشتِ payload: فقط اسکالرِ کوتاه با کلیدِ امن — متنِ خام ساختاراً رد ─────────
_KEY_OK_RE = re.compile(r"^[a-z0-9_]{1,32}$")
_KEY_BLOCK_RE = re.compile(
    r"(body|text|desc|prompt|content|message|caption|address|email|phone|"
    r"name|applicant|raw|note|comment)", re.I)
_MAX_STR = 80


def flag_on() -> bool:
    return event_spine.flag_on()


def sanitize_payload(payload) -> dict:
    """صافیِ ساختاریِ ضدِ PII/متنِ خام: فقط کلیدهای snake_case امن با مقدارِ bool/int/float
    یا strِ تک‌خطیِ ≤۸۰ کاراکتر عبور می‌کنند؛ هر چیزِ دیگر (متنِ بلند، nested، کلیدِ متنی
    مثل description/prompt/…) بی‌صدا حذف می‌شود — نه truncate (تا تکهٔ متنِ خام هم نشت نکند)."""
    out = {}
    if not isinstance(payload, dict):
        return out
    for k, v in payload.items():
        ks = str(k)
        if not _KEY_OK_RE.match(ks) or _KEY_BLOCK_RE.search(ks):
            continue
        if isinstance(v, bool) or isinstance(v, (int, float)):
            out[ks] = v
        elif isinstance(v, str) and len(v) <= _MAX_STR and "\n" not in v and "\r" not in v:
            out[ks] = v
        # هر نوعِ دیگر (list/dict/None/متنِ بلند) → حذف
    return out


def _default_db_path():
    """مسیرِ استانداردِ spine (همانی که wiring می‌نویسد): opslib.STATE_DIR/spine/spine.db.
    opslib در دسترس نبود → None (پیش‌فرضِ خودِ event_spine: OCTOPUS_STATE_DIR یا _ops/state)."""
    try:
        _b = str(_HERE.parent / "budget")
        if _b not in sys.path:
            sys.path.insert(0, _b)
        import opslib  # noqa: WPS433 — lazy تا env تست اثر کند
        return Path(opslib.STATE_DIR) / "spine" / "spine.db"
    except Exception:  # noqa: BLE001
        return None


def emit_canonical(*, event: str, domain: str, correlation_id: str, subject=None,
                   mission_id=None, producer=None, trust: str = "ADVISORY",
                   payload=None, idempotency_key=None, spine=None) -> dict:
    """یک رویدادِ canonical را shadow-publish کن. **هرگز raise نمی‌کند.**
    flag خاموش → قبل از هر I/O برمی‌گردد (spine.db ساخته نمی‌شود). spine=None → خودش
    باز می‌کند و می‌بندد (WAL checkpoint — ضدِ قفلِ فایلِ ویندوز)."""
    try:
        if event not in CANONICAL_EVENTS:
            return {"published": False, "reason": f"non-canonical event {event!r}"}
        if not flag_on():
            return {"published": False, "reason": "flag-off"}
        own = spine is None
        if own:
            p = _default_db_path()
            if p is not None:
                p.parent.mkdir(parents=True, exist_ok=True)
                spine = event_spine.EventSpine(path=p)
            else:
                spine = event_spine.EventSpine()
        try:
            ev = {"event_type": event, "domain": str(domain or ""),
                  "correlation_id": str(correlation_id or ""),
                  "mission_id": (str(mission_id)[:64] if mission_id else None),
                  "subject": (str(subject)[:64] if subject else None),
                  "producer": (str(producer)[:48] if producer else None),
                  "trust": trust, "payload": sanitize_payload(payload)}
            if idempotency_key:
                ev["idempotency_key"] = str(idempotency_key)[:200]
            return event_spine.dual_write(spine, ev)
        finally:
            if own and spine is not None:
                spine.close()
    except Exception as e:  # noqa: BLE001 — آداپتور هرگز مسیرِ اصلی را نمی‌کشد
        return {"published": False, "reason": f"failsoft:{type(e).__name__}"}


# ── C4: سطحِ تولیدِ واحدِ عام (single producer surface) ─────────────────────────
# قرارداد envelope (step 10): هر رویدادِ spine باید این‌ها را داشته باشد. publish خودش
# event_id/occurred_at/recorded_at/schema_version را می‌سازد و correlation_id/event_type/
# domain را اجباری می‌کند؛ این‌جا provenance (producer/trust) را هم به قرارداد اضافه می‌کنیم.
REQUIRED_ENVELOPE = ("event_id", "idempotency_key", "event_type", "domain",
                     "occurred_at", "recorded_at", "producer", "correlation_id",
                     "trust", "schema_version")


def validate_row(row: dict) -> "tuple[bool, list]":
    """قراردادِ envelope را روی یک ردیفِ spine (dict از events) بسنج. (ok, missing/invalid)."""
    missing = [k for k in REQUIRED_ENVELOPE
               if row.get(k) is None or (isinstance(row.get(k), str) and not row.get(k).strip())]
    bad = []
    if not event_spine.tax.is_event_type(str(row.get("event_type") or "")):
        bad.append("event_type")
    if not event_spine.tax.is_trust(row.get("trust")):
        bad.append("trust")
    return (not missing and not bad, missing + [f"invalid:{b}" for b in bad])


def emit_event(*, event_type: str, domain: str, correlation_id: str, subject=None,
               mission_id=None, producer: str = "unknown", trust: str = "ADVISORY",
               payload=None, idempotency_key=None, spine=None) -> dict:
    """**سطحِ تولیدِ واحدِ spine** (C4). هر producer — چه دامنه‌ایِ typed و چه verdict/lead —
    از همین در می‌گذرد؛ نه dual_write خام. مثلِ emit_canonical است ولی به CANONICAL_EVENTS
    محدود نیست (هر event_typeِ معتبرِ taxonomy). producer اجباری (provenance هرگز null).
    هرگز raise نمی‌کند؛ flag خاموش → صفر I/O؛ idempotent."""
    try:
        if not flag_on():
            return {"published": False, "reason": "flag-off"}
        if not str(producer or "").strip():
            producer = "unknown"
        own = spine is None
        if own:
            p = _default_db_path()
            spine = event_spine.EventSpine(path=p) if p is not None else event_spine.EventSpine()
        try:
            ev = {"event_type": str(event_type or ""), "domain": str(domain or ""),
                  "correlation_id": str(correlation_id or ""),
                  "mission_id": (str(mission_id)[:64] if mission_id else None),
                  "subject": (str(subject)[:64] if subject else None),
                  "producer": str(producer)[:48], "trust": trust,
                  "payload": sanitize_payload(payload)}
            if idempotency_key:
                ev["idempotency_key"] = str(idempotency_key)[:200]
            return event_spine.dual_write(spine, ev)
        finally:
            if own and spine is not None:
                spine.close()
    except Exception as e:  # noqa: BLE001 — سطحِ تولید هرگز مسیرِ اصلی را نمی‌کشد
        return {"published": False, "reason": f"failsoft:{type(e).__name__}"}


# ── آداپتورهای نامدار (قراردادِ هر دامنه یک‌جا) ─────────────────────────────────
def proposal_issued(*, proposal_id: str, domain: str, leg_id: str = "unknown",
                    kind: str = "", correlation_id=None, mission_id=None,
                    producer=None, payload=None, spine=None) -> dict:
    """صدورِ proposal (propose-only). corr پیش‌فرض prop_<pid> — هم‌خانوادهٔ Sol-T4 تا
    رأیِ بعدیِ مالک روی همان proposal در یک زنجیرهٔ correlation بنشیند."""
    pid = str(proposal_id or "")
    if not pid:
        return {"published": False, "reason": "proposal_id required"}
    corr = str(correlation_id or ("prop_" + pid))
    base = {"leg_id": str(leg_id or "unknown")[:40], "kind": str(kind or "")[:40],
            "propose_only": True}
    base.update(payload if isinstance(payload, dict) else {})
    return emit_canonical(event="proposal-issued", domain=domain, correlation_id=corr,
                          subject=pid, mission_id=mission_id,
                          producer=producer or ("leg:" + str(leg_id or "unknown"))[:40],
                          trust="ADVISORY", payload=base,
                          idempotency_key=f"{corr}|{pid}|proposal-issued", spine=spine)


def owner_verdict_recorded(*, proposal_id: str, verdict_event: str, correlation_id=None,
                           mission_id=None, leg_id=None, producer: str = "owner_verdict",
                           payload=None, spine=None) -> dict:
    """آداپتورِ Worker A/coordinator برای owner-verdict-recorded (domain=proposal، بدونِ
    دست‌زدن به فایل‌های تلگرام). فقط measurement (accepted-measurement/rejected/deferred) —
    هرگز delivered/settled/درآمد. کلیدِ idempotency شاملِ خودِ verdict است تا تغییرِ رأی
    (deferred→accepted) رویدادِ نو بسازد ولی تکرارِ همان رأی suppressed بماند."""
    pid = str(proposal_id or "")
    if not pid:
        return {"published": False, "reason": "proposal_id required"}
    ve = str(verdict_event or "").strip().lower()
    if ve not in _MEASUREMENT_VERDICTS:
        return {"published": False, "reason": f"non-measurement verdict_event {ve!r}"}
    corr = str(correlation_id or ("prop_" + pid))
    base = {"leg_id": str(leg_id or "unknown")[:40], "verdict_event": ve,
            "measurement_only": True}
    base.update(payload if isinstance(payload, dict) else {})
    return emit_canonical(event="owner-verdict-recorded", domain="proposal",
                          correlation_id=corr, subject=pid, mission_id=mission_id,
                          producer=producer, trust="OWNER_CONFIRMED", payload=base,
                          idempotency_key=f"{corr}|{pid}|owner-verdict-recorded|{ve}",
                          spine=spine)


def mission_created(*, mission_id: str, domain: str, correlation_id=None, source: str = "",
                    target_leg: str = "", risk: str = "", producer=None, spine=None) -> dict:
    """ثبتِ تولدِ mission envelope (mission_contract.make_envelope). corr پیش‌فرض trace
    نداری → mis_<id>. **آداپتور-فقط تا وقتی call siteِ تولید (owner_menu، فایلِ تلگرام —
    مالکیتِ Worker A) وصل شود؛ این دامنه هنوز covered ادعا نمی‌شود.**"""
    mid = str(mission_id or "")
    if not mid:
        return {"published": False, "reason": "mission_id required"}
    corr = str(correlation_id or ("mis_" + mid))
    return emit_canonical(event="mission-created", domain=domain, correlation_id=corr,
                          subject=mid, mission_id=mid, producer=producer,
                          trust="DETERMINISTIC",
                          payload={"source": str(source)[:40], "target_leg": str(target_leg)[:40],
                                   "risk": str(risk)[:16]},
                          idempotency_key=f"{corr}|{mid}|mission-created", spine=spine)


def decision_recorded(*, receipt_id: str, domain: str, correlation_id: str,
                      mission_id=None, subject=None, effect_class: str = "",
                      producer=None, spine=None) -> dict:
    """ثبتِ canonicalِ یک Decision Receipt (فقط شناسه‌ها — هرگز محتوای تصمیم/CoT)."""
    rid = str(receipt_id or "")
    if not rid or not str(correlation_id or ""):
        return {"published": False, "reason": "receipt_id and correlation_id required"}
    return emit_canonical(event="decision-recorded", domain=domain,
                          correlation_id=str(correlation_id), subject=subject or rid,
                          mission_id=mission_id, producer=producer, trust="DETERMINISTIC",
                          payload={"receipt_id": rid[:64], "effect_class": str(effect_class)[:8]},
                          idempotency_key=f"{correlation_id}|{rid}|decision-recorded",
                          spine=spine)


def outcome_recorded(*, domain: str, correlation_id: str, subject=None, mission_id=None,
                     producer=None, trust: str = "ADVISORY", payload=None,
                     spine=None) -> dict:
    """ثبتِ canonicalِ یک outcome (نتیجهٔ داخلی/سنجش) — payload فقط شناسه/عددِ کوتاه."""
    corr = str(correlation_id or "")
    if not corr:
        return {"published": False, "reason": "correlation_id required"}
    subj = str(subject)[:64] if subject else None
    return emit_canonical(event="outcome-recorded", domain=domain, correlation_id=corr,
                          subject=subj, mission_id=mission_id, producer=producer,
                          trust=trust, payload=payload,
                          idempotency_key=f"{corr}|{subj or '-'}|outcome-recorded",
                          spine=spine)
