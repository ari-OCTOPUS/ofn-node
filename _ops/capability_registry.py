"""capability_registry — هر چیزی که ارگانیسم می‌تواند نشان دهد، خودش پیدا می‌شود.

مسئله‌ای که این حل می‌کند
─────────────────────────
۲۵۰ ماژول در ارگانیسم هست و ۲۰ دستور در تلگرام. شمردنِ ۲۰۲۶-۰۷-۲۷: **۱۰** ماژول
تابعِ `card()` ِ بی‌آرگومان دارند — یعنی صریحاً برای چشمِ مالک ساخته شده‌اند و
هیچ ورودی‌ای هم لازم ندارند — ولی فقط **۳** تای آن‌ها از تلگرام قابلِ لمس بود.
هفت کارت وجود داشتند و هیچ‌کس نمی‌توانست بازشان کند.

(شمارشِ اولِ من ۱۶ گفت چون `card_delivery_ready` و هم‌خانواده‌هایش را هم می‌شمرد.
عددِ درست ۱۰ است — و دقیقاً همین‌جا معلوم شد چرا کشف باید نحوی باشد نه گرپی.)

و این یک اشتباهِ موردی نیست؛ یک **کژیِ ساختاری** است: هر توانایی باید دستی به
`center.py` سیم شود، پس هر ماژولِ تازه‌ای که ساخته می‌شود پیش‌فرضاً نامرئی است.
سطح ساختاراً از بدن عقب می‌ماند و شکاف با گذرِ زمان **بزرگ‌تر** می‌شود، نه کمتر.

پس به‌جای بستنِ ده شکاف، قاعده عوض می‌شود: هر ماژولی که `card()` بی‌آرگومان
داشته باشد **خودبه‌خود** در فهرست می‌آید. ماژولِ بعدی هم بدونِ لمسِ این فایل
دیده می‌شود.

چرا AST و نه import
───────────────────
کشف با پارسِ نحوی انجام می‌شود، نه با import. واردکردنِ ۲۵۰ ماژول برای دیدنِ
اینکه کدامشان `card()` دارند یعنی اجرای هر اثرِ جانبیِ import-time — از جمله
تماس‌های شبکه‌ای و نوشتنِ فایل. کشف باید ارزان و بی‌ضرر باشد؛ importِ واقعی فقط
برای همان یک کارتی که مالک خواسته.

مرزها
─────
· فقط `card()` **بی‌آرگومان**. کارتی که ورودی می‌خواهد دستورِ اختصاصیِ خودش را
  لازم دارد و این‌جا نمی‌آید.
· فقط داخلِ `_ops`. مسیرِ بیرونی هرگز import نمی‌شود.
· فقط از فهرستِ کشف‌شده. کلیدِ دلخواهِ کاربر هرگز به `import` نمی‌رسد.
· فقط‌خواندنی. هیچ کارتی از این‌جا چیزی را اجرا نمی‌کند.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = "capability-registry.v1"

# پوشه‌هایی که اسکن می‌شوند. `tests` عمداً نیست (کارتِ تست کارتِ مالک نیست) و
# `_code`/`.git` طبقِ قانونِ اساسی هرگز.
SCAN_DIRS = ("", "telegram_center", "doctor", "heart", "outcomes", "cortex",
             "budget", "legs", "neural", "chord", "tg")
_SKIP_PARTS = {"tests", "_code", ".git", "__pycache__", "_Archive", "_Duplicates"}

# عنوانِ فارسیِ خوانا برای ماژول‌هایی که خودشان اعلام نمی‌کنند. ماژولِ تازه
# می‌تواند `CARD_TITLE = "..."` بگذارد و این جدول را دور بزند.
_TITLES = {
    "decision_gate": "⚖️ گیتِ تصمیم",
    "trajectory_log": "🧭 دفترِ مسیر",
    "teacher_loop": "🎓 حلقهٔ معلم",
    "stuck_money": "💰 پرداختِ نیمه‌کاره",
    "autonomy_grant": "🔓 مرزِ اختیار",
    "initiative": "💬 ابتکار",
    "verdict_probe": "🗳 رأی‌های منقضی",
    "identity_equations": "🧬 معادلاتِ هویت",
    "blackbox_map": "📦 نقشهٔ جعبه‌سیاه",
    "blackbox_scanner": "🔦 اسکنِ جعبه‌سیاه",
    "self_patch": "🩹 وصلهٔ خودکار",
    "operator_doctrine": "📖 دکترینِ اپراتور",
    "mirror_room": "🪞 اتاقِ آینه",
    "negotiate": "🤝 مذاکره",
    "ask_brain": "🧠 پرسش از مغز",
    "pending_card_recovery": "♻️ بازیابیِ کارت",
    "capability_registry": "🗂 فهرستِ توانایی‌ها",
}

_cache: "dict | None" = None


def _zero_arg_card(path: Path) -> "dict | None":
    """آیا این فایل `card()` بی‌آرگومان دارد؟ فقط پارسِ نحوی — هیچ اجرایی."""
    try:
        # ماژول‌های دیگران ممکن است escapeِ نامعتبر داشته باشند؛ هشدارشان
        # خروجیِ کشف را آلوده می‌کند و ربطی به کارِ ما ندارد.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text("utf-8"))
    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
        return None
    title = None
    flag = ""
    has_card = False
    for node in tree.body:                       # فقط سطحِ ماژول
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "card":
            a = node.args
            required = [x for x in a.args if x.arg not in ("self", "cls")]
            n_req = len(required) - len(a.defaults)
            kw_req = sum(1 for d in a.kw_defaults or [] if d is None)
            if n_req <= 0 and kw_req <= 0:
                has_card = True
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if not isinstance(t, ast.Name):
                    continue
                if t.id == "CARD_TITLE" and isinstance(node.value, ast.Constant):
                    title = str(node.value.value)
                elif t.id == "FLAG" and isinstance(node.value, ast.Constant):
                    flag = str(node.value.value)
    if not has_card:
        return None
    return {"title": title, "flag": flag}


def discover(refresh: bool = False) -> list:
    """فهرستِ توانایی‌هایی که کارت دارند. مرتب بر اساسِ عنوان.

    هر ردیف: {key, module, path, title, flag, flag_on}. `flag_on` می‌گوید این
    کارت الان چیزِ واقعی نشان می‌دهد یا فقط «خاموشم» — تفاوتی که مالک باید
    **قبل** از بازکردنش بداند."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    out = []
    seen = set()
    for sub in SCAN_DIRS:
        d = _HERE / sub if sub else _HERE
        if not d.is_dir():
            continue
        try:
            files = sorted(d.glob("*.py"))
        except OSError:
            continue
        for f in files:
            if set(f.parts) & _SKIP_PARTS or f.name.startswith("test_"):
                continue
            info = _zero_arg_card(f)
            if info is None:
                continue
            key = f.stem
            if key in seen:
                continue
            seen.add(key)
            flag = info["flag"]
            out.append({
                "key": key,
                "module": key,
                "path": str(f.relative_to(_HERE)).replace("\\", "/"),
                "title": info["title"] or _TITLES.get(key, key),
                "flag": flag,
                "flag_on": (True if not flag else
                            str(os.environ.get(flag, "")).strip().lower()
                            in ("1", "true", "yes", "on")),
            })
    out.sort(key=lambda r: r["title"])
    _cache = out
    return out


