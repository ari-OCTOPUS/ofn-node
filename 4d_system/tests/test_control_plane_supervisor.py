"""تست‌های v5 Supervisor (سخت‌شده پس از بازبینیِ خصمانه‌ی 2026-07-12).

پوشش: crash→restart با backoff · gave_up با ریستِ زمانی · HALT/owner-stop/clean-exit
هرگز restart · adoptionِ pid-محور (ضدِ daemon/telegramِ تکراری) · تشخیصِ hangِ
دومرحله‌ای (ضدِ false-positive) · escalationِ spawn-failure · گیتِ flag در لایه‌ی
اجرا · قفلِ تک‌نمونه.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from tests import _bootstrap  # noqa: F401

from control_plane.policy import Level, evaluate
from control_plane.supervisor import (GIVE_UP_COOLDOWN_S, HUNG_FREEZE_S,
                                      HUNG_GRACE_S, OWNER_STOP_FLAG,
                                      RESTART_LIMIT, Supervisor, _default_spawn)


class FakeProc:
    """شبیه‌سازیِ subprocess.Popen — terminate و kill هر دو (مثلِ واقعی) وجود دارند."""
    def __init__(self, pid=111, ignores_terminate=False, ignores_kill=False):
        self.pid = pid
        self.rc = None
        self.terminated = False
        self.killed = False
        self.ignores_terminate = ignores_terminate
        self.ignores_kill = ignores_kill

    def poll(self):
        return self.rc

    def terminate(self):
        self.terminated = True
        if not self.ignores_terminate:
            self.rc = -15   # مرگ با SIGTERM

    def kill(self):
        self.killed = True
        if not self.ignores_kill:
            self.rc = -9    # مرگ با SIGKILL (escalation)


def _mk(tmp: Path, telegram=False, dry=False, now0=1_000_000.0, pid_alive=False):
    """Supervisor تزریق‌شده — هیچ فرایندِ واقعی/notify؛ pid_alive قابلِ‌کنترل (deterministic)."""
    state = {"now": now0}
    spawned: list[str] = []
    notes: list[tuple] = []
    procs: list[FakeProc] = []

    def spawn(module, log_path, cwd):
        spawned.append(module)
        p = FakeProc(pid=100 + len(spawned))
        procs.append(p)
        return p

    alive = pid_alive if callable(pid_alive) else (lambda _p: pid_alive)
    sup = Supervisor(out=tmp, audit_dir=tmp / "audit",
                     spawn_fn=spawn,
                     notify_fn=lambda *a: notes.append(a),
                     now_fn=lambda: state["now"],
                     telegram_enabled_fn=lambda: telegram,
                     pid_alive_fn=alive,
                     dry_run=dry)
    return sup, state, spawned, notes, procs


def _decision(actions, child):
    return next(a for a in actions if a["child"] == child)["decision"]


class TestPolicy(unittest.TestCase):
    def test_self_heal_autonomous_but_halt_needs_approval(self):
        r = evaluate("self_heal_restart")
        self.assertEqual(r.level, int(Level.SHADOW_LOG))
        self.assertFalse(r.requires_approval)
        h = evaluate("restart_after_halt")
        self.assertTrue(h.requires_approval)


class TestFlagGate(unittest.TestCase):
    def _clear(self):
        p = mock.patch.dict(os.environ)
        p.start()
        self.addCleanup(p.stop)
        for k in list(os.environ):
            if k.startswith("CONTROL_PLANE_"):
                del os.environ[k]

    def test_run_forever_refuses_without_flag(self):
        self._clear()
        with tempfile.TemporaryDirectory() as td:
            sup, _, spawned, *_ = _mk(Path(td))
            res = sup.run_forever(max_ticks=1)
            self.assertFalse(res["ok"])
            self.assertIn("خاموش", res["reason"])
            self.assertEqual(spawned, [])   # هیچ spawnی با flagِ خاموش

    def test_default_spawn_blocks_real_process_when_flag_off(self):
        """#13/#16: گیتِ لایه‌ی اجرا — spawnِ واقعی با flagِ خاموش باید رد شود."""
        self._clear()
        with self.assertRaises(RuntimeError):
            _default_spawn("brain.daemon", Path(tempfile.mkdtemp()) / "x.log",
                           Path(tempfile.mkdtemp()))

    def test_tick_with_flag_off_and_real_spawn_does_not_launch(self):
        """با flag خاموش، حتی tick()ِ مستقیم (spawnِ واقعی) فرایندِ واقعی نمی‌سازد."""
        self._clear()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            # spawn_fn پیش‌فرض = _default_spawn (واقعی) → با flag خاموش raise → SPAWN_FAILED
            sup = Supervisor(out=out, audit_dir=out / "audit",
                             notify_fn=lambda *a: None,
                             now_fn=lambda: 1e6, telegram_enabled_fn=lambda: False,
                             pid_alive_fn=lambda p: False)
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "SPAWN_FAILED")


