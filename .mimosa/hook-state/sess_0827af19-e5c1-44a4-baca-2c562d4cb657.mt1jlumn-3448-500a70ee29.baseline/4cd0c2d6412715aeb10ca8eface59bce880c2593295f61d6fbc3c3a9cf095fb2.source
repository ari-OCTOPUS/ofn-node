#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fence_ledger.py — دفترِ شمارشِ غربالِ context-fence: «آیا اصلاً شلیک کرد؟»

چرا این فایل هست
────────────────
تا امروز تنها اقدامِ یک screenِ مثبت **یک alert** بود. alert دو لایه خفه‌کننده
دارد که هر دو عمدی و درست‌اند (`opslib.alert_throttled` پنجرهٔ ۳۰دقیقه‌ای per-task،
و dedupِ ۶ساعتهٔ خودِ `alert` که بعد از ۳ تکرار دیگر چیزی نمی‌نویسد). نتیجه: زیرِ
یک سیلِ واقعیِ تزریق — دقیقاً همان لحظه‌ای که فنس برای آن ساخته شده — ردِ اکثرِ
شلیک‌ها **پاک می‌شود**، و مالک هیچ راهی ندارد بپرسد «این هفته چند بار؟ از کجا؟».

قاعدهٔ خانه: **ثبت همیشه، گیت فقط روی تحویل.** alert تحویل است و حق دارد throttle
شود؛ شمارش حق ندارد. این ماژول همان نیمهٔ گم‌شده است — و بدونش، مسلح‌کردنِ فلگ
ادعایی می‌شد که هیچ مشاهده‌ای نمی‌توانست ابطالش کند («مسلح ولی اثبات‌ناپذیر»).

قرارداد
───────
* **content-free مطلق.** فقط شناسهٔ ایستای call-site + برچسبِ provenance + کدهای
  یافته (واژگانِ بستهٔ خودِ `context_fence`) + زمان. هرگز promptِ خام، هرگز PII،
  هرگز secret. هر رشته scrub و کوتاه می‌شود.
* **کراندار.** یک فایلِ JSONِ کوچک با سقفِ صداکننده و سقفِ روز — نه لاگِ بی‌انتها
  روی مسیرِ داغِ LLM.
* **fail-soft مطلق.** هر استثنا بلعیده می‌شود و `False` برمی‌گردد. دفتر هرگز
  مسیرِ LLM را نمی‌کشد.
* stdlib فقط؛ صفر شبکه؛ خودِ این ماژول هیچ فلگی چک نمی‌کند — فقط از مسیرهایی صدا
  زده می‌شود که از قبل پشتِ `OCTOPUS_WIRE_CONTEXT_FENCE` هستند. فلگ خاموش =
  هیچ صداکننده‌ای = فایل حتی ساخته نمی‌شود (رفتارِ امروز، بایت‌به‌بایت).

سطحِ مالک:
    python _ops/cortex/fence_ledger.py           # کارتِ فارسی
    python _ops/cortex/fence_ledger.py --json    # ماشین‌خوان
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

SCHEMA = "context-fence-hits.v1"
FILENAME = "context-fence-hits.json"

# کران‌ها: دفتر باید در یک نگاه خوانده شود، نه grep.
MAX_CALLERS = 40
MAX_DAYS = 14
MAX_CODES_PER_HIT = 8

_HERE = Path(__file__).resolve().parent          # _ops/cortex
_SCRUB = re.compile(r"[^\w:.\-/@]")


def _scrub(v, n: int = 48) -> str:
    return _SCRUB.sub("_", str(v or "unknown"))[:n]


def _state_dir() -> Path:
    """پوشهٔ state — env-اول تا harnessِ تست هرگز به درختِ زنده نریزد.

    ترتیب عمدی: `OCTOPUS_STATE_DIR` (همان چیزی که harness پین می‌کند) →
    `OPS_DIR/state` → همسایهٔ خودِ ماژول. هیچ مسیرِ جاافتاده‌ای نمی‌ماند که
    بی‌صدا به `F:\\backup` بیفتد."""
    p = os.environ.get("OCTOPUS_STATE_DIR")
    if p:
        return Path(p)
    p = os.environ.get("OPS_DIR")
    if p:
        return Path(p) / "state"
    return _HERE.parent / "state"


