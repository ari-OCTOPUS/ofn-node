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
import json
import os
import socket
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("paper-lead-mvo-e2e")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "outcomes"), str(_OPS / "spine"),
           str(_OPS / "memory"), str(_OPS / "metrics"), str(_OPS / "telegram_center")):
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
import paper_mvo                      # noqa: E402
import metric_separation as ms        # noqa: E402

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


def t_value_loop_gaps_ids_duplicate_failed_replay_negatives():
    """بستنِ شکاف‌های ممیزیِ حلقهٔ ارزش (Wave2-F) روی همان زنجیرهٔ production — یک حلقهٔ کامل:
      (الف) IDها در «کلِ» زنجیره ثابت: correlation/mission/proposal/leg/lead در receipt +
            هر رویدادِ outcome + spine یکی‌اند (نه فقط proposal_id).
      (ب) وضعِ صریحِ sandbox/fake-delivery: channel=sandbox روی رویدادِ durable؛
            metric_separation آن را fake می‌شمارد، هرگز real.
      (ج) رأیِ تکراریِ مالک → هیچ outcome/metric/spineِ تکراری (idempotent در زنجیره).
      (د) تحویلِ ساختگیِ شکست‌خورده (مسیرِ productionِ paper_mvo) → هرگز delivered/seen/verdict.
      (هـ) restart/reopen → «عیناً» همان رویدادها و همان metrics (بازساختِ قطعیِ Wave1-D).
      (و) منفی‌ها enforce شده: socket قفل (صفر شبکه در کلِ حلقه)؛ رأیِ settled/delivered/
            verified/paid رد می‌شود؛ واژگانِ store ساختاراً settled/verified ندارد؛
            confirmed_revenue=0 و validated_value=0 (revenue هرگز استنتاج نمی‌شود)؛
            هیچ ماژولِ effector/settle/approval_channel/tg_api/ps_writeback بار نشده."""
    os.environ[lor.FLAG] = "1"    # OCTOPUS_WIRE_LEAD_OUTCOME
    os.environ[esx.FLAG] = "1"    # OCTOPUS_WIRE_SPINE

    def _no_net(*_a, **_k):
        raise AssertionError("NETWORK FORBIDDEN: paper value loop must be socket-free")

    _orig_net = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)
    socket.socket.connect = _no_net
    socket.create_connection = _no_net
    socket.getaddrinfo = _no_net
    try:
        with _tmp() as _td:
            td = Path(_td)
            o_path, r_path, s_path = td / "outcomes.db", td / "receipts.db", td / "spine.db"
            o = osx.OutcomeStore(path=o_path)
            r = drx.DecisionReceiptStore(r_path)
            spine = esx.EventSpine(path=s_path)

            # (1) زنجیرهٔ production با IDهای صریح: intake→score→quote→receipt→delivered(sandbox)
            res = lor.record_lead_decision(_LEAD, o, r,
                                           mission_id="mis-e2e-gap", correlation_id="e2e-gap-corr")
            assert res.get("delivered") is True and res.get("verdict") == "PENDING", res
            pid, corr = res["proposal_id"], res["correlation_id"]
            mis, lid, claim = res["mission_id"], res["lead_id"], res["value_aud_claimed"]
            assert (corr, mis, lid) == ("e2e-gap-corr", "mis-e2e-gap", _LEAD["id"]), res

            # (2) وضعِ صریحِ sandbox/fake روی رویدادِ durable + تفکیکِ fake≠real (Wave1-D)
            dev = [e for e in o.events(correlation_id=corr) if e["event_type"] == "delivered"]
            assert len(dev) == 1, dev
            assert json.loads(dev[0]["payload_json"]).get("channel") == "sandbox", dev[0]
            assert ms.is_real_delivery(dev[0]) is False, "sandbox هرگز real نیست"
            sep0 = ms.from_outcome_store(o)
            assert sep0["proposal_fake_delivered"] == 1 and sep0["proposal_delivered"] == 0, sep0

            # (3) کارتِ fake-TG (render خالص، صفر send — گاردِ socket فعال است)
            card_text, card_kb = tgrender.render_decision(
                {"id": pid, "q": f"quote ~${claim:.0f} (sandbox)", "source": "lead"})
            assert card_text and card_kb

            # (4) رأیِ شبیه‌سازی‌شدهٔ مالک با threadingِ کاملِ IDها (mission+leg+lead)
            v1 = vr.record_owner_verdict(o, proposal_id=pid, verdict="approved",
                                         correlation_id=corr, mission_id=mis, leg_id="lead",
                                         lead_id=lid, value_aud_claimed=claim, event_spine=spine)
            assert v1["recorded"] is True and v1["event_type"] == "accepted-measurement", v1

            # (5) IDها در «کلِ» زنجیره ثابت: receipt + هر دو رویدادِ outcome + spine
            rec = r.resolve(res["receipt_id"])
            assert rec["trace_id"] == corr and rec["mission_id"] == mis, rec
            assert rec["links"]["outcome_ref"] == res["outcome_ref"], rec["links"]
            evs = o.events(correlation_id=corr)
            assert {e["event_type"] for e in evs} == {"delivered", "accepted-measurement"}, evs
            for e in evs:
                assert (e["proposal_id"], e["mission_id"], e["leg_id"], e["lead_id"],
                        e["correlation_id"]) == (pid, mis, "lead", lid, corr), e
            vev = [e for e in evs if e["event_type"] == "accepted-measurement"][0]
            vp = json.loads(vev["payload_json"])
            assert vp.get("measurement_only") is True and vev["verdict"] == "measurement", vev
            sev = spine.events(correlation_id=corr)
            assert len(sev) == 1 and sev[0]["domain"] == "proposal", sev
            assert sev[0]["mission_id"] == mis and sev[0]["subject"] == pid, sev[0]

            # (6) رأیِ تکراری → outcome/metrics/spine تکثیر نمی‌شود
            m_mid, sep_mid = o.metrics(), ms.from_outcome_store(o)
            v2 = vr.record_owner_verdict(o, proposal_id=pid, verdict="approved",
                                         correlation_id=corr, mission_id=mis, leg_id="lead",
                                         lead_id=lid, value_aud_claimed=claim, event_spine=spine)
            assert v2["recorded"] is False, v2
            assert o.metrics() == m_mid and ms.from_outcome_store(o) == sep_mid
            assert len(o.events(correlation_id=corr)) == len(evs)
            assert len(spine.events(correlation_id=corr)) == 1, "spine هم idempotent"

            # (7) تحویلِ ساختگیِ شکست‌خورده (production paper_mvo) → هرگز delivered/seen
            lead2 = dict(_LEAD, id="LD-e2e-2")
            out2 = paper_mvo.run_paper_mvo(lead2, o, mission_id="mis-e2e-gap2",
                                           correlation_id="e2e-gap-corr2", deliver_ok=False)
            assert out2["delivered"] is False and out2["verdict"] is None, out2
            evs2 = o.events(correlation_id="e2e-gap-corr2")
            assert {e["event_type"] for e in evs2} == {"failed"}, evs2
            sep1 = ms.from_outcome_store(o)
            assert sep1["proposal_fake_delivered"] == 1, sep1   # فقط حلقهٔ سالم
            assert sep1["proposal_delivered"] == 0, sep1        # هیچ تحویلِ واقعی، هرگز
            assert sep1["owner_verdict"] == 1, sep1             # شکست‌خورده seen/verdict ندارد
            assert sep1["work_attempted"] == 2, sep1            # ولی تلاش صادقانه شمرده شد

            # (8) منفی‌ها: استنتاجِ approval/settle/revenue ممنوع و بی‌اثر
            m_pre_bad = o.metrics()
            for bad in ("settled", "delivered", "verified", "paid"):
                rb = vr.record_owner_verdict(o, proposal_id=pid, verdict=bad,
                                             correlation_id=corr)
                assert rb["recorded"] is False, (bad, rb)
            assert o.metrics() == m_pre_bad, "رأیِ ممنوع نباید هیچ ردیفی بنویسد"
            assert "settled" not in osx.EVENT_TYPES and "verified" not in osx.EVENT_TYPES
            assert m_pre_bad["confirmed_revenue_aud"] == 0.0, m_pre_bad
            assert sep1["validated_outcome"] == 0 and sep1["validated_value_aud"] == 0.0, sep1
            assert sep1["value_aud_claimed_accepted"] == round(claim, 2), sep1  # claim، نه revenue
            _loaded = [m for m in sys.modules
                       for banned in ("effector", "settle", "approval_channel",
                                      "tg_api", "ps_writeback")
                       if banned in m.lower()]
            assert not _loaded, f"ماژولِ مسیرِ اثر/پول بار شده: {_loaded}"

            # (9) restart/reopen → «عیناً» همان رویدادها و همان metrics (بازساختِ قطعی)
            evs_all, m_before = o.events(), o.metrics()
            sep_before, sp_all = ms.from_outcome_store(o), spine.events()
            spine.close()
            o.close()
            r.close()
            o2 = osx.OutcomeStore(path=o_path)
            spine2 = esx.EventSpine(path=s_path)
            r2 = drx.DecisionReceiptStore(r_path)
            try:
                assert o2.events() == evs_all, "reopen باید هر row را عیناً بازسازی کند"
                assert o2.metrics() == m_before
                assert ms.from_outcome_store(o2) == sep_before   # بازساختِ قطعیِ Wave1-D
                assert spine2.events() == sp_all
                rec2 = r2.resolve(res["receipt_id"])
                assert rec2["integrity_ok"] is True, rec2
                assert rec2["links"]["outcome_ref"] == res["outcome_ref"], rec2["links"]

                # (10) digestِ مالک از storeِ reopen-شده (render خالص، صفر send)
                digest, _kb2 = tgrender.render_decision(
                    {"id": pid, "q": f"digest: accepted-measurement ${claim:.0f} claim "
                                     f"(fake={sep_before['proposal_fake_delivered']})",
                     "source": "lead"})
                assert digest
            finally:
                for _s in (o2, spine2, r2):
                    _s.close()
            print(f"     trace corr={corr} mission={mis} proposal={pid} leg=lead lead={lid}")
    finally:
        socket.socket.connect, socket.create_connection, socket.getaddrinfo = _orig_net
        os.environ.pop(lor.FLAG, None)
        os.environ.pop(esx.FLAG, None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_paper_lead_mvo_e2e: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
