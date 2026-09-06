"""Repair API — the self-healing pharmacy locks (owner mandate 2026-09-03).

Pins: whitelist-only actions; dry_run default executes NOTHING; conservation
mode refuses every mutating action; every plan/done lands in the append-only
repair log with a rollback; the server binds loopback only; unknown actions
fail closed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import repair_api as ra  # noqa: E402


def test_whitelist_is_exactly_the_proven_heals() -> None:
    assert set(ra.ACTIONS) == {
        "mesh_archive_expired", "mesh_drain", "git_pull_ff",
        "doctor_summary", "timesync_status"}


def test_unknown_action_fails_closed() -> None:
    res = ra.plan("systemctl restart everything", {})
    assert res["ok"] is False and res["error"] == "unknown-action"
    assert "restart" not in " ".join(res["allowed"])


def test_dry_run_plan_moves_nothing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ra, "MESH", tmp_path)
    q = tmp_path / "outbox"
    q.mkdir()
    old = q / "m.json"
    old.write_text(json.dumps(
        {"expires_at": "2026-08-01T00:00:00Z"}), encoding="utf-8")
    res = ra.plan("mesh_archive_expired", {"queue": "outbox"})
    assert res["ok"] and res["expired"] == ["m.json"]
    assert old.exists(), "plan must not move files"
    assert "rollback" in res


def test_execute_moves_expired_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ra, "MESH", tmp_path)
    monkeypatch.setattr(ra, "_conservation_on", lambda: False)
    monkeypatch.setattr(ra, "LOG", tmp_path / "repair-log.jsonl")
    q = tmp_path / "outbox"
    q.mkdir()
    (q / "dead.json").write_text(json.dumps(
        {"expires_at": "2026-08-01T00:00:00Z"}), encoding="utf-8")
    (q / "live.json").write_text(json.dumps(
        {"expires_at": "2099-01-01T00:00:00Z"}), encoding="utf-8")
    res = ra.execute("mesh_archive_expired", {"queue": "outbox"})
    assert res["moved"] == 1
    assert (q / "live.json").exists()
    assert not (q / "dead.json").exists()
    assert any((tmp_path / d.name).is_dir()
               for d in tmp_path.iterdir() if "expired" in d.name)


def test_conservation_refuses_mutating_actions(monkeypatch) -> None:
    monkeypatch.setattr(ra, "_conservation_on", lambda: True)
    for a in ("mesh_archive_expired", "mesh_drain", "git_pull_ff"):
        res = ra.plan(a, {})
        assert res["ok"] is False and res["error"] == "conservation-on", a


def test_conservation_allows_readonly_actions(monkeypatch) -> None:
    monkeypatch.setattr(ra, "_conservation_on", lambda: True)
    assert ra.plan("doctor_summary", {})["error"] != "conservation-on"


def test_doctor_summary_absent_report_fails_closed(tmp_path, monkeypatch) -> None:
    import opslib
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    res = ra.plan("doctor_summary", {})
    assert res["ok"] is False and res["error"] == "report-absent"


def test_execute_logs_plan_and_done(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ra, "MESH", tmp_path)
    monkeypatch.setattr(ra, "LOG", tmp_path / "repair-log.jsonl")
    monkeypatch.setattr(ra, "_conservation_on", lambda: False)
    (tmp_path / "outbox").mkdir()
    ra.execute("mesh_archive_expired", {"queue": "outbox"})
    lines = (tmp_path / "repair-log.jsonl").read_text(
        encoding="utf-8").splitlines()
    phases = [json.loads(l)["phase"] for l in lines]
    assert "plan" in phases and "done" in phases


def test_binds_loopback_only_constant() -> None:
    assert ra.HOST == "127.0.0.1", "the pharmacy never faces the network"


def test_source_has_no_restarts_no_sends_no_flag_writes() -> None:
    src = (AGENTS / "repair_api.py").read_text(encoding="utf-8")
    for banned in ("systemctl restart", "systemctl start", "systemctl stop",
                   "sendMessage", "managed_flags", "os.remove"):
        assert banned not in src, banned
