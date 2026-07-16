"""
control_plane/supervisor.py — v5: ترمیمِ خود (self-healing) برای اجرای ۲۴/۷.

خواسته‌ی مالک (2026-07-12): لپ‌تاپ همیشه روشن، ارتباط فقط از تلگرامِ ساده،
سیستم خودش را ارتقا می‌دهد — پس اگر daemon یا telegram_bot بیفتد، باید خودش
بلند شود، بدونِ دستِ مالک.

چه می‌کند:
  • brain.daemon و brain.telegram_bot را به‌عنوان فرایندِ فرزند اجرا و پایش می‌کند.
  • crash (exit code ≠ 0) → راه‌اندازیِ دوباره با backoff و سقفِ تلاش (با ریستِ زمانی).
  • hang (فرایند زنده ولی heartbeat کهنه) → terminate + راه‌اندازیِ دوباره — فقط برای
    daemonِ خودمان، فقط بعد از ۲ مشاهده‌ی پیاپیِ بدونِ پیشرفت (تا tickِ طولانیِ سالم
    اشتباهاً کشته نشود). فرایندِ بیرونیِ هنگ‌کرده را هرگز نمی‌کشد — فقط خبر می‌دهد.
  • ضدِ تکراری‌شدن: قبل از هر START، زنده‌بودنِ نمونه‌ی بیرونی را با PID می‌سنجد
    (daemon از daemon_state.json.pid؛ telegram از فایلِ pidِ خودمان). نمونه‌ی زنده →
    ADOPT (فقط پایش)، نه spawnِ دوم. یک قفلِ تک‌نمونه هم از اجرای دو supervisor جلو می‌گیرد.

چه *نمی‌کند* (خطِ قرمز — kill-switch همیشه بر self-heal می‌چربد):
  • بعد از HALT حفاظتی (daemon_state.halted_at) هرگز restart نمی‌کند — فقط خبر می‌دهد.
  • با وجودِ outputs/daemon.stop **یا** نشانِ دائمیِ owner_intent_stop.flag هرگز
    daemon را بلند نمی‌کند (نیتِ مالک؛ چون daemon خودش daemon.stop را مصرف/حذف می‌کند،
    نشانِ دائمی لازم است تا kill دوام بیاورد). لغو: killswitch.cancel_stop.
  • خروجِ تمیزِ daemon (exit 0) را restart نمی‌کند — توقفِ تمیز یعنی خواسته.
  • daemon.stop فقط daemon را می‌بندد، نه telegram — تلگرام کانالِ کنترلِ توست و باید
    زنده بماند. توقفِ کلِ پایش = outputs/supervisor.stop.
  • هیچ خطی از brain/daemon.py یا brain/telegram_bot.py تغییر نمی‌دهد.

کنترل:
  • flag: CONTROL_PLANE_SELF_HEAL — default-off. هم run_forever و هم spawnِ واقعیِ
    فرایند (_default_spawn) در لایه‌ی اجرا این را چک می‌کنند؛ با flagِ خاموش هیچ
    فرایندِ واقعی‌ای اجرا نمی‌شود حتی اگر tick() مستقیم صدا زده شود.
  • توقفِ خودِ supervisor: outputs/supervisor.stop یا Ctrl+C (فرزندهای سالم نمی‌میرند).
  • evidence: outputs/control_plane/supervisor_log.jsonl + supervisor_state.json.

اجرا:  python -m control_plane.supervisor            (loop کامل)
       python -m control_plane.supervisor --dry-run  (فقط تصمیم‌ها، بدونِ spawn)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from control_plane.flags import flag
from control_plane.policy import evaluate
from control_plane.snapshot import DEFAULT_OUT, daemon_status

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_DIR = SYSTEM_ROOT / "outputs" / "control_plane"
AUDIT_FILE = "supervisor_log.jsonl"
STATE_FILE = "supervisor_state.json"
OWNER_STOP_FLAG = "owner_intent_stop.flag"   # نشانِ دائمیِ توقفِ مالک (در out)
SUP_LOCK_FILE = "supervisor.lock"            # قفلِ تک‌نمونه (در out)

RESTART_WINDOW_S = 3600.0    # پنجره‌ی شمارشِ crashها
RESTART_LIMIT = 5            # بیش از این در پنجره → تسلیم + خبر به مالک
GIVE_UP_COOLDOWN_S = 3600.0  # بعد از این مدت بدونِ crashِ نو، gave_up ریست می‌شود
BACKOFF_S = [10.0, 30.0, 60.0, 300.0, 900.0]
HUNG_GRACE_S = 120.0         # بعد از spawn این‌قدر صبر تا heartbeat جا بیفتد
# hang فقط وقتی که heartbeat برای این مدتِ *مطلق* یخ‌زده بماند (نه فقط چند tick).
# یک run_one()ِ جسورِ LLM می‌تواند دقایقی طول بکشد؛ ۱۰ دقیقه یخ‌زدگی تقریباً حتماً
# hangِ واقعی است، نه tickِ طولانیِ سالم. (رفعِ false-positiveِ #7)
HUNG_FREEZE_S = 600.0
# قبل از spawnِ daemon وقتی رکوردِ state هست ولی زنده‌بودن تأیید نشده، این‌قدر
# مشاهده صبر کن تا daemonِ در حالِ بوت pid خود را ثبت کند (رفعِ dupِ پنجره‌ی
# startup/restart: #6 + regressionِ DST/startup-crash).
START_CONFIRM = 2

CHILDREN: list[tuple[str, str]] = [
    ("daemon", "brain.daemon"),
    ("telegram", "brain.telegram_bot"),
]


def self_heal_live() -> bool:
    return flag("CONTROL_PLANE_SELF_HEAL")


def _tick_seconds() -> float:
    try:
        return max(5.0, float(os.getenv("CONTROL_PLANE_SUPERVISOR_TICK", "30")))
    except ValueError:
        return 30.0


def _daemon_tick_s() -> float:
    try:
        return max(1.0, float(os.getenv("DAEMON_TICK_SECONDS", "30")))
    except ValueError:
        return 30.0


def _pid_alive(pid: Any) -> bool:
    """آیا فرایندی با این pid زنده است؟ خطا/نامعتبر → False (fail-closed برای adoption)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            k = ctypes.windll.kernel32
            h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            try:
                code = ctypes.c_ulong()
                if k.GetExitCodeProcess(h, ctypes.byref(code)):
                    return code.value == STILL_ACTIVE
                return True
            finally:
                k.CloseHandle(h)
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def _default_spawn(module: str, log_path: Path, cwd: Path):
    """فرزند را با لاگِ append و بدونِ پنجره‌ی کنسول اجرا می‌کند.

    گیتِ لایه‌ی اجرا: با flagِ خاموش هیچ فرایندِ واقعی اجرا نمی‌شود (حتی اگر
    tick() بی‌واسطه صدا زده شود) — هم‌تراز با killswitch/approvals که هر action
    را در لحظه‌ی اجرا گیت می‌کنند.
    """
    if not self_heal_live():
        raise RuntimeError("CONTROL_PLANE_SELF_HEAL خاموش است — spawnِ واقعی مسدود")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(log_path, "a", encoding="utf-8", errors="replace")
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        kwargs["creationflags"] = 0x08000000 | 0x00000200
    return subprocess.Popen([sys.executable, "-m", module], cwd=str(cwd),
                            stdout=f, stderr=subprocess.STDOUT, **kwargs)


