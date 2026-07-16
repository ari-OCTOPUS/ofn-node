"""تست‌های snapshot — observe-only واقعی: هیچ نوشتنی، هیچ secretی، UNKNOWN صادق."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from tests import _bootstrap  # noqa: F401

from control_plane import snapshot


def _walk(p: Path) -> set[str]:
    return {str(f.relative_to(p)) for f in p.rglob("*")}


class TestSnapshotIsReadOnly(unittest.TestCase):
    def test_collect_on_empty_dir_writes_nothing_and_stays_unknown(self):
        """دایرکتوریِ خالی → همه UNKNOWN (نه crash، نه silent-pass، نه نوشتن)."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            before = _walk(out)
            snap = snapshot.collect_status(out=out, db=out / "no.db")
            after = _walk(out)
            self.assertEqual(before, after, "observe-only نباید چیزی بنویسد")
            for section in ("daemon", "budget", "events", "workspace",
                            "notify", "approvals"):
                self.assertEqual(snap[section]["status"], "UNKNOWN",
                                 f"{section} باید UNKNOWN باشد، نه ادعای سلامت")

    def test_no_secret_access_in_sources(self):
        """هیچ فایلی در control_plane نباید dotenv/کلید/توکن بخواند."""
        pkg = Path(snapshot.__file__).parent
        for f in pkg.glob("*.py"):
            src = f.read_text(encoding="utf-8")
            for forbidden in ("dotenv", "API_KEY", "BOT_TOKEN", "SECRET",
                              "TELEGRAM_CHAT_ID"):
                self.assertNotIn(forbidden, src,
                                 f"{f.name} نباید به secrets نزدیک شود ({forbidden})")


