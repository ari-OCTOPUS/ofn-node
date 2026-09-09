"""GAP-013 — the six glass commands, each executed once against its snapshot
contract (expected: 6 passed).

The runner existed but the six owner commands had never been executed as a
set. Each test pins one command's dispatch path: the right snapshot builder
is called with the right source, file-backed commands read their real file
shape, and missing sources fail soft to `{}` rather than raising.
"""

from __future__ import annotations

import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

from ofn.adapters import telegram_glass as tg  # noqa: E402
import glass_runner as gr                      # noqa: E402


def test_command_status_uses_status_snapshot(monkeypatch) -> None:
    seen = {}
    monkeypatch.setattr(tg, "build_status_snapshot",
                        lambda repo_root=None: {"status_sentinel": 1, **seen})
    assert gr.build_snapshot("/status")["status_sentinel"] == 1


def test_command_money_uses_learning_runs_path(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(tg, "build_learning_snapshot",
                        lambda ledger_path=None: {"learning": str(ledger_path)})
    out = gr.build_snapshot("/money")
    assert "learning" in out
    assert out["learning"].replace("\\", "/").endswith(
        "ofn/09-LANES/ECONOMIC-LEARNING/runs")


def test_command_self_uses_self_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(tg, "build_self_snapshot",
                        lambda producer=None: {"self_sentinel": True})
    assert gr.build_snapshot("/self") == {"self_sentinel": True}


def test_command_doctor_reads_report_and_counts_failures(
        tmp_path, monkeypatch) -> None:
    report = tmp_path / "report.json"
    report.write_text('{"counts": {"failed": 2}}', encoding="utf-8")
    monkeypatch.setattr(gr, "_DOCTOR_REPORT", report)
    out = gr.build_snapshot("/doctor")
    assert out["failed_units"] == 2 and out["doctor_snapshot"]["counts"] == {
        "failed": 2}


def test_command_queue_reads_owner_queue_capped_at_1500(
        tmp_path, monkeypatch) -> None:
    q = tmp_path / "OWNER-QUEUE.md"
    q.write_text("x" * 3000, encoding="utf-8")
    monkeypatch.setattr(gr, "_OWNER_QUEUE", q)
    out = gr.build_snapshot("/queue")
    assert len(out["owner_queue"]) == 1500


def test_command_receipts_has_no_snapshot_file_and_stays_known() -> None:
    # receipts ride inside the reply itself — the builder must not guess a
    # file, and the command must remain in the glass command set.
    assert gr.build_snapshot("/receipts") == {}
    assert "/receipts" in tg.COMMANDS


def test_missing_sources_fail_soft_to_empty(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(gr, "_DOCTOR_REPORT", tmp_path / "absent.json")
    monkeypatch.setattr(gr, "_OWNER_QUEUE", tmp_path / "absent.md")
    assert gr.build_snapshot("/doctor") == {}
    assert gr.build_snapshot("/queue") == {}
