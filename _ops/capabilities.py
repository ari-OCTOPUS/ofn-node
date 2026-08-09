#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capabilities.py — پلِ گم‌شده بینِ «رأیِ مالک» و «قابلیتِ واقعی».

مسئله‌ای که می‌بندد (اندازه‌گیریِ ۲۰۲۶-۰۸-۰۴ روی دفترِ زنده)
──────────────────────────────────────────────────────────
    ۳۶ درخواستِ ابزار  →  همه `pending`
     ۴ پاسخ            →  همه `granted`

مالک «بله» گفته بود و **هیچ کدی آن `granted` را مصرف نمی‌کرد**. خودِ
`approval_channel` صادقانه اعتراف می‌کند:

    «✅ ثبت شد: بگیر. ▸ تا وقتی ابزار واقعاً وصل نشود،
      این فقط یک رأی است نه یک قابلیت.»

نتیجهٔ زیسته: اختاپوس **۳۶ بار همان چیز را خواست** — و شکایتِ مالک شد
«انگار هرکاری می‌کنم دیده نمی‌شود».

و کشفِ تعیین‌کننده: **آن قابلیت از قبل وجود داشت و روشن بود.**
هر ۳۶ درخواست یک چیز می‌خواستند — «نشستِ shell ِ پایدار با خواندن/نوشتنِ
checkout و اجرای تست». ولی `cortex/code_autonomy` دقیقاً همان را می‌دهد،
در شکلِ **گیت‌دار**: پیشنهادِ پچ → تستِ سایه‌ای در ایزوله → اعمال با **هشت
گیتِ هم‌زمان** → کیل‌سوییچِ خودکار روی هر قرمزِ canary. و `active()` همین
حالا `True` است.

پس اختاپوس داشت نسخهٔ **خام** چیزی را گدایی می‌کرد که نسخهٔ **امنش** را
داشت و خبر نداشت. این ماژول همان خبر است.

مرزِ سختِ این ماژول
────────────────────
⚠️ این‌جا **هیچ قابلیتِ تازه‌ای ساخته نمی‌شود.** فقط قابلیت‌هایی که از قبل
   کد دارند و گیتِ خودشان را دارند، **نام‌دار و قابلِ‌پرسش** می‌شوند.
⚠️ `granted` ِ مالک هرگز به‌تنهایی چیزی را باز نمی‌کند: هر قابلیت گیتِ خودش
   را نگه می‌دارد (`gate_fn`). رأیِ مالک **شرطِ لازم** است نه کافی.
⚠️ صفر اجرا، صفر شبکه، صفر نوشتن در مسیرِ کد. این ماژول فقط **می‌خواند** و
   یک ردیفِ اثر می‌نویسد.
⚠️ shell ِ خام عمداً **ثبت نشده** — بند ۳ ِ `_WHY_NO_SHELL` پایین.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "capability.v1"

#: ⚠️ ۲۰۲۶-۰۸-۰۴ — این متن **تاریخچه** است، نه سیاستِ جاری.
#: نگرانی مطرح شد، مالک **دوباره تأیید کرد** («shell خام رو هم بازش کن»)، و شل
#: ساخته و مسلح شد: `_ops/shell_capability.py`. متن می‌ماند چون استدلالش هنوز
#: توضیح می‌دهد **چرا مهارها لازم‌اند** — نه اینکه چرا نباید باشد.
_WHY_NO_SHELL = """
هشدارِ اصلی (هنوز برقرار): شلِ POSIX ِ خام روی همین ماشین کنارِ `.env` (توکنِ
Fugu/GLM/تلگرام)، دادهٔ مالی، و یک مسیرِ ایمیلِ خروجیِ مسلح می‌دود.
پس باز شد **ولی مهارشده**: فعال‌سازیِ صریحِ مالک · دو کیل‌سوییچ · رسیدِ
ماندگارِ قبل‌از‌اجرا · سقفِ زمان/خروجی · و deny-list ای که مو‌به‌مو §۰ ِ منشور
است (هرگز حذف · هرگز `.git`/`_code`/secret) نه سلیقهٔ ایجنت.
و همچنان: برای «بخوان، پچ بزن، تست کن»، مسیرِ `code_autonomy` با هشت گیت
**ترجیح دارد** — شل برای کاری است که آن پوشش نمی‌دهد.
"""


