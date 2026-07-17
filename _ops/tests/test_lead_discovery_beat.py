#!/usr/bin/env python3
"""تستِ مرحلهٔ ۲ نقشهٔ لید (2026-07-15): lead_discovery_beat — اولین حلقهٔ خودکارِ لید.

اثبات می‌کند:
  (الف) flag خاموش → None و صندوق دست‌نخورده (بایت‌به‌بایتِ امروز).
  (ب) flag روشن → SENSE (صندوقِ فایل) → SCORE → فقط draft به intake می‌رسد؛
      save/skip فقط آرشیو؛ فایل‌ها به processed/ منتقل (نه حذف) + سایدکارِ نتیجه؛
      سایدکارِ ORGANISM-STATE.lead_discovery نوشته می‌شود.
  (ج) dedup: همان محتوا دوباره → duplicate، هیچ proposeِ دوم (idempotent).
  (د) kill-switch (STOP) → None حتی با flag روشن.
  (هـ) cadence: beat غیرِ مضربِ N → None.
  (و) ساختاری: organism.py واقعاً beat را صدا می‌زند + flag خارج از PAPER_FULL_FLAGS.
$0 آفلاین؛ state ایزوله (OPS_DIR موقتِ harness)؛ FakeLeg ضبط‌کنندهٔ intake.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-discovery")

_OPS = harness.REAL_VAULT / "_ops"
for _p in [str(_OPS), str(_OPS / "legs")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib        # noqa: E402
import wiring        # noqa: E402
import lead_sense    # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")
WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")

STRATA = {"description": ("Remedial works to common property including rendering and "
                          "repainting of external facade to residential flat building "
                          "of 24 units."),
          "address": "12 Wattle Crescent, Pyrmont NSW 2009",
          "cost_of_development": 820000, "lat": -33.87, "lng": 151.195,
          "applicant": "Pyrmont Owners Corp", "expected_aud": 8000}
FITOUT = {"description": ("Change of use to a retail premises, including internal "
                          "fitout and business identification signage."),
          "address": "106 King Street Sydney NSW 2000",
          "lat": -33.8675, "lng": 151.2070}
NOISE = {"description": "Demolition only of existing dwelling house.",
         "address": "5 Quiet St, Sydney NSW 2000", "cost_of_development": 60000}


class FakeLeg:
    """ضبط‌کنندهٔ intake — قراردادِ LeadLeg.intake بدونِ لجرِ واقعی."""
    def __init__(self):
        self.calls = []

    def intake(self, lead_name, expected_aud, cell="lead.doer", description="", day=None):
        self.calls.append({"name": lead_name, "exp": expected_aud,
                           "cell": cell, "desc": description, "day": day})
        return {"ok": True, "attribution_id": f"LEAD-TEST-{len(self.calls):03d}",
                "cell": cell, "expected_aud": expected_aud}


def _drop(name: str, lead: dict) -> Path:
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    box.mkdir(parents=True, exist_ok=True)
    p = box / f"{name}.json"
    p.write_text(json.dumps(lead, ensure_ascii=False), "utf-8")
    return p


def t_a_flag_off_is_noop():
    """flag خاموش → None؛ فایلِ صندوق دست‌نخورده."""
    os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
    p = _drop("untouched", STRATA)
    assert wiring.lead_discovery_beat(FakeLeg(), beat=0) is None
    assert p.exists(), "flag خاموش نباید صندوق را لمس کند"
    p.unlink()   # پاکسازیِ fixtureِ تستی (state موقت، نه vault)


def t_b_sense_score_propose():
    """flag روشن: ۳ کاندید → ۱ propose (strata) + ۱ save + ۱ skip؛ انتقال + سایدکار."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    try:
        _drop("a-strata", STRATA)
        _drop("b-fitout", FITOUT)
        _drop("c-noise", NOISE)
        leg = FakeLeg()
        wiring._EPOCH_STATE.clear()   # epoch-gate: هر پنجره یک شلیک؛ beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(leg, beat=30)
        assert r is not None and r["propose_only"] is True, r
        assert (r["sensed"], r["proposed"], r["saved"], r["skipped"]) == (3, 1, 1, 1), r
        # فقط strata به intake رسید، با نام/توضیح/ارزشِ درست
        assert len(leg.calls) == 1, leg.calls
        assert leg.calls[0]["name"] == "Pyrmont Owners Corp"
        assert leg.calls[0]["exp"] == 8000.0
        # فایل‌ها منتقل شدند (نه حذف) + سایدکارِ نتیجه
        box = opslib.STATE_DIR / "legs" / "lead-inbox"
        assert not list(box.glob("*.json")), "صندوق باید خالی شده باشد"
        allj = list((box / "processed").glob("*.json"))
        sides = [p for p in allj if p.name.endswith(".result.json")]
        moved = [p for p in allj if not p.name.endswith(".result.json")
                 and p.name != "_seen.json"]
        assert len(moved) == 3, moved
        assert len(sides) == 3, sides
        # سایدکارِ وضعیتِ ارگانیسم
        sp = opslib.STATE_DIR / "ORGANISM-STATE.lead_discovery"
        d = json.loads(sp.read_text("utf-8"))
        assert d["proposed"] == 1 and "updated_at" in d, d
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_c_dedup_idempotent():
    """همان محتوایِ strata دوباره → duplicate؛ هیچ intakeِ دوم (پایپ‌لاین idempotent)."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    try:
        _drop("a-strata-again", STRATA)
        leg = FakeLeg()
        wiring._EPOCH_STATE.clear()
        r = wiring.lead_discovery_beat(leg, beat=30)
        assert r["duplicates"] == 1 and r["proposed"] == 0, r
        assert leg.calls == [], leg.calls
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_d_killswitch_wins():
    """STOP مقدم بر flag — حتی روشن هم None."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    try:
        opslib.STOP_ORGANISM.write_text("test", "utf-8")
        try:
            assert wiring.lead_discovery_beat(FakeLeg(), beat=0) is None
        finally:
            opslib.STOP_ORGANISM.unlink()
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_e_cadence_and_no_leg():
    """beat غیرِ مضربِ N → None؛ lead_leg=None (بدونِ OCTOPUS_WIRE_LEAD) → None."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    try:
        assert wiring.lead_discovery_beat(FakeLeg(), beat=7) is None      # epoch 0 (beat<30)
        assert wiring.lead_discovery_beat(None, beat=0) is None           # بدونِ پا
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_f_structurally_wired_and_out_of_profile():
    """organism.py این beat را صدا می‌زند؛ flag عمداً خارج از PAPER_FULL_FLAGS."""
    assert "lead_discovery_beat(" in ORGANISM_SRC, "organism باید beat را صدا بزند"
    assert '"lead_discovery"' in ORGANISM_SRC, "کلیدِ merge در ORGANISM-STATE"
    assert "OCTOPUS_WIRE_LEAD_DISCOVERY" not in str(wiring.PAPER_FULL_FLAGS), \
        "flag نباید در پروفایلِ paper-full باشد (تولیدکنندهٔ PROPOSAL واقعی)"
    assert 'flag("OCTOPUS_WIRE_LEAD_DISCOVERY")' in WIRING_SRC


if __name__ == "__main__":
    for f in (t_a_flag_off_is_noop, t_b_sense_score_propose, t_c_dedup_idempotent,
              t_d_killswitch_wins, t_e_cadence_and_no_leg,
              t_f_structurally_wired_and_out_of_profile):
        f()
        print("ok", f.__name__)
    print("PASS test_lead_discovery_beat")
