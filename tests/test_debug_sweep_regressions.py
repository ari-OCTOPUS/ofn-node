"""Debug-sweep regressions (2026-09-04 board sweep) — two live-caught bugs.

BUG-1: learning_feeder crashed on the board with NameError (import time
missing) — feed() was never executed end-to-end by any test. This test
runs feed() with the subprocess/RUNS patched so the date-formatting and
output-writing path actually executes.

BUG-2: external_witness default repo-dir assumed the laptop layout
(parents[2]/ofn-node); on the board (~/ofn) local HEAD read returned None
→ main_head UNKNOWN despite a perfectly good checkout. The default must
resolve per-host (env first, then first candidate holding .git — file or
dir, since worktrees use a .git FILE)."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import learning_feeder as lf  # noqa: E402
import external_witness as ew  # noqa: E402


def test_feed_runs_end_to_end_and_writes_run(tmp_path, monkeypatch) -> None:
    """کل feed() اجرا شود — همان مسیری که روی بورد NameError داد."""
    # رویداد تازه بساز
    d = tmp_path / "legs" / "lead-inbox"
    d.mkdir(parents=True)
    import datetime as dt
    at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (d / "events.jsonl").write_text(json.dumps(
        {"event_type": "communication.sent", "occurred_at": at,
         "correlation_id": "lead:x"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(lf, "EVENTS", d / "events.jsonl")
    monkeypatch.setattr(lf, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(lf, "LEDGER", tmp_path / "ledger.jsonl")

    def fake_run(cmd, **kw):
        out_dir = Path(cmd[cmd.index("--out") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "run-summary.json").write_text("{}", encoding="utf-8")
        return types.SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(lf.subprocess, "run", fake_run)
    res = lf.feed()
    assert res["ok"] is True, res
    assert res["events_used"] == 1


def test_default_repo_dir_finds_a_git_root() -> None:
    d = ew.default_repo_dir()
    assert (d / ".git").exists(), f"resolved {d} but no .git there"


def test_default_repo_dir_env_override(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "fakerepo"
    fake.mkdir()
    (fake / ".git").mkdir()
    monkeypatch.setenv("OFN_REPO_ROOT", str(fake))
    assert ew.default_repo_dir() == fake


def test_worktree_style_git_file_counts(tmp_path, monkeypatch) -> None:
    """worktreeها .git به‌صورت فایل‌اند نه پوشه — باید پذیرفته شود."""
    wt = tmp_path / "as-worktree"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: /somewhere\n", encoding="utf-8")
    monkeypatch.setenv("OFN_REPO_ROOT", str(wt))
    assert ew.default_repo_dir() == wt
