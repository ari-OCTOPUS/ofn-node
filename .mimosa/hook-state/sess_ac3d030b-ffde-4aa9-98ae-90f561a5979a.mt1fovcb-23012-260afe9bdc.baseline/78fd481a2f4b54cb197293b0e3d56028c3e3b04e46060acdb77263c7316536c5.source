#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cockpit_brain_tick.py — یک بیداریِ مغز، با سیم‌های واقعی وصل.

    `cockpit_brain.py` عمداً هیچ سیمِ بیرونی ندارد (تا تست‌پذیر بماند و
    هرگز تصادفی پیام ندهد). این فایل نازک است و فقط دو چیز را وصل می‌کند:
      · `think_fn` → مدل (ردهٔ GLM، رأیِ مالک)
      · `speak_fn` → کارتِ زندهٔ تلگرام (یک کارت، جای خودش به‌روز می‌شود)

    ⚠️ کارتِ زنده نه پیامِ نو: مالک یک بار ۱۰۴ ارسالِ یکسان گرفت و بعد از
    آن هیچ کارتی را جدی نمی‌گرفت. یک کارت که جای خودش عوض شود، تنها شکلی
    است که سکوت را هم معنادار می‌کند.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex"),
           str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cockpit_brain as brain  # noqa: E402

CARD_NAME = "cockpit-brain"


def _speak(text: str) -> None:
    """یک کارتِ زنده به مالک. شکست **صدادار** است، نه بلعیده‌شده.

    ⚠️ اولین نسخه `tg_client_min.Client` را صدا می‌زد — ماژولی که **وجود
    ندارد**. حدس زدم به‌جای اینکه بخوانم، و نتیجه `ModuleNotFoundError` شد:
    مغز فکر کرد، تماسِ پولی زد، در حافظه ثبت کرد، و **حرف نزد**.
    کلاسِ واقعی `tg_api.TgClient` است و خودش توکن را از env می‌خواند
    (`TG_CENTER_BOT_TOKEN` با fallback به باتِ اصلی)، پس توکن دستی پاس
    داده نمی‌شود.
    """
    import os
    import env_loader
    env_loader.load_env()
    import living_card
    import tg_api

    chat = int(os.environ["TELEGRAM_OWNER_CHAT_ID"])
    living_card.put(tg_api.TgClient(), name=CARD_NAME, text=text, chat_id=chat)


def main() -> int:
    if not brain.enabled():
        print(json.dumps({"skipped": "flag off"}, ensure_ascii=False))
        return 0
    # ⚠️ `speak_fn` تنبل تزریق می‌شود: اگر ساختنِ کلاینت بترکد، مغز باز هم
    # فکر می‌کند و در حافظه ثبت می‌شود — فقط حرف نمی‌زند، و همان شکست در
    # گزارش می‌آید. قابلیتی که با شکستِ یک لایه کاملاً بمیرد، شکننده است.
    rep = brain.tick(think_fn=brain.think, speak_fn=_speak)
    # خروجیِ فشرده برای لاگِ رانر — هرگز متنِ پرامپت یا کلید.
    print(json.dumps({
        "changes": [c["key"] for c in rep.get("changes", [])],
        "spoke": rep.get("spoke"), "paid": rep.get("paid"),
        "quota": rep.get("quota"), "reason": rep.get("reason"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[attr-defined]
    sys.exit(main())