def render(key: str) -> str:
    """کارتِ یک توانایی. کلید **باید** از فهرستِ کشف‌شده باشد.

    اجازهٔ import فقط از allowlistِ مشتق از اسکن می‌آید — نه از ورودیِ کاربر.
    بدونِ این، یک `key` ِ ساختگی می‌توانست هر ماژولی را وارد کند."""
    k = str(key or "").strip()
    row = next((r for r in discover() if r["key"] == k), None)
    if row is None:
        return "❔ چنین توانایی‌ای نیست."
    try:
        import importlib
        pkg = Path(row["path"]).parent.as_posix()
        name = row["module"] if pkg in (".", "") else f"{pkg.replace('/', '.')}.{row['module']}"
        try:
            mod = importlib.import_module(name)
        except ImportError:
            # بعضی زیرپوشه‌ها پکیج نیستند؛ مسیرشان مستقیم اضافه می‌شود.
            p = str((_HERE / pkg).resolve())
            if p not in sys.path:
                sys.path.insert(0, p)
            mod = importlib.import_module(row["module"])
        body = mod.card()
    except Exception as e:  # noqa: BLE001 — کارتِ خراب نباید منو را بکشد
        return (f"⚠️ «{_esc(row['title'])}» باز نشد: {type(e).__name__}\n"
                "▸ نکنی: هیچ — بقیهٔ کارت‌ها سالم‌اند.")
    out = str(body) if body else "▸ این توانایی الان چیزی برای گفتن ندارد."

    # کارتِ خاموش تا امروز بن‌بست بود: می‌گفت «خاموشم» و تمام. مالک می‌دید که
    # چیزی هست ولی هیچ راهی نداشت. حالا که عبارتِ مجوز واقعاً جایی می‌نشیند
    # (owner_auth_log)، می‌شود دقیقاً همان جمله را نشانش داد — پس مسیر کامل
    # می‌شود: می‌بینم ← می‌دانم چه بنویسم ← می‌نویسم ← ثبت می‌شود.
    #
    # عمداً **جمله** نشان داده می‌شود نه دکمه: دکمه یعنی یک تپ فلگ را بچرخاند،
    # و مسلح‌کردن عملِ استقرار است نه پیام.
    if row["flag"] and not row["flag_on"]:
        out += ("\n\n🔑 برای روشن‌کردنش این را بنویس:\n"
                f"<code>OWNER_AUTH: ARM FLAG {_esc(row['flag'])}</code>\n"
                "▸ ثبت می‌شود؛ اجرا با تو یا ایجنتی که کار را می‌کند.")
    return out


