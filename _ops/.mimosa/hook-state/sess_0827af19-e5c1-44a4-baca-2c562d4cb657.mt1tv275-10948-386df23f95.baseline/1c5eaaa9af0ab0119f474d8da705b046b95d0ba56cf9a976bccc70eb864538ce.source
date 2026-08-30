#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_learning_wire.py — W1: تصمیمِ لید → خاطرهٔ **رسیددار و قابلِ‌استناد**.
قبل از پچ: خاطره episodic و بی‌رسید بود (هیچ خواننده‌ای ندارد) → قرمز.
$0 آفلاین؛ صفر شبکه/پول/effect؛ held-out استاب می‌شود تا لجرِ زندهٔ ژنوم subprocess نشود."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("lead-learning-wire")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "memory"), str(_OPS / "outcomes"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                       # noqa: E402
import memory_store as ms           # noqa: E402
import decision_receipt as dr       # noqa: E402
import outcome_store as osx         # noqa: E402
import learning_gate as lg          # noqa: E402
import lead_scorer                  # noqa: E402
import lead_outcome_recorder as lor  # noqa: E402
import wiring                       # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_DESC = "interior painting three bedrooms"
_LEAD = {"id": "L-w1", "description": _DESC}


def _close(*objs):
    for o in objs:
        try:
            o.close()
        except Exception:  # noqa: BLE001
            pass


def t_lead_decision_writes_receipted_citable_memory():
    for f in ("OCTOPUS_WIRE_MEMORY_GATE", "OCTOPUS_WIRE_LEAD_OUTCOME",
              "OCTOPUS_WIRE_LEARN_FROM_LEAD"):
        os.environ[f] = "1"
    # گیتِ held-out استاب (wiring همین ماژول را lazy import می‌کند → همین آبجکت)
    lg.fast_ledger_eval = lambda **_k: {"overall_verdict": "pass", "anti_hacking_flag": False}

    out = wiring._record_lead_decisions([(_LEAD, "attr-w1")], beat=1)
    assert out["recorded"] == 1, out
    assert out.get("memories_written") == 1, f"خاطره باید نوشته شود: {out}"

    store = ms.MemoryStore(path=_STATE / "memory" / "memory.db")
    # GAP-1 (۰۷-۳۱): مخزنِ رسید یکی شد — مسیرِ canonical همان receipts/receipts.db
    # است که c6_trigger/verdict_recorder می‌نویسند؛ outcomes/receipts.db دوپارهٔ کهنه بود.
    rcp = dr.DecisionReceiptStore(_STATE / "receipts" / "receipts.db")
    oc = osx.OutcomeStore(path=_STATE / "outcomes" / "outcomes.db")
    try:
        rows = store._conn.execute(
            "SELECT namespace, memory_id FROM memory "
            "WHERE admission_state='ADMITTED'").fetchall()
        assert rows, "هیچ خاطرهٔ admitted نوشته نشد"
        # (۱) در namespaceی که واقعاً خوانده می‌شود (lead_outcome_recorder.py:66)
        assert all(ns == "semantic" for ns, _ in rows), f"باید semantic باشد: {rows}"
        mid = rows[0][1]
        # (۲) no uncited admission — رسیدِ یادگیری واقعاً وجود دارد
        n = rcp._conn.execute("SELECT COUNT(*) FROM receipts WHERE receipt_json LIKE ?",
                              (f"%{mid}%",)).fetchone()[0]
        assert n == 1, f"خاطرهٔ admitted باید دقیقاً یک رسید داشته باشد: {n}"
        # (۳) حلقه بسته می‌شود: تصمیمِ بعدیِ هم‌دسته این خاطره را استناد می‌کند
        cat = str(lead_scorer.score_lead(_LEAD).category)
        dec = lor.record_lead_decision({"id": "L-w1b", "description": f"{_DESC} {cat}"},
                                       oc, rcp, memory_store=store,
                                       correlation_id="corr-w1b")
        cited = [m["memory_id"] for m in rcp.resolve(dec["receipt_id"]).get("memories_used", [])]
        assert mid in cited, f"تصمیمِ بعدی باید خاطرهٔ یادگرفته را استناد کند: {cited}"
    finally:
        _close(store, rcp, oc)


def t_flag_off_is_todays_behaviour():
    os.environ["OCTOPUS_WIRE_LEARN_FROM_LEAD"] = "0"
    out = wiring._record_lead_decisions([({"id": "L-w2", "description": _DESC}, "attr-w2")], beat=2)
    assert out["recorded"] == 1 and not out.get("learn_receipts"), out


if __name__ == "__main__":
    sys.exit(1 if harness.run([
        ("[W1] تصمیمِ لید → خاطرهٔ رسیددارِ semantic + استنادِ تصمیمِ بعدی",
         t_lead_decision_writes_receipted_citable_memory),
        ("[W1] flag خاموش = رفتارِ امروز", t_flag_off_is_todays_behaviour),
    ]) else 0)
