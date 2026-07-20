#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_outcome_wiring.py — قابلِ‌رسیدن‌بودنِ تولیدکنندهٔ spine در ضربانِ واقعی.

lead_outcome_recorder تا امروز flag داشت ولی صفر caller = ۱/۳ سیم‌کشی (آنتی‌الگوی
dead-flag). این تست اثبات می‌کند که lead_discovery_beat اکنون آن را واقعاً صدا می‌زند:
  (الف) OCTOPUS_WIRE_LEAD_OUTCOME خاموش → beat عیناً مثلِ امروز (کلیدِ "outcomes" نیست،
        receipts.db ساخته نمی‌شود) — بایت‌به‌بایت no-op.
  (ب)  روشن → لیدِ draft‌شده یک Decision Receiptِ immutable (E1) + Outcome (delivered،
        sandbox) پایدار می‌کند؛ verdict=PENDING (بدونِ جعل)؛ decision→outcome لینک است.
  (ج)  spineِ کامل: اگر Memory Gate از قبل db داشته باشد، receipt.memories_used پر می‌شود.
  (د)  fail-soft: اگر recorder throw کند، beat نمی‌میرد (فقط errors می‌شمارد).
  (ه)  ساختاری: flag در wiring خوانده می‌شود (reachability) + هیچ send/money در helper.
$0 آفلاین؛ state ایزوله (harness)؛ FakeLeg ضبط‌کنندهٔ intake. صفر شبکه/تلگرام/پول.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-outcome-wiring")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "outcomes"), str(_OPS / "memory")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib             # noqa: E402
import wiring             # noqa: E402
import outcome_store as osx        # noqa: E402
import decision_receipt as drx     # noqa: E402

WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")

STRATA = {"description": ("Remedial works to common property including rendering and "
                          "repainting of external facade to residential flat building "
                          "of 24 units."),
          "address": "12 Wattle Crescent, Pyrmont NSW 2009",
          "cost_of_development": 820000, "lat": -33.87, "lng": 151.195,
          "applicant": "Pyrmont Owners Corp", "expected_aud": 8000}


class FakeLeg:
    """ضبط‌کنندهٔ intake — قراردادِ LeadLeg.intake بدونِ لجرِ واقعی؛ attribution_id قطعیِ
    مختصِ هر تست (tag) تا correlation بین تست‌ها تصادم نکند."""
    def __init__(self, tag="TEST"):
        self.calls = []
        self.tag = tag

    def intake(self, lead_name, expected_aud, cell="lead.doer", description="", day=None):
        self.calls.append({"name": lead_name, "exp": expected_aud})
        return {"ok": True, "attribution_id": f"LEAD-{self.tag}-{len(self.calls):03d}",
                "cell": cell, "expected_aud": expected_aud}


def _drop(name: str, lead: dict) -> Path:
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    box.mkdir(parents=True, exist_ok=True)
    p = box / f"{name}.json"
    p.write_text(json.dumps(lead, ensure_ascii=False), "utf-8")
    return p


def _clean_inbox():
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    import shutil
    if box.exists():
        shutil.rmtree(box, ignore_errors=True)


def _receipts_db() -> Path:
    return opslib.STATE_DIR / "outcomes" / "receipts.db"


def _run_beat(tag):
    """یک لیدِ strataِ یکتا drop کن و beat را با FakeLeg(tag) در پنجرهٔ epoch شلیک کن.
    خروجی: (result, correlation_id) — corr = lead_LEAD-<tag>-001 (اولین intake)."""
    _clean_inbox()
    lead = dict(STRATA, description=STRATA["description"] + f" ref-{tag}")
    _drop(f"strata-{tag}", lead)
    wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
    r = wiring.lead_discovery_beat(FakeLeg(tag), beat=30)
    return r, f"lead_LEAD-{tag}-001"


def t_a_flag_off_no_spine_write():
    """OUTCOME خاموش (DISCOVERY روشن) → beat کارِ عادی؛ کلیدِ outcomes نیست، receipts.db دست‌نخورده."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ.pop("OCTOPUS_WIRE_LEAD_OUTCOME", None)
    try:
        pre = _receipts_db().exists()
        r, _corr = _run_beat("off")
        assert r is not None and r["proposed"] == 1, r          # کارِ عادیِ beat انجام شد
        assert "outcomes" not in r, "flag خاموش نباید spine را اجرا کند"
        assert _receipts_db().exists() == pre, "flag خاموش نباید receipts.db بسازد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_b_flag_on_persists_receipt_and_outcome_pending():
    """OUTCOME روشن → receiptِ E1 + outcome delivered پایدار؛ verdict=PENDING؛ لینک بسته."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTCOME"] = "1"
    try:
        r, corr = _run_beat("on")
        assert r["outcomes"]["recorded"] == 1 and r["outcomes"]["errors"] == 0, r
        o = osx.OutcomeStore(path=opslib.STATE_DIR / "outcomes" / "outcomes.db")
        try:
            evs = o.events(correlation_id=corr)
            assert evs and evs[0]["event_type"] == "delivered", evs
            assert evs[0]["verdict"] in (None, "PENDING", ""), evs[0]["verdict"]  # هرگز جعلِ رأی
            rid = json.loads(evs[0]["payload_json"])["receipt_id"]
        finally:
            o.close()
        rs = drx.DecisionReceiptStore(_receipts_db())
        try:
            rec = rs.resolve(rid)
            assert rec and rec["effect_class"] == "E1", rec
            assert rec["links"]["outcome_ref"] != "PENDING", rec["links"]   # decision→outcome بسته
            assert rec["integrity_ok"] is True
        finally:
            rs.close()
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTCOME", None)


