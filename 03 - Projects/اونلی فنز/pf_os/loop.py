#!/usr/bin/env python3
"""loop.py — حلقه‌ی tick مستقلِ Project-F OS.

پشتِ flag OCTOPUS_WIRE_PROJECTF_LOOP. بدونِ flag = هیچ‌چیز اجرا نمی‌شود.

هر tick (دوره از PF_OS_TICK_SECONDS، پیش‌فرض ۳۰۰s = ۵ دقیقه):
  1. snapshot از saba-link (pending drafts, halt, capacity)
  2. اگر درفتِ جدید داریم → on_new_draft → notify به صبا
  3. brain.think یک دور (low-cost, heuristic fallback اگر cortex پایین)
  4. publish به bridge (brain_tick_done)
  5. اگر halt است → notify_periodic به صبا (آیا لازم است کاری کنه)
  6. fail-soft: یک stage خطا loop را نکُشد

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import os
import time
import threading
from pathlib import Path
from typing import Optional

from . import config, brain as _brain, saba_link as _sl, bridge as _br


class PFTickRunner:
    """حلقه‌ی tick مستقل. پشتِ flag."""

    def __init__(self, brain: Optional[_brain.BrainCore] = None,
                 tick_seconds: Optional[float] = None):
        self.brain = brain or _brain.BrainCore()
        self.tick_seconds = tick_seconds or config.TICK_SECONDS
        self._stop = False
        self._thread: Optional[threading.Thread] = None
        self._tick_n = 0
        self._last_pending_count = -1

    @property
    def tick_n(self) -> int:
        return self._tick_n

    def stop(self) -> None:
        self._stop = True

    def _stop_file(self) -> Path:
        return Path(config.PF_STATE) / "STOP-PFOS"

    def _should_stop(self) -> bool:
        return self._stop or self._stop_file().exists()

    # ── یک tick ──
    def tick_once(self) -> dict:
        """اجرای یک tick. fail-soft. برمی‌گرداند summary dict (content-free)."""
        self._tick_n += 1
        n = self._tick_n
        result: dict = {"tick": n, "ts": int(time.time()), "stages": []}
        # holderِ سبکِ بین-مرحله‌ای (content-free): سیگنالِ «درفتِ جدید» از stage 1 به
        # stage مسیریابی می‌رسد تا واقعاً به مغز route شود (نه اینکه new دور ریخته شود).
        detected: dict = {"new": False}

        def _stage(name: str, fn):
            try:
                out = fn()
                result["stages"].append({"name": name, "ok": True,
                                         "result": out if isinstance(out, (str, int, float, bool)) else "ok"})
            except Exception as e:  # noqa: BLE001
                result["stages"].append({"name": name, "ok": False,
                                         "error": f"{type(e).__name__}: {str(e)[:80]}"})

        # stage 1: snapshot saba
        def _s1():
            snap = _sl.snapshot()
            cur_pending = snap.get("pending_drafts", 0)
            new = cur_pending > self._last_pending_count if self._last_pending_count >= 0 else False
            self._last_pending_count = cur_pending
            result["pending_drafts"] = cur_pending
            result["saba_halted"] = snap.get("saba_halted", False)
            # سیگنالِ درفتِ جدید را نگه دار (قبلاً دور ریخته می‌شد) تا route شود.
            detected["new"] = new
            result["new_draft_detected"] = new
            return cur_pending
        _stage("snapshot_saba", _s1)

        # stage 2: درفتِ جدید → on_new_draft → مغز *واقعاً* صدا زده می‌شود (propose-only)
        # این همان وعده‌ی docstring است: «درفتِ جدید → on_new_draft → notify به صبا».
        def _s_route():
            if not detected.get("new"):
                return "no-new-draft"
            drafts = _sl.pending_drafts()
            if not drafts:
                return "no-pending"
            # جدیدترین درفتِ pending را به مغز مسیر بده. on_new_draft (fix #1) واقعاً
            # brain.respond_to_saba/_classify_saba_intent را روی محتوای درفت صدا می‌زند.
            sent = _sl.on_new_draft(drafts[-1], brain=self.brain)
            result["routed_new_draft"] = bool(sent)
            return "routed" if sent else "routed-empty"
        _stage("route_new_draft", _s_route)

        # stage 2: اگر halt است → notify_periodic
        def _s2():
            if result.get("saba_halted"):
                _sl.send_notify("tick: saba halted", "awaiting resume")
                return "notified-halt"
            return "no-halt"
        _stage("halt_check", _s2)

        # stage 3: brain یک دور کوتاه (heuristic یا cortex)
        def _s3():
            # یک سؤالِ سبکِ عملیاتی به مغز — برای warm-up/observation
            r = self.brain.think("tick", "pf_os tick: brief status check", max_tokens=60)
            result["last_brain_source"] = r.source
            return r.source
        _stage("brain_tick", _s3)

        # stage 4: publish to bridge (brain_tick_done)
        def _s4():
            ok = _br.notify_brain_tick(tick_n=n,
                                       source=result.get("last_brain_source", ""))
            return "published" if ok else "skipped"
        _stage("publish_bridge", _s4)

        # stage 5: eval→learn (پشتِ flag OCTOPUS_WIRE_PROJECTF_EVAL؛ shadow/propose-only)
        # حلقهٔ bandit + ضدگودهارت را در همان tick اجرا می‌کند. flag-off = هیچ‌کار.
        def _s5():
            if not config.flag(config.WIRE_EVAL):
                return "eval-off"
            loop = self._eval_loop()
            if loop is None:
                return "eval-unavailable"
            step = loop.step(n)
            result["eval_chosen"] = step.get("chosen")
            result["eval_alarms"] = len(step.get("alarms", []))
            return f"eval-day-{n}"
        _stage("eval_learn", _s5)

        return result

    def _eval_loop(self):
        """سازندهٔ lazy حلقهٔ eval→learn (cache می‌شود). fail-soft."""
        if getattr(self, "_eval", None) is not None:
            return self._eval
        try:
            from .eval_loop import EvalLearnLoop
            self._eval = EvalLearnLoop()
            return self._eval
        except Exception:  # noqa: BLE001
            self._eval = None
            return None

    # ── loop blocking ──
    def run_blocking(self) -> int:
        """اجرایِ حلقه تا STOP. blocks. Ctrl+C یا STOP-PFOS file برای توقف."""
        if not config.flag(config.WIRE_LOOP):
            return 0  # flag-off = silent no-op
        config.ensure_pf_state()
        print(f"🟢 pf_os tick loop (every {self.tick_seconds}s) — Ctrl+C or STOP-PFOS file to stop.")
        try:
            while not self._should_stop():
                try:
                    r = self.tick_once()
                    print(f"[tick {r['tick']}] "
                          f"pending={r.get('pending_drafts', 0)} "
                          f"halted={r.get('saba_halted', False)} "
                          f"brain={r.get('last_brain_source', '?')}")
                except Exception as e:  # noqa: BLE001 — یک tick خطا loop را نکُشد
                    print(f"[tick error] {type(e).__name__}: {e}")
                time.sleep(self.tick_seconds)
        except KeyboardInterrupt:
            print("\nخروج.")
        return 0

    # ── loop non-blocking (در thread جدا) ──
    def start_background(self) -> bool:
        """شروعِ loop در thread جدا. برای integration با api/سایر services."""
        if not config.flag(config.WIRE_LOOP):
            return False
        if self._thread is not None and self._thread.is_alive():
            return True
        self._stop = False
        self._thread = threading.Thread(target=self.run_blocking, daemon=True)
        self._thread.start()
        return True


def main() -> int:
    """اجرا از CLI: python -m pf_os.loop"""
    runner = PFTickRunner()
    if not config.flag(config.WIRE_LOOP):
        print(f"🔴 {config.WIRE_LOOP}=off.")
        print(f"   برای فعال‌سازی: set {config.WIRE_LOOP}=1 سپس python -m pf_os.loop")
        return 0
    return runner.run_blocking()


if __name__ == "__main__":
    raise SystemExit(main())
