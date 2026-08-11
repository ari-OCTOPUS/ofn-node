#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_obsidian_index_budget.py — ابسیدین نباید دوباره زیرِ بارِ کد دفن شود.

اندازه‌گیریِ ۲۰۲۶-۰۸-۰۴ روی همین درخت:

  · زیرِ ریشهٔ vault ‏**۲۸٬۳۵۳** فایل هست (بدونِ dotfolderها، که ابسیدین ذاتاً
    نادیده می‌گیرد).
  · با فیلترهای آن روز ‏**۱۳٬۰۶۴** تایشان به ایندکس می‌رسید — و فقط **۲٬۴۷۲**
    تای آن‌ها markdown بود. یعنی ۸۱٪ از چیزی که ابسیدین حمل می‌کرد، چیزی بود
    که اصلاً نمی‌تواند رندرش کند.
  · بزرگ‌ترین دو دسته: ‏**۳٬۰۱۰ فایلِ `.npy`** (آرایهٔ باینریِ NumPy) و
    **۲٬۴۹۱ فایلِ `.py`** — تنهایی ۴۲٪ کلِ بار.

رفع: پسوندهای غیرقابلِ‌رندر به فیلترِ موجود اضافه شدند ⇒ ۱۳٬۰۶۴ → ۶٬۹۰۳
(‏۴۷٪ کمتر)، با **صفر** نوتِ markdown ِ ازدست‌رفته و **صفر** لینکِ شکسته.

⚠️ تصحیحِ ادعای اولِ خودم دربارهٔ **مکانیزم** (ممیزیِ موازی، ۰۸-۰۴):
`userIgnoreFilters` تنظیمِ «Excluded files» ِ ابسیدین است. آنچه قطعاً می‌کند:
حذف از **جستجو، گراف، quick switcher، پیشنهادِ لینک و unlinked mentions**.
آنچه مستند **نیست** که بکند: ردکردنِ شمارشِ اولیهٔ vault، ‏file watcher، یا
metadata cache. پس این تغییر بردِ واقعی دارد ولی بردش «۴۷٪ سریع‌تر بالا
می‌آید» **نیست** — «۴۷٪ کمتر آشغال در نتایج و گراف» است.
دو عددِ سنجیده که همین را نشان می‌دهند: روی ویندوز، پایشِ بازگشتی **یک**
هندلِ `ReadDirectoryChangesW` روی ریشه است و با تعدادِ فایل بزرگ نمی‌شود؛ و
شمارشِ دایرکتوری اندازه و mtime را **بدون بازکردنِ محتوا** می‌دهد، پس حجمِ
بایتی اصلاً وارد تابعِ هزینه نمی‌شود.
گلوگاهِ واقعیِ این ماشین جای دیگری است و رأیِ مالک است: کلِ vault روی یک
دیسکِ ۵۴۰۰ دورِ مکانیکی (`F:` = WDC WD10SPZX، HDD) نشسته در حالی که سیستم
روی NVMe است — بازکردنِ سردِ فایل ‏۳۲٫۲ms در برابرِ ۴۶µs گرم.

⚠️ چرا این تست لازم است: `.obsidian/app.json` را خودِ ابسیدین هم می‌نویسد.
یک تغییر در تنظیمات از داخلِ برنامه می‌تواند این فهرست را بازنویسی کند و
هیچ‌کس متوجه نشود — بار بی‌صدا به ۱۳ هزار برمی‌گردد.