class TestDaemonStatus(unittest.TestCase):
    def _write_state(self, out: Path, **kw):
        (out / "daemon_state.json").write_text(
            json.dumps(kw, ensure_ascii=False), encoding="utf-8")

    def test_stopped(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            t = "2026-07-11T15:35:52"
            self._write_state(out, last_tick_at=t, stopped_at=t, pid=1)
            self.assertEqual(snapshot.daemon_status(out)["status"], "STOPPED")

    def test_running_fresh_heartbeat(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            now = datetime.now().isoformat(timespec="seconds")
            self._write_state(out, last_tick_at=now, pid=1)
            self.assertEqual(snapshot.daemon_status(out)["status"], "RUNNING")

    def test_paused_via_existing_contract_file(self):
        """قراردادِ موجودِ daemon.pause باید عیناً دیده شود."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            now = datetime.now().isoformat(timespec="seconds")
            self._write_state(out, last_tick_at=now, pid=1)
            (out / "daemon.pause").write_text("", encoding="utf-8")
            d = snapshot.daemon_status(out)
            self.assertEqual(d["status"], "PAUSED")
            self.assertTrue(d["pause_file"])

    def test_stale(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
            self._write_state(out, last_tick_at=old, pid=1)
            self.assertEqual(snapshot.daemon_status(out)["status"], "STALE")


class TestBudgetAndEvents(unittest.TestCase):
    def test_budget_counts_cloud_only(self):
        """مطابق brain/budget: ollama محلی است و در سقف نمی‌شمارد."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            today = datetime.now().strftime("%Y-%m-%d")
            (out / "llm_budget.json").write_text(json.dumps(
                {"date": today, "calls": {"fugu": 2, "glm": 3, "ollama": 50}}),
                encoding="utf-8")
            b = snapshot.budget_status(out)
            self.assertEqual(b["cloud_calls"], 5)
            self.assertEqual(b["remaining"], b["cap"] - 5)

    def _make_bus(self, db: Path, rows):
        conn = sqlite3.connect(str(db))
        conn.execute("""CREATE TABLE dashboard_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, trace_id TEXT,
            agent_id TEXT, event_name TEXT, status TEXT, summary TEXT,
            duration_ms INTEGER, next_action TEXT, approval_state TEXT)""")
        conn.executemany(
            "INSERT INTO dashboard_events (timestamp, trace_id, agent_id, event_name,"
            " status, summary, duration_ms, next_action, approval_state)"
            " VALUES (?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        conn.close()

    def test_events_summary_and_pending(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "bus.db"
            self._make_bus(db, [
                ("t1", "tr1", "explore", "task.completed", "ok", "s", 0, "", "not_required"),
                ("t2", "tr1", "guard", "task.completed", "ok", "s", 0, "", "not_required"),
                ("t3", "tr2", "evolve", "approval.required", "blocked", "s", 0, "", "pending"),
            ])
            ev = snapshot.events_summary(db)
            self.assertEqual(ev["total"], 3)
            self.assertEqual(ev["pending_approvals"], 1)
            ws = snapshot.workspace_status(db)
            # tr1 دو ایجنت دارد → ignition
            self.assertGreaterEqual(ws["max_ignition"], 2)

    def test_approvals_reads_self_code_queue_readonly(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            pdir = out / "self_code_proposals" / "20260711-1"
            pdir.mkdir(parents=True)
            (pdir / "meta.json").write_text(json.dumps(
                {"id": "20260711-1", "target": "brain/frontier.py",
                 "status": "pending_approval", "goal": "g",
                 "created_at": "2026-07-11T12:00:00", "proposer": "auto"}),
                encoding="utf-8")
            before = _walk(out)
            ap = snapshot.approvals_status(out, db=out / "no.db")
            self.assertEqual(_walk(out), before)
            self.assertEqual(len(ap["self_code_pending"]), 1)
            self.assertEqual(ap["self_code_counts"], {"pending_approval": 1})


class TestHardeningFixes(unittest.TestCase):
    def test_restarted_daemon_with_resumed_at_is_not_stopped(self):
        """#3/#9: resumed_at تازه‌تر از stopped_at → RUNNING، نه STOPPED کاذب."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            now = datetime.now().isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(json.dumps({
                "last_tick_at": "2026-07-11T15:00:00",
                "stopped_at": "2026-07-11T15:00:03",
                "resumed_at": now, "pid": 1}), encoding="utf-8")
            self.assertEqual(snapshot.daemon_status(out)["status"], "RUNNING")

    def test_genuine_clean_stop_still_stopped(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "daemon_state.json").write_text(json.dumps({
                "last_tick_at": "2026-07-11T15:00:00",
                "stopped_at": "2026-07-11T15:00:05", "pid": 1}), encoding="utf-8")
            self.assertEqual(snapshot.daemon_status(out)["status"], "STOPPED")

    def test_budget_whitelist_ignores_unknown_local_provider(self):
        """#14: شمارشِ cloud با whitelist؛ providerِ محلیِ با کلیدِ دیگر بیش‌شماری نمی‌شود."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            today = datetime.now().strftime("%Y-%m-%d")
            (out / "llm_budget.json").write_text(json.dumps(
                {"date": today, "calls": {"fugu": 2, "glm": 3, "qwen2.5": 99, "mock": 50}}),
                encoding="utf-8")
            b = snapshot.budget_status(out)
            self.assertEqual(b["cloud_calls"], 5)   # فقط fugu+glm، نه qwen/mock

    def test_notify_badge_only_connected_on_real_delivery(self):
        """#20: badge فقط با delivered=='telegram' متصل است، نه با queued(error)."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            jl = out / "decision_packets.jsonl"
            jl.write_text(json.dumps({"delivered": "queued (error: ConnectionError)"}) + "\n",
                          encoding="utf-8")
            self.assertFalse(snapshot.notify_status(out)["telegram_configured"])
            jl.write_text(json.dumps({"delivered": "telegram"}) + "\n", encoding="utf-8")
            self.assertTrue(snapshot.notify_status(out)["telegram_configured"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