def path() -> Path:
    return _state_dir() / FILENAME


def _load() -> dict:
    try:
        d = json.loads(path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001 — دفترِ خراب/غایب = دفترِ خالی
        return {}


def record(caller: str, findings, provenance: str = "") -> bool:
    """یک screenِ مثبت را بشمار. خروجی: True اگر نوشته شد.

    این تابع **هیچ‌وقت** استثنا نمی‌دهد و هیچ‌وقت متنِ خام را لمس نمی‌کند —
    امضایش عمداً متن نمی‌گیرد تا نشتِ محتوا ساختاراً ناممکن باشد."""
    try:
        codes = [_scrub(c, 32) for c in (findings or [])][:MAX_CODES_PER_HIT]
        cal = _scrub(caller)
        prov = _scrub(provenance, 24) if provenance else ""
        now = time.time()
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))

        d = _load()
        d["schema"] = SCHEMA
        d["total"] = int(d.get("total") or 0) + 1
        d.setdefault("first_ts", iso)
        d["last_ts"] = iso

        by_code = d.get("by_code") if isinstance(d.get("by_code"), dict) else {}
        for c in codes:
            by_code[c] = int(by_code.get(c) or 0) + 1
        d["by_code"] = by_code

        by_caller = d.get("by_caller") if isinstance(d.get("by_caller"), dict) else {}
        rec = by_caller.get(cal) if isinstance(by_caller.get(cal), dict) else {}
        rec["n"] = int(rec.get("n") or 0) + 1
        rec["last"] = iso
        rec["last_epoch"] = round(now, 3)
        provs = [p for p in (rec.get("provenance") or []) if isinstance(p, str)]
        if prov and prov not in provs:
            provs.append(prov)
        rec["provenance"] = provs[-4:]
        seen = [c for c in (rec.get("codes") or []) if isinstance(c, str)]
        for c in codes:
            if c not in seen:
                seen.append(c)
        rec["codes"] = seen[-MAX_CODES_PER_HIT:]
        by_caller[cal] = rec
        if len(by_caller) > MAX_CALLERS:      # کهنه‌ترین‌ها می‌افتند، شمارِ کل نه
            by_caller = dict(sorted(by_caller.items(),
                                    key=lambda kv: (kv[1] or {}).get("last_epoch", 0)
                                    )[-MAX_CALLERS:])
        d["by_caller"] = by_caller

        by_day = d.get("by_day") if isinstance(d.get("by_day"), dict) else {}
        by_day[day] = int(by_day.get(day) or 0) + 1
        if len(by_day) > MAX_DAYS:
            by_day = dict(sorted(by_day.items())[-MAX_DAYS:])
        d["by_day"] = by_day

        p = path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
        return True
    except Exception:  # noqa: BLE001 — دفتر هرگز مسیرِ LLM را نمی‌کشد
        return False


def _armed_from_state():
    """وضعیتِ فلگ از **سنجهٔ قطعیِ ARMING-ORDER**: `ORGANISM-STATE.json → wiring`.

    این همان کلیدی است که همین جلسه به `wire_summary()` اضافه شد؛ ارگانیسم آن را
    از خروجیِ خودِ `flag()` و **بعد از** `apply_profile` می‌نویسد. ندانستن → None."""
    try:
        d = json.loads((_state_dir() / "ORGANISM-STATE.json").read_text("utf-8"))
        w = d.get("wiring")
        if isinstance(w, dict) and "wire_context_fence" in w:
            return bool(w["wire_context_fence"])
    except Exception:  # noqa: BLE001 — stateِ غایب/خراب = ندانستن
        pass
    return None


def _armed_from_env():
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import context_fence as _fence      # noqa: WPS433 — همسایهٔ همین ماژول
        return bool(_fence.enabled())
    except Exception:  # noqa: BLE001
        return None


def armed_source() -> str:
    return "organism-state" if _armed_from_state() is not None else "process-env"


