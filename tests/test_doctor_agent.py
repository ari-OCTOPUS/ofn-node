"""Board doctor — the four-state honesty locks (OCTOPUS-AUTONOMY-SPEC §1.6).

This module pins: UNPROBED never becomes HEALTHY in aggregation; every
measurement carries measured_at + a reproducible command; the doctor has
zero remediation paths (no restart/start/stop, no flag writes — its only
write is its own report); and an unarmed host gets an honest all-unprobed
JSON with exit 0, never a traceback and never a green lie."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import doctor  # noqa: E402


def test_imports() -> None:
    import doctor as d  # noqa: F401
    assert d.SCHEMA == "octopus.doctor.v1"


def test_unarmed_host_is_honest_json_not_a_traceback() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "doctor.py")],
        capture_output=True, text=True, timeout=90, cwd=str(AGENTS),
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    report = json.loads(proc.stdout)
    assert report["schema"] == "octopus.doctor.v1"
    assert report["verdict"] in {"healthy", "incomplete", "degraded"}
    # on a dev/CI host nothing board-side was actually probed clean
    assert report["verdict"] != "healthy"
    assert report["unprobed"]["count"] + report["unknown"]["count"] > 0


def test_every_measurement_has_measured_at_and_command() -> None:
    report = doctor.build_report()
    for m in report["measurements"]:
        assert m["measured_at"], m["name"]
        assert m["command"], m["name"]
        assert m["verdict"] in {"healthy", "unhealthy", "unprobed", "unknown"}


def test_unprobed_never_aggregates_to_healthy() -> None:
    six_green = [
        doctor.Measurement(f"u{i}", True, doctor.Verdict.HEALTHY, "t",
                           "2026-09-03T00:00:00Z", "cmd")
        for i in range(6)
    ]
    two_unprobed = [
        doctor.Measurement(n, None, doctor.Verdict.UNPROBED, "t",
                           "2026-09-03T00:00:00Z", "cmd")
        for n in ("octopus-heartbeat", "octopus-digest")
    ]
    report = doctor.build_report(families=[six_green + two_unprobed])
    assert report["verdict"] == "incomplete"
    assert report["probed"]["healthy"] == 6
    assert report["unprobed"]["names"] == [
        "octopus-heartbeat", "octopus-digest"]
    assert "NOT a clean bill of health" in report["banner"]


def test_any_unhealthy_is_degraded() -> None:
    ms = [
        doctor.Measurement("a", True, doctor.Verdict.HEALTHY, "t",
                           "2026-09-03T00:00:00Z", "cmd"),
        doctor.Measurement("b", False, doctor.Verdict.UNHEALTHY, "t",
                           "2026-09-03T00:00:00Z", "cmd"),
    ]
    assert doctor.build_report(families=[ms])["verdict"] == "degraded"


def test_units_family_without_systemctl_is_unprobed(monkeypatch) -> None:
    # simulate a host without systemctl: runner must never be called
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    ms = doctor.probe_units(runner=lambda cmd: (_ for _ in ()).throw(
        AssertionError("runner called without systemctl")))
    assert ms[0].verdict is doctor.Verdict.UNPROBED
    assert "units.discovery" in ms[0].name


def test_units_discovery_failure_is_unprobed_not_crash() -> None:
    ms = doctor.probe_units(runner=lambda cmd: (1, ""))
    assert ms[0].verdict is doctor.Verdict.UNPROBED


def test_unit_show_failure_lands_in_unprobed_names(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    responses = {
        "list": (0, "octopus-heartbeat.service load active active OCTOPUS heartbeat\n"
                    "octopus-router.service load active active OCTOPUS router\n"),
        "fail": (1, ""),
        "ok": (0, "ActiveState=active\nResult=success\nUnitFileState=static\n"),
    }

    def runner(cmd: list[str]) -> tuple[int, str]:
        if "list-units" in cmd:
            return responses["list"]
        # مستقل از موقعیتِ آرگومان: قبلاً به cmd[-4] چسبیده بود و هر propertyِ
        # تازه‌ای در فرمان show این تست را بی‌صدا بی‌معنا می‌کرد (مقصود همان مانده).
        if any("octopus-heartbeat" in c for c in cmd):  # show heartbeat -> fails
            return responses["fail"]
        return responses["ok"]

    ms = doctor.probe_units(runner=runner)
    by_name = {m.name: m for m in ms}
    assert by_name["unit.octopus-heartbeat.service"].verdict \
        is doctor.Verdict.UNPROBED
    assert by_name["unit.octopus-router.service"].verdict \
        is doctor.Verdict.HEALTHY
    report = doctor.build_report(families=[ms])
    assert "unit.octopus-heartbeat.service" in report["unprobed"]["names"]


def test_failed_unit_result_is_unhealthy(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")

    def runner(cmd: list[str]) -> tuple[int, str]:
        if "list-units" in cmd:
            return 0, "octopus-x.service load inactive dead X\n"
        return 0, "ActiveState=failed\nResult=exit-code\nUnitFileState=enabled\n"

    ms = doctor.probe_units(runner=runner)
    assert ms[0].verdict is doctor.Verdict.UNHEALTHY


def test_managed_flags_missing_is_unknown_fail_closed(tmp_path) -> None:
    ms = doctor.probe_flags(managed_flags=tmp_path / "absent.json",
                            node_env=tmp_path / "absent.env")
    kinds = {m.name: m.verdict for m in ms}
    assert kinds["flags.managed"] is doctor.Verdict.UNKNOWN
    assert kinds["flags.node_env"] is doctor.Verdict.UNPROBED


def test_managed_flags_corrupt_json_is_unknown_not_partial(tmp_path) -> None:
    mf = tmp_path / "managed_flags.json"
    mf.write_text("{not json", encoding="utf-8")
    ms = doctor.probe_flags(managed_flags=mf, node_env=None)
    m = [x for x in ms if x.name == "flags.managed"][0]
    assert m.verdict is doctor.Verdict.UNKNOWN
    assert "corrupt" in (m.detail or "")
    assert m.sha256  # hash recorded even for the corrupt read


def test_flags_classify_intent_only_vs_load_bearing(tmp_path) -> None:
    mf = tmp_path / "managed_flags.json"
    mf.write_text(json.dumps({"OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "1"}),
                  encoding="utf-8")
    ne = tmp_path / "node.env"
    ne.write_text("OFN_WIRE_OUTBOUND=1\nOFN_KEEP_GATES_OPEN=1\n",
                  encoding="utf-8")
    ms = doctor.probe_flags(managed_flags=mf, node_env=ne)
    env = [m for m in ms if m.name == "flags.node_env"][0]
    assert env.value["OFN_WIRE_OUTBOUND"]["class"].startswith("intent-only")
    assert env.value["OFN_KEEP_GATES_OPEN"]["class"] == "load-bearing"


def test_pulse_stale_receipt_is_unhealthy(tmp_path) -> None:
    ev = tmp_path / "events.jsonl"
    ev.write_text(json.dumps({"occurred_at": "2026-09-01T00:00:00Z"}) + "\n",
                  encoding="utf-8")
    ms = doctor.probe_pulse(events_path=ev, now=1788470000.0)
    assert ms[0].verdict is doctor.Verdict.UNHEALTHY


def test_pulse_missing_file_is_unprobed(tmp_path) -> None:
    ms = doctor.probe_pulse(events_path=tmp_path / "none.jsonl")
    assert ms[0].verdict is doctor.Verdict.UNPROBED


def test_report_write_is_atomic_and_hashed(tmp_path) -> None:
    report = doctor.build_report(families=[[
        doctor.Measurement("only", True, doctor.Verdict.HEALTHY, "t",
                           "2026-09-03T00:00:00Z", "cmd")]])
    p, sha = doctor.write_report(report, tmp_path / "r.json")
    assert p.exists() and not p.with_suffix(".json.tmp").exists()
    assert len(sha) == 64


# ── منفی‌ها: دکتر هیچ مسیر ترمیم ندارد (§6 سند) ──────────────────────────────

def test_doctor_source_has_no_remediation_paths() -> None:
    src = (AGENTS / "doctor.py").read_text(encoding="utf-8")
    for banned in ("systemctl restart", "systemctl start", "systemctl stop",
                   "systemctl disable", "systemctl enable", "os.remove",
                   "os.unlink", "shutil.rmtree"):
        assert banned not in src, banned


def test_doctor_only_write_is_its_report() -> None:
    src = (AGENTS / "doctor.py").read_text(encoding="utf-8")
    # every write call must live inside write_report and target the report path
    assert src.count(".write_text(") == 1
    assert "tmp.write_text" in src  # the single atomic report write
    assert "managed_flags" in src and "w+" not in src


# ── GAP-017: دِینِ طبقه‌بندی oneshot — inactive+success ابهام نیست ────────────
#
# دِین ثبت‌شدهٔ دکتر: ده یونیت oneshot که بین دو اجرا inactive+success بودند
# (حالتِ طبیعی‌شان) به‌اشتباه UNKNOWN گرفته می‌شدند، چون سنجه ActiveState بود
# نه تازگیِ آخرین اجرا. این تست‌ها همان قاعده را قفل می‌کنند.

def _oneshot_runner(
    body: str, unit: str = "octopus-doctor.service"
):
    def runner(cmd: list[str]) -> tuple[int, str]:
        if "list-units" in cmd:
            return 0, f"{unit} load inactive dead OCTOPUS doctor\n"
        return 0, body
    return runner


def test_fresh_oneshot_between_runs_is_healthy_not_unknown(monkeypatch) -> None:
    """قلبِ GAP-017: oneshotِ سالمِ بین دو شلیک باید HEALTHY باشد."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    # آخرین خروج در ثانیهٔ ۱۰۰۰ از بوت؛ «الان» ثانیهٔ ۴۶۰۰ ⇒ سنِ یک‌ساعته
    body = (
        "ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
        "Type=oneshot\nExecMainExitTimestampMonotonic=1000000000\n"
    )
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.HEALTHY, m.detail
    assert m.value["type"] == "oneshot"
    assert m.value["last_run_age_s"] == 3600


