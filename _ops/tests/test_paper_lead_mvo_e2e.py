#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_paper_lead_mvo_e2e.py — Sol Step 5: حلقهٔ ارزشِ Paper Lead سرتاسری (معیارِ اصلیِ پایان).

یک لیدِ synthetic از توابعِ **واقعیِ production** می‌گذرد و کلِ حلقه با IDهای ثابت بسته می‌شود:
  synthetic lead → score (lead_scorer) → quote/proposal (lead_quote + pricing) → fake TG card
  (render.render_decision، sandbox، صفر send) → durable decision (lead_outcome_recorder:
  Decision Receipt E1 + delivered outcome، PENDING) → simulated owner verdict (verdict_recorder:
  accepted-measurement) → event spine (verdict، دامنهٔ proposal) → replay (reopen) →
  deterministic metrics → owner digest.

قیود: صفر Telegram API / network / پول / send / PocketSmith / settle / EffectorGate.
revenue = claim فقط (نه confirmed). fake delivery صراحتاً sandbox. **همهٔ IDها (correlation/
proposal/leg) در تمامِ مسیر ثابت** — و outcomes.db همان delivered و همان accepted-measurement
را برای همان proposal دارد → حلقه واقعاً بسته است. storeها temp.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("paper-lead-mvo-e2e")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "outcomes"), str(_OPS / "spine"),
           str(_OPS / "memory"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lead_scorer                    # noqa: E402
import lead_quote                     # noqa: E402
import pricing                        # noqa: E402
import outcome_store as osx           # noqa: E402
import decision_receipt as drx        # noqa: E402
import event_spine as esx             # noqa: E402
import lead_outcome_recorder as lor   # noqa: E402
import verdict_recorder as vr         # noqa: E402
import render as tgrender             # noqa: E402

_LEAD = {"id": "LD-e2e-1", "source": "planningalerts",
         "description": "exterior repaint of 3-storey apartment facade strata remedial works",
         "applicant": "Pyrmont Owners Corp", "address": "12 Wattle Cres, Pyrmont NSW",
         "expected_aud": 8000, "size_m2": 300, "cost_of_development": 820000}


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def t_paper_lead_value_loop_end_to_end():
    os.environ[lor.FLAG] = "1"    # OCTOPUS_WIRE_LEAD_OUTCOME
    os.environ[esx.FLAG] = "1"    # OCTOPUS_WIRE_SPINE
    try:
        with _tmp() as _td:
            td = Path(_td)
            o_path, r_path, s_path = td / "outcomes.db", td / "receipts.db", td / "spine.db"

            # (1) SCORE — تابعِ واقعی
            scored = lead_scorer.score_lead(_LEAD)
            assert scored.action in ("draft", "save", "skip"), scored.action

            # (2) QUOTE/PROPOSAL — توابعِ واقعی (بدونِ leg، بدونِ شبکه)
            intake = lead_quote.lead_to_intake(_LEAD, scored.as_dict())
            bd = pricing.estimate_price(intake).to_dict()
            total = bd.get("total_incl_gst")
            claim = float(total[1]) if isinstance(total, (list, tuple)) and len(total) == 2 else 0.0
            assert claim >= 0.0, bd

            # (3) FAKE TG DELIVERY — کارتِ owner-visibleِ واقعی (render)، sandbox، صفر send
            card_text, card_kb = tgrender.render_decision(
                {"id": "e2e-card", "q": f"{scored.category} — quote ~${claim:.0f}", "source": "lead"})
            assert card_text and card_kb, "کارتِ owner-visible باید render شود"
            assert any("ok:" in str(b.get("callback_data", "")) for row in card_kb for b in row), card_kb

            # (4) DURABLE DECISION — Decision Receipt (E1) + delivered outcome (PENDING)
            o = osx.OutcomeStore(path=o_path)
            r = drx.DecisionReceiptStore(r_path)
            res = lor.record_lead_decision(_LEAD, o, r, correlation_id="e2e-corr")
            assert res["delivered"] is True and res["verdict"] == "PENDING", res
            pid, corr = res["proposal_id"], res["correlation_id"]
            rec = r.resolve(res["receipt_id"])
            assert rec["effect_class"] == "E1", rec

            # (5) SIMULATED OWNER VERDICT → durable outcome (همان proposal/correlation) + spine
            spine = esx.EventSpine(path=s_path)
            v = vr.record_owner_verdict(o, proposal_id=pid, verdict="approved",
                                        correlation_id=corr, leg_id="lead",
                                        value_aud_claimed=claim, event_spine=spine)
            assert v["recorded"] and v["event_type"] == "accepted-measurement", v
            assert v["event_type"] not in ("delivered", "settled", "failed"), v   # هرگز تحویل/تسویه

            # (6) EVENT SPINE — رأی به دامنهٔ proposal رفت
            sev = spine.events(correlation_id=corr)
            assert sev and sev[0]["domain"] == "proposal", sev
            spine.close()

            # (7) REPLAY — بستن و بازکردنِ store؛ رویدادها پایدارند و حلقه بسته است
            o.close()
            r.close()
            o2 = osx.OutcomeStore(path=o_path)
            try:
                evs = o2.events(correlation_id=corr)
                ets = {e["event_type"] for e in evs}
                assert "delivered" in ets and "accepted-measurement" in ets, ets   # حلقهٔ بسته
                # همهٔ IDها ثابت در تمامِ مسیر
                for e in evs:
                    assert e["proposal_id"] == pid, (e["event_type"], e["proposal_id"], pid)

                # (8) DETERMINISTIC METRICS (replay از rowsِ durable)
                m1, m2 = o2.metrics(), o2.metrics()
                assert m1 == m2, "metrics باید قطعی/بازتولیدپذیر باشد"
                assert m1["delivered"] >= 1 and m1["accepted_measurement"] >= 1, m1
                # revenue استنتاج نمی‌شود: value فقط CLAIM
                assert "revenue" not in m1 or float(m1.get("revenue") or 0.0) == 0.0
            finally:
                o2.close()

            # (9) OWNER DIGEST RENDERING — owner-visible، بدونِ send
            digest, _kb = tgrender.render_decision(
                {"id": pid, "q": f"lead {scored.category}: verdict accepted (measurement, ${claim:.0f} claim)",
                 "source": "lead"})
            assert digest and (scored.category.lower() in digest.lower()
                               or "lead" in digest.lower()), digest
    finally:
        os.environ.pop(lor.FLAG, None)
        os.environ.pop(esx.FLAG, None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_paper_lead_mvo_e2e: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