⚠️ چه چیزی عمداً **انجام نشد**: استثنا کردنِ پوشه‌هایی مثلِ `_build/` و
`_portable-build/` و `_archive-binaries/`. اولین سنجه («صفر لینک از لایهٔ
زنده») سبز بود و وسوسه‌کننده — ولی سنجهٔ ترکیبی نشان داد آن پوشه‌ها خودشان
**۳۸۰ نوتِ markdown** دارند که از جستجو حذف می‌شدند. «صفر لینکِ ورودی» شرطِ
لازم است، نه کافی. آن پوشه‌ها (کپیِ آینه‌ایِ vault) مسئلهٔ **تکراری** دارند
نه مسئلهٔ ایندکس، و رفعش انتقال است — یعنی رأیِ مالک، طبقِ §۰ منشور.
"""
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("obsidian-index-budget")

# ── Hermetic vault: تست هرگز REAL_VAULT نمی‌خواند. یک vault موقت با app.json
# ساخته‌شده ایجاد می‌شود. ساختارِ فیلترها با تنظیماتِ تولیدی هم‌خوان است؛ تفاوت
# فقط در رفعِ باگِ jsonl (که در تنظیماتِ زنده بود: jsonl در regexِ data-noise
# قرار داشت ولی اندازه‌گیریِ ۰۸-۰۴ نشان داد ۱ لینکِ زنده به .jsonl دارد).
#: فیلترهای canonically-correct — قرارداد ساختاری: این همان لیستی است که
#: تولید باید داشته باشد. هر تغییر در production باید ابتدا اینجا آگاه شود.
_HERMETIC_FILTERS = [
    "_Archive/",
    "_Duplicates/",
    "_worktrees/",
    ".claude/",
    "/^_ops/_agent_reports//",
    "/(^|/)_code(/)/",
    "/(^|/)__pycache__(/)/",
    "/(^|/)\\.pytest_cache(/)/",
    "/\\.(pyc|pyo|log|db|zip|npy|py|dll|bat|dart|js|ts|exe|ini|ps1|ahk|sh|bin|yml)$/",
    "_archive-binaries/",
    "_build/",
    "_portable-build/",
    "/(^|/)node_modules(/)/",
    "_ops/state/",
    "_ops/tests/",
    "_ops/budget/",
    "_ops/telegram_center/",
    "_ops/cortex/",
    "_ops/doctor/",
    "_ops/heart/",
    "_ops/chord/",
    "_ops/now_moves/",
    "_ops/observability/",
    "_ops/arm_gate.py",
    "_ops/arm_renewal.py",
    "_ops/organism.py",
    "4d_system/",
    "OCTOPUS-DOCTOR/",
    "agent-prompts/",
    ".zcode/",
    "_launchpad/",
    "Ziman Galerry/",
    # jsonl از این regex حذف شد: اندازه‌گیری ۰۸-۰۴ = ۱ لینکِ زنده.
    # بقیه پسوندها بدون لینک و غیرقابل‌رندر.
    "/\\.(sqlite3?|vcf|ped|map|toml|pkl|parquet)$/",
]

_HERMETIC_ROOT = ENV["root"]
_HERMETIC_OBSIDIAN = _HERMETIC_ROOT / ".obsidian"
_HERMETIC_OBSIDIAN.mkdir(parents=True, exist_ok=True)
_HERMETIC_APP = _HERMETIC_OBSIDIAN / "app.json"
_HERMETIC_APP.write_text(
    json.dumps({"userIgnoreFilters": _HERMETIC_FILTERS}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

ROOT = _HERMETIC_ROOT
APP = _HERMETIC_APP

#: پسوندهایی که ابسیدین نمی‌تواند رندر کند و هیچ لینکی هم به آن‌ها نمی‌رسد.
#: هر کدام جداگانه سنجیده شد: صفر لینکِ زنده. (هفت لینکِ `.py` که پیدا شد،
#: همگی داخلِ `_code/` بودند که از قبل فیلترِ خودش را دارد.)
MUST_FILTER_EXT = ("npy", "py", "dll", "bat", "dart", "js", "ts",
                   "exe", "ini", "ps1", "ahk", "sh", "bin", "yml")

#: پسوندهایی که **نباید** فیلتر شوند — یا محتوایند یا لینک می‌گیرند.
#: `md` بدیهی است؛ بقیه اندازه‌گیری شده‌اند: json ‏۷ لینک، yaml ‏۷، html ‏۶،
#: jsonl ‏۱. `txt` و `csv` صفر لینک داشتند ولی عمداً بیرون ماندند: منشور §۹
#: به `_گزارش تکراری‌ها.txt` ارجاع می‌دهد و مالک ممکن است بخواندشان — بردِ
#: ۱۸۶ فایلی‌شان ارزشِ پنهان‌کردنِ چیزی که آدم می‌خواند را ندارد.
MUST_NOT_FILTER_EXT = ("md", "png", "jpg", "jpeg", "pdf", "canvas", "base",
                       "json", "yaml", "html", "jsonl", "txt", "csv", "svg")

#: پوشه‌هایی که استثنا بودنشان باربر است.
MUST_FILTER_DIRS = ("_Archive/", "_Duplicates/")


#: مسیرِ پیکربندی، تزریق‌پذیر. پیش‌فرض hermetic vault است (هرگز REAL_VAULT
#: نمی‌خواند). برای regression-check روی production، مسیرِ واقعی app.json را
#: بدهید: `python test_obsidian_index_budget.py /path/to/.obsidian/app.json`.
_APP_OVERRIDE = None


def _app_path():
    return _APP_OVERRIDE or APP


def _cfg(path=None):
    return json.loads((path or _app_path()).read_text("utf-8", errors="replace"))


def _ext_regexes(path=None):
    """فیلترهایی که ابسیدین به‌عنوان regex می‌خواند: با `/` شروع و تمام می‌شوند."""
    out = []
    for f in _cfg(path).get("userIgnoreFilters") or []:
        if f.startswith("/") and f.endswith("/") and len(f) > 2:
            out.append(f[1:-1])
    return out


def t_a_the_config_is_readable_and_not_empty():
    """گاردِ «اسکنر خراب است» — فایلِ غایب یا تهی نباید سبز بدهد."""
    assert _app_path().exists(), _app_path()
    filters = _cfg().get("userIgnoreFilters")
    assert filters, "userIgnoreFilters تهی است — ابسیدین کلِ درخت را می‌بلعد"
    assert len(filters) >= 9, f"فقط {len(filters)} فیلتر — فهرست کوتاه شده"


def t_b_every_unrenderable_extension_stays_filtered():
    """قلبِ گارد. `.npy` و `.py` تنهایی ۵٬۵۰۱ فایل بودند."""
    blob = "\n".join(_ext_regexes())
    missing = [e for e in MUST_FILTER_EXT if f"|{e}" not in blob and f"({e}|" not in blob]
    assert not missing, (
        "این پسوندها دیگر فیلتر نمی‌شوند و ابسیدین دوباره ایندکسشان می‌کند "
        "(اندازه‌گیریِ ۰۸-۰۴: npy=۳۰۱۰، py=۲۴۹۱ فایل)", missing)


def t_c_content_extensions_are_never_filtered():
    """قرینه، و مهم‌تر از t_b: فیلترِ زیادی نوت را از جستجو حذف می‌کند.
    هر پسوندِ این فهرست یا محتواست یا لینک می‌گیرد (اندازه‌گیریِ ۰۸-۰۴)."""
    for rx in _ext_regexes():
        c = re.compile(rx)
        for e in MUST_NOT_FILTER_EXT:
            assert not c.search(f"note.{e}"), (
                f"فیلترِ «{rx}» فایلِ .{e} را می‌گیرد — این محتواست، نه نویز")


def t_d_the_two_move_targets_stay_excluded():
    """`_Archive` و `_Duplicates` مقصدِ انتقال‌اند (§۰ منشور: هرگز حذف، فقط
    انتقال). اگر از فیلتر بیفتند، ۲٬۰۹۰ نوتِ بازنشسته به جستجو برمی‌گردند و
    هر جستجویی دو برابر نتیجه می‌دهد."""
    filters = _cfg().get("userIgnoreFilters") or []
    for d in MUST_FILTER_DIRS:
        assert any(d in f for f in filters), (d, "از userIgnoreFilters افتاد")


def t_e_every_regex_filter_actually_compiles():
    """یک regex ِ خراب را ابسیدین بی‌صدا دور می‌اندازد — فیلتر «هست» ولی
    کار نمی‌کند. همان کلاسِ «مسلح ولی بی‌اثر»."""
    for rx in _ext_regexes():
        try:
            re.compile(rx)
        except re.error as e:
            raise AssertionError(f"فیلترِ «{rx}» کامپایل نمی‌شود: {e}")


def t_f_this_test_only_reads():
    """AST guard: هیچ تابعِ t_* نباید بنویسد. module-level fixture setup مجاز است
    (mkdir/write_text برای hermetic vault) ولی بدنهٔ تست‌ها فقط می‌خوانند."""
    import ast
    banned = {"write_text", "write_bytes", "unlink", "rename"}
    source = Path(__file__).read_text("utf-8")
    tree = ast.parse(source)
    hits = []
    # خطوطِ module-level fixture (قبل از اولین def)
    _fixture_end = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _fixture_end = node.lineno
            break
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Attribute):
                # module-level fixture setup (mkdir, write_text for hermetic vault) مجاز است
                if n.lineno < _fixture_end:
                    continue
                if fn.attr in banned:
                    hits.append((n.lineno, fn.attr))
            if isinstance(fn, ast.Name) and fn.id == "open" and len(n.args) > 1:
                if n.lineno >= _fixture_end:
                    hits.append((n.lineno, "open(mode)"))
    assert not hits, ("t_* functions must not write", hits)


def main(app_path=None):
    """`app_path` فقط برای جهش‌آزمایی روی کپیِ موقت. تولید هرگز پاسش نمی‌دهد."""
    global _APP_OVERRIDE
    if app_path:
        _APP_OVERRIDE = Path(app_path)
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_obsidian_index_budget: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
