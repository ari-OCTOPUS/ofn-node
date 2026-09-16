"""test_legs_adapter.py — پذیرش V3 (آداپتور ترکیبی پاها).

از طراحی `06-EVIDENCE/DESIGNS-NBB-CP-2026-08-16.md` §V3:
  ۱. ثبت نام‌یکتا (درس C-014) ۲. سکوت > ۹۰s ⇒ stale (نه مرگ)
  ۳. پیشنهاد هرگز اجرا نمی‌شود ۴. سقف بودجهٔ per-leg در ثبت
  ۵. رجیستری/heartbeat/پیشنهاد پایه + رفتار خاص زیمان
"""
from __future__ import annotations

import time

from nbb_cp.adapters.legs import LegAdapter, LegRegistry
from nbb_cp.adapters.legs.legs.ziman import ZimanLeg
from nbb_cp.adapters.legs.legs.lead_painting import LeadPaintingLeg


def test_unique_registration_rejects_duplicate():
    r = LegRegistry()
    r.register(ZimanLeg())
    try:
        r.register(ZimanLeg())
        raised = False
    except ValueError as e:
        raised = "C-014" in str(e) or "تکراری" in str(e)
    assert raised, "ثبت نام تکراری باید ValueError بدهد (بدون آن، دو نمونه = دو کار)"


def test_base_leg_id_rejected():
    r = LegRegistry()
    try:
        r.register(LegAdapter())
        raised = False
    except ValueError:
        raised = True
    assert raised, "leg_id='base' نباید قابل ثبت باشد"


def test_heartbeat_stale_after_90s_not_dead():
    leg = ZimanLeg()
    t0 = 1_000_000.0
    leg.heartbeat(ts=t0)
    fresh = leg.status(now=t0 + 10)
    assert fresh.alive and not fresh.stale
    stale = leg.status(now=t0 + 91)
    assert stale.alive and stale.stale, "سکوت ⇒ stale، نه مرگ (درس C-014: سکوت ≠ حذف)"


def test_proposal_never_executed_in_adapter_layer():
    leg = LeadPaintingLeg()
    p = leg.propose("stop_campaign", {"campaign": "x"})
    assert p.executed is False
    assert leg.proposal(p.proposal_id) is p
    assert leg.pending_proposals() == [p], "پیشنهاد باید pending بماند — اجرا فقط از گیت V2/V4"


def test_budget_cap_per_leg():
    assert ZimanLeg().budget_cap_aud == 20.0
    assert LeadPaintingLeg().budget_cap_aud == 0.0, "صفر = بدون بودجهٔ مصرفی (پیش‌فرض محافظه‌کارانه)"


def test_ziman_transform_outbound():
    z = ZimanLeg()
    out = z.transform_outbound("  کارت   محصول\n تست  ")
    assert out.startswith("🌸 ") and "  " not in out and "\n" not in out


def test_registry_stale_legs_listing():
    r = LegRegistry()
    z = ZimanLeg(); lp = LeadPaintingLeg()
    r.register(z); r.register(lp)
    t0 = 2_000_000.0
    z.heartbeat(ts=t0)                      # فقط زیمان تازه
    lp.heartbeat(ts=t0 - 10_000)            # لیدنقاشی کهنه
    assert r.stale_legs(now=t0) == ["lead_painting"]


def test_proposal_ids_unique_and_scoped():
    z = ZimanLeg(); lp = LeadPaintingLeg()
    p1 = z.propose("x"); p2 = lp.propose("x")
    assert p1.proposal_id != p2.proposal_id
    assert p1.leg_id == "ziman" and p2.leg_id == "lead_painting"
