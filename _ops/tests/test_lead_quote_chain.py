#!/usr/bin/env python3
"""تستِ مرحلهٔ ۵ نقشهٔ لید (2026-07-15): لیدِ امتیازخورده → پیش‌فاکتورِ قیمت‌خوردهٔ DRAFT.

یتیمِ create_quote (۰ caller) بسته شد. اثبات می‌کند:
  (الف) lead_to_intake: نگاشتِ قطعیِ لیدِ strata → segment/area/prep/access/risk درست.
  (ب) end-to-end واقعی (بدونِ mock در مسیرِ اصلی): lead_discovery_beat با LeadLegِ واقعی +
      attributionِ واقعی (لجرِ ایزولهٔ harness) + OCTOPUS_WIRE_LEAD_DRAFT →
      یک PROPOSALِ واقعیِ LEAD-YYYYMMDD-nnn + فایلِ lead-quote.v1 با همان attribution_id،
      draft_only=True و sent=False — صفر ارسال.
  (پ) flag LEAD_DRAFT خاموش → propose هست ولی هیچ draftی ساخته نمی‌شود.
  (ت) probeِ ساختگیِ زنجیرهٔ قدیمی حذف شده (بدونِ pendingِ واقعی → drafted=False).
$0 آفلاین؛ state/لجر ایزوله.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-quote-chain")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib      # noqa: E402
import wiring      # noqa: E402
import lead_quote  # noqa: E402
from leg import TaskPacket   # noqa: E402
from lead_leg import LeadLeg  # noqa: E402

STRATA = {"description": ("Remedial works to common property including rendering and "
                          "repainting of external facade and internal common areas of "
                          "heritage residential flat building of 24 units."),
          "address": "12 Wattle Crescent, Pyrmont NSW 2009",
          "cost_of_development": 820000, "lat": -33.87, "lng": 151.195,
          "applicant": "Pyrmont Owners Corp", "expected_aud": 8000, "size_m2": 450}


def _real_leg() -> LeadLeg:
    packet = TaskPacket(
        leg_id="lead-naghshi", organ="LEAD_PAINTING",
        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
        tools=("draft_quote",), budget_aud=5.0)
    return LeadLeg(packet, organ_table={"LEAD_PAINTING": 100.0})


def _drop(name, lead):
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    box.mkdir(parents=True, exist_ok=True)
    (box / f"{name}.json").write_text(json.dumps(lead, ensure_ascii=False), "utf-8")


def t_a_lead_to_intake_mapping():
    scored = {"category": "strata_remedial", "score": 100, "action": "draft"}
    intake = lead_quote.lead_to_intake(STRATA, scored)
    assert intake.segment == "strata", intake
    assert intake.area_type == "both", intake          # facade+internal → both
    assert intake.prep_level == "heavy", intake        # remedial
    assert intake.access_type == "scaffold", intake    # flat building
    assert "heritage" in intake.risk_flags, intake
    assert intake.size_m2 == 450.0, intake
    # لیدِ خالی → پیش‌فرض‌های امن، نه exception
    d = lead_quote.lead_to_intake({}, None)
    assert d.segment == "residential" and d.area_type == "interior", d


def t_b_end_to_end_real_propose_and_draft():
    """سختترین اثبات: پای واقعی + لجرِ واقعی + flag → PROPOSAL + lead-quote.v1."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_DRAFT"] = "1"
    try:
        _drop("strata-e2e", STRATA)
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(_real_leg(), beat=30)
        assert r is not None and r["proposed"] == 1, r
        # نتیجهٔ آرشیوی: intake ok با idِ واقعی + quote
        box = opslib.STATE_DIR / "legs" / "lead-inbox" / "processed"
        res = json.loads(sorted(box.glob("*.result.json"))[-1].read_text("utf-8"))
        aid = res["intake"]["attribution_id"]
        assert re.fullmatch(r"LEAD-\d{8}-\d{3}", aid), aid     # mintِ واقعی
        assert res.get("quote", {}).get("qt_number", "").startswith("QT-"), res
        # فایلِ draft با همان aid، draft_only + sent=False + قیمتِ بازه‌ای واقعی
        dpath = opslib.STATE_DIR / "legs" / "lead-drafts" / f"{aid}.json"
        d = json.loads(dpath.read_text("utf-8"))
        assert d["schema"] == "lead-quote.v1" and d["draft_only"] is True, d
        assert d["sent"] is False, d
        lo, hi = d["breakdown"]["total_incl_gst"]
        assert 0 < lo < hi, (lo, hi)                            # ۴۵۰m² → بازهٔ ناصفر
        assert d["intake"]["segment"] == "strata", d["intake"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_DRAFT", None)


def t_c_no_draft_without_flag():
    """LEAD_DRAFT خاموش → propose انجام می‌شود ولی هیچ quote ساخته نمی‌شود."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ.pop("OCTOPUS_WIRE_LEAD_DRAFT", None)
    try:
        lead = dict(STRATA, description=STRATA["description"] + " (بدونِ draft)")
        _drop("strata-nodraft", lead)
        drafts_before = set((opslib.STATE_DIR / "legs" / "lead-drafts").glob("*.json")) \
            if (opslib.STATE_DIR / "legs" / "lead-drafts").is_dir() else set()
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(_real_leg(), beat=30)
        assert r["proposed"] == 1, r
        box = opslib.STATE_DIR / "legs" / "lead-inbox" / "processed"
        res = json.loads(sorted(box.glob("*.result.json"),
                                key=lambda p: p.stat().st_mtime)[-1].read_text("utf-8"))
        assert "quote" not in res, res
        drafts_after = set((opslib.STATE_DIR / "legs" / "lead-drafts").glob("*.json")) \
            if (opslib.STATE_DIR / "legs" / "lead-drafts").is_dir() else set()
        assert drafts_after == drafts_before, "بدونِ flag نباید draftِ نو ساخته شود"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_d_probe_removed_from_chain():
    """زنجیرهٔ قدیمی دیگر LEAD-PROBE نمی‌سازد — الگوی صدازدنِ probe (f-string) باید
    از کد رفته باشد (ذکرش در docstringِ تاریخچه اشکالی ندارد)."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    assert 'f"LEAD-PROBE-' not in src, "callِ probeِ ساختگی باید حذف شده باشد"


if __name__ == "__main__":
    for f in (t_a_lead_to_intake_mapping, t_b_end_to_end_real_propose_and_draft,
              t_c_no_draft_without_flag, t_d_probe_removed_from_chain):
        f()
        print("ok", f.__name__)
    print("PASS test_lead_quote_chain")
