#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""supervisor.py — پروسهٔ Control Plane. جمع می‌کند، می‌نویسد، تمام.

جایگاه (حکمِ معماریِ مالک ۲۰۲۶-۰۸-۰۳)
─────────────────────────────────────
    Octopus/MCP روی لپ‌تاپ
            │ stdio محلی
            ▼
    Control Plane (این فایل)      ← فاز ۱: فقط‌خواندنی
            ├──── Telegram Bot
            ├──── Telegram Mini App
            └──── Event/Notification Stream

قاعدهٔ مالکیتِ حالت — چرا این پروسهٔ دوم امن است
────────────────────────────────────────────────
در این ارگانیسم «دو نویسنده روی یک فایلِ حالت» دو بار باگ ساخته: نوسانِ
کارت‌های گروه (۰۷-۳۰) و دو مرکز روی یک توکن (۰۷-۲۹). مالک پروسهٔ مستقل را
انتخاب کرد، پس ریسک با **قاعده** بسته می‌شود نه با امید:

  · این پروسه **فقط** داخلِ `state/control_plane/` می‌نویسد.
  · هیچ فایلی که پروسهٔ دیگری مالکِ آن است لمس نمی‌شود — نه نبض، نه فلگ،
    نه صفِ تأیید، نه دفترها.
  · جمع‌آوری از `collector` می‌آید که خودش **صفر نوشتن** دارد.

هر تخطی از این قاعده باید تستِ `test_control_plane` را قرمز کند، نه اینکه در
مرورِ کد کشف شود.

مرزهای امنیتی (همه در فاز صفر رأی گرفتند)
─────────────────────────────────────────
· صفر پورتِ ورودی. سوکت فقط برای **قفلِ تک‌نمونگی** روی `127.0.0.1` است و
  هیچ‌وقت `accept` نمی‌کند. روی ویندوز `SO_EXCLUSIVEADDRUSE` — نه
  `SO_REUSEADDR`، که آن‌جا دقیقاً برعکس عمل می‌کند و دو نمونه را اجازه می‌دهد.
· صفر خروجی. این فاز چیزی به تلگرام نمی‌فرستد؛ فقط snapshot می‌نویسد.
· صفر secret. متن‌ها از `redact` ِ کاکپیت رد می‌شوند.
· fail-closed: خطا ⇒ توقفِ نوشتن، نه نوشتنِ عکسِ ناقص به‌عنوانِ سلامت.

فلگ
───
پیش‌فرض **خاموش**. با `OCTOPUS_WIRE_CONTROL_PLANE=1` روشن می‌شود.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from collector import snapshot  # noqa: E402

FLAG = "OCTOPUS_WIRE_CONTROL_PLANE"
SCHEMA = "control-plane.supervisor.v1"

# پورتِ قفل — فقط برای تک‌نمونگی. هرگز listen/accept نمی‌شود.
LOCK_PORT = int(os.environ.get("OCTOPUS_CONTROL_PLANE_LOCK_PORT", "8778"))
INTERVAL_S = max(5, int(os.environ.get("OCTOPUS_CONTROL_PLANE_INTERVAL", "30")))

# تنها مسیری که این پروسه اجازهٔ نوشتن دارد.
_OWNED_DIRNAME = "control_plane"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def owned_dir() -> "Path | None":
    """فضای‌نامِ انحصاریِ این پروسه. بیرونِ این، هیچ نوشتنی مجاز نیست."""
    try:
        import opslib  # noqa: WPS433
        return Path(opslib.STATE_DIR) / _OWNED_DIRNAME
    except Exception:  # noqa: BLE001
        return None


def acquire_singleton(port: int = LOCK_PORT):
    """قفلِ تک‌نمونگی. `None` یعنی نمونهٔ دیگری زنده است.

    تلهٔ ویندوز: `SO_REUSEADDR` این‌جا bind را **موفق** می‌کند حتی وقتی کسی
    نشسته است — یعنی دقیقاً همان دو-نمونگی که می‌خواهیم جلویش را بگیریم.
    `SO_EXCLUSIVEADDRUSE` رفتارِ درست را می‌دهد."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        s.bind(("127.0.0.1", port))
        return s
    except OSError:
        try:
            s.close()
        except OSError:
            pass
        return None


def _atomic_write(path: Path, payload: dict) -> bool:
    """نوشتنِ اتمیک — عکسِ نیمه‌نوشته بدتر از نبودِ عکس است."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), "utf-8")
        os.replace(str(tmp), str(path))
        return True
    except Exception:  # noqa: BLE001
        return False


def write_snapshot() -> "Path | None":
    """یک چرخه: جمع کن، اعتبارسنجی کن، بنویس. مسیر خارج از فضای‌نام ⇒ توقف."""
    d = owned_dir()
    if d is None:
        return None
    # گاردِ مالکیت: حتی اگر روزی کسی مسیر را عوض کند، نوشتن بیرونِ فضای‌نامِ
    # این پروسه انجام نمی‌شود.
    if d.name != _OWNED_DIRNAME:
        return None
    try:
        snap = snapshot()
    except Exception:  # noqa: BLE001
        return None          # fail-closed: عکسِ ناقص ننویس
    snap["supervisor"] = SCHEMA
    target = d / "snapshot.json"
    return target if _atomic_write(target, snap) else None


def main() -> int:  # pragma: no cover
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not enabled():
        print(f"control_plane: خاموش ({FLAG} ست نشده) — هیچ کاری نکردم.")
        return 0
    lock = acquire_singleton()
    if lock is None:
        print(f"control_plane: نمونهٔ دیگری روی {LOCK_PORT} زنده است — خارج شدم.")
        return 0
    print(f"control_plane: زنده. هر {INTERVAL_S}s یک عکس در {owned_dir()}")
    try:
        while True:
            p = write_snapshot()
            print(f"  {'✅' if p else '⚠️'} {p or 'نوشتن انجام نشد'}")
            time.sleep(INTERVAL_S)
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            lock.close()
        except OSError:
            pass


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
