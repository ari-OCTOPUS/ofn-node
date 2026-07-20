#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_metric_separation.py — Worker D: تپش ≠ کار ≠ پیشنهاد ≠ نتیجه ≠ ارزش.

پوشش (تست‌های اجباری بریف):
  (a) heartbeat-only → liveness بدونِ هیچ کار/ارزشِ validated
  (b) پیشنهادِ بی‌رأی → صفر outcome/value
  (c) accepted-measurement → هرگز revenue
  (d) rejected/deferred جدا و بی‌ارزشِ مالی
  (e) fake delivery (sandbox/no-send) ≠ real delivery؛ compatِ مصرف‌کنندهٔ قدیم حفظ
  (f) بازساختِ قطعی پس از close/reopenِ store
  (g) goal_directed: baselineِ بی‌کلید هرگز moved نمی‌سازد (missing data ≠ success)
  (h) goal_directed: تحویلِ ارسال‌نشده moved نمی‌سازد وقتی producer صادق است
  (i) reachability (proposal_metrics→goal_directed) + سازگاریِ عقب‌روِ producerِ قدیمی
  (j) ساختاری: صفر شبکه/effector در ماژولِ جدید
$0 آفلاین؛ storeهای temp؛ state فقط در sandboxِ harness.
"""
import ast
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
ENV = harness.setup("metric-separation")

_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "metrics"),
           str(_OPS / "cortex"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                     # noqa: E402
import outcome_store as osx       # noqa: E402
import verdict_recorder as vr     # noqa: E402
import metric_separation as ms    # noqa: E402
import goal_directed as gd        # noqa: E402

_STATE_JSON = opslib.STATE_DIR / "ORGANISM-STATE.json"


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def _delivered(store, pid, channel, value=0.0):
    store.record({"correlation_id": f"c-{pid}", "proposal_id": pid, "leg_id": "lead",
                  "event_type": "delivered", "value_aud_claimed": value,
                  "idempotency_key": f"c-{pid}|{pid}|delivered",
                  "payload": ({"channel": channel} if channel is not None else {})})


def _reset_gd_state():
    for p in (gd.OUTCOMES, _STATE_JSON):
        if p.exists():
            p.unlink()


def _write_intent(baseline: dict, iid: str = "i1"):
    gd.OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with open(gd.OUTCOMES, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": "2026-07-21T00:00:00+00:00", "id": iid,
                            "title": "t", "baseline": baseline}, ensure_ascii=False) + "\n")


def _write_pm(pm: dict):
    _STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    _STATE_JSON.write_text(json.dumps({"proposal_metrics": pm}, ensure_ascii=False), "utf-8")


def t_a_heartbeat_only_liveness_no_work_no_value():
    """تپشِ خالی (فقط beat) → liveness > 0 ولی همهٔ tierهای کار/ارزش = صفر."""
    with _tmp() as td:
        st = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            m = ms.separated_metrics(st, state={"chrono": {"beat": 42}})
            assert m["liveness"] == 42
            for k in ("work_attempted", "proposal_issued", "proposal_delivered",
                      "proposal_fake_delivered", "owner_verdict", "validated_outcome",
                      "learning_update"):
                assert m[k] == 0, f"{k} باید با heartbeat-only صفر بماند: {m[k]}"
            assert m["validated_value_aud"] == 0.0
        finally:
            st.close()
    # storeِ غایب هم موفقیت نیست — صفرهای صادق
    m0 = ms.separated_metrics(None, state=None)
    assert m0["liveness"] == 0 and m0["proposal_delivered"] == 0
    assert m0["validated_value_aud"] == 0.0


def t_b_proposal_without_verdict_no_outcome_no_value():
    """پیشنهادِ تحویل‌شده ولی بی‌رأی → کار/تحویل شمرده می‌شود، outcome/ارزش هرگز."""
    with _tmp() as td:
        st = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            _delivered(st, "P-real", "telegram", value=300.0)
            m = ms.from_outcome_store(st)
            assert m["work_attempted"] == 1 and m["proposal_issued"] == 1
            assert m["proposal_delivered"] == 1 and m["proposal_fake_delivered"] == 0
            assert m["owner_verdict"] == 0 and m["validated_outcome"] == 0
            assert m["validated_value_aud"] == 0.0            # quote-claim درآمد نیست
            assert m["value_aud_quoted"] == 300.0             # claim جدا و با اسمِ صادق
        finally:
            st.close()


def t_c_accepted_measurement_is_not_revenue():
    """رأیِ «آره»ی مالک = سنجش با claim؛ هرگز revenue/validated نمی‌شود."""
    with _tmp() as td:
        st = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            r = vr.record_owner_verdict(st, proposal_id="P1", verdict="approved",
                                        value_aud_claimed=500.0)
            assert r["recorded"] is True
            m = ms.from_outcome_store(st)
            assert m["owner_accepted_measurement"] == 1 and m["owner_verdict"] == 1
            assert m["value_aud_claimed_accepted"] == 500.0
            assert m["validated_value_aud"] == 0.0 and m["validated_outcome"] == 0
            # compatِ قدیمی هم ناوردی را نگه می‌دارد
            assert st.metrics()["confirmed_revenue_aud"] == 0.0
        finally:
            st.close()


def t_d_rejected_deferred_distinct_no_value():
    """رد/تعویق جدا نمایندگی می‌شوند؛ هیچ‌کدام ارزش نمی‌سازند."""
    with _tmp() as td:
        st = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            vr.record_owner_verdict(st, proposal_id="Pn", verdict="rejected",
                                    value_aud_claimed=900.0)
            vr.record_owner_verdict(st, proposal_id="Pd", verdict="later",
                                    value_aud_claimed=900.0)
            m = ms.from_outcome_store(st)
            assert m["owner_rejected"] == 1 and m["owner_deferred"] == 1
            assert m["owner_accepted_measurement"] == 0
            assert m["value_aud_claimed_accepted"] == 0.0
            assert m["validated_value_aud"] == 0.0
        finally:
            st.close()


def t_e_fake_delivery_split_and_old_consumer_preserved():
    """sandbox/no-send/کانالِ نامعلوم = fake؛ کانالِ واقعی = real؛
    metrics() قدیمی (مصرف‌کنندهٔ داشبورد) دست‌نخورده جمعِ کل را می‌بیند."""
    with _tmp() as td:
        st = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            _delivered(st, "P-sbx", "sandbox")
            _delivered(st, "P-tg", "telegram")
            _delivered(st, "P-noch", None)          # payload بدونِ channel = اثبات‌نشده
            m = ms.from_outcome_store(st)
            assert m["proposal_delivered"] == 1, m
            assert m["proposal_fake_delivered"] == 2, m
            assert st.metrics()["delivered"] == 3   # compat: معنای قدیمی حفظ، جعل نشده
        finally:
            st.close()


def t_f_deterministic_rebuild_after_reopen():
    """separated metrics پس از close/reopenِ همان فایل عیناً بازساخته می‌شود."""
    with _tmp() as td:
        p = Path(td) / "o.db"
        st = osx.OutcomeStore(path=p)
        _delivered(st, "P-a", "sandbox", value=100.0)
        _delivered(st, "P-b", "telegram", value=250.0)
        vr.record_owner_verdict(st, proposal_id="P-b", verdict="approved",
                                value_aud_claimed=250.0)
        vr.record_owner_verdict(st, proposal_id="P-a", verdict="later")
        m1 = ms.separated_metrics(st)
        st.close()
        st2 = osx.OutcomeStore(path=p)              # restart
        try:
            m2 = ms.separated_metrics(st2)
            assert m1 == m2, f"بازساختِ قطعی شکست: {m1} != {m2}"
            assert m2["proposal_delivered"] == 1 and m2["proposal_fake_delivered"] == 1
            assert m2["owner_verdict"] == 2
        finally:
            st2.close()


def t_g_missing_baseline_key_never_becomes_success():
    """baselineِ قدیمی که متریکِ proposal را نسنجیده، از رشدِ آن moved نمی‌گیرد؛
    baselineِ کامل (صفرِ سنجیده) طبقِ قبل moved می‌گیرد (سازگارِ عقب‌رو)."""
    _reset_gd_state()
    try:
        # (۱) baselineِ pre-P0-G3: کلیدهای proposal اصلاً سنجیده نشده‌اند
        _write_intent({"confirmed_revenue": 0, "revenue_cells": 0,
                       "total_discoveries": 0}, iid="old1")
        _write_pm({"proposals_delivered": 5, "proposal_outcomes": 0,
                   "proposal_value_aud": 0.0})
        m = gd.measure()
        assert m["tracked"] >= 1
        assert m["moved"] is False, "کلیدِ نسنجیده در baseline نباید moved بسازد"
        # (۲) baselineِ کامل با صفرِ سنجیده → رشدِ واقعی moved می‌سازد (رفتارِ قبلی)
        _reset_gd_state()
        _write_intent({"confirmed_revenue": 0, "revenue_cells": 0, "total_discoveries": 0,
                       "proposals_delivered": 0, "proposal_outcomes": 0,
                       "proposal_value_aud": 0.0}, iid="new1")
        _write_pm({"proposals_delivered": 5, "proposal_outcomes": 0,
                   "proposal_value_aud": 0.0})
        assert gd.measure()["moved"] is True
    finally:
        _reset_gd_state()


def t_h_unsent_delivery_does_not_move_when_producer_honest():
    """producerِ صادق (proposals_sent موجود): کارتِ send-نشده کار نیست → moved=False؛
    اولین ارسالِ واقعی → moved=True."""
    _reset_gd_state()
    try:
        base = {"confirmed_revenue": 0, "revenue_cells": 0, "total_discoveries": 0,
                "proposals_delivered": 0, "proposal_outcomes": 0,
                "proposal_value_aud": 0.0, "proposals_sent": 0}
        _write_intent(base, iid="h1")
        _write_pm({"proposals_delivered": 4, "proposals_sent": 0,
                   "proposal_outcomes": 0, "proposal_value_aud": 0.0})
        assert gd.measure()["moved"] is False, "۴ تحویلِ ارسال‌نشده نباید moved بسازد"
        _write_pm({"proposals_delivered": 4, "proposals_sent": 1,
                   "proposal_outcomes": 0, "proposal_value_aud": 0.0})
        assert gd.measure()["moved"] is True, "ارسالِ واقعی باید moved بسازد"
    finally:
        _reset_gd_state()


def t_i_reachability_and_legacy_producer_compat():
    """(الف) reachability در سورس: organism هر tick متریکِ روتر را به state می‌نویسد و
    goal_directed از همان‌جا می‌خواند. (ب) producerِ قدیمی (بدونِ proposals_sent) →
    دقیقاً رفتارِ قبلی (رشدِ delivered → moved)."""
    org_src = (_OPS / "organism.py").read_text("utf-8")
    assert "_live_loop.proposal_metrics()" in org_src
    assert '"proposal_metrics"' in org_src
    gd_src = (_OPS / "cortex" / "goal_directed.py").read_text("utf-8")
    assert "proposal_metrics" in gd_src
    assert gd._METRIC_KEYS == ("confirmed_revenue", "revenue_cells", "total_discoveries",
                               "proposals_delivered", "proposal_outcomes",
                               "proposal_value_aud"), "قراردادِ کلیدهای قدیمی نباید عوض شود"
    # producerِ قدیمی: pm بدونِ proposals_sent → baseline هم کلید را ندارد (جعلِ صفر ممنوع)
    _reset_gd_state()
    try:
        _write_pm({"proposals_delivered": 0, "proposal_outcomes": 0,
                   "proposal_value_aud": 0.0})
        b = gd._baseline_metrics()
        assert "proposals_sent" not in b, "کلیدِ ناموجودِ producer نباید جعل شود"
        _write_intent(b, iid="lg1")
        _write_pm({"proposals_delivered": 2, "proposal_outcomes": 0,
                   "proposal_value_aud": 0.0})
        assert gd.measure()["moved"] is True   # رفتارِ قدیمی حفظ (backward-compatible)
    finally:
        _reset_gd_state()


def t_j_structural_zero_network_or_effector():
    """ماژولِ جدید ساختاراً بیرونِ مسیرِ اثر است: صفر import/نامِ شبکه/Telegram/settle."""
    src = (_OPS / "metrics" / "metric_separation.py").read_text("utf-8")
    tree = ast.parse(src)
    forbidden_imports = {"requests", "socket", "urllib", "http", "telegram", "tg_api",
                         "approval_channel", "effector", "approval_state_machine"}
    forbidden_names = {"EffectorGate", "settle", "sendMessage", "send_message",
                       "approval_channel", "record_effect", "mark_paid"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in forbidden_imports, a.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports, node.module
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden_names, node.id
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names, node.attr


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_metric_separation: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