def test_stale_oneshot_is_unhealthy(monkeypatch) -> None:
    """کهنه‌بودن واقعی باید هنوز گرفته شود — اصلاح، کورکردن نیست."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = (
        "ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
        "Type=oneshot\nExecMainExitTimestampMonotonic=1000000\n"
    )
    now = 1.0 + doctor.ONESHOT_MAX_AGE_S + 60
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=now)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNHEALTHY
    assert "timer likely not firing" in (m.detail or "")


def test_oneshot_without_timestamp_stays_unknown_fail_closed(monkeypatch) -> None:
    """بدون رسیدِ زمان، حدس نزن — همان UNKNOWNِ امروز، هرگز HEALTHYِ کاذب."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = ("ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
            "Type=oneshot\n")
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNKNOWN
    assert "unavailable" in (m.detail or "")


def test_oneshot_with_unparseable_timestamp_stays_unknown(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = ("ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
            "Type=oneshot\nExecMainExitTimestampMonotonic=n/a\n")
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNKNOWN


def test_oneshot_never_run_stays_unknown(monkeypatch) -> None:
    """صفر یعنی هنوز اجرا نشده — ادعای سلامت نکن."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = ("ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
            "Type=oneshot\nExecMainExitTimestampMonotonic=0\n")
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNKNOWN


def test_disabled_oneshot_still_unknown_deliberate(monkeypatch) -> None:
    """دو یونیتِ عمداً disabled باید UNKNOWN بمانند — اصلاح آن‌ها را نمی‌بلعد."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = (
        "ActiveState=inactive\nResult=success\nUnitFileState=disabled\n"
        "Type=oneshot\nExecMainExitTimestampMonotonic=1000000000\n"
    )
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNKNOWN
    assert "deliberate" in (m.detail or "")


