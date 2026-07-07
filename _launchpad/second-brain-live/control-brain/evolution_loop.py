# -*- coding: utf-8 -*-
"""حلقهٔ مغز تکاملی — هفته‌ای یک Proposal (پیش‌فرض یکشنبه، EVO_DAY/EVO_HOUR).

propose-only: فقط در core.db می‌نویسد؛ کارتش را Notifier برای ادمین می‌فرستد.
سطح ۱ kill: فایل STOP-EVO کنار همین فایل → pause تمیز.
TTL: اول هر دور، پیشنهادهای بی‌verdict >۳۰ روز expired می‌شوند (fail-closed).

حالت‌ها:
  python evolution_loop.py --selftest    → آفلاین با gateway فیک
  python evolution_loop.py --once        → یک پیشنهاد واقعی الان
  python evolution_loop.py               → حلقهٔ هفتگی
"""
from __future__ import annotations

import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.gateway import Gateway, GatewayError, BudgetExceeded   # noqa: E402
from core.memory import Memory                                    # noqa: E402
from evolution.brain import EvolutionBrain                        # noqa: E402

STOP = ROOT / "STOP-EVO"


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def run_once() -> str:
    memory = Memory(ROOT / "core.db")
    expired = memory.expire_proposals(30)
    if expired:
        print(f"⏳ {expired} پیشنهاد کهنه expired شد (TTL)")
    brain = EvolutionBrain(memory, Gateway(memory))
    # اگر بودجه Fugu جا دارد escalate، وگرنه cheap — هر دو حالت valid
    tier = "escalate" if os.environ.get("EVO_USE_FUGU", "0") == "1" else "cheap"
    try:
        pid = brain.propose(tier=tier)
        return f"✅ Proposal #{pid} ساخته شد (کارت تأیید به تلگرامت می‌آید)"
    except (BudgetExceeded, GatewayError) as e:
        return f"⚠️ این دور بدون پیشنهاد: {e}"


def selftest() -> int:
    import tempfile

    class FakeGW:
        def llm(self, prompt, system="", tier="cheap", business="",
                max_tokens=900, use_cache=True):
            return ("عنوان: کش نتایج جستجو طولانی‌تر شود\nمشکل: تحقیق‌ها تکراری‌اند\n"
                    "راه‌حل: TTL کش از ۲۴ به ۴۸ ساعت\nریسک: کهنگی داده\n"
                    "اثر: ~۳۰٪ کاهش هزینه\nبرگشت: برگرداندن مقدار قبلی")

    memory = Memory(Path(tempfile.mkdtemp()) / "core.db")
    brain = EvolutionBrain(memory, FakeGW())
    pid = brain.propose()
    assert memory.pending_proposals(), "پیشنهاد ذخیره نشد"
    msg = brain.resolve(pid, "approved")
    assert "CHANGELOG" in msg and memory.get_proposal(pid)[7] == "approved"
    # پیشنهاد دوم → رد
    pid2 = brain.propose()
    brain.resolve(pid2, "rejected")
    assert memory.get_proposal(pid2)[7] == "rejected"
    print("selftest ok — propose/approve(CHANGELOG)/reject همه سالم")
    return 0


def loop() -> None:
    day = int(os.environ.get("EVO_DAY", "6"))    # 0=دوشنبه … 6=یکشنبه
    hour = int(os.environ.get("EVO_HOUR", "20"))
    print(f"مغز تکاملی روشن — هفتگی روز {day} ساعت {hour}:00 (STOP-EVO=pause)")
    last = ""
    while not STOP.exists():
        now = datetime.now()
        stamp = f"{date.today().isocalendar()[1]}"   # شمارهٔ هفته
        if now.weekday() == day and now.hour >= hour and last != stamp:
            last = stamp
            print(f"— دور هفتهٔ {stamp} —")
            try:
                print(run_once())
            except Exception as e:  # noqa: BLE001
                print(f"خطای دور: {e}")
        time.sleep(120)
    print("STOP-EVO — pause تمیز.")


if __name__ == "__main__":
    _load_env()
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--once" in sys.argv:
        print(run_once())
    else:
        loop()
