#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_learning_loop.py — C3: حلقهٔ یادگیریِ durable + ضدخودفریبی، end-to-end.

پوشش (لیستِ اجباریِ C3):
  1. learn_from_outcome: outcomeِ trustِ بالا + held-out سبز → artifactِ durable (memory_id + رسید)
  2. loop closes: تصمیمِ بعدی (record_lead_decision واقعی) خاطرهٔ یادگرفته را **استناد** می‌کند (memory_id در memories_used)
  3. held-out FAIL → یادگیریِ مضر مسدود (صفر خاطره)
  4. anti-hacking (internal pass ولی held-out fail) → مسدود + پرچم
  5. dedupِ یادگیری: همان درسِ دوبار → دومی learned=False (صفر تکرار)
  6. outcome≠preference: trustِ پایین (ADVISORY) → یاد گرفته نمی‌شود
  7. rollback: خاطرهٔ مضر supersede/invalidate می‌شود (append-only)
  8. restart: خاطرهٔ یادگرفته بعد از reopen می‌ماند و همچنان بازیابی/استناد می‌شود
$0 آفلاین؛ صفر شبکه/پول/effect؛ store در sandbox.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("learning-loop")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "memory"),
           str(_OPS / "outcomes"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import memory_store as ms  # noqa: E402
import gate as gate_mod  # noqa: E402
import decision_receipt as dr  # noqa: E402
import outcome_store as osx  # noqa: E402
import learning_gate as lg  # noqa: E402
import lead_outcome_recorder as lor  # noqa: E402
import verdict_recorder as vr  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))


def _env_on():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTCOME"] = "1"


def _stores(tag):
    """per-test DB paths → بدونِ unlinkِ فایلِ قفل‌شده (Windows) بینِ تست‌ها."""
    memdb = _STATE / "memory" / f"memory-{tag}.db"
    rcpt = _STATE / "receipts" / f"receipts-{tag}.db"
    outdb = _STATE / "outcomes" / f"outcomes-{tag}.db"
    for p in (memdb, rcpt, outdb):
        p.parent.mkdir(parents=True, exist_ok=True)
    store = ms.MemoryStore(path=memdb)
    g = gate_mod.MemoryGate(store)
    rc = dr.DecisionReceiptStore(rcpt)
    oc = osx.OutcomeStore(path=outdb)
    return store, g, rc, oc, memdb


def _close(*objs):
    for o in objs:
        try:
            o.close()
        except Exception:  # noqa: BLE001
            pass


def _eval_pass(*, internal_metric_pass=True, **kw):
    return {"overall_verdict": "pass", "anti_hacking_flag": False}


def _eval_fail(*, internal_metric_pass=True, **kw):
    return {"overall_verdict": "fail", "anti_hacking_flag": False}


def _eval_anti_hack(*, internal_metric_pass=True, **kw):
    # internal گفت pass ولی held-out گفت fail → پرچمِ hacking
    return {"overall_verdict": "fail",
            "anti_hacking_flag": bool(internal_metric_pass)}


_LESSON = "painting leads scoring high in category interior tend to be accepted by owner"


_OREF = "corr-L1|P1|accepted-measurement"


def _learn(g, rc, oc, evaluator, mkey="lesson-interior-1", trust="OWNER_CONFIRMED",
           internal=True, salience=0.7, oref=_OREF, record_outcome=True):
    # outcome-binding: رأی واقعی مالک را از مسیر canonical ثبت می‌کنیم تا attestation
    # معتبر داشته باشیم (نه outcomeِ دستیِ خودنوشته).
    if record_outcome:
        vr.record_owner_verdict(oc, proposal_id="P1", verdict="approved",
                                correlation_id="corr-L1", leg_id="lead",
                                value_aud_claimed=0.0)
    return lg.learn_from_outcome(
        memory_gate=g, receipt_store=rc, outcome_store=oc,
        signal={"content": _LESSON, "mkey": mkey, "correlation_id": "corr-L1",
                "outcome_ref": oref, "trust": trust,
                "salience": salience, "source": "owner", "producer": "verdict_recorder"},
        evaluator=evaluator, internal_metric_pass=internal)


# ── ۱: artifactِ durable ────────────────────────────────────────────────────────
def t_learn_produces_durable_artifact():
    _env_on()
    store, g, rc, oc, _ = _stores("t1")
    try:
        r = _learn(g, rc, oc, _eval_pass)
        assert r["learned"] and r["memory_id"] and r["receipt_id"] and str(r["receipt_id"]).startswith("dr_"), f"{r}"
        assert store.get("semantic", "lesson-interior-1") is not None, "artifact باید در store باشد"
    finally:
        _close(store, rc, oc)