class TestHealing(unittest.TestCase):
    def test_starts_daemon_when_down_and_skips_unconfigured_telegram(self):
        with tempfile.TemporaryDirectory() as td:
            sup, _, spawned, notes, _ = _mk(Path(td))
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "START")
            self.assertEqual(_decision(actions, "telegram"), "SKIP_DISABLED")
            self.assertEqual(spawned, ["brain.daemon"])
            self.assertTrue(any("ترمیم" in n[1] for n in notes))

    def test_crash_restart_with_backoff_then_give_up(self):
        with tempfile.TemporaryDirectory() as td:
            sup, state, spawned, notes, procs = _mk(Path(td))
            for _ in range(RESTART_LIMIT):
                sup.tick()                      # START
                procs[-1].rc = 1                # crash
                sup.tick()                      # CRASHED + schedule
                state["now"] += 500             # از backoff رد شو ولی داخلِ پنجره‌ی ۱h
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "GAVE_UP")
            self.assertEqual(len(spawned), RESTART_LIMIT)
            self.assertTrue(any("تسلیم" in n[1] for n in notes))

    def test_gave_up_clears_after_cooldown(self):
        """#4 HIGH: یک burstِ گذرا نباید برای همیشه خاموش کند — بعد از cooldown بازمی‌گردد."""
        with tempfile.TemporaryDirectory() as td:
            sup, state, spawned, _, procs = _mk(Path(td))
            for _ in range(RESTART_LIMIT):
                sup.tick(); procs[-1].rc = 1; sup.tick()
                state["now"] += 300
            self.assertIn("daemon", sup.gave_up)
            self.assertEqual(_decision(sup.tick(), "daemon"), "GAVE_UP")
            # خطا رفع شد؛ زمان از پنجره‌ی crash + cooldown می‌گذرد
            state["now"] += max(GIVE_UP_COOLDOWN_S, 3600.0) + 10
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "START")   # بازیابیِ خودکار
            self.assertNotIn("daemon", sup.gave_up)

    def test_backoff_wait_before_retry(self):
        with tempfile.TemporaryDirectory() as td:
            sup, state, spawned, _, procs = _mk(Path(td))
            sup.tick()
            procs[-1].rc = 1
            sup.tick()                          # CRASHED → retry_in 10s
            state["now"] += 3
            self.assertEqual(_decision(sup.tick(), "daemon"), "WAIT_BACKOFF")
            state["now"] += 20
            self.assertEqual(_decision(sup.tick(), "daemon"), "START")

    def test_clean_exit_is_never_restarted(self):
        with tempfile.TemporaryDirectory() as td:
            sup, _, spawned, notes, procs = _mk(Path(td))
            sup.tick()
            procs[-1].rc = 0
            self.assertEqual(_decision(sup.tick(), "daemon"), "CLEAN_EXIT")
            self.assertEqual(_decision(sup.tick(), "daemon"), "HELD_CLEAN_EXIT")
            self.assertEqual(len(spawned), 1)

    def test_spawn_failure_escalates_with_backoff_and_notify(self):
        """#5: شکستِ spawn باید backoff + escalation بدهد، نه loopِ بی‌صدا."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            notes: list = []
            state = {"now": 1e6}

            def bad_spawn(m, log, cwd):
                raise OSError("CreateProcess failed")
            sup = Supervisor(out=tmp, audit_dir=tmp / "a", spawn_fn=bad_spawn,
                             notify_fn=lambda *a: notes.append(a),
                             now_fn=lambda: state["now"],
                             telegram_enabled_fn=lambda: False, pid_alive_fn=lambda p: False)
            for _ in range(RESTART_LIMIT):
                self.assertEqual(_decision(sup.tick(), "daemon"), "SPAWN_FAILED")
                state["now"] += 500
            # پس از سقف: تسلیم + خبر (نه loopِ بی‌پایانِ بی‌خبر)
            self.assertIn("daemon", sup.gave_up)
            self.assertTrue(any("تسلیم" in n[1] for n in notes))
            self.assertGreater(sup.next_allowed["daemon"], 0.0)   # backoff اعمال شد


class TestNoDuplicate(unittest.TestCase):
    def test_telegram_adopted_not_duplicated_across_supervisor_restart(self):
        """#1/#3 HIGH: supervisorِ دوم نباید telegramِ زنده را دوباره spawn کند."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup1, _, sp1, _, _ = _mk(out, telegram=True, pid_alive=lambda p: p is not None)
            sup1.tick()
            self.assertIn("brain.telegram_bot", sp1)
            # supervisorِ تازه (restart): pidِ قبلی هنوز زنده
            sup2, _, sp2, _, _ = _mk(out, telegram=True, pid_alive=lambda p: p is not None)
            self.assertEqual(sup2.decide("telegram")[0], "ADOPT_EXTERNAL")
            sup2.tick()
            self.assertNotIn("brain.telegram_bot", sp2)   # هیچ نمونه‌ی دوم

    def test_daemon_pid_alive_is_adopted_even_if_status_stopped(self):
        """#2/#6 HIGH: در پنجره‌ی restart (STOPPED کاذب) اگر pid زنده باشد → ADOPT."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "daemon_state.json").write_text(json.dumps({
                "last_tick_at": "2026-07-11T15:00:00",
                "stopped_at": "2026-07-11T15:00:03", "pid": 4242}), encoding="utf-8")
            sup, _, spawned, _, _ = _mk(out, pid_alive=lambda p: p is not None)
            self.assertEqual(sup.decide("daemon")[0], "ADOPT_EXTERNAL")
            sup.tick()
            self.assertEqual(spawned, [])

    def test_daemon_restart_with_resumed_at_not_stopped(self):
        """#3 HIGH: resumed_at تازه → snapshot زنده گزارش می‌کند؛ supervisor با pidِ
        زنده ADOPT می‌کند (نه STOPPED کاذب، نه dup)."""
        from control_plane.snapshot import daemon_status
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            now = datetime.now().isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(json.dumps({
                "last_tick_at": "2026-07-11T15:00:00",     # heartbeatِ قدیمیِ اجرای قبل
                "stopped_at": "2026-07-11T15:00:03",
                "resumed_at": now, "pid": 4242}), encoding="utf-8")
            self.assertEqual(daemon_status(out)["status"], "RUNNING")   # display
            sup, _, spawned, _, _ = _mk(out, pid_alive=lambda p: p is not None)
            self.assertEqual(sup.decide("daemon")[0], "ADOPT_EXTERNAL")

    def test_no_duplicate_daemon_during_startup_window(self):
        """#6: در پنجره‌ی startup (رکوردِ state هست، pid هنوز ثبت نشده) اول صبر؛ وقتی
        daemonِ در حالِ بوت pid ثبت کرد → ADOPT، نه نمونه‌ی دوم."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old, "pid": 4242}), encoding="utf-8")
            alive = {"v": False}
            sup, state, spawned, _, _ = _mk(out, pid_alive=lambda p: alive["v"])
            self.assertEqual(_decision(sup.tick(), "daemon"), "WAIT_START_CONFIRM")
            self.assertEqual(spawned, [])
            alive["v"] = True                       # daemonِ در حالِ بوت pid ثبت کرد
            # زنده تشخیص داده می‌شود → adopt/monitor، نه نمونه‌ی دوم (چه ADOPT چه
            # STALE_EXTERNAL بسته به تازگیِ heartbeat؛ نکته: هیچ dup)
            self.assertIn(_decision(sup.tick(), "daemon"), ("ADOPT_EXTERNAL", "STALE_EXTERNAL"))
            self.assertEqual(spawned, [])

    def test_owned_cleared_on_crash_allows_later_external_adopt(self):
        """#10: بعد از crashِ فرزندِ خودمان، daemonِ بیرونیِ بعدی باید ADOPT شود نه تکراری."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, _, procs = _mk(out)
            sup.tick()                                  # START (owned)
            procs[-1].rc = 1
            sup.tick()                                  # CRASHED → owned discarded
            self.assertNotIn("daemon", sup.owned)
            # یک daemonِ بیرونیِ زنده ظاهر می‌شود
            now = datetime.now().isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": now, "pid": 7}), encoding="utf-8")
            state["now"] += 1000                        # از backoff رد شو
            self.assertEqual(sup.decide("daemon")[0], "ADOPT_EXTERNAL")


class TestRedLines(unittest.TestCase):
    def test_daemon_stop_blocks_daemon_but_not_telegram(self):
        """#12: daemon.stop فقط daemon را می‌بندد؛ telegram (کانالِ کنترل) زنده می‌ماند."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "daemon.stop").write_text("", encoding="utf-8")
            sup, _, spawned, _, _ = _mk(out, telegram=True)
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "SKIP_OWNER_STOP")
            self.assertEqual(_decision(actions, "telegram"), "START")
            self.assertEqual(spawned, ["brain.telegram_bot"])

    def test_durable_owner_stop_flag_blocks_resurrection(self):
        """#1/#4 HIGH: بعد از اینکه daemon فایلِ daemon.stop را مصرف کرد، نشانِ دائمی
        باید جلوی زنده‌کردنِ دوباره را بگیرد."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            # daemon.stop مصرف/حذف شده؛ فقط نشانِ دائمی مانده
            (out / OWNER_STOP_FLAG).write_text("x", encoding="utf-8")
            (out / "daemon_state.json").write_text(json.dumps({
                "last_tick_at": "2026-07-11T15:05:00",
                "stopped_at": "2026-07-11T15:05:03", "pid": 4242}), encoding="utf-8")
            sup, _, spawned, _, _ = _mk(out, pid_alive=lambda p: False)
            self.assertEqual(sup.decide("daemon")[0], "SKIP_OWNER_STOP")
            sup.tick()
            self.assertEqual(spawned, [])

    def test_halt_never_restarted_and_notified_once(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "daemon_state.json").write_text(json.dumps(
                {"last_tick_at": "2026-07-11T15:00:00",
                 "halted_at": "2026-07-11T15:00:01"}), encoding="utf-8")
            sup, _, spawned, notes, _ = _mk(out)
            sup.tick(); sup.tick()
            self.assertEqual(spawned, [])
            self.assertEqual(len([n for n in notes if "HALT" in n[1]]), 1)

    def test_fresh_external_daemon_is_adopted_not_duplicated(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            now = datetime.now().isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": now}), encoding="utf-8")
            sup, _, spawned, _, _ = _mk(out)
            self.assertEqual(_decision(sup.tick(), "daemon"), "ADOPT_EXTERNAL")
            self.assertEqual(spawned, [])

    def test_stale_external_alive_is_reported_not_killed(self):
        """#17: نمونه‌ی بیرونیِ زنده‌ولی‌stale → گزارش، هرگز kill (guard واقعاً اجرا شود)."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old, "pid": 999}), encoding="utf-8")
            sup, _, spawned, notes, _ = _mk(out, pid_alive=lambda p: p is not None)   # بیرونی زنده
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "STALE_EXTERNAL")
            self.assertEqual(spawned, [])
            self.assertIsNone(sup.procs.get("daemon"))   # هیچ handle → هیچ terminate ممکن
            self.assertTrue(any("hang" in n[1] for n in notes))

    def test_stale_external_dead_is_recovered(self):
        """اگر daemonِ بیرونی واقعاً مرده (pid dead) و stale → اول صبرِ startup، بعد recover."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old, "pid": 999}), encoding="utf-8")
            sup, state, spawned, _, _ = _mk(out, pid_alive=lambda p: False)
            self.assertEqual(_decision(sup.tick(), "daemon"), "WAIT_START_CONFIRM")
            self.assertEqual(spawned, [])
            state["now"] += 20
            self.assertEqual(_decision(sup.tick(), "daemon"), "START")
            self.assertEqual(spawned, ["brain.daemon"])

    def test_owner_stop_reaped_so_cancel_can_revive(self):
        """regression#1: بعد از owner-stop، handle reap شود تا cancel بتواند daemon را احیا کند."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, _, procs = _mk(out)
            sup.tick()                                   # START, owns daemon
            (out / OWNER_STOP_FLAG).write_text("x", encoding="utf-8")
            procs[0].rc = 0                              # daemon تمیز خارج شد
            self.assertEqual(_decision(sup.tick(), "daemon"), "SKIP_OWNER_STOP")
            self.assertIsNone(sup.procs.get("daemon"))   # handle reap شد
            self.assertNotIn("daemon", sup.held)         # HELD نچسبید
            (out / OWNER_STOP_FLAG).unlink()             # cancel
            self.assertEqual(_decision(sup.tick(), "daemon"), "START")   # احیا شد

    def test_kill_unconfirmed_keeps_handle_and_alerts(self):
        """regression#2: اگر terminate بی‌اثر بماند، handle نگه داشته و مالک خبردار شود."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, notes, _ = _mk(out)
            stubborn = FakeProc(pid=1, ignores_terminate=True, ignores_kill=True)
            sup.procs["daemon"] = stubborn
            sup.owned.add("daemon")
            sup.spawned_at["daemon"] = state["now"]
            old = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old}), encoding="utf-8")
            state["now"] += HUNG_GRACE_S + 10
            sup.tick()                                   # اولین یخ‌زدگی → RUNNING_OK
            state["now"] += HUNG_FREEZE_S + 10
            actions = sup.tick()                         # KILL → terminate نادیده
            self.assertEqual(_decision(actions, "daemon"), "KILL_UNCONFIRMED")
            self.assertIs(sup.procs.get("daemon"), stubborn)   # handle نگه داشته شد
            self.assertTrue(stubborn.terminated and stubborn.killed)  # هر دو تلاش شدند
            self.assertTrue(any("بی‌اثر" in n[1] for n in notes))

    def test_kill_escalation_via_sigkill_reaps(self):
        """اگر terminate بی‌اثر ولی kill (SIGKILL) مؤثر باشد → escalation می‌کشد و reap می‌کند."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, _, _ = _mk(out)
            p = FakeProc(pid=1, ignores_terminate=True, ignores_kill=False)  # فقط kill مؤثر
            sup.procs["daemon"] = p
            sup.owned.add("daemon")
            sup.spawned_at["daemon"] = state["now"]
            old = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old}), encoding="utf-8")
            state["now"] += HUNG_GRACE_S + 10
            sup.tick()                                    # اولین یخ‌زدگی
            state["now"] += HUNG_FREEZE_S + 10
            actions = sup.tick()                          # terminate no-op → kill مؤثر → reap
            self.assertEqual(_decision(actions, "daemon"), "KILL_RESTART")
            self.assertTrue(p.terminated and p.killed)    # escalation فراخوانده شد
            self.assertIsNone(sup.procs.get("daemon"))    # reap شد (نه UNCONFIRMED)

    def test_hung_own_child_killed_only_after_freeze_window(self):
        """#7: tickِ طولانیِ سالم کشته نمی‌شود؛ فقط بعد از یخ‌زدگیِ *مطلقِ* طولانی."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, _, procs = _mk(out)
            sup.tick()                          # START (owned)
            old = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": old}), encoding="utf-8")
            state["now"] += HUNG_GRACE_S + 30   # بعد از grace، heartbeat یخ‌زده
            self.assertEqual(_decision(sup.tick(), "daemon"), "RUNNING_OK")  # هنوز نه
            self.assertFalse(procs[0].terminated)
            state["now"] += HUNG_FREEZE_S + 10  # یخ‌زدگیِ طولانی → hangِ واقعی
            self.assertEqual(_decision(sup.tick(), "daemon"), "KILL_RESTART")
            self.assertTrue(procs[0].terminated)

    def test_slow_but_progressing_daemon_not_killed(self):
        """#7: اگر heartbeat جلو برود (کندِ سالم) → هرگز KILL، حتی بعد از مدتِ طولانی."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sup, state, spawned, _, procs = _mk(out)
            sup.tick()
            state["now"] += HUNG_GRACE_S + 10
            for i in range(6):
                t = (datetime.now() - timedelta(seconds=300 - i * 5)).isoformat(timespec="seconds")
                (out / "daemon_state.json").write_text(
                    json.dumps({"last_tick_at": t}), encoding="utf-8")
                state["now"] += 300             # زمانِ زیاد می‌گذرد ولی heartbeat جلو می‌رود
                self.assertEqual(_decision(sup.tick(), "daemon"), "RUNNING_OK")
            self.assertFalse(procs[0].terminated)


