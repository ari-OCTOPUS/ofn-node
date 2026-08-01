"""orphan_scan — چه چیزهایی ساخته شده‌اند و به هیچ‌جا وصل نیستند.

چرا این یک تواناییِ خودآگاهی است
────────────────────────────────
اسکنِ ۲۰۲۶-۰۷-۲۷ (شش ایجنت + راستی‌آزماییِ متخاصم) ۲۲ توانایی را تأیید کرد که
از تلگرام دست‌نیافتنی‌اند — و برای بخشِ بزرگی از آن‌ها دلیل «فلگِ خاموش» نبود،
بلکه چیزِ بدتری بود: **هیچ صداکننده‌ای در کلِ مخزن نداشتند**. نگهبانِ افتِ
سرمایه، دروازهٔ مسلح‌کردن، افزونهٔ ناظر — همه نوشته شده، تست شده، و به هیچ‌جا
وصل نشده.

ارگانیسمی که نمی‌داند کدام اندامش به بدن وصل نیست، خودآگاه نیست. این ماژول
همان را می‌شمارد — و چون از **خودِ کد** می‌شمارد، نمی‌تواند کهنه شود.

روش، و صادق‌بودن دربارهٔ حدودش
─────────────────────────────
پارسِ نحوی، بدونِ import. یک ماژول «وصل» شمرده می‌شود اگر هر یک از این‌ها باشد:
  · جایی import شود (`import x` یا `from x import …`)
  · نامش به‌شکلِ رشته جایی بیاید (importِ پویا با `importlib`)
  · یکی از نام‌های عمومی‌اش جای دیگری صدا زده شود

**این روش محافظه‌کار است و عمداً کم‌گزارش می‌دهد**: هر ابهام به نفعِ «وصل» حل
می‌شود. پس فهرستِ خروجی کفِ مسئله است، نه سقفش — چیزی که این‌جا می‌آید، تقریباً
حتماً یتیم است.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = "orphan-scan.v1"
CARD_TITLE = "🔌 ساخته‌شده ولی وصل‌نشده"
_SKIP = {"tests", "_code", ".git", "__pycache__", "_Archive", "_Duplicates",
         "eval", "smoke"}

# ماژول‌هایی که یتیم‌بودنشان طبیعی است — نقطهٔ ورودی یا ابزارِ دستی‌اند.
# ۰۷-۳۱: `center` اضافه شد — مرکزِ تلگرام با `python center.py` (bat/schtask)
# بالا می‌آید و هیچ importer ای ندارد؛ تا وقتی شاهدِ رشته‌ایِ شل او را «وصل»
# می‌شمرد این دیده نمی‌شد. entry point ِ بی‌importer یتیم نیست.
_EXPECTED_STANDALONE = re.compile(
    r"^(organism|run_|smoke_|.*_cli|setup|conftest|__init__|owner_ping|center$)")

# نشانه‌های اینکه یتیم‌بودن **مهم** است: پول، ایمنی، یا گیت.
_WEIGHTY = re.compile(
    r"(drawdown|guard|gate|watchdog|halt|kill|budget|money|spend|payment|"
    r"arm|breaker|limit|safety|invoice|revenue|recover)", re.I)


def _files() -> list:
    out = []
    for f in sorted(_HERE.rglob("*.py")):
        if set(f.parts) & _SKIP or f.name.startswith("test_"):
            continue
        out.append(f)
    return out


def _public_names(tree) -> set:
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not n.name.startswith("_"):
                out.add(n.name)
    return out


def scan() -> dict:
    """{orphans: [...], total, checked}. فقط خواندن."""
    import warnings
    files = _files()
    trees, texts = {}, {}
    for f in files:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                src = f.read_text("utf-8")
                trees[f] = ast.parse(src)
                texts[f] = src
        except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
            continue

    # هر ارجاعی که از **فایلِ دیگری** می‌آید
    # ۲۰۲۶-۰۸-۰۱ — `called` نامِ **برهنه** را می‌گرفت و همان یک نقصِ کور بود:
    # هر فایلی که تابعی به نامِ `verdict` صدا می‌زد، `drawdown_guard` را (که
    # نامِ عمومی‌اش `verdict` است) «متصل» می‌کرد. حالا شاهد باید به خودِ ماژول
    # بسته باشد: `attr_called` سه‌تایی (فایل، شیء، صفت) است، پس فقط
    # `drawdown_guard.verdict(...)` شاهد است نه هر `verdict(...)`ی.
    imported, attr_called, quoted = set(), set(), set()
    for f, tree in trees.items():
        # ۰۷-۳۱ (کورِ اسکن که test_orphan_scan رو کرد): رشتهٔ ثابت فقط وقتی
        # شاهدِ «اتصال» است که همان فایل واقعاً importِ پویا انجام دهد
        # (import_module/__import__). وگرنه نامِ ماژول در denylist ِ
        # scope_guard — که یعنی «این ماژول هرگز هدف نشود» — به‌عنوانِ صداکننده
        # شمرده می‌شد و یتیمِ واقعی (arm_gate) از گزارش می‌افتاد: حفاظت ≠ سیم.
        dyn_import = any(
            isinstance(n, ast.Call) and (
                getattr(n.func, "id", None) == "__import__"
                or getattr(n.func, "attr", None) == "import_module")
            for n in ast.walk(tree))
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    imported.add((f, a.name.split(".")[-1]))
            elif isinstance(n, ast.ImportFrom) and n.module:
                imported.add((f, n.module.split(".")[-1]))
                # شکلِ چهارم (درسِ ثبت‌شدهٔ reachability): `from pkg import mod`
                # خودِ mod را import می‌کند ولی فقط pkg ثبت می‌شد — center با
                # همین شکل صدا می‌خورد و بعد از سفت‌شدنِ شاهدِ رشته‌ای، هشدارِ
                # کاذبِ «یتیم» گرفت. نام‌های وارد‌شده هم شاهدِ اتصال‌اند.
                for a in n.names:
                    imported.add((f, a.name))
            elif isinstance(n, ast.Call):
                # فقط تماسِ **صفتی** روی یک نام: obj.attr(...) — و obj باید
                # همان نامِ ماژول (یا aliasِ importش) باشد تا شاهد حساب شود.
                fn = n.func
                if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                    attr_called.add((f, fn.value.id, fn.attr))
            elif dyn_import and isinstance(n, ast.Constant) \
                    and isinstance(n.value, str):
                v = n.value.strip()
                if v and len(v) < 60:
                    quoted.add((f, v.split(".")[-1]))

    orphans = []
    for f, tree in trees.items():
        stem = f.stem
        if _EXPECTED_STANDALONE.match(stem):
            continue
        pub = _public_names(tree)
        if not pub:
            continue
        others = [g for g in trees if g != f]
        wired = any(
            (g, stem) in imported or (g, stem) in quoted or
            any((g, stem, p) in attr_called for p in pub)
            for g in others)
        if wired:
            continue
        orphans.append({
            "module": str(f.relative_to(_HERE)).replace("\\", "/"),
            "public": sorted(pub)[:6],
            "lines": len(texts.get(f, "").splitlines()),
            "weighty": bool(_WEIGHTY.search(stem) or _WEIGHTY.search(" ".join(pub))),
        })
    orphans.sort(key=lambda r: (not r["weighty"], -r["lines"]))
    return {"schema": SCHEMA, "checked": len(trees),
            "orphans": orphans, "total": len(orphans),
            "weighty": sum(1 for r in orphans if r["weighty"])}


def card() -> str:
    """کارت — و صادق دربارهٔ اینکه این فهرست کف است نه سقف."""
    import html
    r = scan()
    if not r["orphans"]:
        return ("🔌 <b>هیچ اندامِ وصل‌نشده‌ای پیدا نشد</b>\n"
                "▸ نکنی: هیچ.")
    lines = [f"🔌 <b>{r['total']} ماژول ساخته شده و به هیچ‌جا وصل نیست</b>",
             f"▸ {r['weighty']} تای‌شان دربارهٔ پول یا ایمنی‌اند.",
             ""]
    for o in r["orphans"][:10]:
        mark = "⚠️ " if o["weighty"] else "▸ "
        lines.append(f"{mark}<code>{html.escape(o['module'])}</code> "
                     f"({o['lines']} خط)")
    if r["total"] > 10:
        lines.append(f"▸ … و {r['total'] - 10} تای دیگر")
    lines += ["",
              "<b>این فهرست کف است نه سقف</b> — روش عمداً محافظه‌کار است و هر "
              "ابهام را به نفعِ «وصل» حل می‌کند. پس چیزی که این‌جا آمده تقریباً "
              "حتماً یتیم است.",
              "",
              "▸ نکنی: هیچ — این فقط شمارش است."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    r = scan()
    print(json.dumps({k: r[k] for k in ("schema", "checked", "total", "weighty")},
                     ensure_ascii=False))
    for o in r["orphans"][:20]:
        print(f"  {'⚠️' if o['weighty'] else '  '} {o['module']:44s} {o['lines']:5d} خط  {o['public'][:3]}")
