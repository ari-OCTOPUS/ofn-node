"""
brain/git_watcher.py — نگهبانِ گیت و triggerِ خودارتقایی (CH-10).

وظیفه: تغییراتِ git repository را پایش (poll) کند و هنگامِ commitِ جدید،
فایل‌های .pyِ تغییریافته را به self_code.auto_propose_once() بدهد — فقط پیشنهاد،
هرگز اعمالِ خودکار. این channel، تیک‌بیسِ daemon را به event-driven تبدیل می‌کند:

  Source  : git working tree (HEAD diff / post-commit signal)
  Transform : git_watcher (filter + guardrails + cooldown)
  Sink      : self_code.auto_propose_once() → proposals dir → telegram approval

طراحیِ ایمنی:
  • فقط propose (read-only analysis)؛ هیچ کدی بی‌تأییدِ مالک اجرا/اعمال نمی‌شود.
  • TCB guard: فایل‌های core/, tests/, config/, guardrails.py, ... نادیده گرفته می‌شوند.
  • Cooldown: حداقل فاصله بینِ پیشنهادها (default ۱۰ دقیقه) تا flood نشود.
  • Windows-safe: polling-based (نه git hook) چون hook روی Windows Git محدود است.
"""
from __future__ import annotations

import os
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Optional

from brain import guardrails, events
from config.settings import setup_logging

logger = logging.getLogger(__name__)

# ── پیکربندی (از env) ────────────────────────────────────────────────────

_GW_ENABLED = os.getenv("GIT_WATCHER_ENABLED", "1").lower() in ("1", "true", "yes")
_GW_POLL_SECONDS = max(10.0, float(os.getenv("GIT_WATCHER_POLL_SECONDS", "60.0")))
_GW_COOLDOWN_SECONDS = max(60.0, float(os.getenv("GIT_WATCHER_COOLDOWN_SECONDS", "600.0")))
_GW_MAX_FILE_BYTES = int(os.getenv("GIT_WATCHER_MAX_FILE_BYTES", "12000"))  # هم‌سنج با self_code
_GW_PROPOSE_LIMIT_PER_RUN = max(1, int(os.getenv("GIT_WATCHER_PROPOSE_LIMIT", "2")))

# پوشه‌هایی که همیشه نادیده گرفته می‌شوند (حتی اگر خارج از TCB باشند)
_GW_SKIP_DIRS = frozenset({
    "__pycache__", ".git", ".claude", ".venv", "venv",
    "node_modules", ".pytest_cache", "outputs", "_ops", "OCTOPUS",
})


# ════════════════════════════════════════════════════════════════════════
#  مسیرها و وضعیت
# ════════════════════════════════════════════════════════════════════════

def _root() -> Path:
    """ریشه‌ی پروژه (یک سطح بالاتر از 4d_system/)."""
    from config.settings import SYSTEM_ROOT
    return SYSTEM_ROOT.parent


def _state_dir() -> Path:
    from config.settings import OUTPUT_DIR
    d = OUTPUT_DIR / "git_watcher"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return _state_dir() / "state.json"


def _signal_path() -> Path:
    """فایلِ سیگنالِ post-commit (برای hook-based trigger)."""
    return _state_dir() / "post_commit.signal"


# ════════════════════════════════════════════════════════════════════════
#  Git helpers — فراخوانی‌های subprocess با error handling
# ════════════════════════════════════════════════════════════════════════

def _run_git(*args: str, cwd: Optional[Path] = None, timeout: float = 10.0) -> tuple[bool, str]:
    """اجرای یک دستورِ git با capture_output. برمی‌گرداند (ok, stdout)."""
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd or _root()),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if r.returncode != 0:
            err = (r.stderr or "").strip()[:200]
            logger.debug("git %s failed: %s", " ".join(args), err)
            return False, ""
        return True, r.stdout or ""
    except FileNotFoundError:
        logger.warning("git binary not found in PATH")
        return False, ""
    except subprocess.TimeoutExpired:
        logger.warning("git %s timed out", " ".join(args))
        return False, ""
    except Exception as e:
        logger.warning("git %s error: %s", " ".join(args), e)
        return False, ""


def _current_head() -> Optional[str]:
    """hashِ کاملِ commitِ HEAD یا None."""
    ok, out = _run_git("rev-parse", "HEAD")
    return out.strip() if ok else None


def _repo_toplevel() -> Optional[Path]:
    """مسیرِ top-levelِ git repo یا None."""
    ok, out = _run_git("rev-parse", "--show-toplevel")
    return Path(out.strip()) if ok else None