class TestSingletonLock(unittest.TestCase):
    def test_second_supervisor_refuses_when_lock_held(self):
        """قفلِ race-free: اگر OS lock در دستِ فرایندِ زنده‌ی دیگر باشد → رد."""
        with mock.patch.dict(os.environ, {"CONTROL_PLANE_SELF_HEAL": "1"}):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td)
                sup = Supervisor(out=out, audit_dir=out / "a",
                                 notify_fn=lambda *a: None, now_fn=lambda: 1e6,
                                 telegram_enabled_fn=lambda: False,
                                 lock_fn=lambda path: None)   # قفل در دستِ دیگری
                res = sup.run_forever(max_ticks=1)
                self.assertFalse(res["ok"])
                self.assertIn("تک‌نمونه", res["reason"])

    def test_real_os_lock_blocks_second_instance(self):
        """regression#3 (race-free): قفلِ واقعیِ OS، نمونه‌ی دومِ هم‌زمان را رد می‌کند
        و با آزادشدن دوباره قابلِ‌گرفتن است — بدونِ دزدیده‌شدن با فایلِ خالی."""
        from control_plane.supervisor import _os_try_lock
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "supervisor.lock"
            h1 = _os_try_lock(lock)
            self.assertNotIn(h1, (None,))          # اولی گرفت
            if h1 != "NOLOCK":                      # اگر OS قفل را پشتیبانی می‌کند
                self.assertIsNone(_os_try_lock(lock))   # دومی رد شد (نه دزدی)
                h1.close()
                h3 = _os_try_lock(lock)             # آزاد شد → دوباره قابلِ‌گرفتن
                self.assertNotIn(h3, (None,))
                if h3 != "NOLOCK":
                    h3.close()