def armed() -> bool | None:
    """آیا فنس در **پروسهٔ ارگانیسم** مسلح است؟ ندانستن → None (نه False).

    ⚠️ چرا env ِ همین پروسه کافی نیست: کارت را مالک از یک شلِ ساده اجرا می‌کند که
    `OCTOPUS-flags.cmd` را نخوانده. اگر فقط env را می‌خواندیم، بعد از یک مسلح‌کردنِ
    **واقعی** کارت می‌گفت «خاموش … «۰» یعنی اندازه نگرفتیم» — یک جملهٔ صریحاً
    **غلط** دقیقاً از همان جنسی که این ماژول برای جلوگیری‌اش ساخته شد. پس اول
    stateِ ارگانیسم، بعد env ِ همین پروسه، و اگر هیچ‌کدام: None (نه False)."""
    a = _armed_from_state()
    return a if a is not None else _armed_from_env()


def summary() -> dict:
    """خلاصهٔ خواندنی. دفترِ غایب دروغ نمی‌گوید: `total=0` با `ever=False`."""
    d = _load()
    total = int(d.get("total") or 0)
    return {
        "schema": SCHEMA,
        "armed": armed(),
        "armed_source": armed_source(),
        "ever": bool(total),
        "total": total,
        "first_ts": d.get("first_ts"),
        "last_ts": d.get("last_ts"),
        "by_code": d.get("by_code") or {},
        "by_caller": d.get("by_caller") or {},
        "by_day": d.get("by_day") or {},
        "file": str(path()),
    }


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_LRI, _PDI, _RLM = "\u2066", "\u2069", "\u200f"


def fa_num(x) -> str:
    return str(x).translate(_FA_DIGITS)


def ltr(s: str) -> str:
    """نامِ لاتین را ایزوله کن تا bidi متنِ فارسی را جابه‌جا نکند."""
    return f"{_LRI}{s}{_PDI}"


def render(s: dict | None = None) -> str:
    """کارتِ کوتاهِ فارسی — عدد اول، بعد از کجا، بعد چه‌کار."""
    s = summary() if s is None else s
    a = s.get("armed")
    head = {True: "🛡 فنسِ کانتکست: مسلح",
            False: "⚪ فنسِ کانتکست: خاموش (پیش‌فرض)",
            None: "❔ فنسِ کانتکست: وضعیتِ فلگ نامعلوم"}[a]
    if not s.get("ever"):
        # سه‌حالتی عمدی: «نمی‌دانم» نه با «خاموش» یکی می‌شود نه با «مسلح».
        tail = {
            True: "\nهیچ غربالِ مثبتی تا امروز ثبت نشده.",
            False: "\nخاموش است، پس هیچ غربالی اجرا نمی‌شود — «۰» این‌جا یعنی "
                   "«اندازه نگرفتیم»، نه «حمله‌ای نبود».",
            None: "\nوضعیتِ فلگ خوانده نشد (نه stateِ ارگانیسم، نه env ِ این "
                  "پروسه) — «۰» این‌جا هیچ حکمی نیست.",
        }[a]
        return _RLM + head + tail
    top = sorted((s.get("by_caller") or {}).items(),
                 key=lambda kv: -(kv[1] or {}).get("n", 0))[:4]
    rows = "\n".join(f"{_RLM}  · {ltr(k)} — {fa_num((v or {}).get('n', 0))} بار"
                     for k, v in top)
    codes = "، ".join(f"{ltr(k)}×{fa_num(v)}" for k, v in
                      sorted((s.get("by_code") or {}).items(), key=lambda kv: -kv[1])[:5])
    return (_RLM + head + f"\n{fa_num(s['total'])} غربالِ مثبت "
            f"(آخرین: {ltr(str(s.get('last_ts') or '?'))})\n" + rows
            + (f"\n{_RLM}کدها: {codes}" if codes else "")
            + f"\n{_RLM}این‌ها فقط **مشاهده**اند — هیچ promptی بازنویسی یا بلاک نشد.")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    s = summary()
    if "--json" in argv:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print(render(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