def _gate_raw_shell() -> tuple:
    """گیتِ واقعیِ شلِ خام — همان که خودِ `run()` هم می‌سنجد، نه یک کپی."""
    try:
        import shell_capability as _sc  # noqa: PLC0415
        return _sc.active()
    except Exception as e:  # noqa: BLE001
        return False, f"shell_capability در دسترس نیست ({type(e).__name__})"


def _ledger_path() -> Path:
    return opslib.STATE_DIR / "capability-effects.jsonl"


# ── رجیستری ──────────────────────────────────────────────────────────────────
# هر ورودی: نامِ قابلیت → (توضیح، تابعِ گیت، «چطور استفاده کن»)
# `gate_fn` هرگز از این‌جا دور زده نمی‌شود.

def _gate_code_autonomy() -> tuple:
    """گیتِ واقعیِ سطح A — همان که `apply_approved` هم می‌سنجد."""
    try:
        import code_autonomy as ca  # noqa: PLC0415
        return bool(ca.active()), ("ACTIVATION-CODE-AUTONOMY.flag هست و "
                                   "STOP-CODE-AUTONOMY نیست")
    except Exception as e:  # noqa: BLE001
        return False, f"code_autonomy در دسترس نیست ({type(e).__name__})"


REGISTRY = {
    "code.patch_and_test": {
        "چیست": "خواندنِ کدِ درخت، نوشتنِ پچ، تستِ ایزوله، و اعمال با هشت گیت.",
        "ماژول": "_ops/cortex/code_autonomy.py",
        "gate_fn": _gate_code_autonomy,
        "چطور": ("۱) `code_autonomy.low_risk_patch(target, content)` برای سنجشِ ریسک · "
                 "۲) `shadow_test(patch)` — اجرا در ایزوله، صفر اثر روی درختِ زنده · "
                 "۳) `propose_to_owner(patch)` — کارتِ ✅/❌ برای مالک · "
                 "۴) `apply_approved(patch, approval_id)` — فقط با تأیید، هشت گیت."),
        "جایگزینِ_چه_درخواستی": "نشستِ shell پایدار با خواندن/نوشتنِ checkout و اجرای تست",
    },
    "shell.raw": {
        "چیست": ("اجرای فرمانِ پوسته در ریشهٔ vault — رأیِ مالک ۰۸-۰۴. "
                 "مهارشده: دو کیل‌سوییچ، رسیدِ قبل‌از‌اجرا، سقفِ ۱۲۰ثانیه/۲۰KB."),
        "ماژول": "_ops/shell_capability.py",
        "gate_fn": _gate_raw_shell,
        "چطور": ("`shell_capability.run(cmd, reason=...)` — همیشه dict، هرگز "
                 "استثنا. ⚠️ deny-list = §۰ ِ منشور: حذف ممنوع (mv کن)، "
                 "`.git`/`_code`/secret دست‌نخوردنی، خروجِ شبکه‌ای ممنوع. "
                 "برای پچ‌زدنِ کد، `code.patch_and_test` **ترجیح دارد** چون "
                 "هشت گیت و تستِ سایه‌ای دارد؛ شل برای بقیهٔ کارهاست."),
        "جایگزینِ_چه_درخواستی": "همان ۳۶ درخواستِ «نشستِ shell پایدار»",
    },
}


