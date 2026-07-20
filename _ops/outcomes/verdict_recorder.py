#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verdict_recorder.py — رأیِ مالک روی پیشنهاد → OutcomeStoreِ پایدار (MEASUREMENT-only).

قوسِ شکسته (ممیزیِ Sol، T2): رأیِ دکمهٔ کارتِ تلگرام در `live_loop` فقط **in-memory** می‌نشست
و با restart گم می‌شد → سیستم از پذیرش/ردِ مالک به‌شکلِ پایدار یاد نمی‌گرفت. این ماژول رأی را
به‌عنوان رویدادِ **measurement** در همان `outcomes.db` ثبت می‌کند.

قیودِ سخت (enforce‌شده):
  - event_type فقط از {accepted-measurement, rejected, deferred} — **هرگز delivered/settled/failed**.
    یعنی رأیِ مالک هرگز به «تحویل/تسویه/دیده‌شدن/درآمد» تعبیر نمی‌شود.
  - value_aud_claimed فقط CLAIMِ روی accepted (مبلغِ انتظاریِ پیشنهاد)، هرگز روی rejected/deferred،
    هرگز confirmed revenue.
  - idempotent (کلید correlation|proposal|event_type) → همان رأی دوباره = رویدادِ نو نوشته نمی‌شود.
  - single-use را caller تضمین می‌کند (اولین تصمیمِ برنده)؛ این‌جا هم idempotent است (defense-in-depth).
  - صفر ledger/effector/approval/settle/pay — ساختاراً (بدونِ importِ آن‌ها؛ تستِ ast).
پشتِ OCTOPUS_WIRE_VERDICT_OUTCOME (پیش‌فرض خاموش). stdlib فقط.
"""
from __future__ import annotations

import os

FLAG = "OCTOPUS_WIRE_VERDICT_OUTCOME"

# رأیِ خامِ مالک → event_typeِ measurement (taxonomy). هرچه این‌جا نیست = ثبت نمی‌شود.
_VERDICT_EVENT = {
    "approved": "accepted-measurement", "accepted": "accepted-measurement",
    "yes": "accepted-measurement", "ok": "accepted-measurement",
    "rejected": "rejected", "no": "rejected",
    "deferred": "deferred", "later": "deferred",
}
# نگهبانِ ناوردی: این‌ها هرگز نباید از یک رأی تولید شوند (delivery/settlement/failure استنتاج ممنوع)
_FORBIDDEN_EVENT = {"delivered", "settled", "failed", "verified"}


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def event_type_for(verdict: str) -> "str | None":
    return _VERDICT_EVENT.get(str(verdict or "").strip().lower())


def record_owner_verdict(outcome_store, *, proposal_id: str, verdict: str,
                         correlation_id: str = None, mission_id: str = None,
                         leg_id: str = None, value_aud_claimed: float = 0.0,
                         event_spine=None) -> dict:
    """رأیِ مالک را MEASUREMENTِ پایدار ثبت کن. خروجی: {recorded, event_type?, reason?}.

    idempotent: همان (proposal, event_type) دوباره → recorded=False (رویدادِ نو نوشته نشد).
    هرگز delivered/settled/revenue استنتاج نمی‌کند؛ value فقط CLAIMِ accepted.

    Sol-T4: اگر event_spine داده شود (و flagش روشن باشد)، همین رأی را با **domain="proposal"**
    به SoTِ یگانه هم dual-write می‌کند — spine را از lead-only به دو دامنه می‌برد (اثباتِ
    گسترش؛ نه ادعای system-wide تا accounting/ziman/doctor هم producer داشته باشند)."""
    et = event_type_for(verdict)
    if et is None:
        return {"recorded": False, "reason": f"non-measurement verdict {verdict!r}"}
    if et in _FORBIDDEN_EVENT:   # ناوردیِ سخت — نباید هرگز رخ دهد
        return {"recorded": False, "reason": "forbidden event class"}
    pid = str(proposal_id or "")
    if not pid:
        return {"recorded": False, "reason": "proposal_id required"}
    corr = str(correlation_id or ("prop_" + pid))
    idem = f"{corr}|{pid}|{et}"
    # ارزش فقط CLAIMِ روی accepted — هرگز confirmed revenue، صفر روی rejected/deferred
    val = float(value_aud_claimed or 0.0) if et == "accepted-measurement" else 0.0
    ev = {"correlation_id": corr, "mission_id": str(mission_id or ""),
          "proposal_id": pid, "leg_id": str(leg_id or "unknown"),
          "event_type": et, "value_aud_claimed": val, "idempotency_key": idem,
          "verdict": "measurement",   # هرگز 'settled'/'delivered' — رأی سنجش است نه تسویه
          "payload": {"owner_verdict_raw": str(verdict)[:40], "source": "tg-proposal-button",
                      "measurement_only": True}}
    wrote = bool(outcome_store.record(ev))
    spine_wrote = False
    if event_spine is not None:   # Sol-T4: دامنهٔ دومِ spine (proposal) — fail-soft
        try:
            import event_spine as _esx   # noqa: WPS433
            if _esx.flag_on():
                _esx.dual_write(event_spine, {
                    "event_type": et, "domain": "proposal",
                    "correlation_id": corr, "mission_id": str(mission_id or ""),
                    "subject": pid, "producer": "owner_verdict", "trust": "OWNER_CONFIRMED",
                    "payload": {"leg_id": str(leg_id or "unknown"), "measurement_only": True}})
                spine_wrote = True
        except Exception:  # noqa: BLE001 — spine نباید ثبتِ رأی را بکشد
            spine_wrote = False
    return {"recorded": wrote, "event_type": et, "idempotency_key": idem,
            "value_aud_claimed": val, "spine": spine_wrote}
