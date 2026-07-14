"""
brain/daemon.py — اجراکننده‌ی بی‌مراقبِ ماهانه (headless، مستقل از مرورگر).

تصمیمِ مالک: «یک ماه زنده بشه، نتایجو بسنجیم». لوپِ داشبورد داخلِ تبِ مرورگر
(`@st.fragment`) می‌چرخد و با بستنِ تب می‌ایستد؛ این daemon همان AutomationController
را بی‌وقفه و بدونِ مرورگر می‌چرخاند:

  • هر tick: یک گامِ خودمختار (explore/real/introspect/create/mutate/evolve/…).
  • دوره‌ی: پیشنهادِ خودکارِ بهبودِ کد (auto_propose_once) — فقط پیشنهاد+آزمون+صف،
    هرگز اعمال؛ اعمال نیازِ approveِ صریحِ مالک است.
  • دوره‌ی: git_watcher (CH-10) — پایشِ تغییراتِ git → triggerِ self-evolution.
  • دوره‌ی: flush_digest (≤ NOTIFY_MAX_PER_DAY بار در روز) + housekeeping.
  • بودجه‌ی ابری خودکار مهار می‌شود (brain/budget → router/clients).

توقفِ تمیز: فایلِ outputs/daemon.stop یا Ctrl+C (SIGINT/SIGTERM).
اجرا:  python -m brain.daemon
"""
from __future__ import annotations

import os
import time
import signal
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

_STOP = {"flag": False}


def _tick_seconds() -> float:
    try:
        return max(1.0, float(os.getenv("DAEMON_TICK_SECONDS", "30")))
    except ValueError:
        return 30.0


def _state_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "daemon_state.json"


def _stop_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "daemon.stop"


def _pause_path() -> Path:
    """وجودِ این فایل = مکثِ نرم (فرایند زنده می‌ماند، گامِ خودمختار اجرا نمی‌شود).
    تلگرام‌بات با ساخت/حذفِ آن، بدونِ کشتنِ daemon، مکث/ادامه می‌دهد."""
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "daemon.pause"


def _load_state() -> dict:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    p = _state_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except Exception as e:
        logger.warning("daemon state save failed: %s", e)


def _install_signals() -> None:
    def _handler(signum, _frame):
        logger.info("daemon: signal %s → graceful stop", signum)
        _STOP["flag"] = True
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass


def run_forever(max_ticks: int | None = None) -> dict:
    """حلقه‌ی اصلیِ daemon. برای تست max_ticks و DAEMON_TICK_SECONDS=0.x بده."""
    _install_signals()
    from brain.automation import AutomationController
    from brain import budget, notify

    propose_every = int(os.getenv("DAEMON_PROPOSE_EVERY", "20"))
    gw_every = int(os.getenv("DAEMON_GIT_WATCHER_EVERY", "10"))
    digest_every = int(os.getenv("DAEMON_DIGEST_EVERY", "20"))
    hk_every = int(os.getenv("DAEMON_HK_EVERY", "120"))
    self_code_on = os.getenv("SELF_CODE_ENABLED", "0").lower() in ("1", "true", "yes")

    # مالکِ اجرای ماهانه: use_llm=True (اجرای واقعیِ «جسور»؛ بودجه مهارش می‌کند)
    ctrl = AutomationController(use_llm=True)

    state = _load_state()
    state.setdefault("started_at", datetime.now().isoformat(timespec="seconds"))
    state.setdefault("total_ticks", 0)
    state["resumed_at"] = datetime.now().isoformat(timespec="seconds")
    state["pid"] = os.getpid()
    _save_state(state)

    tick = 0
    props_made = 0
    errors = 0
    logger.info("daemon start · tick=%.0fs · propose_every=%d · gw_every=%d · self_code=%s",
                _tick_seconds(), propose_every, gw_every, self_code_on)

    try:
        while not _STOP["flag"]:
            if max_ticks is not None and tick >= max_ticks:
                break
            if _stop_path().exists():
                logger.info("daemon: stop file present → graceful stop")
                try:
                    _stop_path().unlink()
                except Exception:
                    pass
                break

            # مکثِ نرم (از تلگرام): فرایند زنده، ولی گامِ خودمختار اجرا نمی‌شود
            if _pause_path().exists():
                state["paused"] = True
                state["last_tick_at"] = datetime.now().isoformat(timespec="seconds")
                _save_state(state)
                time.sleep(_tick_seconds())
                continue
            state["paused"] = False

            tick += 1
            state["total_ticks"] += 1

            # ۱) یک گامِ خودمختار
            try:
                res = ctrl.run_one()
                # توقفِ حفاظتی: نقضِ ثابتِ ریاضی → daemon همان‌جا می‌ایستد (بی‌مراقب
                # نباید ادامه دهد). یک پیامِ بحرانی force-flush می‌شود.
                if isinstance(res, dict) and res.get("halt"):
                    logger.error("daemon: protective HALT (invariant violation) → stopping")
                    state["halted_at"] = datetime.now().isoformat(timespec="seconds")
                    try:
                        notify.queue_for_digest(
                            "blocked", "توقفِ حفاظتی: نقضِ لنگرِ ریاضی",
                            "daemon بی‌مراقب متوقف شد", "بررسیِ دستی لازم است",
                            "سیستم در حالتِ امن ایستاد")
                        notify.flush_digest(force=True)
                    except Exception:
                        pass
                    break
            except Exception as e:
                errors += 1
                logger.error("daemon run_one error: %s: %s", type(e).__name__, e)

            # ۲) پیشنهادِ خودکارِ بهبودِ کد — هدف‌محور (خودمدل + اهداف)؛ فقط ایستا
            if self_code_on and tick % max(1, propose_every) == 0:
                try:
                    from brain import self_code, self_growth
                    focus = self_growth.current_focus(tick)
                    res = self_code.auto_propose_once(
                        target_rel=focus.get("target"), seed=tick,
                        goal=focus.get("motivation", ""))
                    if res.get("ok"):
                        props_made += 1
                        notify.queue_for_digest(
                            "approve", f"پیشنهادِ کد آماده‌ی تأیید (pid {res.get('pid','?')})",
                            "گیتِ تست سبز شد", "در داشبورد بازبینی و approve/reject کن",
                            "تا تأیید نکنی، کدِ زنده عوض نمی‌شود")
                except Exception as e:
                    logger.error("auto_propose error: %s", e)

            # ۲b) git_watcher — triggerِ خودارتقایی از روی تغییراتِ git (event-driven)
            if self_code_on and tick % max(1, gw_every) == 0:
                try:
                    from brain import git_watcher
                    gw_res = git_watcher.check_and_trigger()
                    gw_proposed = gw_res.get("proposals", {}).get("proposed", [])
                    if gw_proposed:
                        props_made += len(gw_proposed)
                        for p in gw_proposed:
                            notify.queue_for_digest(
                                "approve",
                                f"git-trigger proposal {p.get('pid','?')} for {p.get('target','?')}",
                                "فایلِ تغییریافته در گیت شناسایی شد",
                                "در داشبورد بازبینی و approve/reject کن",
                                "تا تأیید نکنی، کدِ زنده عوض نمی‌شود",
                            )
                except Exception as e:
                    logger.error("git_watcher error: %s", e)

            # ۳) flush digest (خودش ≤ سقفِ روزانه را رعایت می‌کند)
            if tick % max(1, digest_every) == 0:
                try:
                    notify.flush_digest(force=False)
                except Exception as e:
                    logger.warning("digest flush error: %s", e)

            # ۴) housekeeping + به‌روزرسانیِ خودنگاره (خودشناسی)
            if tick % max(1, hk_every) == 0:
                try:
                    from brain.housekeeping import run_housekeeping
                    run_housekeeping()
                except Exception as e:
                    logger.warning("housekeeping error: %s", e)
                try:
                    from brain import self_growth
                    self_growth.save_self_portrait()
                except Exception as e:
                    logger.debug("self_portrait error: %s", e)

            # ۵) heartbeat + وضعیتِ git_watcher
            state.update({
                "last_tick_at": datetime.now().isoformat(timespec="seconds"),
                "tick_this_run": tick,
                "proposals_this_run": props_made,
                "errors_this_run": errors,
                "budget": budget.status(),
                "digest": notify.digest_status(),
                "generation": int(ctrl.evolved.get("_generation", 0)) if hasattr(ctrl, "evolved") else 0,
            })
            # git_watcher status (lightweight read-only)
            try:
                from brain import git_watcher
                gw_state = git_watcher._load_state()
                state["git_watcher"] = {
                    "enabled": git_watcher._GW_ENABLED,
                    "last_head": gw_state.get("last_head", "")[:8],
                    "check_count": gw_state.get("check_count", 0),
                    "proposals_total": gw_state.get("proposals_total", 0),
                }
            except Exception:
                pass
            _save_state(state)

            if max_ticks is None or tick < max_ticks:
                time.sleep(_tick_seconds())
    finally:
        state["stopped_at"] = datetime.now().isoformat(timespec="seconds")
        _save_state(state)
        logger.info("daemon stop · ticks=%d · proposals=%d · errors=%d · git_watcher=%s",
                    tick, props_made, errors,
                    state.get("git_watcher", {}).get("proposals_total", 0))

    return {"ticks": tick, "proposals": props_made, "errors": errors}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    print("4d_system daemon — Ctrl+C یا `touch outputs/daemon.stop` برای توقف")
    run_forever()
