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
  · جایی import شود (`import x` · `from x import …` · `from pkg import x`)
  · نامش به‌شکلِ رشته در فایلی بیاید که واقعاً importِ پویا می‌کند
  · یکی از نام‌های عمومی‌اش **روی خودش** صدا زده شود (`x.foo()`، نه هر `foo()`)
  · ۰۸-۰۳ — `card()` ِ بی‌آرگومان داشته باشد و داخلِ `SCAN_DIRS` ِ
    `capability_registry` باشد: آن رجیستری خودش پیدایش می‌کند و `center.py`
    رندرش می‌کند، پس از تلگرام قابلِ لمس است حتی با صفر importer
  · ۰۸-۰۳ — از یک `.bat`/`.cmd`/`.ps1` با نامِ `x.py` اجرا شود (نقطهٔ ورود)

دو موردِ آخر تا ۰۸-۰۳ مدل نمی‌شدند و ~۳۱ هشدارِ کاذب می‌ساختند — از جمله
`watchdog`، `miniapp_gateway`، `budget_judge`، `dark_capabilities` و **خودِ این
ماژول**. آشکارسازی که خودش را یتیم اعلام کند، خاموش می‌شود.

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
         # union از لِینِ موازی (۰۸-۰۱): `.claude` ~۵.۵GB و ۶۷k فایل در
         # ۱۸ worktree است که ۹۶٪ رونوشت‌اند — اسکنشان هم کند است هم
         # نتیجه را با کپی‌های خودمان آلوده می‌کند.
         ".claude", "worktrees",
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


# ۰۸-۰۳ — اندام‌های تولیدی که نامشان با `test_` شروع می‌شود.
# `_files()` هر `test_*` را رد می‌کند (درست، برای کاندیداها)، ولی این‌ها
# **صداکننده**اند: `test_cycle.py` حلقهٔ آزمونِ ۷روزه است (رأیِ مالک ۰۷-۳۰،
# کادنس و دفترِ خودش) و `goal_action_bridge` / `receipt_critic` /
# `cycle_evaluator` را صدا می‌زند. تا وقتی این فایل از جمع‌آوریِ ارجاع بیرون
# بود، آن سه «یتیم» گزارش می‌شدند در حالی که مسلح و زنده‌اند.
#
# تفکیکِ کلیدی: «کاندیدِ یتیمی» و «منبعِ ارجاع» دو فهرستِ متفاوت‌اند.
_PROD_TEST_NAMED = {"test_cycle.py"}


def _files() -> list:
    out = []
    for f in sorted(_HERE.rglob("*.py")):
        # ⚠️ نسبت به ریشهٔ اسکن، نه مسیرِ مطلق. لِینِ موازی `.claude` و
        # `worktrees` را به _SKIP اضافه کرد (درست: ۵.۵GB رونوشت) ولی با
        # parts ِ مطلق، هر اجرایی از داخلِ یک worktree خودش را حذف می‌کرد
        # — `checked: 0` و گزارشِ «صفر یتیم»، یعنی سکوتی که سلامت خوانده
        # می‌شود. مسیرِ نسبی در هر دو درخت درست کار می‌کند.
        try:
            _rel_parts = set(f.relative_to(_HERE).parts)
        except ValueError:
            _rel_parts = set(f.parts)
        if _rel_parts & _SKIP or f.name.startswith("test_"):
            continue
        out.append(f)
    return out


def _caller_files() -> list:
    """فایل‌هایی که برای **یافتنِ ارجاع** خوانده می‌شوند.

    اَبَرمجموعهٔ کاندیداها: به‌علاوهٔ اندام‌های تولیدیِ `test_`-نام. این‌ها
    کاندیدِ یتیمی نیستند (نامشان تستی است و `t_forbidden_paths_are_never_scanned`
    درست می‌گوید تستی نباید در فهرست بیاید) ولی صداکنندهٔ واقعی‌اند."""
    out = _files()
    seen = {f.resolve() for f in out}
    for name in _PROD_TEST_NAMED:
        p = _HERE / name
        if p.is_file() and p.resolve() not in seen:
            out.append(p)
    return out


def _public_names(tree) -> set:
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not n.name.startswith("_"):
                out.add(n.name)
    return out


def _card_scan_dirs() -> tuple:
    """`SCAN_DIRS` ِ capability_registry — با **پارس**، نه import.

    عمداً از خودِ فایل خوانده می‌شود نه رونوشتِ دستی: اگر روزی پوشه‌ای به آن
    رجیستری اضافه شود، این‌جا خودبه‌خود درست می‌ماند. importش هم ممنوع است —
    `t_the_scanner_imports_nothing_it_scans` هر ماژولِ تازه در `sys.modules` را
    قرمز می‌کند."""
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse((_HERE / "capability_registry.py").read_text("utf-8"))
    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
        return ()
    for n in tree.body:
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "SCAN_DIRS":
                try:
                    return tuple(str(x) for x in ast.literal_eval(n.value))
                except (ValueError, SyntaxError, TypeError):
                    return ()
    return ()


