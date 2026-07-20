#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""metric_separation.py — جداسازیِ صادقانهٔ متریک‌ها: تپش ≠ کار ≠ پیشنهاد ≠ نتیجه ≠ ارزش.

(Worker D — metrics/learning) مسئله: یک عددِ واحد («delivered» یا بیتِ moved) می‌تواند
«زنده بودن» را «مولد بودن» جا بزند. این ماژول tierهای جدا و بازساخت‌پذیر می‌سازد که
هر کدام فقط یک چیز را می‌شمارند — از substrateِ durable (OutcomeStore) به‌شکلِ قطعی.

قواعدِ سخت (enforce شده در همین ماژول + تست):
  - heartbeat != productivity          → liveness هرگز واردِ هیچ tierِ کار/ارزش نمی‌شود.
  - proposal != outcome                → تحویلِ پیشنهاد هرگز outcome/value نمی‌سازد.
  - accepted-measurement != revenue    → رأیِ مالک claim است؛ validated_value همیشه جدا.
  - fake delivery != real delivery     → تحویلِ sandbox/no-send/ارسال‌نشده جدا شمرده می‌شود.
  - missing data must not become success → کانال/فایل/رویدادِ غایب = صفر، هرگز موفقیت.

stdlib فقط؛ read-only (هیچ نوشتی جز خواندنِ store)؛ صفر شبکه/Telegram/effector/settle.
بدونِ flag — خواندنِ خالص است و side-effect ندارد؛ مصرف‌کننده‌های قدیمیِ
`outcome_store.metrics()` دست‌نخورده می‌مانند (این ماژول additive است).
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA = "metric-separation.v1"

# tierهای قراردادی (ترتیب = زنجیرهٔ ارزش؛ هر tier فقط از شواهدِ خودش پر می‌شود).
TIERS = ("liveness", "work_attempted", "proposal_issued", "proposal_fake_delivered",
         "proposal_delivered", "owner_verdict", "validated_outcome",
         "validated_value_aud", "learning_update")

_VERDICT_EVENTS = ("accepted-measurement", "rejected", "deferred")
# event_typeهایی که «نتیجهٔ بیرونیِ اعتبارسنجی‌شده» می‌شمارند — امروز عمداً تهی:
# هیچ producerی settled/verified ندارد (verdict_recorder آن‌ها را ممنوع کرده).
# نبودِ داده هرگز موفقیت نمی‌شود → این tierها ساختاراً صفر می‌مانند تا producerِ
# واقعیِ reconcile بیاید. هرگز از claim پر نمی‌شوند.
_VALIDATED_EVENTS: tuple = ()
# کانال‌هایی که تحویلِ واقعی نیستند (record-only/paper/no-send).
_FAKE_CHANNELS = {"", "sandbox", "none", "no-send", "paper", "dry-run"}


def _zero() -> dict:
    """صفرهای صادق — کلیدها همیشه حاضرند (schema پایدار) ولی هرگز از غیاب پر نمی‌شوند."""
    return {"schema": SCHEMA, "liveness": 0, "work_attempted": 0, "proposal_issued": 0,
            "proposal_fake_delivered": 0, "proposal_delivered": 0,
            "owner_verdict": 0, "owner_accepted_measurement": 0, "owner_rejected": 0,
            "owner_deferred": 0, "validated_outcome": 0, "validated_value_aud": 0.0,
            "value_aud_quoted": 0.0, "value_aud_claimed_accepted": 0.0,
            "learning_update": 0}


def _payload(ev: dict) -> dict:
    try:
        p = json.loads(ev.get("payload_json") or "{}")
    except (TypeError, ValueError):
        return {}
    return p if isinstance(p, dict) else {}


def is_real_delivery(ev: dict) -> bool:
    """تحویلِ واقعی = event_type=delivered با کانالِ صریحِ غیر-fake.
    payload خراب/غایب یا کانالِ نامشخص → fake (تحویلِ اثبات‌نشده تحویل نیست)."""
    if str(ev.get("event_type")) != "delivered":
        return False
    ch = str(_payload(ev).get("channel") or "").strip().lower()
    return ch not in _FAKE_CHANNELS