def _changed_files_since(commit_hash: str) -> list[str]:
    """لیستِ فایل‌های تغییریافته از commit_hash تا HEAD (relative paths)."""
    ok, out = _run_git("diff", "--name-only", commit_hash, "HEAD")
    if not ok:
        return []
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return files


def _uncommitted_changes() -> list[str]:
    """فایل‌های unstaged / staged در working tree."""
    ok, out = _run_git("status", "--porcelain")
    if not ok:
        return []
    files = []
    for line in out.splitlines():
        if len(line) >= 3 and line[2] == " ":
            fname = line[3:].strip()
            if fname:
                files.append(fname)
    return files


# ════════════════════════════════════════════════════════════════════════
#  وضعیتِ پایدار (state persistence)
# ════════════════════════════════════════════════════════════════════════

def _load_state() -> dict:
    p = _state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("git_watcher state load failed: %s", e)
        return {}


def _save_state(state: dict) -> None:
    p = _state_path()
    try:
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except Exception as e:
        logger.warning("git_watcher state save failed: %s", e)


# ════════════════════════════════════════════════════════════════════════
#  فیلتر و اعتبارسنجی — کدام فایل‌ها واجدِ پیشنهادند؟
# ════════════════════════════════════════════════════════════════════════

def _is_eligible_py(rel_path: str) -> bool:
    """آیا یک فایلِ relative واجدِ پیشنهادِ self_code است؟"""
    p = Path(rel_path)
    if p.suffix != ".py":
        return False
    # نادیده‌گرفتنِ پوشه‌های skip
    if any(part in _GW_SKIP_DIRS for part in p.parts):
        return False
    # guardrail TCB
    root = _root()
    full = (root / rel_path).resolve()
    ok, reason = guardrails.assert_code_target_allowed(full)
    if not ok:
        logger.debug("git_watcher skip %s: %s", rel_path, reason)
        return False
    # اندازه
    try:
        if full.stat().st_size > _GW_MAX_FILE_BYTES:
            logger.debug("git_watcher skip %s: file too large (> %d bytes)",
                         rel_path, _GW_MAX_FILE_BYTES)
            return False
    except Exception:
        return False
    return True


def _system_rel(git_rel: str) -> str | None:
    """تبدیلِ مسیرِ relative به git-root → relative به SYSTEM_ROOT.

    git diff روی repo root (F:/backup) مسیرهایی مثل `4d_system/brain/x.py` برمی‌گرداند؛
    self_code.auto_propose_once انتظار دارد مسیر relative به SYSTEM_ROOT باشد
    (مثلاً `brain/x.py`). اگر فایل خارج از 4d_system باشد → None.
    """
    p = Path(git_rel)
    parts = p.parts
    if parts[0:1] == ("4d_system",):
        return str(Path(*parts[1:]).as_posix())
    return None


def _pick_targets(changed_files: list[str], seed: int = 0) -> list[str]:
    """از میانِ فایل‌های تغییریافته، فقط .pyِ مجاز را انتخاب و sort می‌کند.

    خروجی relative به SYSTEM_ROOT است (برای self_code.auto_propose_once).
    """
    targets: list[str] = []
    seen = set()
    for f in changed_files:
        sys_rel = _system_rel(f)
        if not sys_rel:
            continue
        if not _is_eligible_py(f):
            continue
        if sys_rel not in seen:
            seen.add(sys_rel)
            targets.append(sys_rel)
    return sorted(targets)


def _cooldown_ok(state: dict) -> bool:
    """آیا از last_propose_at به اندازه‌ی کافی زمان گذشته؟"""
    last_str = state.get("last_propose_at")
    if not last_str:
        return True
    try:
        last = datetime.fromisoformat(last_str)
        return datetime.now() - last >= timedelta(seconds=_GW_COOLDOWN_SECONDS)
    except Exception:
        return True


# ════════════════════════════════════════════════════════════════════════
#  Trigger — اتصال به self_code
# ════════════════════════════════════════════════════════════════════════

