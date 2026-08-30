#!/usr/bin/env python3
"""run_saba.py — runner که SabaStudio را با مغزِ pf_os تزریق می‌کند و راه می‌اندازد.

این «راه‌اندازیِ واقعیِ پلِ من↔صبا» است. دو حالت:

  1. SHADOW (پیش‌فرض، $0): هیچ token لازم نیست. SabaStudio روی stdin/stdout
     اجرا می‌شود با chat_id=0. مغزِ pf_os وصل است، یعنی می‌توانی نوع‌پیام بفرستی
     و ببینی چطور مغز پاسخ می‌دهد. برای تست/دیباگ.

  2. LIVE (وقتی token set شد): env TELEGRAM_SABA_BOT_TOKEN + TELEGRAM_SABA_CHAT_ID
     set شوند → SabaStudio واقعاً به تلگرام long-poll می‌زند و با صبا حرف می‌زند.

قرارداد (طبقِ saba_studio:380):
  saba_studio از self.brain.respond_to_saba(text) استفاده می‌کند.
  pf_os.BrainCore دقیقاً همین متد را دارد.

اجرا:
  SHADOW: python -m pf_os.run_saba
  LIVE:   set TELEGRAM_SABA_BOT_TOKEN=... & set TELEGRAM_SABA_CHAT_ID=... & python -m pf_os.run_saba

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Project-F root روی sys.path
_HERE = Path(__file__).resolve().parent           # .../pf_os
_PROJ = _HERE.parent                               # .../اونلی فنز
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))
_STUDIO = _PROJ / "studio"
if str(_STUDIO) not in sys.path:
    sys.path.insert(0, str(_STUDIO))

from pf_os import brain as B  # noqa: E402
from pf_os import saba_link as SL  # noqa: E402
from pf_os import config  # noqa: E402
from pf_os import singleton as _sgl  # noqa: E402 — قفلِ تک‌نمونه (توصیه‌ی architect-agent)


def build_brain() -> B.BrainCore:
    """ساختِ BrainCore با heuristic (dual_brain_v3 اگر موجود)."""
    try:
        from dual_brain_v3 import DualBrainV3  # type: ignore
        return B.BrainCore(heuristic=DualBrainV3())
    except Exception:  # noqa: BLE001
        return B.BrainCore()


def shadow_demo() -> int:
    """حالتِ shadow: stdin/stdout، برای تست. $0."""
    # قفلِ تک‌نمونه — دو تا shadow نباید هم‌زمان اجرا شوند (توصیه‌ی architect §3)
    lock = _sgl.acquire_pid_lock("pf_os_shadow")
    if lock is None:
        print("🔴 یک pf_os shadow قبلاً در حالِ اجراست. خروج. (lock file در pf_os_state/)")
        return 1
    try:
        return _shadow_demo_body()
    finally:
        _sgl.release_pid_lock(lock)


def _shadow_demo_body() -> int:
    bot_brain = build_brain()
    print("=" * 60)
    print("🎭 pf_os↔Saba SHADOW MODE — برای تست/دیباگ")
    print("=" * 60)
    print(f"  brain heuristic_loaded: {bot_brain.status()['heuristic_loaded']}")
    print(f"  cortex wired: {bot_brain.status()['cortex']['wired']}")
    print(f"  studio dir: {SL._studio_dir()}")
    print()
    print("نمونه: متن بده (مثلاً «قیمت؟»، «کی پست کنم؟»، «خسته شدم»).")
    print("برای خروج: Ctrl+C یا 'quit'.")
    print("-" * 60)
    while True:
        try:
            text = input("صبا> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nخروج.")
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue
        r = bot_brain.respond_to_saba(text)
        if r is None:
            print("  [pf_os: scrub-reject — fallback به منوی saba_studio]")
        else:
            print(f"  ← {r}")
        last = bot_brain._last_saba_response
        print(f"  [intent={last.get('intent')} source={last.get('source')} "
              f"tier={last.get('tier','?')} ms={last.get('ms',0)}]")
    # نمایشِ snapshot نهایی
    print()
    print("─" * 60)
    print("Snapshot:")
    for k, v in SL.snapshot().items():
        print(f"  {k}: {v}")
    return 0


def live() -> int:
    """حالتِ live: SabaStudio واقعی به تلگرام وصل. نیاز به token دارد."""
    # قفلِ تک‌نمونه — جلویِ double-run که باعث 409 تلگرام می‌شود (توصیه‌ی architect §3)
    lock = _sgl.acquire_pid_lock("pf_os_saba_live")
    if lock is None:
        print("🔴 pf_os Saba bot قبلاً در حالِ اجراست. دو instance = 409 تلگرام. خروج.")
        return 1
    try:
        return _live_body()
    finally:
        _sgl.release_pid_lock(lock)


def _live_body() -> int:
    token = os.environ.get("TELEGRAM_SABA_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_SABA_CHAT_ID", "0").strip()
    if not token or chat_id == "0":
        print("🔴 LIVE mode نیاز دارد: TELEGRAM_SABA_BOT_TOKEN + TELEGRAM_SABA_CHAT_ID")
        print("   token از @BotFather، chat_id از @userinfobot.")
        print("   اگر token نداری، حالتِ shadow را اجرا کن: python -m pf_os.run_saba")
        return 1
    bot_brain = build_brain()
    print(f"🟢 LIVE: SabaStudio با مغزِ pf_os (chat_id={chat_id})")
    # تزریقِ مغز به SabaStudio و راه‌اندازیِ loop
    import saba_studio as S  # noqa: E402
    bot = S.SabaStudio(brain=bot_brain, token=token, saba_chat_id=int(chat_id))
    print(f"  {bot!r}")
    SL.send_notify("🟢 pf_os وصل شد — مغزِ زنده آماده‌ست.", "سؤالی داری بپرس.")
    try:
        bot.run()  # long-poll loop
    except KeyboardInterrupt:
        print("\nخروج.")
    return 0


def main() -> int:
    # اگر token هست → live؛ وگرنه shadow
    token = os.environ.get("TELEGRAM_SABA_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_SABA_CHAT_ID", "0").strip()
    if token and chat_id != "0":
        return live()
    return shadow_demo()


if __name__ == "__main__":
    raise SystemExit(main())
