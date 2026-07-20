#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_outcome_spine.py — durable outcome spine + Paper Lead MVO (پیرو Stage-1).

پوشش (۹ سناریوی اجباری + UTC/schema): restart-replay · duplicate-suppression ·
concurrent-consume · failed-delivery-state · deferred-persistence · proposal→outcome-linkage ·
zero-external-side-effect (structural) · no-approval/settle-inference · deterministic-metrics.
$0 آفلاین؛ store روی temp path (state واقعی لمس نمی‌شود). بدونِ شبکه/Telegram/پول.
"""
import re
import sys
import tempfile
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "outcomes"),
           str(_HERE.parent / "legs"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("outcome-spine")

import outcome_store as osx    # noqa: E402
import paper_mvo               # noqa: E402

_LEAD = {"id": "LD-paper-1", "source": "planningalerts",
         "description": "exterior repaint of 3-storey apartment facade, weatherboard, peeling",
         "address": "12 Test St, Sydney NSW", "size_m2": 240}


def _store(td):
    return osx.OutcomeStore(path=Path(td) / "outcomes.db")


def t_a_paper_mvo_happy_path_and_linkage():
    """MVO کامل: delivered + accepted-measurement با IDهای مشترک (linkageِ proposal→outcome)."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        out = paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_test1")
        assert out["delivered"] is True and out["verdict"] == "accepted-measurement"
        evs = st.events(proposal_id=out["proposal_id"])
        assert {e["event_type"] for e in evs} == {"delivered", "accepted-measurement"}
        # همهٔ رویدادها IDهای یکسان دارند (linkage)
        for e in evs:
            assert e["correlation_id"] == out["correlation_id"]
            assert e["mission_id"] == "mis_test1"
            assert e["proposal_id"] == out["proposal_id"]
            assert e["leg_id"] == "lead" and e["lead_id"] == out["lead_id"]
        st.close()


def t_b_restart_replay_metrics_rebuilt():
    """پس از close/reopenِ همان فایل، metrics از rowsِ durable بازساخته می‌شود (replay)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "outcomes.db"
        st = osx.OutcomeStore(path=p)
        paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_r")
        m1 = st.metrics()
        st.close()
        st2 = osx.OutcomeStore(path=p)          # restart
        m2 = st2.metrics()
        assert m2["total_events"] == m1["total_events"] >= 2
        assert m2["delivered"] == 1 and m2["accepted_measurement"] == 1
        assert m2 == m1, "metrics باید پس از restart یکسان بازساخته شوند"
        st2.close()


def t_c_duplicate_suppression():
    """همان idempotency_key دوبار → یک ردیف؛ record دوم False."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        ev = {"correlation_id": "c1", "proposal_id": "P-x", "leg_id": "lead",
              "event_type": "delivered", "idempotency_key": "c1|P-x|delivered"}
        assert st.record(ev) is True
        assert st.record(dict(ev)) is False        # duplicate
        assert st.metrics()["delivered"] == 1
        st.close()


def t_d_concurrent_consume_exactly_once_per_key():
    """۱۶ threadِ همزمان با idempotency_keyِ یکسان → دقیقاً یک ردیفِ durable."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        results, start = [], threading.Event()
        ev = {"correlation_id": "cc", "proposal_id": "P-cc", "leg_id": "lead",
              "event_type": "delivered", "idempotency_key": "cc|P-cc|delivered"}

        def _w():
            start.wait()
            results.append(st.record(dict(ev)))
        ts = [threading.Thread(target=_w) for _ in range(16)]
        for t in ts:
            t.start()
        start.set()
        for t in ts:
            t.join()
        assert sum(1 for r in results if r) == 1, f"دقیقاً یک درجِ نو: {results}"
        assert st.metrics()["delivered"] == 1
        st.close()


def t_e_failed_delivery_not_marked_delivered():
    """deliver_ok=False → رویدادِ failed ثبت؛ هرگز delivered/accepted (failed≠seen)."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        out = paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_f", deliver_ok=False)
        assert out["delivered"] is False and out["verdict"] is None
        m = st.metrics()
        assert m["failed"] == 1 and m["delivered"] == 0 and m["accepted_measurement"] == 0
        st.close()


def t_f_deferred_persists_across_restart():
    """verdict=deferred → رویدادِ deferred پس از restart باقی می‌ماند."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "outcomes.db"
        st = osx.OutcomeStore(path=p)
        paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_d", verdict="deferred")
        st.close()
        st2 = osx.OutcomeStore(path=p)
        assert st2.metrics()["deferred"] == 1
        st2.close()


def t_g_deterministic_metrics():
    """ورودیِ یکسان روی دو storeِ تازه → metricsِ یکسان (بدونِ value/schema-drift)."""
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        s1, s2 = _store(td1), _store(td2)
        paper_mvo.run_paper_mvo(_LEAD, s1, mission_id="m", correlation_id="fixed")
        paper_mvo.run_paper_mvo(_LEAD, s2, mission_id="m", correlation_id="fixed")
        m1, m2 = s1.metrics(), s2.metrics()
        assert m1 == m2
        assert m1["schema_version"] == osx.SCHEMA_VERSION
        s1.close()
        s2.close()


def t_h_no_approval_or_settle_inference():
    """vocabulary سنجش ≠ تأییدِ I7: verdict «yes-measurement» است نه «approved»؛
    confirmed_revenue=0 (بدونِ reconcile)؛ value فقط claim."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_i")
        evs = st.events()
        verdicts = {e["verdict"] for e in evs if e["verdict"]}
        assert "approved" not in verdicts and "yes-measurement" in verdicts
        m = st.metrics()
        assert m["confirmed_revenue_aud"] == 0.0
        assert m["value_aud_claimed"] >= 0.0     # claim، نه revenue
        st.close()


def t_i_zero_external_side_effect_structural():
    """ساختاری (via ast — نه grepِ متنی، تا docstring را false-positive نگیرد): outcome_store/
    paper_mvo هیچ import از شبکه/Telegram و هیچ ارجاعِ کدیِ واقعی به settle/EffectorGate/
    approval_channel/send ندارند (spineِ outcome بیرونِ مسیرِ اثر است)."""
    import ast
    forbidden_imports = {"requests", "socket", "urllib", "http", "telegram", "approval_channel",
                         "effector", "tg_api", "approval_state_machine"}
    forbidden_names = {"EffectorGate", "settle", "sendMessage", "send_message",
                       "approval_channel", "record_effect"}
    for name in ("outcome_store.py", "paper_mvo.py"):
        src = (_HERE.parent / "outcomes" / name).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in forbidden_imports, f"{name} imports {a.name}"
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden_imports, \
                    f"{name} imports from {node.module}"
            elif isinstance(node, ast.Name):
                assert node.id not in forbidden_names, f"{name} references name {node.id}"
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, f"{name} references .{node.attr}"


def t_j_utc_aware_and_schema_versioned():
    """timestampها UTC-aware (offset دارند) و schema_version ثبت می‌شود."""
    with tempfile.TemporaryDirectory() as td:
        st = _store(td)
        paper_mvo.run_paper_mvo(_LEAD, st, mission_id="mis_u")
        e = st.events()[0]
        assert e["schema_version"] == osx.SCHEMA_VERSION
        # ISO با offset (…+00:00) = aware، نه naive
        assert e["recorded_at"].endswith("+00:00") and e["occurred_at"].endswith("+00:00")
        st.close()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_outcome_spine: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