def _trigger_proposals(targets: list[str], state: dict) -> dict:
    """برای هر targetِ واجد، auto_propose_once را صدا می‌زند (propose-only)."""
    results = {"proposed": [], "skipped": [], "errors": []}
    if not _GW_ENABLED:
        logger.info("git_watcher disabled (GIT_WATCHER_ENABLED=0)")
        return results

    from brain import self_code, self_growth

    limit = min(_GW_PROPOSE_LIMIT_PER_RUN, len(targets))
    for i, target in enumerate(targets[:limit]):
        try:
            focus = self_growth.current_focus(seed=i)
            goal = focus.get("motivation", "")
            # هدفِ self_code را مستقیم به فایلِ تغییریافته می‌چسبانیم
            res = self_code.auto_propose_once(
                target_rel=target,
                seed=i,
                goal=goal,
            )
            if res.get("ok"):
                results["proposed"].append({
                    "target": target,
                    "pid": res.get("pid"),
                    "goal": goal,
                })
                state["last_propose_at"] = datetime.now().isoformat(timespec="seconds")
                events.emit(
                    "approval.required",
                    f"git-trigger proposal {res.get('pid','?')} for {target}",
                    status="pending",
                    agent_id="git_watcher",
                    approval_state="pending",
                    next_action="مالک در داشبورد/تلگرام تأیید/رد کند",
                )
            else:
                results["skipped"].append({
                    "target": target,
                    "reason": res.get("reason", "?"),
                })
        except Exception as e:
            logger.error("git_watcher propose error for %s: %s", target, e)
            results["errors"].append({"target": target, "error": str(e)})

    return results


# ════════════════════════════════════════════════════════════════════════
#  حلقه‌ی اصلی — check_and_trigger
# ════════════════════════════════════════════════════════════════════════

def check_and_trigger(
    *,
    force: bool = False,
    state: Optional[dict] = None,
) -> dict:
    """
    یک بار git را چک می‌کند؛ اگر commitِ جدیدی آمده (یا فایل‌های unstagedِ واجد باشند)،
    self_code.auto_propose_once را trigger می‌کند.

    Args:
        force: اگر True، cooldown را نادیده می‌گیرد (برای test/manual).
        state: وضعیتِ قبلی (اگر None، از disk می‌خواند).

    Returns:
        dict با کلیدهای: head, changed_files, targets, proposals, cooldown, new_state
    """
    if state is None:
        state = _load_state()

    result = {
        "head": None,
        "changed_files": [],
        "targets": [],
        "proposals": {"proposed": [], "skipped": [], "errors": []},
        "cooldown": False,
        "new_state": state,
    }

    if not _GW_ENABLED:
        result["status"] = "disabled"
        return result

    # بررسیِ وجودِ git repo
    head = _current_head()
    if head is None:
        logger.warning("git_watcher: not a git repo or git not available")
        result["status"] = "no_git"
        return result

    result["head"] = head
    last_head = state.get("last_head")

    # اگر HEAD تغییر نکرده، فقط unstaged / working tree را چک کن (soft trigger)
    changed: list[str] = []
    if last_head and head != last_head:
        changed = _changed_files_since(last_head)
        if changed:
            logger.info("git_watcher: new commit %s → %s files changed", head[:8], len(changed))
    else:
        # soft trigger: working tree changes (uncommitted)
        changed = _uncommitted_changes()
        if changed:
            logger.debug("git_watcher: %d uncommitted changes", len(changed))

    # همیشه HEAD را ذخیره کن (حتی اگر تغییری نبود)
    state["last_head"] = head
    state["last_check_at"] = datetime.now().isoformat(timespec="seconds")
    state["check_count"] = state.get("check_count", 0) + 1

    if not changed:
        result["status"] = "no_change"
        _save_state(state)
        return result

    result["changed_files"] = changed
    targets = _pick_targets(changed)
    result["targets"] = targets

    if not targets:
        result["status"] = "no_eligible_targets"
        logger.info("git_watcher: %d changes but no eligible .py target", len(changed))
        _save_state(state)
        return result

    # cooldown check
    if not force and not _cooldown_ok(state):
        result["cooldown"] = True
        result["status"] = "cooldown"
        logger.info("git_watcher: %d targets found but cooldown active", len(targets))
        _save_state(state)
        return result

    # trigger proposals
    props = _trigger_proposals(targets, state)
    result["proposals"] = props
    result["status"] = "triggered" if props["proposed"] else "skipped"

    state["last_trigger_at"] = datetime.now().isoformat(timespec="seconds")
    state["proposals_total"] = state.get("proposals_total", 0) + len(props["proposed"])
    _save_state(state)

    if props["proposed"]:
        events.emit(
            "task.completed",
            f"git_watcher triggered {len(props['proposed'])} proposal(s)",
            status="ok",
            agent_id="git_watcher",
            next_action="owner approval queue",
        )
    return result


# ════════════════════════════════════════════════════════════════════════
#  حلقه‌ی پس‌زمینه (برای ادغام با daemon.py)
# ════════════════════════════════════════════════════════════════════════

