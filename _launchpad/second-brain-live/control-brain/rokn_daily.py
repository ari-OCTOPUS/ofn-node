# -*- coding: utf-8 -*-
"""حلقهٔ روزانهٔ دو رکن — برای هر بیزنس: تحقیق (رکن A) → بریف → پیام پیشنهادی (رکن B) → صف تأیید.

هیچ ارسال مستقیمی به هیچ‌کس ندارد؛ فقط در core.db می‌نویسد (بریف + outbox pending).
کارت‌ها را Notifier ی پروسهٔ اصلی (app.py) برای ادمین می‌فرستد — جداسازی تمیز.

حالت‌ها:
  python rokn_daily.py --selftest      → سیم‌کشی آفلاین با gateway فیک (بدون شبکه)
  python rokn_daily.py --once [biz]    → یک دور واقعی (همهٔ بیزنس‌ها یا یکی)
  python rokn_daily.py                 → حلقهٔ روزانه: هر روز ساعت RESEARCH_HOUR (پیش‌فرض ۸)
kill: فایل STOP کنار همین فایل.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from adapters.business import ALL, engines_for          # noqa: E402
from core.gateway import BudgetExceeded, Gateway, GatewayError  # noqa: E402
from core.memory import Memory                           # noqa: E402

STOP = ROOT / "STOP-ROKN"


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def run_business(biz: str, gateway, memory, force: bool = False) -> str:
    """یک دور کامل دو رکن برای یک بیزنس. خروجی: خلاصهٔ یک‌خطی برای لاگ.

    گارد idempotent (یافتهٔ code-review): اگر امروز بریف این بیزنس ساخته شده،
    دور تکرار نمی‌شود — restart وسط روز = بدون duplicate."""
    if not force:
        recent = memory.recent_briefs(1, business=biz)
        if recent and recent[0].created[:10] == date.today().isoformat():
            return f"⏭ {biz}: امروز قبلاً اجرا شده (بریف #{recent[0].id})"
    research, owner = engines_for(biz, gateway, memory)
    try:
        # رکن A: یادگیری از بازخوردهای قبلی → تحقیق → بریف
        research.learn(memory.feedback_for(biz, n=10))
        brief = research.run(research.gather_context())
        # رکن B: بریف → پیام پیشنهادی → صف تأیید (status=pending؛ Notifier کارت می‌فرستد)
        memory.add_outbox(owner.compose(brief))
        # کشف‌های مستقل رکن B (مثل مناسبت‌های زیمان)
        for msg in owner.discover():
            memory.add_outbox(msg)
        return f"✅ {biz}: بریف #{brief.id} + پیام در صف"
    except BudgetExceeded as e:
        memory.knowledge_add(f"BUDGET-STOP {biz}: {e}", tag="alert", business=biz)
        return f"⛔ {biz}: بودجه — {e}"
    except GatewayError as e:
        return f"⚠️ {biz}: آفلاین/خطا — {e}"


def run_all(only: str = "") -> None:
    memory = Memory(ROOT / "core.db")
    gateway = Gateway(memory)
    targets = [only] if only else list(ALL.keys())
    for biz in targets:
        print(run_business(biz, gateway, memory))


def selftest() -> int:
    """سیم‌کشی کامل بدون شبکه — gateway فیک."""
    import tempfile

    class FakeGW:
        def search(self, q, business="", n=5):
            return [{"title": "t", "url": "u", "content": "c"}]

        def llm(self, prompt, system="", tier="cheap", business="",
                max_tokens=900, use_cache=True):
            return "عنوان: تست\nفرصت: فرصت تستی\nچرا: چون تست است\nاقدام: اقدام تستی\nمنبع: تحلیل داخلی"

    memory = Memory(Path(tempfile.mkdtemp()) / "core.db")
    gw = FakeGW()
    for biz in ALL:
        out = run_business(biz, gw, memory)
        assert out.startswith("✅"), out
    st = memory.stats()
    assert st["briefs"] == len(ALL) and st["pending"] >= len(ALL)
    print(f"selftest ok — {st['briefs']} بریف و {st['pending']} پیام pending برای {len(ALL)} بیزنس")
    return 0


def loop() -> None:
    hour = int(os.environ.get("RESEARCH_HOUR", "8"))
    print(f"حلقهٔ رکن‌ها روشن — هر روز ساعت {hour}:00 (STOP-ROKN برای خاموشی)")
    last_day = ""
    while not STOP.exists():
        now = datetime.now()
        if now.hour >= hour and last_day != date.today().isoformat():
            last_day = date.today().isoformat()
            print(f"— دور روزانهٔ {last_day} —")
            try:
                run_all()
            except Exception as e:  # noqa: BLE001
                print(f"خطای دور: {e}")
        time.sleep(60)
    print("STOP-ROKN دیده شد — خروج تمیز.")


if __name__ == "__main__":
    _load_env()
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--once" in sys.argv:
        i = sys.argv.index("--once")
        only = sys.argv[i + 1] if len(sys.argv) > i + 1 else ""
        run_all(only)
    else:
        loop()