def from_outcome_store(store) -> dict:
    """تفکیکِ قطعی از rowsِ durable — پس از close/reopenِ store عیناً بازساخته می‌شود.
    liveness این‌جا همیشه ۰ است (تپش از outcome-store استنتاج نمی‌شود — تپش کار نیست)."""
    m = _zero()
    if store is None:
        return m                      # storeِ غایب = صفرها، نه موفقیت
    evs = store.events()
    delivered_all = [e for e in evs if e.get("event_type") == "delivered"]
    real = [e for e in delivered_all if is_real_delivery(e)]
    failed = [e for e in evs if e.get("event_type") == "failed"]
    accepted = [e for e in evs if e.get("event_type") == "accepted-measurement"]
    rejected = [e for e in evs if e.get("event_type") == "rejected"]
    deferred = [e for e in evs if e.get("event_type") == "deferred"]
    validated = [e for e in evs if e.get("event_type") in _VALIDATED_EVENTS]
    m.update({
        "work_attempted": len(delivered_all) + len(failed),
        "proposal_issued": len({e.get("proposal_id") for e in evs if e.get("proposal_id")}),
        "proposal_delivered": len(real),
        "proposal_fake_delivered": len(delivered_all) - len(real),
        "owner_verdict": len(accepted) + len(rejected) + len(deferred),
        "owner_accepted_measurement": len(accepted),
        "owner_rejected": len(rejected),
        "owner_deferred": len(deferred),
        "validated_outcome": len(validated),          # امروز ساختاراً ۰ (producer ندارد)
        # ارزش‌ها: quoted = claimِ روی کارت/کوت؛ accepted = claimِ تأییدِ سنجشیِ مالک.
        # validated_value_aud هرگز از این دو پر نمی‌شود (claim ≠ revenue) — تا reconcile.
        "value_aud_quoted": round(sum(float(e.get("value_aud_claimed") or 0.0)
                                      for e in delivered_all), 2),
        "value_aud_claimed_accepted": round(sum(float(e.get("value_aud_claimed") or 0.0)
                                                for e in accepted), 2),
        "validated_value_aud": 0.0,
    })
    return m


def liveness_from_state(state) -> int:
    """تپش (beat) از snapshotِ ORGANISM-STATE — فقط liveness. هرگز واردِ tierهای کار/ارزش
    نمی‌شود؛ state خراب/غایب = ۰ (missing data ≠ liveness هم)."""
    if not isinstance(state, dict):
        return 0
    chrono = state.get("chrono")
    beat = chrono.get("beat") if isinstance(chrono, dict) else state.get("beat")
    try:
        return max(0, int(beat or 0))
    except (TypeError, ValueError):
        return 0


def count_learning_updates(outcomes_jsonl) -> int:
    """آپدیتِ یادگیریِ واقعی = رکوردهای بستارِ goal_directed (kind='closure') در
    outcomes.jsonl — شواهدِ نوشته‌شده، نه حدس. فایلِ غایب/خراب → ۰."""
    try:
        p = Path(outcomes_jsonl)
        if not p.exists():
            return 0
        n = 0
        for ln in p.read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("kind") == "closure":
                n += 1
        return n
    except OSError:
        return 0


def separated_metrics(store=None, *, state=None, outcomes_jsonl=None) -> dict:
    """نمای کامل: durable tiers از store + liveness از state + learning از بستارها.
    هر ورودیِ غایب = صفرِ همان tier (هرگز موفقیتِ ضمنی). قطعی و بازساخت‌پذیر."""
    m = from_outcome_store(store)
    m["liveness"] = liveness_from_state(state)
    if outcomes_jsonl is not None:
        m["learning_update"] = count_learning_updates(outcomes_jsonl)
    return m


if __name__ == "__main__":
    print(json.dumps(_zero(), ensure_ascii=False, indent=2))
