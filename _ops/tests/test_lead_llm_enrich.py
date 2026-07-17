#!/usr/bin/env python3
"""تستِ مرحلهٔ ۴ نقشهٔ لید (2026-07-15): غنی‌سازیِ اختیاریِ $0 با LLMِ محلی.

اثبات می‌کند:
  (الف) flag خاموش (پیش‌فرض): هیچ llm_note و هیچ callِ ask — بایت‌به‌بایتِ مرحلهٔ ۲.
  (ب) flag روشن + askِ mock: llm_note در نتیجهٔ آرشیوی می‌آید ولی score/action
      از امتیازدهندهٔ قطعی دست‌نخورده می‌ماند (llm هرگز gate را عوض نمی‌کند).
  (پ) askِ خراب (exception) → fail-soft، beat سالم.
$0 آفلاین؛ ask مونکی‌پچ؛ state ایزوله.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-llm-enrich")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib         # noqa: E402
import wiring         # noqa: E402
import model_router   # noqa: E402

STRATA = {"description": ("Remedial works to common property including rendering and "
                          "repainting of external facade to residential flat building "
                          "of 24 units."),
          "address": "12 Wattle Crescent, Pyrmont NSW 2009",
          "cost_of_development": 820000, "lat": -33.87, "lng": 151.195,
          "applicant": "Pyrmont Owners Corp"}


class FakeLeg:
    def intake(self, lead_name, expected_aud, cell="lead.doer", description="", day=None):
        return {"ok": True, "attribution_id": "LEAD-TEST-001",
                "cell": cell, "expected_aud": expected_aud}


def _drop(name, lead):
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    box.mkdir(parents=True, exist_ok=True)
    (box / f"{name}.json").write_text(json.dumps(lead, ensure_ascii=False), "utf-8")


def _last_result():
    box = opslib.STATE_DIR / "legs" / "lead-inbox" / "processed"
    sides = sorted(box.glob("*.result.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(sides[-1].read_text("utf-8"))


def t_a_flag_off_no_llm_call():
    burned = []
    orig = model_router.ask
    model_router.ask = lambda *a, **k: burned.append(1) or {"ok": True, "text": "x"}
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ.pop("OCTOPUS_WIRE_LEAD_LLM", None)
    try:
        _drop("s1", STRATA)
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(FakeLeg(), beat=30)
        assert r["proposed"] == 1, r
        assert burned == [], "با flag خاموش نباید ask صدا شود"
        assert "llm_note" not in _last_result(), _last_result()
    finally:
        model_router.ask = orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_b_flag_on_enriches_without_changing_gate():
    orig = model_router.ask
    model_router.ask = lambda *a, **k: {"ok": True, "tier": "local",
                                        "text": "لیدِ strata، فوریتِ بالا"}
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_LLM"] = "1"
    try:
        lead = dict(STRATA, description=STRATA["description"] + " (llm-b)")
        _drop("s2", lead)
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(FakeLeg(), beat=30)
        assert r["proposed"] == 1, r
        res = _last_result()
        assert res.get("llm_note", "").startswith("لیدِ strata"), res
        # امتیازدهندهٔ قطعی مرجع ماند: همان score/actionِ مرحلهٔ ۲
        assert res["score"] == 100 and res["action"] == "draft", res
    finally:
        model_router.ask = orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_LLM", None)


def t_c_llm_failure_fail_soft():
    orig = model_router.ask
    def _boom(*a, **k):
        raise RuntimeError("ollama down")
    model_router.ask = _boom
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_LLM"] = "1"
    try:
        lead = dict(STRATA, description=STRATA["description"] + " (llm-c)")
        _drop("s3", lead)
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(FakeLeg(), beat=30)
        assert r is not None and r["proposed"] == 1, r     # beat زنده ماند
        assert "llm_note" not in _last_result()
    finally:
        model_router.ask = orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_LLM", None)


if __name__ == "__main__":
    for f in (t_a_flag_off_no_llm_call, t_b_flag_on_enriches_without_changing_gate,
              t_c_llm_failure_fail_soft):
        f()
        print("ok", f.__name__)
    print("PASS test_lead_llm_enrich")