def _has_zero_arg_card(tree) -> bool:
    """همان قاعدهٔ `capability_registry._zero_arg_card` — کارتی که ورودی بخواهد
    خودکار کشف نمی‌شود، پس شاهدِ اتصال هم نیست."""
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != "card":
            continue
        a = node.args
        required = [x for x in a.args if x.arg not in ("self", "cls")]
        n_req = len(required) - len(a.defaults)
        kw_req = sum(1 for d in a.kw_defaults or [] if d is None)
        if n_req <= 0 and kw_req <= 0:
            return True
    return False


def _card_discoverable(trees) -> set:
    """ماژول‌هایی که رجیستریِ توانایی‌ها خودش پیدایشان می‌کند.

    مرزِ `SCAN_DIRS` جدی است: `card()` بیرونِ آن پوشه‌ها **کشف نمی‌شود**، پس
    شاهدِ اتصال نیست. اگر این را نادیده بگیریم، دقیقاً همان اشتباهِ برعکس
    می‌شود — یتیمِ واقعی را «وصل» اعلام کردن."""
    dirs = _card_scan_dirs()
    if not dirs:
        return set()
    out = set()
    for f, tree in trees.items():
        try:
            rel_dir = f.relative_to(_HERE).parent.as_posix()
        except ValueError:
            continue
        if rel_dir == ".":
            rel_dir = ""
        if rel_dir in dirs and _has_zero_arg_card(tree):
            out.add(f.stem)
    return out


def _script_launched() -> set:
    """ماژول‌هایی که یک `.bat`/`.cmd`/`.ps1` اجرایشان می‌کند — نقطهٔ ورود."""
    out = set()
    for pattern in ("*.bat", "*.cmd", "*.ps1"):
        for s in _HERE.rglob(pattern):
            try:
                rel_parts = set(s.relative_to(_HERE).parts)
            except ValueError:
                rel_parts = set(s.parts)
            if rel_parts & _SKIP:
                continue
            try:
                txt = s.read_text("utf-8", errors="replace")
            except OSError:
                continue
            # `%~dp0acceptance_journey.py` بدونِ این پاک‌سازی به
            # `dp0acceptance_journey` می‌خورد (رقم هم `\w` است) و یک نقطهٔ
            # ورودِ واقعی «یتیم» گزارش می‌شد.
            txt = re.sub(r"%~?[a-zA-Z]*\d*%?", " ", txt)
            for m in re.finditer(r"([A-Za-z_][\w]*)\.py", txt):
                out.add(m.group(1))
    return out


def scan() -> dict:
    """{orphans: [...], total, checked}. فقط خواندن."""
    import warnings
    files = _files()
    candidates = set(files)

    # `ref_trees` اَبَرمجموعه است: کاندیداها + اندام‌های تولیدیِ `test_`-نام.
    # کاندیدِ یتیمی از `candidates` می‌آید، شاهدِ ارجاع از `ref_trees`.
    trees, texts = {}, {}
    for f in _caller_files():
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
            elif isinstance(n, ast.ImportFrom):
                # ۰۸-۰۳ — گاردِ قبلی `and n.module` بود، پس `from . import X`
                # (که `n.module is None` دارد) **کلِ شاخه** را می‌انداخت. چهار
                # ماژولِ زنده از همین راه یتیمِ کاذب شدند: `emit` از
                # `epistemics/__init__.py:7`، و `contradiction`/`novelty`/
                # `opportunity` از `world_discovery/octopus_adapter.py:24`.
                if n.module:
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

    # دو مکانیزمِ صداکننده که تا ۰۸-۰۳ مدل نمی‌شدند. هر دو **مستقل از importer**
    # اند، پس ماژولی که هیچ‌کس importش نمی‌کند باز هم می‌تواند کاملاً زنده باشد.
    card_ok = _card_discoverable(trees)
    cli_ok = _script_launched()

    orphans = []
    for f, tree in trees.items():
        # اندامِ `test_`-نام صداکننده است ولی کاندیدِ یتیمی نیست.
        if f not in candidates:
            continue
        stem = f.stem
        if _EXPECTED_STANDALONE.match(stem):
            continue
        pub = _public_names(tree)
        if not pub:
            continue
        if stem in card_ok or stem in cli_ok:
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
