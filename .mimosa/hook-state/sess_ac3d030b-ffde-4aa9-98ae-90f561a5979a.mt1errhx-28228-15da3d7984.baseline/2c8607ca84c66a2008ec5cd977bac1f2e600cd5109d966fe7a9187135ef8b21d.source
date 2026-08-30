#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_event_spine.py — Ops Event Spine v1 (envelope + trace_id اجباری + replay + reconcile).

قیودِ اثبات‌شده: flag-off dual_write=no-op · trace_id اجباری (رد بی‌corr) · event_type از taxonomy ·
idempotent · replay_mission قطعی · restart-persist · concurrency exactly-once · reconcile mismatch ·
zero external side-effect (ast). $0 آفلاین، spine روی temp.
"""
import os
import re
import sys
import tempfile
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "spine"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("event-spine")

import event_spine as es    # noqa: E402
import spine_reconcile as rec   # noqa: E402 (renamed to avoid budget/reconcile.py collision)


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def _spine(td):
    return es.EventSpine(path=Path(td) / "spine.db")


def _ev(**over):
    base = {"event_type": "delivered", "domain": "lead", "correlation_id": "corr-1",
            "mission_id": "mis-1", "subject": "lead:LD1", "trust": "GRADED",
            "producer": "leg.lead", "payload": {"score": 80}}
    base.update(over)
    return base


def _on():
    class _C:
        def __enter__(self):
            self.p = os.environ.get(es.FLAG)
            os.environ[es.FLAG] = "1"
            return self

        def __exit__(self, *a):
            if self.p is None:
                os.environ.pop(es.FLAG, None)
            else:
                os.environ[es.FLAG] = self.p
    return _C()


def t_a_trace_id_mandatory():
    with _tmp() as td:
        sp = _spine(td)
        try:
            sp.publish(_ev(correlation_id=""))
            assert False, "بی trace_id باید رد شود"
        except ValueError as e:
            assert "MANDATORY" in str(e) or "trace" in str(e).lower()
        sp.close()


def t_b_unknown_event_type_and_domain_rejected():
    with _tmp() as td:
        sp = _spine(td)
        for bad in ({"event_type": "nope"}, {"domain": ""}):
            try:
                sp.publish(_ev(**bad))
                assert False, f"باید رد: {bad}"
            except ValueError:
                pass
        sp.close()


def t_c_publish_and_idempotent():
    with _tmp() as td:
        sp = _spine(td)
        e1 = sp.publish(_ev(idempotency_key="k1"))
        assert e1 and e1.startswith("evt_")
        assert sp.publish(_ev(idempotency_key="k1")) is None    # idempotent
        assert sp.metrics()["total"] == 1
        sp.close()


def t_d_replay_mission_deterministic():
    with _tmp() as td:
        sp = _spine(td)
        sp.publish(_ev(event_type="delivered", idempotency_key="a"))
        sp.publish(_ev(event_type="accepted-measurement", idempotency_key="b"))
        st = sp.replay_mission("mis-1")
        assert st["n_events"] == 2 and st["last_status"] == "accepted-measurement"
        assert st["correlation_ids"] == ["corr-1"]
        assert [t["type"] for t in st["timeline"]] == ["delivered", "accepted-measurement"]
        sp.close()


def t_e_restart_persist():
    with _tmp() as td:
        p = Path(td) / "spine.db"
        sp = es.EventSpine(path=p)
        sp.publish(_ev(idempotency_key="persist"))
        sp.close()
        sp2 = es.EventSpine(path=p)
        assert sp2.metrics()["total"] == 1
        sp2.close()


def t_f_concurrent_exactly_once():
    with _tmp() as td:
        sp = _spine(td)
        results, start = [], threading.Event()

        def _w():
            start.wait()
            results.append(sp.publish(_ev(idempotency_key="same")))
        ts = [threading.Thread(target=_w) for _ in range(16)]
        for t in ts:
            t.start()
        start.set()
        for t in ts:
            t.join()
        assert sum(1 for r in results if r) == 1, f"دقیقاً یک: {results}"
        assert sp.metrics()["total"] == 1
        sp.close()


def t_g_dual_write_flag_off_noop():
    with _tmp() as td:
        sp = _spine(td)
        out = es.dual_write(sp, _ev())     # flag off
        assert out["published"] is False and out["reason"] == "flag-off"
        assert sp.metrics()["total"] == 0
        with _on():
            out2 = es.dual_write(sp, _ev(idempotency_key="dw"))
            assert out2["published"] is True and out2["event_id"]
        sp.close()


def t_h_reconcile_mismatch():
    r = rec.reconcile_keys(["a", "b", "c"], ["b", "c", "d"])
    assert r["matched"] == 2 and r["only_in_spine"] == ["a"] and r["only_in_domain"] == ["d"]
    assert r["mismatch"] == 2
    # by-correlation against a spine
    with _tmp() as td:
        sp = _spine(td)
        sp.publish(_ev(correlation_id="x", idempotency_key="1"))
        r2 = rec.reconcile_by_correlation(sp, ["x", "y"])
        assert r2["only_in_domain"] == ["y"] and r2["matched"] == 1
        sp.close()


def t_i_zero_external_side_effect_structural():
    import ast
    forbidden_imports = {"requests", "socket", "urllib", "http", "telegram", "tg_api",
                         "approval_channel", "effector", "mission_runner", "organism", "wiring"}
    forbidden_names = {"EffectorGate", "settle", "sendMessage", "send_message", "self_apply"}
    for name in ("event_spine.py", "spine_reconcile.py"):
        src = (_HERE.parent / "spine" / name).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in forbidden_imports, f"{name} imports {a.name}"
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden_imports, f"{name} from {node.module}"
            elif isinstance(node, ast.Name):
                assert node.id not in forbidden_names, f"{name} name {node.id}"
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, f"{name} .{node.attr}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_event_spine: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