def run_loop(
    *,
    stop_event: Optional[Event] = None,
    poll_seconds: Optional[float] = None,
    max_checks: Optional[int] = None,
) -> dict:
    """
    حلقه‌ی دائمیِ polling (برای تردِ پس‌زمینه در daemon یا standalone).

    Args:
        stop_event: threading.Event برای توقفِ نرم.
        poll_seconds: فاصله‌ی polling (default از env).
        max_checks: محدودیت برای test (None = نامحدود).

    Returns:
        خلاصه‌ی اجرا (total_checks, proposals, errors).
    """
    poll = poll_seconds or _GW_POLL_SECONDS
    ev = stop_event or Event()

    summary = {"total_checks": 0, "proposals": 0, "errors": 0, "started_at": datetime.now().isoformat(timespec="seconds")}
    logger.info("git_watcher loop start · poll=%.0fs · enabled=%s", poll, _GW_ENABLED)

    events.emit(
        "system.heartbeat",
        "git_watcher loop started",
        status="info",
        agent_id="git_watcher",
    )

    while not ev.is_set():
        if max_checks is not None and summary["total_checks"] >= max_checks:
            break
        summary["total_checks"] += 1
        try:
            res = check_and_trigger()
            summary["proposals"] += len(res.get("proposals", {}).get("proposed", []))
            summary["errors"] += len(res.get("proposals", {}).get("errors", []))
        except Exception as e:
            logger.error("git_watcher loop error: %s", e)
            summary["errors"] += 1

        # sleep با stop_event (قابلِقطع)
        ev.wait(timeout=poll)

    summary["stopped_at"] = datetime.now().isoformat(timespec="seconds")
    logger.info("git_watcher loop stop · checks=%d · proposals=%d · errors=%d",
                summary["total_checks"], summary["proposals"], summary["errors"])
    return summary


def run_once() -> dict:
    """یک بار چک و trigger (برای cron / manual / test)."""
    return check_and_trigger()


# ════════════════════════════════════════════════════════════════════════
#  hook helper — ساختنِ post-commit hook (برای Linux/macOS)
# ════════════════════════════════════════════════════════════════════════

def install_post_commit_hook() -> dict:
    """
    یک post-commit hook نمونه در .git/hooks می‌سازد که فایلِ سیگنال می‌نویسد.
    daemon یا run_loop می‌تواند این سیگنال را بخواند و فوراً react کند
    (polling سریع‌تر بدون نیاز به hook execution مستقیم روی Windows).
    """
    toplevel = _repo_toplevel()
    if not toplevel:
        return {"ok": False, "reason": "not a git repo"}
    hook = toplevel / ".git" / "hooks" / "post-commit"
    signal_file = _signal_path()

    script = (
        "#!/bin/sh\n"
        f'# OCTOPUS git_watcher signal — written by install_post_commit_hook()\n'
        f'echo "$(git rev-parse HEAD) $(date -Iseconds)" > "{signal_file}"\n'
    )
    if sys.platform == "win32":
        # روی Windows فایلِ hook به‌صورتِ .sample استفاده نمی‌شود؛
        # به‌جای آن از polling استفاده می‌کنیم ولی فایل را به‌عنوانِ doc می‌سازیم.
        doc = hook.with_suffix(".post-commit.octopus")
        doc.write_text(script, encoding="utf-8")
        return {"ok": True, "reason": "Windows: hook doc written (polling still used)", "path": str(doc)}
    else:
        hook.write_text(script, encoding="utf-8")
        hook.chmod(0o755)
        return {"ok": True, "reason": "post-commit hook installed", "path": str(hook)}


# ════════════════════════════════════════════════════════════════════════
#  CLI / test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("""Usage: python -m brain.git_watcher [command]

Commands:
  (none)      — run one check and print result
  loop        — run polling loop (Ctrl+C to stop)
  install     — install post-commit hook (Linux/macOS)
  status      — print current state
""")
        sys.exit(0)

    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "status":
        state = _load_state()
        print("git_watcher state:")
        print(json.dumps(state, ensure_ascii=False, indent=2))
    elif cmd == "install":
        r = install_post_commit_hook()
        print("install:", r)
    elif cmd == "loop":
        print("git_watcher loop — Ctrl+C to stop")
        try:
            run_loop()
        except KeyboardInterrupt:
            print("\nstopped.")
    else:
        print("enabled:", _GW_ENABLED)
        print("last head:", _load_state().get("last_head", "—"))
        res = run_once()
        print("result:")
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
