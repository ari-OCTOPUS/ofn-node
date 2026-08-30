"""
world_model.py — چشمِ ایجنت در دنیای واقعی.

World State امروز را از منابعِ مختلف جمع می‌کند:
  • داخلی (همیشه): آخرین log، daily_state، streak  ← از db
  • محلی (اختیاری): commitهای امروزِ یک repo (از LANGAR_GIT_REPO، بدونِ احراز هویت)
  • فایل (اختیاری): اکسپورتِ Apple Health (مسیر از LANGAR_HEALTH_FILE)
  • API (اختیاری): آب‌وهوا — فقط اگر کلید تنظیم شده باشد (به‌صورتِ hook، شبکه را اجباری نمی‌کند)

همه‌ی منابعِ بیرونی graceful‌اند: اگر تنظیم/در‌دسترس نباشند، None می‌دهند و چیزی نمی‌شکند.
db تزریق می‌شود تا تست‌پذیر بماند.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess


class WorldModel:
    def __init__(self, db, config=None):
        self.db = db
        self.config = config

    def get_current_state(self) -> dict:
        today = _dt.date.today().isoformat()
        state = {"date": today}
        # --- داخلی ---
        try:
            row = self.db.last_log()
            if row:
                state["rmssd"] = row["rmssd"]
                state["sleep"] = row["sleep"]
                state["used"] = row["used"]
                state["location"] = row["loc"]
        except Exception:
            pass
        try:
            ds = self.db.get_daily_state(today)
            if ds:
                for k in ("mood", "energy", "stress"):
                    state[k] = ds[k]
        except Exception:
            pass
        try:
            state["log_streak"] = self.db.log_streak()
        except Exception:
            pass
        # --- اختیاری ---
        gc = self._git_commits_today()
        if gc is not None:
            state["git_commits_today"] = gc
        w = self._weather()
        if w is not None:
            state["weather"] = w
        return state

    def _git_commits_today(self):
        repo = os.environ.get("LANGAR_GIT_REPO")
        if not repo:
            return None
        try:
            out = subprocess.run(
                ["git", "-C", repo, "log", "--since=midnight", "--oneline"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode != 0:
                return None
            return len([ln for ln in out.stdout.splitlines() if ln.strip()])
        except Exception:
            return None

    def _weather(self):
        # hook: فقط اگر کلید باشد. شبکه را اینجا اجباری نمی‌کنیم تا وابستگی/ریسک اضافه نشود.
        # برای فعال‌سازی، در گامِ بعد یک adapter با کلیدِ تو اضافه می‌شود.
        return None

    # --- ingest ---
    def ingest_manual(self, source: str, data: dict) -> None:
        try:
            from observability.event_log import log_event
            log_event(self.db, f"ingest_manual:{source}", data)
        except Exception:
            pass

    def ingest_csv(self, text: str) -> dict:
        """ورودِ نیمه‌اتوماتیک (مثلِ Muse). به ماژولِ muse واگذار می‌شود."""
        try:
            import muse
            return muse.compute_from_csv(text)
        except Exception as e:
            return {"ok": False, "reason": str(e)}
