#!/usr/bin/env python3
"""dark_capabilities — کدی که کامل است، تست دارد، صداکننده دارد… و نمی‌دود.

مسئله‌ای که این حل می‌کند
─────────────────────────
هر جلسه چند قابلیت ساخته می‌شود و طبقِ منشور **flag-gated + default-off** است.
این قاعده درست است و باید بماند. ولی عارضه‌اش این است: ایجنتِ بعدی (یا خودِ من
بعد از فراموشی) فایلِ `_ops/legs/foo.py` را باز می‌کند، می‌بیند کامل است، تستش
سبز است، در `wiring.py` صدا زده می‌شود — و **فرض می‌کند کار می‌کند**. نمی‌کند.
یک `if os.environ.get(FLAG) != "1": return` در خطِ اول نشسته و آن env هرگز
مسلح نشده.

این بدترین شکلِ از-دست-رفتنِ انسجام است، چون خطا در جهتِ خوش‌بینی است: سیستم
بزرگ‌تر از آنی به‌نظر می‌رسد که هست، و کسی دنبالِ علتِ سکوت نمی‌گردد.

سنجهٔ ۲۰۲۶-۰۸-۰۱ که این ماژول را ساخت: ۱۶ فلگ در `ARMING-ORDER-2026-07-29.md`
دستی فهرست شده بودند. آن سند از روزِ نوشته‌شدنش شروع به پوسیدن کرد — چون سند
است، و سند با کد همگام نمی‌ماند. این ماژول همان کار را می‌کند ولی از **کد**
می‌پرسد، پس هرگز کهنه نمی‌شود.

جایگاه در میانِ ابزارهای موجود (هیچ‌کدام دوباره‌کاری نمی‌شود)
────────────────────────────────────────────────────────────
    orphan_scan.py          «کدام ماژول به هیچ‌چیز وصل نیست؟»   (صداکننده)
    capability_registry     «چه چیزی می‌توانم به مالک نشان دهم؟» (سطح)
    flag_drift.py           «مسلح در برابرِ بارگذاری‌شده»        (تازگیِ بوت)
    dark_capabilities.py    «خوانده می‌شود ولی هرگز مسلح نشده»   ← این
                            (تقاطعی که هیچ‌کدامِ بالا نمی‌پوشاند)

`flag_drift` فقط دربارهٔ فلگ‌هایی حرف می‌زند که **در فایل هستند**؛ سؤالِ اینجا
دقیقاً برعکس است: کدام فلگ در کد خوانده می‌شود ولی در فایل نیست.

قاعدهٔ سه‌منبعی — چرا «غایب» به‌تنهایی یعنی خاموش نیست
──────────────────────────────────────────────────────
درسِ ثبت‌شدهٔ ۲۰۲۶-۰۷-۲۹: در بوت `wiring.apply_profile()` هر عضوِ
`PAPER_FULL_FLAGS` را که در env **نباشد** روی `1` می‌گذارد. یعنی برای آن فهرست
**غیاب یعنی روشن**. پس حکم از سه منبع می‌آید و نه یکی:

    ۱ `_ops/OCTOPUS-flags.cmd`      — مسلح‌سازیِ صریحِ مالک
    ۲ `wiring.PAPER_FULL_FLAGS`     — روشنِ ضمنی از راهِ پروفایل
    ۳ `state/ORGANISM-STATE.json`   — حقیقتِ زندهٔ **بعد از** apply_profile

منبعِ ۳ داورِ نهایی است ولی فقط دربارهٔ پروسه‌ای حرف می‌زند که آخر بوت شده و
فقط اگر فایل تازه باشد؛ پس وقتی هست وزن دارد و وقتی نیست سکوت می‌کند، نه حدس.

امنیت: هرگز **مقدارِ** هیچ کلیدی خوانده یا چاپ نمی‌شود — فقط نامِ فلگ و
حضور/غیابش. گاردِ نامِ محرمانه از `flag_drift.is_secret_name` قرض گرفته می‌شود
تا دو تعریفِ واگرا نداشته باشیم.

فقط‌خواندنی. هیچ فایلی نمی‌نویسد، هیچ ماژولی را import نمی‌کند (کشف نحوی است،
چون importِ ۲۵۰ ماژول یعنی اجرای هر اثرِ جانبیِ import-time).
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import flag_drift  # noqa: E402  — گاردِ محرمانه و پارسرِ فایلِ فلگ، مشترک

# فقط فلگ‌های خودِ ارگانیسم. کلیدهای `.env` (توکن، پسورد، کلیدِ API) عمداً بیرون
# می‌مانند: آن‌ها فلگِ قابلیت نیستند و شمردنشان این پروب را دائماً قرمز و
# بی‌اعتبار می‌کرد — همان اشتباهی که `flag_drift` در دامنه‌اش تصحیح کرده.
_FLAG_RE = re.compile(r"^(?:OCTOPUS|CORTEX)_[A-Z0-9_]{2,}$")

_SKIP_DIRS = {"_Archive", "_Duplicates", ".git", "__pycache__", "node_modules",
              ".venv", "venv", "site-packages", "tests",
              # ⚠️ ۲۰۲۶-۰۸-۰۱ — `.claude` را حتماً رد کن. اندازه‌گیری روی
              # درختِ زنده: ۵.۵۴ GB و ۶۷٬۸۴۴ فایل در ۱۸ worktree. از ۲۱٬۹۷۳
              # فایلِ `.py` زیرِ ریشه، فقط **۹۵۶** واقعی‌اند و بقیه رونوشت.
              # هر اسکنی که این را نپیماید، ۹۶٪ کارِ بی‌فایده نمی‌کند — و روی
              # ویندوز با دو آنتی‌ویروسِ فعال (Defender + Norton) که هر
              # بازکردنِ فایل را رهگیری می‌کنند، همان ۹۶٪ لپ‌تاپ را می‌خواباند.
              # این ماژول همیشه از `_ops` شروع می‌شود پس عملاً مصون بود، ولی
              # هر کسی که `scan(root)` را از ریشه صدا بزند بی‌آن می‌سوزد.
              ".claude", "worktrees"}

# ⚠️ `flag` ایدیمِ **غالبِ** خودِ این مخزن است: `wiring.flag(name) -> bool`.
# نسخهٔ اول فقط `os.environ.get`/`getenv` را می‌شناخت و در نتیجه **۱۱۸ خوانشِ
# تولیدی** را نمی‌دید (در برابرِ ۱۶۹ که می‌دید) — یعنی نزدیک به نیمی از کلِ
# سطحِ فلگ. عارضه‌اش دوگانه بود: فلگ‌هایی که فقط با `flag()` خوانده می‌شوند
# اصلاً در گزارش نمی‌آمدند، و مسلح‌های واقعی «یتیم» اعلام می‌شدند.
# درسِ ثبت‌شده: اسکنِ صداکننده باید هر شکلِ نحویِ موجود را بشمارد، نه فقط
# شکلِ کتابیِ کتابخانهٔ استاندارد.
_ENV_READERS = {"getenv", "get", "flag"}


def _iter_py(root: Path):
    """همهٔ ماژول‌های تولیدی زیرِ `_ops` — تست‌ها عمداً بیرون‌اند.

    یک تست که فلگی را ست می‌کند دلیلِ زنده‌بودنِ آن فلگ نیست؛ اگر می‌شمردیم،
    هر فلگی که تستِ خوبی داشت «مصرف‌کننده دارد» به‌نظر می‌رسید — همان خطای
    «آرتیفکتِ خودساخته شاهد نیست».
    """
    for p in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        yield p


def _flags_read_by(path: Path) -> tuple[dict[str, bool], set[str]]:
    """نامِ هر فلگی که این فایل واقعاً از env می‌خواند یا ثابتش را نگه می‌دارد.

    چهار شکلِ شناخته‌شده — و شکلِ چهارم همان کورِ ثبت‌شده در حافظه است که
    اسکنِ صداکننده یک‌بار از دستش داد:

        os.environ.get("X") / os.getenv("X")   ← فراخوانی
        os.environ["X"]                        ← اندیس
        FLAG = "X"                             ← ثابتِ ماژول (خواننده جای دیگر)
        FLAGS = ("X", "Y")                     ← چندتایی
    """
    try:
        tree = ast.parse(path.read_text("utf-8", errors="replace"), str(path))
    except (SyntaxError, OSError, ValueError):
        return {}, set()   # ⚠️ dict، نه set — فراخوان `.items()` می‌زند و یک
                           # فایلِ نحواً خرابْ کلِ اسکن را با AttributeError
                           # می‌خواباند.

    found: dict[str, bool] = {}   # flag → «تنظیم است» (نه دروازه)
    # هر ذکرِ نامِ فلگ، در هر بافتی — برای پرسشِ **یتیم**، که سنجهٔ پهن‌تری
    # می‌خواهد: `("mining", "⛏", "OCTOPUS_WIRE_MINING", "business")` در یک
    # جدولِ منو، خوانشِ env نیست ولی قطعاً یعنی «این فلگ زنده است». سنجهٔ باریک
    # آن را یتیم اعلام می‌کرد — آژیرِ کاذب، که بدترین چیز برای ابزارِ ممیزی است.
    mentioned: set[str] = set()

    def _lit(node) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value if _FLAG_RE.match(node.value) else None
        return None

    for _n in ast.walk(tree):
        v = _lit(_n)
        if v:
            mentioned.add(v)

    # ── پاسِ اول: کدام فلگ با توکنِ صدق مقایسه می‌شود؟ ───────────────────────
    # ⚠️ قاعدهٔ اولِ من «پیش‌فرض دارد ⇒ تنظیم» بود و `OCTOPUS_STATE_DIR` را
    # دروازه شمرد، چون نوشته شده `get(X, "")` و رشتهٔ تهی پیش‌فرضِ «معنادار»
    # حساب نمی‌شد. ولی آن یک **مسیر** است، نه دروازه؛ و ۱۴ خواننده داشت، پس
    # صدرِ فهرستِ «تاریک» را با نویز پر می‌کرد. سنجهٔ درست وجودِ پیش‌فرض نیست،
    # **مقایسه با «۱»/«true»** است — همان چیزی که یک دروازه را دروازه می‌کند.
    truth_gated: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left] + list(node.comparators)
        if not any(isinstance(s, ast.Constant)
                   and str(s.value).strip().lower() in _TRUE + ("0", "false", "off")
                   for s in sides):
            continue
        for s in sides:
            for sub in ast.walk(s):
                if isinstance(sub, ast.Call) and sub.args:
                    v = _lit(sub.args[0])
                    if v:
                        truth_gated.add(v)

    def _add(flag: str, defaulted: bool) -> None:
        # «تنظیم» فقط وقتی هیچ خوانشی دروازه‌ای نباشد — سخت‌گیرانه‌ترین حالت.
        tuning = defaulted and flag not in truth_gated
        found[flag] = tuning and found.get(flag, True)

    for node in ast.walk(tree):
        # os.environ.get("X") / os.getenv("X")  ← آرگومانِ دوم = پیش‌فرض
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            if name in _ENV_READERS and node.args:
                v = _lit(node.args[0])
                if v:
                    # **وجودِ** آرگومانِ دوم مهم است، نه مقدارش. `get(X, "")`
                    # یعنی نویسنده غیاب را مدیریت کرده؛ رشتهٔ تهی پیش‌فرضِ
                    # کاملاً معتبری است (مسیر، لیست، رشتهٔ خالی). شرطِ قبلی
                    # `"" not in ("","None")` بود و همین `OCTOPUS_STATE_DIR`
                    # را با ۱۴ خواننده به صدرِ فهرستِ تاریک می‌فرستاد.
                    # دروازه‌بودن از مقایسه با «۱» می‌آید، نه از نبودِ پیش‌فرض.
                    _add(v, len(node.args) > 1)
        # os.environ["X"]  ← هرگز پیش‌فرض ندارد
        elif isinstance(node, ast.Subscript):
            v = _lit(node.slice)
            if v:
                _add(v, False)
        # FLAG = "X"  /  FLAGS = ("X", "Y")  ← ثابت؛ خواندنِ واقعی جای دیگر
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if not isinstance(tgt, ast.Name) or "FLAG" not in tgt.id.upper():
                    continue
                v = _lit(node.value)
                if v:
                    _add(v, False)
                elif isinstance(node.value, (ast.Tuple, ast.List, ast.Set)):
                    for e in node.value.elts:
                        v = _lit(e)
                        if v:
                            _add(v, False)
    # is_secret_name فقط رویِ found اعمال می‌شود (جایی که مقدار/حالتِ گیت گزارش
    # می‌شود) — نه رویِ mentioned، که فقط برایِ پرسشِ orphan_armed («این فلگ اصلاً
    # جایی ذکر شده؟») استفاده می‌شود. فیلترکردنِ mentioned باعث می‌شد فلگ‌هایی مثلِ
    # OCTOPUS_HTTP_AUTH/OCTOPUS_WIRE_CB_TOKEN (که نامشان زیررشتهٔ AUTH/TOKEN دارد،
    # نه خودِ رازی) به‌غلط «مسلح ولی بی‌خواننده» گزارش شوند — رده‌بندیِ فازِ ۴ اسکنِ
    # ۲۰۲۶-۰۸-۰۷.
    return ({f: d for f, d in found.items() if not flag_drift.is_secret_name(f)},
            set(mentioned))


def _armed_in_file(flags_path: Path) -> set[str]:
    """نامِ فلگ‌های مسلحِ صریح. **فقط نام** — مقدار هرگز برنمی‌گردد.

    ⚠️ `parse_flags_file` یک **tuple** ِ `(flags, stats)` برمی‌گرداند، نه dict.
    نسخهٔ اول این را dict فرض کرد، به شاخهٔ لیست افتاد، روی دو عضوِ tuple
    چرخید و بی‌صدا مجموعهٔ تهی داد ⇒ هر فلگِ مسلحی «تاریک» شمرده می‌شد. باز هم
    همان الگو: نه استثنا، نه پیام، فقط جوابِ غلط.
    """
    try:
        parsed = flag_drift.parse_flags_file(flags_path)
    except Exception:  # noqa: BLE001
        return set()
    flags = parsed[0] if isinstance(parsed, tuple) else parsed
    if not isinstance(flags, dict):
        return set()
    # ارزشِ خالی یا صفر = تعریف‌شده ولی خاموش؛ نامش مسلح نیست.
    return {str(k) for k, v in flags.items()
            if _FLAG_RE.match(str(k)) and str(v).strip().lower() in _TRUE}


def _profile_on(ops: Path) -> set[str]:
    """`wiring.PAPER_FULL_FLAGS` — نحوی خوانده می‌شود، نه با import.

    importِ `wiring` یعنی اجرای `apply_profile` و لمسِ envِ همین پروسه.
    """
    w = ops / "wiring.py"
    if not w.exists():
        return set()
    try:
        tree = ast.parse(w.read_text("utf-8", errors="replace"), str(w))
    except (SyntaxError, OSError, ValueError):
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "PAPER_FULL_FLAGS"
                for t in node.targets):
            for e in getattr(node.value, "elts", []):
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    out.add(e.value)
    return out


_TRUE = ("1", "true", "yes", "on")


def _live_by_process(ops: Path) -> tuple[dict[str, set[str]], str]:
    """حقیقتِ زنده، **به تفکیکِ پروسه** — از snapshotهای بوتِ `flag_drift`.

    ⚠️ نسخهٔ اولِ همین تابع `state/ORGANISM-STATE.json` را می‌خواند و دنبالِ
    کلیدِ `flags` می‌گشت. آن کلید **اصلاً وجود ندارد**؛ پس مجموعهٔ تهی برمی‌گشت
    و تابع منبع را `live` اعلام می‌کرد ⇒ «۲۵۷ از ۲۵۷ فلگ تاریک». یعنی این
    ماژول در اولین اجرا دقیقاً همان بیماری‌ای را داشت که برای گرفتنش ساخته شده
    بود: ادعای دانستن، بدونِ دانستن. حکمِ ندانستن باید `absent` باشد نه تهی.

    و چرا per-process: `sys.path[0]` برای هر پروسه فرق دارد و env هر پروسه
    جداگانه بارگذاری می‌شود. همین جلسه دیده شد که یک ماژول فقط از یک cwd
    resolve می‌شد و از چهارتای دیگر نه. یک مجموعهٔ واحد آن شکاف را پنهان
    می‌کند — و پنهان‌کردنِ شکافِ بینِ پروسه‌ها همان چیزی است که `flag_drift`
    در کامنتِ خودش «سبزِ دروغی» می‌نامد.
    """
    snaps = sorted((ops / "state").glob("flags-loaded-*.json"))
    if not snaps:
        return {}, "absent"
    out: dict[str, set[str]] = {}
    for p in snaps:
        proc = p.stem.replace("flags-loaded-", "")
        try:
            d = json.loads(p.read_text("utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        env = d.get("flags")
        if not isinstance(env, dict):
            continue
        out[proc] = {str(k) for k, v in env.items()
                     if _FLAG_RE.match(str(k))
                     and str(v).strip().lower() in _TRUE}
    return (out, "live") if out else ({}, "unreadable")


def scan(ops_root=None) -> dict:
    """گزارشِ کامل. هرگز استثنا نمی‌دهد و هرگز چیزی نمی‌نویسد."""
    ops = Path(ops_root or _HERE).resolve()
    readers: dict[str, set[str]] = {}
    tuning: dict[str, bool] = {}
    mentioned: set[str] = set()
    for f in _iter_py(ops):
        rel = str(f.relative_to(ops)).replace("\\", "/")
        reads, says = _flags_read_by(f)
        mentioned |= says
        for flag, defaulted in reads.items():
            readers.setdefault(flag, set()).add(rel)
            tuning[flag] = defaulted and tuning.get(flag, True)

    armed = _armed_in_file(ops / "OCTOPUS-flags.cmd")
    profile = _profile_on(ops)
    per_proc, live_src = _live_by_process(ops)
    live_all = set().union(*per_proc.values()) if per_proc else set()

    rows = []
    for flag in sorted(readers):
        in_file, in_prof = flag in armed, flag in profile
        on_in = sorted(p for p, s in per_proc.items() if flag in s)
        if tuning[flag]:
            state = "TUNING"          # پیش‌فرض دارد ⇒ قابلیت به‌هرحال می‌دود
        elif live_src == "live":
            # ⚠️ جزئی‌بودن هم یک حالتِ مستقل است، نه گِردشده به ON یا DARK.
            state = ("ON" if len(on_in) == len(per_proc)
                     else "PARTIAL" if on_in else "DARK")
        elif in_file or in_prof:
            state = "ON"
        else:
            state = "DARK"
        rows.append({
            "flag": flag, "state": state,
            "armed_in_file": in_file, "profile_on": in_prof,
            "on_in_processes": on_in if live_src == "live" else None,
            "readers": sorted(readers[flag]),
            "n_readers": len(readers[flag]),
        })

    dark = [r for r in rows if r["state"] == "DARK"]
    partial = [r for r in rows if r["state"] == "PARTIAL"]
    # فلگی که مسلح است و نامش **هیچ‌جای** کدِ تولیدی نمی‌آید: تایپو، یا کدی که
    # حذف شده. سنجهٔ ذکر (پهن) نه سنجهٔ خوانش (باریک) — چون یک نامِ فلگ در یک
    # جدولِ پیکربندی هم گواهِ زنده‌بودن است. تست‌ها عمداً بیرون‌اند: تستی که
    # فلگی را ست می‌کند مصرف‌کنندهٔ تولیدی نیست.
    orphan_armed = sorted(armed - mentioned)
    return {"ops_root": str(ops), "live_source": live_src,
            "processes": sorted(per_proc), "n_live_on": len(live_all),
            "n_flags": len(rows), "n_dark": len(dark), "n_partial": len(partial),
            "n_tuning": sum(1 for r in rows if r["state"] == "TUNING"),
            "rows": rows, "dark": dark, "partial": partial,
            "orphan_armed": orphan_armed}


def render(res: dict) -> str:
    """گزارشِ فارسیِ کوتاه — فقط نام، هرگز مقدار."""
    L = [f"🔦 قابلیت‌های تاریک — {res['n_dark']} دروازهٔ تاریک از "
         f"{res['n_flags']} فلگ  "
         f"(+{res['n_partial']} جزئی · {res['n_tuning']} تنظیمی)",
         f"   منبع: {res['live_source']} — پروسه‌ها: "
         f"{'، '.join(res['processes']) or '—'}"]
    if res["live_source"] != "live":
        L.append("   ⚠️ snapshotِ بوت نیست؛ حکم از فایل+پروفایل است "
                 "(ضعیف‌تر — بعد از ری‌استارت دوباره بسنج).")
    if res["partial"]:
        L.append("")
        L.append("   ⚠️ در بعضی پروسه‌ها روشن، در بعضی نه — بدترین حالت، چون "
                 "نیمی از سیستم فکر می‌کند قابلیت هست:")
        for r in res["partial"]:
            L.append(f"     · {r['flag']}  ← فقط: "
                     f"{'، '.join(r['on_in_processes'])}")
    if res["dark"]:
        L.append("")
        L.append("   خوانده می‌شود، هرگز مسلح نشده:")
        for r in res["dark"]:
            L.append(f"     · {r['flag']}  ({r['n_readers']} خواننده)")
            for rd in r["readers"][:3]:
                L.append(f"         ↳ {rd}")
    if res["orphan_armed"]:
        L.append("")
        L.append("   مسلح ولی هیچ خواننده‌ای ندارد (تایپو؟ کدِ حذف‌شده؟):")
        for f in res["orphan_armed"]:
            L.append(f"     · {f}")
    if not res["dark"] and not res["orphan_armed"]:
        L.append("   ✅ هر فلگی که خوانده می‌شود مسلح است، و برعکس.")
    return "\n".join(L)


def card() -> str:
    """کارتِ «چه چیزی ساخته شده و نمی‌دود» — برای چشمِ مالک در تلگرام.

    چرا کارت و نه فقط CLI: تا امروز تنها راهِ دیدنِ این عدد اجرای دستیِ اسکریپت
    بود، و مالک از گوشی کار می‌کند. `capability_registry` هر ماژولی را که
    `card()` بی‌آرگومان داشته باشد **خودکار** پیدا می‌کند، پس این تابع بدونِ
    لمسِ `center.py` قابلیت را رو می‌آورد.

    هرگز مقدارِ هیچ فلگی چاپ نمی‌شود — فقط نام و شمار.
    """
    import html
    try:
        res = scan()
    except Exception as e:  # noqa: BLE001 — کارت هرگز مرکز را نمی‌کشد
        return f"🔦 <b>قابلیت‌های تاریک</b>\n▸ اسکن نشد: {html.escape(type(e).__name__)}"

    L = [f"🔦 <b>قابلیت‌های تاریک — {res['n_dark']} دروازه</b>",
         f"▸ روشن {res['n_flags'] - res['n_dark'] - res['n_partial'] - res['n_tuning']}"
         f" · تاریک {res['n_dark']} · جزئی {res['n_partial']} · تنظیمی {res['n_tuning']}",
         f"▸ منبع: {html.escape(res['live_source'])}"
         f" ({len(res['processes'])} پروسه)"]
    if res["live_source"] != "live":
        L.append("⚠️ snapshotِ بوت نیست — بعد از ری‌استارت دوباره بسنج.")
    if res["partial"]:
        L.append("")
        L.append("⚠️ <b>در بعضی پروسه‌ها روشن، بعضی نه:</b>")
        for r in res["partial"][:4]:
            L.append(f"▸ <code>{html.escape(r['flag'])}</code>")
    if res["dark"]:
        L.append("")
        L.append("<b>بیشترین کدِ خفته:</b>")
        for r in sorted(res["dark"], key=lambda z: -z["n_readers"])[:6]:
            L.append(f"▸ <code>{html.escape(r['flag'])}</code> — "
                     f"{r['n_readers']} خواننده")
    if res["orphan_armed"]:
        L.append("")
        L.append(f"<b>مسلح ولی بی‌خواننده ({len(res['orphan_armed'])}):</b> "
                 + "، ".join(html.escape(f) for f in res["orphan_armed"][:3]))
    L.append("")
    L.append("▸ نکنی: همین‌طور می‌ماند — کد هست، قابلیت نه.")
    return "\n".join(L)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    res = scan()
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
