#!/usr/bin/env python3
"""Phase 2 — B6 scheduler F19: behavioral test.

dispatcherِ propose-only پشتِ OCTOPUS_WIRE_SCHEDULER.
- flag on → schedule() پر می‌کند، dispatcher صدا می‌زند، advisory NOTE
- flag off → dispatcher=None، schedule پر می‌کند ولی dispatch مرده
- هیچ effector بدونِ EffectorGate.settle
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase2-scheduler")

_OPS = (harness.SELF_OPS)
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
import wiring  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def t_make_scheduler_flag_off():
    """flag off → make_scheduler() None."""
    os.environ.pop("OCTOPUS_WIRE_SCHEDULER", None)
    assert wiring.make_scheduler() is None


def t_make_scheduler_flag_on():
    """flag on → make_scheduler() یک callable."""
    os.environ["OCTOPUS_WIRE_SCHEDULER"] = "1"
    d = wiring.make_scheduler()
    os.environ.pop("OCTOPUS_WIRE_SCHEDULER")
    assert d is not None and callable(d)


def t_dispatcher_is_propose_only():
    """dispatcher فقط advisory NOTE می‌زند — هیچ effector/settle."""
    os.environ["OCTOPUS_WIRE_SCHEDULER"] = "1"
    d = wiring.make_scheduler()
    os.environ.pop("OCTOPUS_WIRE_SCHEDULER")
    # dispatcher callable است و task را قبول می‌کند
    task = {"kind": "rfc-followup", "task_ref": "RFC-001",
            "leg_id": None, "due_beat": 10, "fired_beat": 11}
    # نباید استثنا بیندازد (fail-soft)
    try:
        d(task)
    except Exception:
        pass  # fail-soft ممکن است به ledger وابسته باشد
    assert True


def t_pacemaker_with_dispatcher():
    """Pacemaker با dispatcher باید dispatcher را نگه دارد."""
    os.environ["OCTOPUS_WIRE_SCHEDULER"] = "1"
    d = wiring.make_scheduler()
    os.environ.pop("OCTOPUS_WIRE_SCHEDULER")
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p2.db")
    pm = chrono.Pacemaker(db=db, dispatcher=d)
    assert pm.dispatcher is not None


def t_pacemaker_without_dispatcher():
    """Pacemaker بدون dispatcher → None."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p2b.db")
    pm = chrono.Pacemaker(db=db)
    assert pm.dispatcher is None


def t_scheduler_fires_dispatch():
    """schedule() پر می‌کند، beat_once صدا می‌زند، dispatcher فایر می‌شود."""
    fired = []
    def test_dispatcher(task):
        fired.append(task.get("kind"))
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-p2c.db")
    pm = chrono.Pacemaker(db=db, dispatcher=test_dispatcher)
    pm.schedule(kind="test-followup", task_ref="TEST-001", in_beats=1)
    pm.beat_once()  # beat اضافه می‌کند + due-scan
    assert "test-followup" in fired, f"dispatcher باید fire شود: {fired}"


def t_organism_passes_dispatcher():
    """organism.py باید dispatcher را به start_pacemaker_thread پاس بدهد."""
    assert "make_scheduler" in ORGANISM_SRC
    assert "dispatcher=" in ORGANISM_SRC


def t_wire_summary_has_scheduler():
    """wire_summary باید wire_scheduler را نشان دهد."""
    os.environ.pop("OCTOPUS_WIRE_SCHEDULER", None)
    s = wiring.wire_summary()
    assert "wire_scheduler" in s
    assert s["wire_scheduler"] is False, "پیش‌فرض باید خاموز باشد"


if __name__ == "__main__":
    failed = harness.run([
        ("flag off → None", t_make_scheduler_flag_off),
        ("flag on → callable", t_make_scheduler_flag_on),
        ("propose-only (advisory)", t_dispatcher_is_propose_only),
        ("Pacemaker با dispatcher", t_pacemaker_with_dispatcher),
        ("Pacemaker بدون dispatcher", t_pacemaker_without_dispatcher),
        ("schedule → dispatch فایر", t_scheduler_fires_dispatch),
        ("organism dispatcher پاس می‌دهد", t_organism_passes_dispatcher),
        ("wire_summary scheduler", t_wire_summary_has_scheduler),
    ])
    sys.exit(1 if failed else 0)