def test_failed_oneshot_still_unhealthy(monkeypatch) -> None:
    """اولویتِ UNHEALTHY حفظ شود: خرابی هرگز زیر شاخهٔ oneshot پنهان نشود."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = (
        "ActiveState=failed\nResult=exit-code\nUnitFileState=enabled\n"
        "Type=oneshot\nExecMainExitTimestampMonotonic=1000000000\n"
    )
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNHEALTHY


def test_long_running_service_unaffected_by_oneshot_branch(monkeypatch) -> None:
    """رگرسیون: سرویسِ simpleِ فعال دست‌نخورده بماند."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = (
        "ActiveState=active\nResult=success\nUnitFileState=enabled\n"
        "Type=simple\nExecMainExitTimestampMonotonic=0\n"
    )
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.HEALTHY
    assert "ActiveState=active" in (m.detail or "")


def test_non_oneshot_inactive_still_unknown(monkeypatch) -> None:
    """سرویسِ غیر-oneshot که خوابیده، هنوز ابهام است — دامنهٔ اصلاح باریک است."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    body = (
        "ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
        "Type=simple\nExecMainExitTimestampMonotonic=1000000000\n"
    )
    ms = doctor.probe_units(runner=_oneshot_runner(body), now_monotonic=4600.0)
    m = {x.name: x for x in ms}["unit.octopus-doctor.service"]
    assert m.verdict is doctor.Verdict.UNKNOWN


def test_gap017_expect_zero_unknown_oneshots_on_healthy_board(monkeypatch) -> None:
    """معیارِ بسته‌شدنِ GAP-017 روی بوردِ سالم: صفر oneshotِ UNKNOWN."""
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/systemctl")
    units = [f"octopus-oneshot-{i}.service" for i in range(10)]
    listing = "".join(f"{u} load inactive dead unit {u}\n" for u in units)
    body = (
        "ActiveState=inactive\nResult=success\nUnitFileState=enabled\n"
        "Type=oneshot\nExecMainExitTimestampMonotonic=1000000000\n"
    )

    def runner(cmd: list[str]) -> tuple[int, str]:
        return (0, listing) if "list-units" in cmd else (0, body)

    ms = doctor.probe_units(runner=runner, now_monotonic=4600.0)
    unknown_oneshots = [
        m for m in ms
        if isinstance(m.value, dict) and m.value.get("type") == "oneshot"
        and m.verdict is doctor.Verdict.UNKNOWN
    ]
    assert unknown_oneshots == [], [m.name for m in unknown_oneshots]
    assert len([m for m in ms if m.verdict is doctor.Verdict.HEALTHY]) == 10