# ── ۲: loop closes — تصمیمِ بعدی خاطره را استناد می‌کند ─────────────────────────
def t_next_decision_cites_learned_memory():
    _env_on()
    store, g, rc, oc, _ = _stores("t2")
    try:
        r = _learn(g, rc, oc, _eval_pass)
        learned_mid = r["memory_id"]
        lead = {"id": "L-next", "description": "interior painting high score leads accepted"}
        dec = lor.record_lead_decision(lead, oc, rc, memory_store=store,
                                       correlation_id="corr-next")
        assert dec.get("receipt_id"), dec
        resolved = rc.resolve(dec["receipt_id"])
        cited = [m["memory_id"] for m in resolved.get("memories_used", [])]
        assert learned_mid in cited, f"تصمیمِ بعدی باید خاطره را استناد کند: {cited} vs {learned_mid}"
    finally:
        _close(store, rc, oc)


# ── ۳: held-out FAIL → یادگیریِ مضر مسدود ───────────────────────────────────────
def t_harmful_learning_blocked():
    _env_on()
    store, g, rc, oc, _ = _stores("t3")
    try:
        r = _learn(g, rc, oc, _eval_fail)
        assert not r["learned"] and "harmful" in r["reason"], f"{r}"
        assert store.get("semantic", "lesson-interior-1") is None, "خاطرهٔ مضر نباید نوشته شود"
    finally:
        _close(store, rc, oc)


# ── ۴: anti-hacking ─────────────────────────────────────────────────────────────
def t_anti_hacking_blocked():
    _env_on()
    store, g, rc, oc, _ = _stores("t4")
    try:
        r = _learn(g, rc, oc, _eval_anti_hack, internal=True)
        assert not r["learned"] and r["anti_hacking_flag"], f"{r}"
        assert store.get("semantic", "lesson-interior-1") is None
    finally:
        _close(store, rc, oc)


# ── ۵: dedupِ یادگیری ───────────────────────────────────────────────────────────
def t_duplicate_learning_is_zero():
    _env_on()
    store, g, rc, oc, _ = _stores("t5")
    try:
        r1 = _learn(g, rc, oc, _eval_pass)
        r2 = _learn(g, rc, oc, _eval_pass)   # همان درس دوباره
        assert r1["learned"] and not r2["learned"] and r2.get("dedup"), f"{r1} / {r2}"
        n = store._conn.execute(
            "SELECT COUNT(*) FROM memory WHERE mkey='lesson-interior-1'").fetchone()[0]
        assert n == 1, f"صفر یادگیریِ تکراری — باید فقط یک خاطره باشد: {n}"
    finally:
        _close(store, rc, oc)


# ── ۶: outcome≠preference ───────────────────────────────────────────────────────
def t_preference_not_learned():
    _env_on()
    store, g, rc, oc, _ = _stores("t6")
    try:
        r = _learn(g, rc, oc, _eval_pass, trust="ADVISORY")   # ادعای low-trust
        assert not r["learned"] and "preference" in r["reason"], f"{r}"
    finally:
        _close(store, rc, oc)


# ── ۷: rollback ─────────────────────────────────────────────────────────────────
def t_rollback_supersedes():
    _env_on()
    store, g, rc, oc, _ = _stores("t7")
    try:
        r = _learn(g, rc, oc, _eval_pass)
        mid = r["memory_id"]
        # پیش‌شرط: خاطره پیش از rollback واقعاً بازیابی می‌شود
        assert any(h.get("memory_id") == mid for h in
                   store.search("interior painting accepted", namespace="semantic", k=5))
        rb = lg.rollback_learning(memory_gate=g, memory_id=mid, content=_LESSON,
                                  mkey="lesson-interior-1", reason="regression")
        assert rb["rolled_back"], rb
        # red-team P1 fix: خاطرهٔ rollback‌شده دیگر **بازیابی/citable نیست** (نه فقط valid_to≠null)
        import memory_store as _ms2  # noqa: WPS433
        now = _ms2._utc_now_iso()
        active = store._conn.execute(
            "SELECT 1 FROM memory WHERE memory_id=? AND (valid_to IS NULL OR valid_to>?)",
            (mid, now)).fetchone()
        assert active is None, "خاطرهٔ rollback‌شده باید invalidate شود (valid_to→now)"
        assert not any(h.get("memory_id") == mid for h in
                       store.search("interior painting accepted", namespace="semantic", k=5)), \
            "خاطرهٔ rollback‌شده نباید در search بیاید (citable نباشد)"
    finally:
        _close(store, rc, oc)


# ── ۸: restart continuity ───────────────────────────────────────────────────────
def t_restart_learned_memory_persists():
    _env_on()
    store, g, rc, oc, memdb = _stores("t8")
    try:
        r = _learn(g, rc, oc, _eval_pass)
        mid = r["memory_id"]
    finally:
        _close(store, rc, oc)
    store2 = ms.MemoryStore(path=memdb)   # «restart»: reopen
    try:
        got = store2.get("semantic", "lesson-interior-1")
        assert got is not None and got.get("memory_id") == mid, "خاطره باید بعد از restart بماند"
        hits = store2.search("interior painting accepted", namespace="semantic", k=3)
        assert any(h.get("memory_id") == mid for h in hits), "خاطره باید بعد از restart بازیابی شود"
    finally:
        _close(store2)


