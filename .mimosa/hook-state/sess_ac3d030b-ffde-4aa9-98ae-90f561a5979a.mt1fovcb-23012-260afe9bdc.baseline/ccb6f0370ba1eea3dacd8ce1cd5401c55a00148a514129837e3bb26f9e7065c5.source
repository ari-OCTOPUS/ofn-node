#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_memory_gate.py — Memory Gate v1 (store + FSM) + join واقعی به Decision Receipt.

قیودِ اثبات‌شده: flag-off=no-op · reject(unknown-ns/empty/secret/owner-only) · self_knowledge=
ADVISORY-همیشه (رفعِ حلقهٔ خودتقویت) · procedural/owner_fact از LLM=propose-not-commit، از owner=
OWNER_CONFIRMED · semantic salience-bar · dedupe · supersession · retrieve(get/search) ·
as_memories_used→decision_receipt.record · restart-persist · concurrency · taxonomy=single-source.
$0 آفلاین، store روی temp.
"""
import os
import sys
import tempfile
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "memory"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("memory-gate")

import taxonomy as tax          # noqa: E402
import memory_store as ms       # noqa: E402
import gate as mg               # noqa: E402
import decision_receipt as dr   # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


class _Env:
    def __init__(self, on=True):
        self.on = on

    def __enter__(self):
        self.prev = os.environ.get(mg.FLAG)
        os.environ[mg.FLAG] = "1" if self.on else "0"
        return self

    def __exit__(self, *a):
        if self.prev is None:
            os.environ.pop(mg.FLAG, None)
        else:
            os.environ[mg.FLAG] = self.prev


def _gate(td):
    st = ms.MemoryStore(path=Path(td) / "memory.db")
    return mg.MemoryGate(st, proposal_path=Path(td) / "proposals.jsonl"), st


def t_a_flag_off_is_noop():
    with _Env(on=False), _tmp() as td:
        g, st = _gate(td)
        out = g.submit({"namespace": "semantic", "content": "x", "salience": 0.9})
        assert out["verb"] == "skip" and out["reason"] == "flag-off"
        assert st.metrics()["total"] == 0
        st.close()


def t_b_self_knowledge_always_advisory():
    """رفعِ حلقهٔ خودتقویت: خروجیِ خامِ LLM هرگز OWNER_CONFIRMED/DETERMINISTIC نمی‌شود."""
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        out = g.submit({"namespace": "self_knowledge", "source": "llm:think",
                        "content": "the organism believes X", "mkey": "understanding"})
        assert out["verb"] == "commit" and out["trust"] == "ADVISORY"
        # L-08/E16 (fixed): a claimant-set external_graded flag must NOT promote
        # trust — GRADED requires an INDEPENDENT grader receipt, so a bare
        # external_graded=True from the claimant stays ADVISORY (no self-grading).
        out2 = g.submit({"namespace": "self_knowledge", "source": "llm:think",
                         "content": "graded belief", "external_graded": True})
        assert out2["trust"] == "ADVISORY"
        # هرگز OWNER_CONFIRMED از llm:
        assert st.get("self_knowledge", "understanding")["trust"] == "ADVISORY"
        st.close()


def t_c_procedural_owner_only_propose_not_commit():
    """procedural/owner_fact از LLM/agent = propose (نه commit)؛ از owner = OWNER_CONFIRMED."""
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        # از منبعِ llm → propose، صفر commit
        out = g.submit({"namespace": "procedural", "source": "llm:think",
                        "content": "always deduct 10%", "mkey": "rule1"})
        assert out["verb"] == "propose"
        assert st.get("procedural", "rule1") is None, "LLM نباید procedural را commit کند"
        # از owner → commit OWNER_CONFIRMED
        out2 = g.submit({"namespace": "owner_fact", "source": "owner",
                         "content": "ABN is 123", "mkey": "abn"})
        assert out2["verb"] == "commit" and out2["trust"] == "OWNER_CONFIRMED"
        # deterministic → procedural commit DETERMINISTIC
        out3 = g.submit({"namespace": "procedural", "source": "deterministic",
                         "content": "merchant X -> cat Y", "mkey": "m-x"})
        assert out3["trust"] == "DETERMINISTIC"
        st.close()


def t_d_reject_secret_empty_unknown_owneronly():
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        assert g.submit({"namespace": "semantic", "content": "sk-ABCDEFGHIJKL123 leak"})["verb"] == "reject"
        assert g.submit({"namespace": "semantic", "content": "api_key=xyz"})["verb"] == "reject"
        assert g.submit({"namespace": "semantic", "content": ""})["verb"] == "reject"
        assert g.submit({"namespace": "nope", "content": "x"})["verb"] == "reject"
        assert g.submit({"namespace": "owner_fact", "source": "llm:think",
                         "content": "secret plan", "privacy": "owner_only"})["verb"] == "reject"
        st.close()


def t_e_semantic_salience_bar():
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        assert g.submit({"namespace": "semantic", "content": "high", "salience": 0.9})["verb"] == "commit"
        assert g.submit({"namespace": "semantic", "content": "low", "salience": 0.1})["verb"] == "reject"
        st.close()


def t_f_dedupe_and_supersession():
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        a = g.submit({"namespace": "semantic", "content": "same", "mkey": "k", "salience": 0.9})
        assert a["verb"] == "commit"
        dup = g.submit({"namespace": "semantic", "content": "same", "mkey": "k", "salience": 0.9})
        assert dup["verb"] == "skip" and dup["reason"].startswith("dedupe")
        # supersede: نسخهٔ جدید کهنه را invalidate می‌کند؛ get آخری را می‌دهد
        b = g.submit({"namespace": "semantic", "content": "newer", "mkey": "k",
                      "salience": 0.9, "supersedes": a["memory_id"]})
        assert b["verb"] == "commit"
        cur = st.get("semantic", "k")
        assert cur["content"] == "newer"
        st.close()


def t_g_retrieve_and_join_to_decision_receipt():
    """as_memories_used → decision_receipt.record واقعی (تولیدکنندهٔ گمشدهٔ memories_used)."""
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        g.submit({"namespace": "semantic", "content": "strata remedial pays best",
                  "mkey": "seg-strata", "salience": 0.8})
        recs = st.search("strata", namespace="semantic", k=3)
        assert recs and recs[0]["content_sha256"]
        mem_used = st.as_memories_used(recs)
        assert set(mem_used[0]) == {"memory_id", "content_sha256", "trust_grade", "retrieved_at"}
        # جوینِ واقعی: رسیدِ تصمیم این memoryها را می‌پذیرد (validatorش hex64 می‌خواهد)
        rst = dr.DecisionReceiptStore(Path(td) / "receipts.db")
        rid = rst.record({"objective": "quote strata lead", "effect_class": "E2",
                          "reason_codes": ["SEG_STRATA"], "memories_used": mem_used})
        r = rst.resolve(rid)
        assert r["memories_used"][0]["content_sha256"] == mem_used[0]["content_sha256"]
        rst.close()
        st.close()


def t_h_restart_persist():
    with _Env(), _tmp() as td:
        p = Path(td) / "memory.db"
        st = ms.MemoryStore(path=p)
        mg.MemoryGate(st).submit({"namespace": "semantic", "content": "persist me",
                                  "mkey": "pk", "salience": 0.9})
        st.close()
        st2 = ms.MemoryStore(path=p)
        assert st2.get("semantic", "pk")["content"] == "persist me"
        assert st2.metrics()["active"] == 1
        st2.close()


def t_i_concurrent_submit():
    with _Env(), _tmp() as td:
        g, st = _gate(td)
        start = threading.Event()

        def _w(i):
            start.wait()
            g.submit({"namespace": "semantic", "content": f"c{i}", "mkey": f"k{i}", "salience": 0.9})
        ts = [threading.Thread(target=_w, args=(i,)) for i in range(16)]
        for t in ts:
            t.start()
        start.set()
        for t in ts:
            t.join()
        assert st.metrics()["active"] == 16
        st.close()


def t_j_taxonomy_single_source():
    """taxonomy مرجعِ یگانه است: trust/namespace/effect یکسان در memory + decision_receipt."""
    assert "ADVISORY" in tax.TRUST_GRADES and "OWNER_CONFIRMED" in tax.TRUST_GRADES
    assert tax.trust_at_least("OWNER_CONFIRMED", "ADVISORY") is True
    assert tax.trust_at_least("ADVISORY", "OWNER_CONFIRMED") is False
    assert set(tax.COMMIT_RULES) == set(tax.NAMESPACES)
    # gate/store همان taxonomy را import می‌کنند (نه enumِ محلی)
    assert mg.tax is tax and ms.tax is tax


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_memory_gate: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
