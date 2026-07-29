#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_outcome_recorder.py — بستنِ حلقهٔ لید record-only (spineِ end-to-end).

قیود: flag-off=no-op · lead→receipt→outcome با IDهای مشترک (linkage) · verdict=PENDING (بدونِ
جعل) · memories_used از Memory Gate (اگر باشد) · idempotent (تکرار=همان) · صفر send/money.
$0 آفلاین، همهٔ storeها temp.
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "outcomes"),
           str(_HERE.parent / "memory"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("lead-outcome")

import outcome_store as osx        # noqa: E402
import decision_receipt as dr      # noqa: E402
import memory_store as ms          # noqa: E402
import gate as mg                  # noqa: E402
import lead_outcome_recorder as lor  # noqa: E402

_LEAD = {"id": "LD-real-1", "source": "planningalerts",
         "description": "exterior repaint of 3-storey apartment facade strata remedial",
         "address": "5 Test Rd, Sydney NSW", "size_m2": 300}


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


class _On:
    def __init__(self, on=True):
        self.on = on

    def __enter__(self):
        self.p = os.environ.get(lor.FLAG)
        os.environ[lor.FLAG] = "1" if self.on else "0"
        return self

    def __exit__(self, *a):
        if self.p is None:
            os.environ.pop(lor.FLAG, None)
        else:
            os.environ[lor.FLAG] = self.p


def _stores(td):
    return (osx.OutcomeStore(path=Path(td) / "o.db"),
            dr.DecisionReceiptStore(Path(td) / "r.db"))


def t_a_flag_off_noop():
    with _On(on=False), _tmp() as td:
        o, r = _stores(td)
        assert lor.record_lead_decision(_LEAD, o, r) == {"skipped": "flag-off"}
        assert o.metrics()["total_events"] == 0
        o.close()
        r.close()


def t_b_closes_loop_with_shared_ids_and_pending():
    with _On(), _tmp() as td:
        o, r = _stores(td)
        out = lor.record_lead_decision(_LEAD, o, r, mission_id="mis-real")
        assert out["delivered"] is True and out["verdict"] == "PENDING"   # هرگز جعلِ رأی
        # receipt وجود دارد و به outcome لینک است (linkageِ واقعی)
        rec = r.resolve(out["receipt_id"])
        assert rec["mission_id"] == "mis-real" and rec["effect_class"] == "E1"
        assert rec["links"]["outcome_ref"] == out["outcome_ref"]          # decision→outcome بسته
        # outcome همان correlation/proposal را دارد
        evs = o.events(correlation_id=out["correlation_id"])
        assert evs and evs[0]["proposal_id"] == out["proposal_id"]
        o.close()
        r.close()


def t_c_memories_used_from_gate():
    """اگر Memory Gate حافظه داشته باشد، receipt.memories_used پر می‌شود (spine کامل)."""
    with _On(), _tmp() as td:
        os.environ[mg.FLAG] = "1"
        try:
            mem = ms.MemoryStore(path=Path(td) / "m.db")
            mg.MemoryGate(mem).submit({"namespace": "semantic", "salience": 0.9,
                                       "content": "strata remedial facade pays best", "mkey": "seg"})
            o, r = _stores(td)
            out = lor.record_lead_decision(_LEAD, o, r, memory_store=mem)
            assert out["memories_used"] >= 1, "باید حافظهٔ مرتبط را cite کند"
            rec = r.resolve(out["receipt_id"])
            assert rec["memories_used"] and rec["memories_used"][0]["content_sha256"]
            mem.close()
            o.close()
            r.close()
        finally:
            os.environ.pop(mg.FLAG, None)


def t_d_idempotent_replay():
    with _On(), _tmp() as td:
        o, r = _stores(td)
        a = lor.record_lead_decision(_LEAD, o, r, correlation_id="fixed", mission_id="m")
        b = lor.record_lead_decision(_LEAD, o, r, correlation_id="fixed", mission_id="m")
        assert a["receipt_id"] == b["receipt_id"] and a["outcome_ref"] == b["outcome_ref"]
        # یک outcome رویداد (idempotent)، نه دوتا
        assert o.metrics()["delivered"] == 1
        o.close()
        r.close()


def t_f_memory_prior_changes_action():
    """W2 (2026-07-29): همان لید، یک‌بار بی‌حافظه و یک‌بار با سابقهٔ ردشدهٔ همان
    دسته — اگر action عوض نشود، حافظه تزئینی است (تستِ کمینهٔ پیشنهادیِ خودِ
    سیستم در WS-ALL-cognitive-core §۵۱: استناد ≠ مصرف)."""
    with _On(), _tmp() as td:
        o, r = _stores(td)
        base = lor.record_lead_decision(_LEAD, o, r, correlation_id="base")
        assert base["action"] == base["action_pure"] == "draft", \
            f"فیکسچرِ strata باید بدونِ حافظه draft بدهد (got {base['action_pure']})"
        assert base["memory_prior"] is None
        o.close()
        r.close()
    with _On(), _tmp() as td:
        os.environ[mg.FLAG] = "1"
        try:
            mem = ms.MemoryStore(path=Path(td) / "m.db")
            mg.MemoryGate(mem).submit({
                "namespace": "semantic", "salience": 0.9, "mkey": "prior-1",
                "content": (f"lead-decision category={base['category']} score=80 "
                            f"action=draft verdict=rejected value_aud=0")})
            o, r = _stores(td)
            out = lor.record_lead_decision(_LEAD, o, r, memory_store=mem)
            assert out["action_pure"] == "draft" and out["action"] == "save", \
                f"سابقهٔ rejected باید draft→save کند (got {out['action']})"
            rec = r.resolve(out["receipt_id"])
            assert any(c.startswith("MEM_DEMOTE") for c in rec["reason_codes"]), \
                "اثرِ حافظه باید در reason_codes ممیزی‌پذیر باشد"
            assert rec["selected_alternative"] == "save"
            mem.close()
            o.close()
            r.close()
        finally:
            os.environ.pop(mg.FLAG, None)


def t_g_memory_prior_never_overrides_hard_skip():
    """priorِ حافظه فقط یک پله و هرگز روی skip — hard-filterهای scorer مقدس‌اند."""
    junk = {"id": "LD-skip-1", "source": "test",
            "description": "car respray automotive paint job"}
    with _On(), _tmp() as td:
        os.environ[mg.FLAG] = "1"
        try:
            mem = ms.MemoryStore(path=Path(td) / "m.db")
            o, r = _stores(td)
            base = lor.record_lead_decision(junk, o, r, memory_store=mem)
            if base["action_pure"] == "skip":       # فیکسچر واقعاً hard-skip خورد
                mg.MemoryGate(mem).submit({
                    "namespace": "semantic", "salience": 0.9, "mkey": "prior-2",
                    "content": (f"lead-decision category={base['category']} "
                                f"action=draft verdict=won value_aud=100")})
                out = lor.record_lead_decision(junk, o, r, memory_store=mem,
                                               correlation_id="c2")
                assert out["action"] == "skip", "حافظه نباید skip را لغو کند"
            mem.close()
            o.close()
            r.close()
        finally:
            os.environ.pop(mg.FLAG, None)


def t_e_no_send_no_money_structural():
    import ast
    forbidden = {"requests", "socket", "urllib", "http", "telegram", "tg_api",
                 "approval_channel", "effector", "mission_runner"}
    src = (_HERE.parent / "outcomes" / "lead_outcome_recorder.py").read_text("utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in forbidden, f"imports {a.name}"
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden, f"from {node.module}"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in {"EffectorGate", "settle", "send_message", "sendMessage"}, \
                f".{node.attr}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_lead_outcome_recorder: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