# ── ۹: trustِ جعلی (outcome_ref در outcomes.db نیست) → رد ───────────────────────
def t_forged_trust_rejected():
    _env_on()
    store, g, rc, oc, _ = _stores("t9")
    try:
        # trust=OWNER_CONFIRMED ولی هیچ outcomeِ واقعی ثبت نشده (outcome_ref جعلی)
        r = _learn(g, rc, oc, _eval_pass, oref="corr-FORGED|X|accepted-measurement",
                   record_outcome=False)
        assert not r["learned"] and "unverified outcome" in r["reason"], f"{r}"
        assert store.get("semantic", "lesson-interior-1") is None, "trustِ جعلی نباید یاد گرفته شود"
        # و بدونِ outcome_store هم fail-closed
        r2 = lg.learn_from_outcome(memory_gate=g, receipt_store=rc, outcome_store=None,
                                   signal={"content": _LESSON, "mkey": "x", "trust": "OWNER_CONFIRMED",
                                           "outcome_ref": _OREF, "salience": 0.7},
                                   evaluator=_eval_pass)
        assert not r2["learned"] and "no-outcome-store" in r2["reason"], f"{r2}"
    finally:
        _close(store, rc, oc)


# ── ۱۰ (C7-S2): memory+receipt اتمیک — بدونِ رسید هیچ خاطرهٔ admitted ────────────
def t_no_memory_without_receipt():
    _env_on()
    store, g, rc, oc, _ = _stores("t10")
    try:
        oc.record({"correlation_id": "corr-L1", "proposal_id": "P1", "leg_id": "lead",
                   "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                   "idempotency_key": _OREF})
        base = dict(memory_gate=g, outcome_store=oc,
                    signal={"content": _LESSON, "mkey": "lesson-interior-1", "correlation_id": "corr-L1",
                            "outcome_ref": _OREF, "trust": "OWNER_CONFIRMED", "salience": 0.7,
                            "source": "owner", "producer": "owner"}, evaluator=_eval_pass)
        # (الف) بدونِ receipt_store → learned=False، خاطره admit نمی‌شود
        r1 = lg.learn_from_outcome(receipt_store=None, **base)
        assert not r1["learned"] and "receipt" in r1["reason"], f"{r1}"
        assert store.get("semantic", "lesson-interior-1") is None, "بدونِ رسید نباید خاطره بماند"

        # (ب) receipt_storeِ خطاده → learned=False، خاطره retract (بازیابی‌نشدنی)
        class _BadRcpt:
            def record(self, rec):
                raise RuntimeError("disk full")
        r2 = lg.learn_from_outcome(receipt_store=_BadRcpt(), **base)
        assert not r2["learned"] and "retracted" in r2["reason"], f"{r2}"
        now = ms._utc_now_iso()
        rows = store._conn.execute(
            "SELECT content, valid_to FROM memory WHERE mkey='lesson-interior-1'").fetchall()
        admitted = [c for (c, vt) in rows if (vt is None or vt > now) and not c.startswith("[RETRACTED")]
        assert not admitted, f"no uncited admission — خاطرهٔ بی‌رسید نباید admitted بماند: {admitted}"

        # (ج) با receipt_store سالم → learned=True + receipt_idِ واقعی
        r3 = lg.learn_from_outcome(memory_gate=g, outcome_store=oc, receipt_store=rc,
                                   signal={**base["signal"], "mkey": "lesson-ok"}, evaluator=_eval_pass)
        assert r3["learned"] and str(r3["receipt_id"]).startswith("dr_"), f"{r3}"
    finally:
        _close(store, rc, oc)


if __name__ == "__main__":
    failed = harness.run([
        ("[۱۰] memory+receipt اتمیک (no receipt→no admission)", t_no_memory_without_receipt),
        ("[۹] trustِ جعلی (outcome بایند نشده) رد", t_forged_trust_rejected),
        ("[۱] artifactِ durable (memory+receipt)", t_learn_produces_durable_artifact),
        ("[۲] تصمیمِ بعدی خاطره را استناد می‌کند", t_next_decision_cites_learned_memory),
        ("[۳] held-out FAIL → یادگیریِ مضر مسدود", t_harmful_learning_blocked),
        ("[۴] anti-hacking مسدود", t_anti_hacking_blocked),
        ("[۵] dedupِ یادگیری = صفر تکرار", t_duplicate_learning_is_zero),
        ("[۶] outcome≠preference", t_preference_not_learned),
        ("[۷] rollback supersede/invalidate", t_rollback_supersedes),
        ("[۸] restart: خاطره می‌ماند", t_restart_learned_memory_persists),
    ])
    sys.exit(1 if failed else 0)