def _default_notify(alert_type: str, context: str, why_now: str,
                    recommendation: str, consequence: str) -> None:
    """خبر به مالک از کانالِ موجودِ notify/digest (تلگرام اگر تنظیم باشد)."""
    try:
        from brain import notify
        notify.queue_for_digest(alert_type, context, why_now,
                                recommendation, consequence)
    except Exception:
        pass  # نبودِ notify نباید ترمیم را بشکند


def _telegram_configured() -> bool:
    try:
        from brain.telegram_bot import is_configured
        return bool(is_configured())
    except Exception:
        return False


def _os_try_lock(path: Path):
    """قفلِ انحصاریِ سطحِ OS، غیرمسدودکننده، برای عمرِ فرایند. handle یا None.

    race-free (بر خلافِ pid-file): اگر supervisorِ زنده‌ی دیگری قفل دارد → OS رد
    می‌کند؛ اگر فرایندِ صاحب بمیرد، OS خودکار قفل را آزاد می‌کند (نه فایلِ کهنه‌ی
    گیرافتاده، نه دزدیده‌شدن با فایلِ خالی)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(str(path), "a+")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return None      # قفل در دستِ فرایندِ زنده‌ی دیگر
        try:                 # pid را برای خوانشِ انسان بنویس (informational)
            fh.seek(0); fh.truncate(); fh.write(str(os.getpid())); fh.flush()
        except OSError:
            pass
        return fh
    except OSError:
        return "NOLOCK"      # سیستمِ فایل قفل را پشتیبانی نمی‌کند → مانعِ ترمیم نشو


class Supervisor:
    """پایشگرِ ترمیمِ خود — منطقِ تصمیم جدا و تزریق‌پذیر برای تست."""

    def __init__(self, out: Path | None = None, audit_dir: Path | None = None,
                 spawn_fn: Callable | None = None,
                 notify_fn: Callable | None = None,
                 now_fn: Callable[[], float] | None = None,
                 telegram_enabled_fn: Callable[[], bool] | None = None,
                 pid_alive_fn: Callable[[Any], bool] | None = None,
                 lock_fn: Callable[[Path], Any] | None = None,
                 dry_run: bool = False):
        self.out = Path(out or DEFAULT_OUT)
        self.audit_dir = Path(audit_dir or DEFAULT_AUDIT_DIR)
        self.spawn_fn = spawn_fn or _default_spawn
        self.notify_fn = notify_fn or _default_notify
        self.now_fn = now_fn or time.time
        self.telegram_enabled_fn = telegram_enabled_fn or _telegram_configured
        self.pid_alive_fn = pid_alive_fn or _pid_alive
        self.lock_fn = lock_fn or _os_try_lock
        self.dry_run = dry_run
        self._lock_handle: Any = None

        self.procs: dict[str, Any] = {}
        self.spawned_at: dict[str, float] = {}
        self.owned: set[str] = set()        # فرزندهایی که خودمان spawn کرده‌ایم (زنده)
        self.held: set[str] = set()         # خروجِ تمیز → دیگر بلند نکن
        self.gave_up: set[str] = set()      # سقفِ crash پر شد
        self.gave_up_at: dict[str, float] = {}
        self.crashes: dict[str, deque] = {n: deque() for n, _ in CHILDREN}
        self.next_allowed: dict[str, float] = {n: 0.0 for n, _ in CHILDREN}
        self.notified: set[str] = set()     # کلیدهای notify یک‌باره
        # bookkeepingِ تشخیصِ hang و startup-confirm (فقط daemon)
        self.last_seen_tick: dict[str, str] = {}
        self.frozen_since: dict[str, float] = {}   # چه زمانی heartbeat یخ زد
        self.down_seen: dict[str, int] = {n: 0 for n, _ in CHILDREN}  # مشاهده‌های «پایین»

    # ── فایل‌های کمکی ─────────────────────────────────────────────────────
    def _pidfile(self, name: str) -> Path:
        return self.out / f"{name}.cp.pid"

    def _write_pidfile(self, name: str, pid: Any) -> None:
        try:
            self._pidfile(name).write_text(str(pid), encoding="utf-8")
        except OSError:
            pass

    def _read_pidfile(self, name: str) -> Any:
        try:
            return int(self._pidfile(name).read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def _clear_pidfile(self, name: str) -> None:
        try:
            self._pidfile(name).unlink()
        except OSError:
            pass

    def _owner_stopped(self) -> bool:
        """نیتِ توقفِ مالک — daemon.stop (گذرا) یا نشانِ دائمیِ owner_intent_stop.flag."""
        return (self.out / "daemon.stop").exists() or (self.out / OWNER_STOP_FLAG).exists()

    # ── evidence ─────────────────────────────────────────────────────────
    def _audit(self, rec: dict[str, Any]) -> None:
        if self.dry_run:
            return
        try:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            with open(self.audit_dir / AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _notify_once(self, key: str, alert_type: str, context: str,
                     why: str, rec_: str, cons: str) -> None:
        if key in self.notified or self.dry_run:
            return
        self.notified.add(key)
        self.notify_fn(alert_type, context, why, rec_, cons)

    def _crash_count(self, name: str) -> int:
        now = self.now_fn()
        dq = self.crashes[name]
        while dq and now - dq[0] > RESTART_WINDOW_S:
            dq.popleft()
        return len(dq)

    def _daemon_alive(self, d: dict) -> bool:
        """daemon واقعاً زنده است؟ = pidِ ثبت‌شده زنده، یا heartbeatِ tick تازه.

        عمداً به resumed_at/started_at (که فقط «شروع» را نشان می‌دهند، نه «زنده‌ماندن»)
        اتکا نمی‌کند — تا daemonِ startup-crashـکرده اشتباهاً زنده گزارش و adopt نشود
        (رفعِ regressionِ blind-spotِ startup + مصونیت نسبی به clock-skew/DST، چون
        pid-liveness به timestamp وابسته نیست)."""
        if self.pid_alive_fn(d.get("pid")):
            return True
        age = d.get("heartbeat_age_s")
        return age is not None and age <= 3 * _daemon_tick_s()

    # ── تصمیم (فقط فایل‌ها را می‌خوانَد؛ بدونِ spawn/kill) ──────────────────
    def decide(self, name: str) -> tuple[str, str]:
        """(decision, detail) — بدونِ side effect روی فرایندها."""
        now = self.now_fn()

        if name == "telegram" and not self.telegram_enabled_fn():
            return "SKIP_DISABLED", "token تلگرام تنظیم نیست (کارِ مالک)"

        # نیتِ توقفِ مالک فقط daemon را می‌بندد؛ telegram باید زنده بماند
        if name == "daemon" and self._owner_stopped():
            return "SKIP_OWNER_STOP", "daemon.stop یا owner_intent_stop.flag حاضر — نیتِ مالک"

        d = daemon_status(self.out) if name == "daemon" else {}
        if name == "daemon" and (d.get("halted_at") or ""):
            return "SKIP_HALT", f"HALT حفاظتی ({d.get('halted_at')}) — ترمیمِ خودکار ممنوع"

        # gave_up با ریستِ زمانی (یک burstِ گذرا نباید برای همیشه خاموش کند)
        if name in self.gave_up:
            if (self._crash_count(name) == 0
                    and now - self.gave_up_at.get(name, now) >= GIVE_UP_COOLDOWN_S):
                self.gave_up.discard(name)
                self.gave_up_at.pop(name, None)
            else:
                return "GAVE_UP", f"سقفِ {RESTART_LIMIT} crash در ساعت پر شد (تا cooldown)"

        if name in self.held:
            return "HELD_CLEAN_EXIT", "خروجِ تمیز (rc=0) — restart فقط با نیتِ مالک"

        proc = self.procs.get(name)
        if proc is None:
            # آیا نمونه‌ی بیرونی/قبلی زنده است؟ (ضدِ تکراری‌شدن)
            if name == "daemon":
                if self._daemon_alive(d):
                    if d.get("status") == "STALE":   # زنده ولی heartbeat کهنه، مالِ ما نیست
                        return "STALE_EXTERNAL", ("daemonِ بیرونی زنده ولی heartbeat کهنه — "
                                                  "نمی‌کشم (مالِ ما نیست)؛ فقط خبر")
                    return "ADOPT_EXTERNAL", "daemonِ بیرونی زنده است — فقط پایش"
                # زنده تأیید نشد: اگر رکوردِ state هست (شاید daemon در حالِ بوت است و
                # هنوز pid ثبت نکرده)، قبل از spawn چند مشاهده صبر کن تا dup رخ ندهد.
                if (self.out / "daemon_state.json").exists() \
                        and self.down_seen.get(name, 0) < START_CONFIRM:
                    return "WAIT_START_CONFIRM", ("رکوردِ daemon هست ولی زنده تأیید نشد — "
                                                  "صبر پیش از spawn (ضدِ dupِ پنجره‌ی startup)")
            else:  # telegram
                if self.pid_alive_fn(self._read_pidfile(name)):
                    return "ADOPT_EXTERNAL", "نمونه‌ی قبلیِ telegram هنوز زنده است — فقط پایش"
            if now < self.next_allowed[name]:
                return "WAIT_BACKOFF", f"{self.next_allowed[name] - now:.0f}s مانده"
            return "START", "فرایند پایین است — راه‌اندازی"

        rc = proc.poll()
        if rc is None:
            # hang فقط برای daemonِ خودمان، فقط وقتی heartbeat برای مدتِ *مطلقِ* طولانی
            # یخ‌زده مانده (نه صرفاً چند tick) — تا tickِ طولانیِ سالمِ LLM کشته نشود.
            fz = self.frozen_since.get(name)
            if (name == "daemon" and d.get("status") == "STALE"
                    and now - self.spawned_at.get(name, now) > HUNG_GRACE_S
                    and fz is not None and now - fz >= HUNG_FREEZE_S):
                return "KILL_RESTART", "daemonِ خودمان زنده ولی heartbeat مدتی طولانی یخ‌زده (hang)"
            return "RUNNING_OK", ""
        if rc == 0:
            return "CLEAN_EXIT", "rc=0 — توقفِ خواسته؛ restart نمی‌کنم"
        return "CRASHED", f"rc={rc}"

    # ── bookkeepingِ پیشرفت/hang/down (قبل از decide، فقط daemon) ────────────
    def _observe(self, name: str) -> None:
        if name != "daemon":
            return
        now = self.now_fn()
        d = daemon_status(self.out)
        cur = d.get("last_tick_at") or ""
        proc = self.procs.get(name)
        alive_handle = proc is not None and proc.poll() is None
        stale = d.get("status") == "STALE"
        past_grace = now - self.spawned_at.get(name, now) > HUNG_GRACE_S
        # ردیابیِ یخ‌زدگیِ heartbeat (hang) — فقط برای فرزندِ زنده‌ی خودمان
        if alive_handle and stale and past_grace:
            if name in self.last_seen_tick and cur and cur != self.last_seen_tick[name]:
                self.frozen_since.pop(name, None)          # heartbeat جلو رفت → یخ نیست
            else:
                self.frozen_since.setdefault(name, now)    # شروع/ادامه‌ی یخ‌زدگی
        else:
            self.frozen_since.pop(name, None)
        if cur:
            self.last_seen_tick[name] = cur
        # شمارشِ «پایین» برای startup-confirm — وقتی handle نداریم و زنده تأیید نشده
        if proc is None and not self._daemon_alive(d):
            self.down_seen[name] = self.down_seen.get(name, 0) + 1
        else:
            self.down_seen[name] = 0

    # ── اجرا‌ی یک tick ───────────────────────────────────────────────────
    def tick(self) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        now_iso = datetime.now().isoformat(timespec="seconds")
        for name, module in CHILDREN:
            self._observe(name)
            decision, detail = self.decide(name)
            rec: dict[str, Any] = {
                "timestamp": now_iso, "child": name, "decision": decision,
                "detail": detail, "dry_run": self.dry_run,
                "crashes_1h": self._crash_count(name),
                "rollback": "توقف: outputs/daemon.stop (daemon) · "
                            "outputs/supervisor.stop (خودِ supervisor)",
            }

            if decision == "START" and not self.dry_run:
                pol = evaluate("self_heal_restart")
                rec["policy_action"], rec["policy_level"] = pol.action_type, pol.level
                try:
                    self.procs[name] = self.spawn_fn(
                        module, self.audit_dir / "logs" / f"{name}.out.log",
                        SYSTEM_ROOT)
                    self.spawned_at[name] = self.now_fn()
                    self.owned.add(name)
                    pid = getattr(self.procs[name], "pid", None)
                    rec["pid"] = pid
                    self._write_pidfile(name, pid)
                    self._notify_once(f"heal:{name}:{int(self.now_fn())}",
                                      "notify", f"ترمیمِ خود: {name} بالا آمد",
                                      "فرایند پایین بود", "نیاز به کارِ تو: هیچ",
                                      "ادامه‌ی خودکارِ اجرا")
                except Exception as e:
                    # گیرِ لایه‌ی اجرا (spawnِ خاموش‌شده یا خطای OS): مثلِ شکست
                    # رفتار کن — backoff + escalation، نه loopِ بی‌صدا.
                    rec["decision"] = "SPAWN_FAILED"
                    rec["detail"] = f"{type(e).__name__}: {e}"
                    self.procs[name] = None
                    self.owned.discard(name)
                    self.crashes[name].append(self.now_fn())
                    self._after_failure(name, rec)

            elif decision == "KILL_RESTART" and not self.dry_run:
                p = self.procs.get(name)
                # terminate (SIGTERM/TerminateProcess)؛ اگر بی‌اثر بود، kill
                # (SIGKILL روی POSIX) به‌عنوانِ escalation.
                try:
                    if p is not None:
                        p.terminate()
                except Exception:
                    pass
                try:
                    if p is not None and p.poll() is None:
                        p.kill()
                except Exception:
                    pass
                # تأییدِ مرگ: اگر باز هم زنده ماند، handle را دور نریز — وگرنه فرایندِ
                # رهاشده بعداً STALE_EXTERNAL می‌شود و هرگز دوباره kill نمی‌شود
                # (رفعِ regression). خبر به مالک؛ در پنجره‌ی یخ‌زدگیِ بعدی دوباره تلاش.
                still_alive = False
                try:
                    still_alive = p is not None and p.poll() is None
                except Exception:
                    still_alive = False
                if still_alive:
                    rec["decision"] = "KILL_UNCONFIRMED"
                    rec["detail"] = "terminate+kill بی‌اثر ماند — handle نگه داشته شد"
                    self.frozen_since.pop(name, None)     # HUNG_FREEZE دوباره بگذرد
                    self._notify_once(f"killfail:{name}:{int(self.now_fn())}", "warning",
                                      f"{name}: terminate+kill بی‌اثر ماند",
                                      "فرایند بعد از kill هنوز زنده است",
                                      "نیاز به kill دستی روی سیستم",
                                      "supervisor پس از پنجره‌ی یخ‌زدگیِ بعدی دوباره تلاش می‌کند")
                else:
                    self.procs[name] = None
                    self.owned.discard(name)
                    self._clear_pidfile(name)
                    self.frozen_since.pop(name, None)
                    self.crashes[name].append(self.now_fn())
                    self._after_failure(name, rec)

            elif decision == "CRASHED":
                self.procs[name] = None
                self.owned.discard(name)
                self._clear_pidfile(name)
                if not self.dry_run:
                    self.crashes[name].append(self.now_fn())
                    self._after_failure(name, rec)

            elif decision == "CLEAN_EXIT":
                self.procs[name] = None
                self.owned.discard(name)
                self._clear_pidfile(name)
                self.held.add(name)
                self._notify_once(f"clean:{name}", "notify",
                                  f"{name} تمیز متوقف شد (rc=0)",
                                  "توقفِ خواسته تشخیص داده شد",
                                  "اگر باید بالا بیاید: supervisor را دوباره اجرا کن",
                                  "restart خودکار نمی‌شود")

            elif decision == "SKIP_OWNER_STOP":
                # فرزند به‌خواستِ مالک پایین می‌رود — handleِ مرده را reap کن تا بعد از
                # cancel_stop اشتباهاً CLEAN_EXIT→HELD نشود و بتواند دوباره بالا بیاید
                # (رفعِ regression: cancel_stop نمی‌توانست daemonِ owned را احیا کند).
                if self.procs.get(name) is not None:
                    self.procs[name] = None
                    self.owned.discard(name)
                    self._clear_pidfile(name)
                    self.frozen_since.pop(name, None)

            elif decision == "SKIP_HALT":
                halted = daemon_status(self.out).get("halted_at", "")
                self._notify_once(f"halt:{halted}", "blocked",
                                  "HALT حفاظتی — ترمیمِ خودکار ممنوع",
                                  "نقضِ لنگرِ ریاضی گزارش شده",
                                  "بررسیِ دستی لازم است (policy: approval)",
                                  "daemon تا تصمیمِ تو پایین می‌ماند")

            elif decision == "STALE_EXTERNAL":
                self._notify_once("stale_external", "warning",
                                  "daemon بیرونی hang به نظر می‌رسد",
                                  "heartbeat کهنه ولی فرایند مالِ supervisor نیست",
                                  "خودت ببین: فرایند را ببند یا daemon.stop بگذار",
                                  "supervisor فرایندِ غیرخودی را نمی‌کشد")

            actions.append(rec)
            self._audit(rec)

        self._write_state(actions)
        return actions

    def _after_failure(self, name: str, rec: dict) -> None:
        n = self._crash_count(name)
        rec["crashes_1h"] = n
        if n >= RESTART_LIMIT:
            self.gave_up.add(name)
            self.gave_up_at[name] = self.now_fn()
            rec["gave_up"] = True
            self._notify_once(f"giveup:{name}:{int(self.now_fn())}", "warning",
                              f"ترمیمِ خود تسلیم شد: {name}",
                              f"{n} crash در یک ساعت",
                              "لاگِ outputs/control_plane/logs را ببین",
                              f"تا {int(GIVE_UP_COOLDOWN_S/60)} دقیقه یا رفعِ دستی پایین می‌ماند")
        else:
            delay = BACKOFF_S[min(n - 1, len(BACKOFF_S) - 1)] if n else BACKOFF_S[0]
            self.next_allowed[name] = self.now_fn() + delay
            rec["retry_in_s"] = delay

    def _write_state(self, actions: list[dict]) -> None:
        if self.dry_run:
            return
        state = {
            "last_tick_at": datetime.now().isoformat(timespec="seconds"),
            "flag_live": self_heal_live(),
            "children": {a["child"]: {
                "decision": a["decision"],
                "crashes_1h": a.get("crashes_1h", 0),
                "gave_up": a["child"] in self.gave_up,
                "held": a["child"] in self.held,
            } for a in actions},
        }
        try:
            p = self.audit_dir / STATE_FILE
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            os.replace(tmp, p)
        except OSError:
            pass

    # ── قفلِ تک‌نمونه ──────────────────────────────────────────────────────
    def _acquire_lock(self) -> bool:
        """قفلِ تک‌نمونه‌ی race-free (OS advisory lock). زنده‌ی دیگری دارد → False."""
        if self.dry_run:
            return True
        h = self.lock_fn(self.out / SUP_LOCK_FILE)
        if h is None:
            return False          # supervisorِ زنده‌ی دیگری قفل را دارد
        self._lock_handle = h     # برای عمرِ فرایند نگه دار (بستن = آزادکردن)
        return True

    def _release_lock(self) -> None:
        h = self._lock_handle
        self._lock_handle = None
        if h is None or h == "NOLOCK":
            return
        try:
            h.close()             # بستنِ handle → OS قفل را آزاد می‌کند
        except Exception:
            pass

    # ── حلقه‌ی اصلی ─────────────────────────────────────────────────────
    def run_forever(self, max_ticks: int | None = None) -> dict[str, Any]:
        if not self_heal_live():
            return {"ok": False,
                    "reason": "CONTROL_PLANE_SELF_HEAL خاموش است (default-off) — "
                              "در .env روشنش کن"}
        if not self._acquire_lock():
            return {"ok": False,
                    "reason": "یک supervisorِ دیگر از قبل زنده است (قفلِ تک‌نمونه) — "
                              "برای پرهیز از فرزندِ تکراری اجرا نشد"}
        stop_file = self.out / "supervisor.stop"
        ticks = 0
        try:
            while max_ticks is None or ticks < max_ticks:
                if stop_file.exists():
                    try:
                        stop_file.unlink()
                    except OSError:
                        pass
                    break
                try:
                    self.tick()
                except Exception as e:  # پایشگر نباید با یک خطا بمیرد
                    self._audit({"timestamp": datetime.now().isoformat(timespec="seconds"),
                                 "child": "-", "decision": "TICK_ERROR",
                                 "detail": f"{type(e).__name__}: {e}", "dry_run": False})
                ticks += 1
                if max_ticks is None or ticks < max_ticks:
                    time.sleep(_tick_seconds())
        finally:
            self._release_lock()
        return {"ok": True, "ticks": ticks,
                "note": "فرزندهای سالم زنده می‌مانند — supervisor فقط پایش را بست"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="4d_system self-heal supervisor")
    ap.add_argument("--dry-run", action="store_true",
                    help="فقط تصمیم‌ها را نشان بده؛ هیچ فرایندی اجرا نکن")
    ap.add_argument("--max-ticks", type=int, default=None)
    args = ap.parse_args()

    sup = Supervisor(dry_run=args.dry_run)
    if args.dry_run:
        for a in sup.tick():
            print(json.dumps(a, ensure_ascii=False))
        sys.exit(0)
    res = sup.run_forever(max_ticks=args.max_ticks)
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if res.get("ok") else 1)
