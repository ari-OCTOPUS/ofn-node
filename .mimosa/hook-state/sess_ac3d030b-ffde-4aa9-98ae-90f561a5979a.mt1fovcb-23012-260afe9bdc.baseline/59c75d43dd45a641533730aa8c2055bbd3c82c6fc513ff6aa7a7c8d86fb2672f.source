#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_decision_receipt.py — رسیدِ تصمیمِ immutable + join به outcome_store (قرارداد مالک).

قیودِ سخت که اثبات می‌شوند: immutability · no-chain-of-thought · no-raw-memory/secret ·
verdict=reference-not-authorization · idempotent+replayable outcome join · missing=PENDING
(نه جعلِ موفقیت) · no-self-upgrade (trust/verdict/effect_class) · corruption-detect ·
concurrency · zero-executive-side-effect (ast). $0 آفلاین، store روی temp path.
"""
import sys
import tempfile
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("decision-receipt")

import decision_receipt as dr   # noqa: E402
import outcome_store as osx     # noqa: E402
import paper_mvo                # noqa: E402


def _tmp():
    """TemporaryDirectory مقاوم به lockِ WALِ ویندوز (فایل بعد از close لحظه‌ای lock می‌ماند)."""
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:      # Python < 3.10
        return tempfile.TemporaryDirectory()


def _receipt(**over):
    base = {
        "trace_id": "tr-1", "mission_id": "mis-1",
        "created_at": "2026-07-20T10:00:00+00:00",
        "objective": "quote a painting lead",
        "alternatives": ["draft", "skip"],
        "selected_alternative": "draft",
        "reason_codes": ["SCORE_HIGH", "SEGMENT_STRATA"],
        "assumptions": ["size from description"],
        "memories_used": [{"memory_id": "m1", "content_sha256": "a" * 64,
                           "trust_grade": "MEDIUM", "retrieved_at": "2026-07-20T09:59:00+00:00"}],
        "predicted_outcome": {"accept_prob": 0.4},
        "effect_class": "E2", "policy_sha256": "b" * 64,
    }
    base.update(over)
    return base


def _store(td):
    return dr.DecisionReceiptStore(Path(td) / "receipts.db")


def t_a_record_resolve_roundtrip_pending():
    with _tmp() as td:
        st = _store(td)
        rid = st.record(_receipt())
        r = st.resolve(rid)
        assert r["receipt_id"] == rid and r["status"] == "RECORDED"
        # join‌های غایب = PENDING صریح، نه جعلِ موفقیت
        assert r["links"]["outcome_ref"] == "PENDING" and r["links"]["verdict_ref"] == "PENDING"
        assert r["objective"] == "quote a painting lead" and r["effect_class"] == "E2"
        assert r["integrity_ok"] is True
        st.close()


def t_b_immutable_rerecord_no_overwrite():
    """رسید immutable است: re-record با همان id-fields ولی trust/verdictِ متفاوت → اصل حفظ."""
    with _tmp() as td:
        st = _store(td)
        rid = st.record(_receipt(memories_used=[{"memory_id": "m1", "content_sha256": "a" * 64,
                                                 "trust_grade": "LOW"}]))
        # تلاش برای «ارتقا»ی trust با re-record → باید بی‌اثر بماند (immutable)
        rid2 = st.record(_receipt(memories_used=[{"memory_id": "m1", "content_sha256": "a" * 64,
                                                  "trust_grade": "HIGH"}]))
        assert rid == rid2
        r = st.resolve(rid)
        assert r["memories_used"][0]["trust_grade"] == "LOW", "trust نباید با re-record ارتقا یابد"
        st.close()


def t_c_no_chain_of_thought():
    with _tmp() as td:
        st = _store(td)
        for bad in ({"reasoning": "long..."}, {"chain_of_thought": "x"}, {"transcript": "y"},
                    {"objective": "z" * 400}, {"reason_codes": ["x" * 100]},
                    {"predicted_outcome": {"nested": {"reasoning": "hidden CoT"}}},  # تودرتو
                    {"predicted_outcome": {"deep": [{"thoughts": "x"}]}}):           # در list
            try:
                st.record(_receipt(**bad))
                assert False, f"باید رد شود: {list(bad)[0]}"
            except dr.ReceiptValidationError:
                pass
        st.close()


def t_d_no_raw_memory_or_secret():
    with _tmp() as td:
        st = _store(td)
        for badmem in ([{"content_sha256": "a" * 64, "content": "raw note"}],
                       [{"content_sha256": "a" * 64, "token": "sk-xxx"}],
                       [{"memory_id": "m", "text": "raw"}],       # no hash + raw text
                       [{"memory_id": "m"}],                      # missing content_sha256
                       [{"content_sha256": "a" * 64, "memory_id": "x" * 200}]):  # raw dumped in memory_id
            try:
                st.record(_receipt(memories_used=badmem))
                assert False, f"باید رد شود: {badmem}"
            except dr.ReceiptValidationError:
                pass
        st.close()


def t_e_verdict_is_reference_not_authorization():
    """verdict/approval فقط reference‌اند؛ هیچ flagِ authorized/executable تولید نمی‌شود."""
    with _tmp() as td:
        st = _store(td)
        rid = st.record(_receipt())
        st.link(rid, "verdict", "approval-store:jid-123", note="owner yes")
        st.link(rid, "approval", "aps:jid-123")
        r = st.resolve(rid)
        assert r["links"]["verdict_ref"] == "approval-store:jid-123"
        # صفر نشانهٔ اجرا/مجوز در رسید:
        blob = str(r).lower()
        assert "authorized" not in blob and "execute" not in blob and "granted" not in blob
        st.close()


def t_f_outcome_join_idempotent_and_replayable():
    with _tmp() as td:
        p = Path(td) / "receipts.db"
        st = dr.DecisionReceiptStore(p)
        # یک outcome واقعی از spine بساز و link کن
        ost = osx.OutcomeStore(path=Path(td) / "outcomes.db")
        out = paper_mvo.run_paper_mvo({"id": "LD1", "description": "exterior repaint", "size_m2": 100},
                                      ost, mission_id="mis-1")
        oref = f"{out['correlation_id']}|{out['proposal_id']}|accepted"
        rid = st.record(_receipt())
        assert st.link_outcome(rid, oref) is True
        assert st.link_outcome(rid, oref) is False   # idempotent
        st.close()
        st2 = dr.DecisionReceiptStore(p)             # restart → replay
        assert st2.resolve(rid)["links"]["outcome_ref"] == oref
        ost.close()
        st2.close()


def t_g_no_orphan_link():
    with _tmp() as td:
        st = _store(td)
        try:
            st.link("dr_nonexistent", "outcome", "x")
            assert False, "لینک به رسیدِ ناموجود باید رد شود"
        except dr.ReceiptValidationError:
            pass
        st.close()


def t_h_corruption_detected():
    with _tmp() as td:
        p = Path(td) / "receipts.db"
        st = dr.DecisionReceiptStore(p)
        rid = st.record(_receipt())
        assert st.verify_integrity(rid) is True
        # دستکاریِ out-of-band مستقیم در DB
        st._conn.execute("UPDATE receipts SET receipt_json=? WHERE receipt_id=?",
                         ('{"objective":"TAMPERED"}', rid))
        st._conn.commit()
        assert st.verify_integrity(rid) is False, "دستکاری باید کشف شود"
        assert st.resolve(rid)["integrity_ok"] is False
        st.close()


def t_i_concurrent_link_exactly_once():
    with _tmp() as td:
        st = _store(td)
        rid = st.record(_receipt())
        results, start = [], threading.Event()

        def _w():
            start.wait()
            results.append(st.link_outcome(rid, "same-ref"))
        ts = [threading.Thread(target=_w) for _ in range(16)]
        for t in ts:
            t.start()
        start.set()
        for t in ts:
            t.join()
        assert sum(1 for r in results if r) == 1, f"دقیقاً یک لینکِ نو: {results}"
        st.close()


def t_j_zero_executive_side_effect_structural():
    """ast: decision_receipt هیچ import از runner/telegram/effector/policy/شبکه ندارد و
    هیچ مسیرِ self-apply/mutate-verdict نمی‌سازد (v1 فقط ثبت و join)."""
    import ast
    forbidden_imports = {"requests", "socket", "urllib", "http", "telegram", "tg_api",
                         "approval_channel", "effector", "mission_runner", "organism", "wiring"}
    forbidden_names = {"EffectorGate", "settle", "sendMessage", "send_message", "apply_merge",
                       "self_apply", "execute_effect"}
    src = (_HERE.parent / "outcomes" / "decision_receipt.py").read_text("utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in forbidden_imports, f"imports {a.name}"
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports, f"from {node.module}"
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden_names, f"name {node.id}"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names, f".{node.attr}"
    # هیچ متدِ mutate/upgrade عمومی وجود ندارد (immutable by construction)
    methods = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for m in ("update", "set_trust", "set_verdict", "upgrade", "mutate", "override_effect_class"):
        assert m not in methods, f"نباید متدِ {m} وجود داشته باشد (immutable)"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_decision_receipt: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