class TestEvidenceAndDryRun(unittest.TestCase):
    def test_audit_and_state_written(self):
        with tempfile.TemporaryDirectory() as td:
            sup, *_ = _mk(Path(td))
            sup.tick()
            audit = Path(td) / "audit" / "supervisor_log.jsonl"
            self.assertTrue(audit.exists())
            lines = [json.loads(x) for x in
                     audit.read_text(encoding="utf-8").strip().splitlines()]
            self.assertEqual(len(lines), 2)
            self.assertTrue(all(l.get("rollback") for l in lines))
            self.assertTrue((Path(td) / "audit" / "supervisor_state.json").exists())

    def test_dry_run_spawns_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            sup, _, spawned, notes, _ = _mk(Path(td), dry=True)
            actions = sup.tick()
            self.assertEqual(_decision(actions, "daemon"), "START")
            self.assertEqual(spawned, [])
            self.assertEqual(notes, [])
            self.assertFalse((Path(td) / "audit").exists())

    def test_supervisor_stop_file_ends_loop(self):
        with mock.patch.dict(os.environ, {"CONTROL_PLANE_SELF_HEAL": "1"}):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td)
                (out / "supervisor.stop").write_text("", encoding="utf-8")
                sup, _, spawned, _, _ = _mk(out)
                res = sup.run_forever(max_ticks=5)
                self.assertTrue(res["ok"])
                self.assertEqual(res["ticks"], 0)
                self.assertEqual(spawned, [])
                self.assertFalse((out / "supervisor.stop").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