def t_c_memories_used_through_beat():
    """spineِ کامل: با db حافظهٔ از پیش‌موجود، receipt.memories_used از drون beat پر می‌شود."""
    import memory_store as ms
    import gate as mg
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTCOME"] = "1"
    os.environ[mg.FLAG] = "1"
    mem_db = opslib.STATE_DIR / "memory" / "memory.db"
    mem_db.parent.mkdir(parents=True, exist_ok=True)
    try:
        mem = ms.MemoryStore(path=mem_db)
        try:
            mg.MemoryGate(mem).submit({"namespace": "semantic", "salience": 0.9,
                                       "content": "facade repainting remedial strata pays best",
                                       "mkey": "seg"})
        finally:
            mem.close()   # ببند تا beat خودش بازش کند (single-writer)
        r, corr = _run_beat("mem")
        assert r["outcomes"]["recorded"] == 1, r
        o = osx.OutcomeStore(path=opslib.STATE_DIR / "outcomes" / "outcomes.db")
        try:
            rid = json.loads(o.events(correlation_id=corr)[0]["payload_json"])["receipt_id"]
        finally:
            o.close()
        rs = drx.DecisionReceiptStore(_receipts_db())
        try:
            rec = rs.resolve(rid)
            assert rec["memories_used"], "spine باید حافظهٔ مرتبط را از drون beat cite کند"
            assert rec["memories_used"][0]["content_sha256"], rec["memories_used"]
        finally:
            rs.close()
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTCOME", None)
        os.environ.pop(mg.FLAG, None)
        # پاکسازیِ db حافظه تا t_b/t_a دیگر اثر نگیرند اگر دوباره اجرا شوند
        try:
            mem_db.unlink()
        except OSError:
            pass


def t_d_recorder_failure_is_failsoft():
    """اگر recorder throw کند، beat نمی‌میرد — فقط errors می‌شمارد (§۴)."""
    import lead_outcome_recorder as lor
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTCOME"] = "1"
    orig = lor.record_lead_decision

    def _boom(*a, **k):
        raise RuntimeError("simulated recorder failure")

    lor.record_lead_decision = _boom
    try:
        r, _corr = _run_beat("boom")
        assert r is not None and r["proposed"] == 1, "beat باید زنده بماند"
        assert r["outcomes"]["recorded"] == 0 and r["outcomes"]["errors"] == 1, r["outcomes"]
    finally:
        lor.record_lead_decision = orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTCOME", None)


def t_e_structural_reachable_and_no_send():
    """flag در wiring خوانده می‌شود (reachability بسته) + helper هیچ send/money ندارد."""
    import ast
    assert 'flag("OCTOPUS_WIRE_LEAD_OUTCOME")' in WIRING_SRC, "flag باید در wiring خوانده شود"
    assert "_record_lead_decisions" in WIRING_SRC
    # عمداً خارج از profile: هیچ سوییچِ profile نباید نوشتِ spine را خودکار روشن کند
    assert "OCTOPUS_WIRE_LEAD_OUTCOME" not in str(wiring.PAPER_FULL_FLAGS), \
        "flag نباید در PAPER_FULL_FLAGS باشد (تولیدکنندهٔ نوشتِ پایدار — فقط با رأیِ صریحِ مالک)"
    # helper نباید به effector/telegram/settle/send برسد
    tree = ast.parse(WIRING_SRC)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_record_lead_decisions"), None)
    assert fn is not None, "helper باید وجود داشته باشد"
    banned = {"EffectorGate", "settle", "send_message", "sendMessage", "mark_paid"}
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute):
            assert node.attr not in banned, f"helper نباید .{node.attr} داشته باشد"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""])
            for m in mods:
                assert m.split(".")[0] not in {"requests", "socket", "urllib", "http",
                                               "telegram"}, f"helper نباید {m} import کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_lead_outcome_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