def _esc(s) -> str:
    import html
    return html.escape(str(s if s is not None else ""))


def coverage() -> dict:
    """چند درصدِ کارت‌های ارگانیسم الان محتوای واقعی دارند.

    این عدد خودش یک واقعیت دربارهٔ سیستم است و در تصویرِ خودشناسی می‌نشیند:
    ارگانیسمی که نمی‌داند چقدر از خودش برای مالک دیدنی است، خودآگاه نیست."""
    rows = discover()
    live = [r for r in rows if r["flag_on"]]
    return {"schema": SCHEMA, "total": len(rows), "live": len(live),
            "dark": len(rows) - len(live),
            "dark_keys": [r["key"] for r in rows if not r["flag_on"]]}


def card() -> str:
    """کارتِ خودِ فهرست — «چه چیزهایی می‌توانم نشانت بدهم»."""
    rows = discover()
    c = coverage()
    lines = [f"🗂 <b>{c['total']} چیز می‌توانم نشانت بدهم</b>"]
    if c["dark"]:
        lines.append(f"▸ {c['live']} تای‌شان الان محتوای واقعی دارند؛ "
                     f"{c['dark']} تا پشتِ فلگِ خاموش‌اند و فقط می‌گویند «خاموشم».")
    lines.append("")
    for r in rows:
        mark = "" if r["flag_on"] else " <i>(خاموش)</i>"
        lines.append(f"▸ {_esc(r['title'])}{mark}")
    lines += ["", "▸ نکنی: هیچ — همه‌شان فقط‌خواندنی‌اند."]
    return "\n".join(lines)


def keyboard(page: int = 0, per: int = 8) -> list:
    """دکمه‌های فهرست، صفحه‌بندی‌شده. `x:<key>` یک کارت را باز می‌کند."""
    rows = discover()
    try:
        p = max(0, int(page))
    except (TypeError, ValueError):
        p = 0
    off = p * per
    chunk = rows[off:off + per]
    kb = []
    for i in range(0, len(chunk), 2):
        pair = chunk[i:i + 2]
        kb.append([{"text": (r["title"] if r["flag_on"] else f"{r['title']} ⚪")[:38],
                    "callback_data": f"x:c:{r['key']}"[:64]} for r in pair])
    nav = []
    if off > 0:
        nav.append({"text": "◀️ قبلی", "callback_data": f"x:p:{p - 1}"})
    if off + per < len(rows):
        nav.append({"text": f"بعدی ({len(rows) - off - len(chunk)}) ▶️",
                    "callback_data": f"x:p:{p + 1}"})
    if nav:
        kb.append(nav)
    kb.append([{"text": "🔙 منو", "callback_data": "mn:menu"}])
    return kb


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps({**coverage(),
                      "rows": [{k: r[k] for k in ("key", "title", "flag", "flag_on")}
                               for r in discover()]},
                     ensure_ascii=False, indent=1))