def granted_verdicts() -> dict:
    """`{نیازِ کوتاه: رأی}` از دفترِ درخواست‌های ابزار. هرگز استثنا."""
    out: dict = {}
    try:
        import tool_request as tr  # noqa: PLC0415
        rows = tr._rows()
        ans = {str(r.get("request_id")): r.get("verdict") for r in rows
               if r.get("schema") == tr.SCHEMA + ".answer"}
        for r in rows:
            if r.get("schema") != tr.SCHEMA:
                continue
            v = ans.get(str(r.get("request_id")))
            if v:
                out[str(r.get("need") or "")[:120]] = v
    except Exception:  # noqa: BLE001
        pass
    return out


def status() -> dict:
    """تصویرِ کامل: هر قابلیت، گیتش، و اینکه مالک رأیی داده یا نه.

    فقط‌خواندنی و بی‌استثنا — این تابع در مسیرِ context ِ مغز است و حق ندارد
    چیزی را بترکاند."""
    verdicts = granted_verdicts()
    any_granted = any(v == "granted" for v in verdicts.values())
    caps = {}
    for name, spec in REGISTRY.items():
        try:
            ok, why = spec["gate_fn"]()
        except Exception as e:  # noqa: BLE001
            ok, why = False, f"گیت خطا داد ({type(e).__name__})"
        caps[name] = {
            "در_دسترس": bool(ok),
            "چرا": why,
            "چیست": spec["چیست"],
            "چطور": spec["چطور"],
            "ماژول": spec["ماژول"],
            "مالک_رأیِ_مرتبط_داده": any_granted,
        }
    return {"schema": SCHEMA, "قابلیت‌ها": caps,
            "رأی‌های_مالک": verdicts,
            "شل_خام_چرا_نه": _WHY_NO_SHELL.strip()}


def available() -> list:
    """فقط نامِ قابلیت‌هایی که **همین حالا** گیتشان باز است."""
    return sorted(n for n, c in status()["قابلیت‌ها"].items() if c["در_دسترس"])


def record_effect(capability: str, *, action: str, ok: bool, detail: str = "") -> None:
    """ردیفِ اثر — نیمهٔ دومِ حلقه.

    بدونِ این، «قابلیت داری» یک ادعاست. با این، می‌شود پرسید «از وقتی مالک
    تأیید کرد، چه کاری واقعاً انجام شد؟» — و اگر جواب «هیچ» بود، آن هم یک
    یافته است، نه سکوت."""
    try:
        p = _ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "schema": SCHEMA + ".effect",
                "ts": opslib.now_iso(),
                "capability": str(capability)[:64],
                "action": str(action)[:120],
                "ok": bool(ok),
                "detail": str(detail)[:300],
            }, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — ثبت هرگز مسیرِ اصلی را نمی‌کشد
        pass


def effects(limit: int = 20) -> list:
    out = []
    try:
        p = _ledger_path()
        if p.exists():
            for line in p.read_text("utf-8", errors="replace").splitlines()[-limit:]:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return out


def card() -> str:
    """کارتِ effects — «از وقتی مالک تأیید کرد، چه کاری واقعاً انجام شد؟»

    وایرینگِ ب-۴ (مگاپرامپتِ ۲۰۲۶-۰۸-۰۹): تا امروز `effects()` وجود داشت ولی
    هیچ card() ای برای کشفِ خودکارِ `capability_registry.discover()` نداشت —
    یعنی این پاسخ از تلگرام دیده نمی‌شد. صفر ردیف هم خودش جواب است، نه سکوت."""
    rows = effects(limit=5)
    if not rows:
        return ("🧾 <b>صفر اثرِ ثبت‌شده</b>\n"
                 "▸ هیچ قابلیتی هنوز از این ماژول استفاده نکرده — "
                 "خودش هم یک یافته است، نه سکوت.")
    lines = [f"🧾 <b>{len(rows)} اثرِ اخیر</b>"]
    for r in reversed(rows):
        mark = "✅" if r.get("ok") else "❌"
        cap = str(r.get("capability") or "؟")[:40]
        act = str(r.get("action") or "")[:60]
        lines.append(f"{mark} {cap} — {act}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(status(), ensure_ascii=False, indent=2))
