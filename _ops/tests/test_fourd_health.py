"""test_fourd_health.py — probe فقط‌خواندنِ 4d_system + opt-in در registry/innervation (ADR-038).

آفلاین · $0 · شبیه‌سازی. هرگز فایلِ واقعیِ 4d_system را لمس نمی‌کند (DAEMON_STATE
در تست بازنویسی می‌شود).
"""
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness  # noqa: E402
ENV = harness.setup("cortex")

import fourd_health  # noqa: E402
import registry      # noqa: E402
import innervation   # noqa: E402


def t_a_probe_missing_is_never_healthy():
    """absence → 'missing'، هرگز 'fresh' (قاعدهٔ absence≠healthy)."""
    fourd_health.DAEMON_STATE = Path("/no/such/daemon_state.json")
    rec = fourd_health.probe()
    assert rec["status"] == "missing", rec
    assert rec["mtime"] is None


def t_b_probe_fresh_then_stale_by_mtime():
    fake = Path(tempfile.mkdtemp()) / "daemon_state.json"
    fake.write_text("{}", encoding="utf-8")
    fourd_health.DAEMON_STATE = fake
    assert fourd_health.probe(sla_s=3600)["status"] == "fresh"
    old = time.time() - 7200
    os.utime(fake, (old, old))
    assert fourd_health.probe(sla_s=3600)["status"] == "stale"


def t_c_probe_corrupt_json():
    fake = Path(tempfile.mkdtemp()) / "daemon_state.json"
    fake.write_text("{not valid json", encoding="utf-8")
    fourd_health.DAEMON_STATE = fake
    assert fourd_health.probe()["status"] == "corrupt"


def t_d_persist_and_summary_noop_when_flag_off():
    os.environ.pop("OCTOPUS_OBSERVE_4D", None)
    assert fourd_health.persist() is None
    assert fourd_health.summary() is None


def t_e_registry_excludes_when_off_includes_when_on():
    os.environ.pop("OCTOPUS_OBSERVE_4D", None)
    assert "fourd_system" not in [m["id"] for m in registry.sweep()["members"]]
    os.environ["OCTOPUS_OBSERVE_4D"] = "1"
    try:
        ids = [m["id"] for m in registry.sweep()["members"]]
        assert "fourd_system" in ids, ids
    finally:
        os.environ.pop("OCTOPUS_OBSERVE_4D", None)


def t_f_innervation_excludes_when_off_includes_when_on():
    os.environ.pop("OCTOPUS_OBSERVE_4D", None)
    assert "fourd" not in [o["id"] for o in innervation.check()["organs"]]
    os.environ["OCTOPUS_OBSERVE_4D"] = "1"
    try:
        oids = [o["id"] for o in innervation.check()["organs"]]
        assert "fourd" in oids, oids
    finally:
        os.environ.pop("OCTOPUS_OBSERVE_4D", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_fourd_health: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
