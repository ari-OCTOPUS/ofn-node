"""test_metadata_scan_honesty — نقشه‌ای که خودش را ۸ برابر می‌شمرد (C9).

اندازه‌گیریِ پیش از تغییر: از ۵۰٬۰۰۰ رکوردِ آخرین اسکن، **۴۹٬۹۳۹** زیرِ
`.claude/worktrees/` بودند — نُه رونوشتِ کهنهٔ vault از برنچ‌های جلسه‌ای. یعنی
اسکنر هرگز یک نوتِ واقعیِ vault را ثبت نکرده بود، و کارتِ گزارش ۱۶٬۱۶۲ می‌گفت
در حالی که markdownِ trackedِ واقعی ۲٬۱۲۸ است.

سه ناوردی این‌جا سنجیده می‌شوند — هر کدام یک دروغِ مستقل را می‌بندد:

  ۱) `.claude` (و `.git`) هرگز شمرده نمی‌شوند؛ پوشه‌های عادی شمرده می‌شوند.
  ۲) `truncated` درجه‌یک است و **دو جهته** — سقفِ کوچک ⇒ True، سقفِ بزرگ ⇒ False —
     و اسکنِ به‌سقف‌خورده به‌جای عدد `UNKNOWN` رندر می‌کند.
  ۳) سقف فقط در ثابتِ ماژول اعلام می‌شود؛ `center.py::_handle_map_callback` دیگر
     `max_files` خودش را پاس نمی‌دهد (وگرنه بالابردنِ ثابت باز هم بی‌اثر می‌شود).

هیچ اسکنی روی `F:\\backup` اجرا نمی‌شود — فقط درختِ فیکسچرِ temp. هر تست
مسیرهای خروجیِ ماژول را به sandboxِ خودش می‌برد و assert می‌کند که آن sandbox
**بیرونِ** درختِ زنده است.
"""
import ast
import io
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness   # noqa: E402
ENV = harness.setup("metadata-scan-honesty")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import metadata_scan as ms   # noqa: E402

_LIVE = Path(r"F:\backup").resolve()


def _sandbox():
    """sandboxِ تازه + انتقالِ همهٔ مسیرهای خروجیِ ماژول داخلش.

    درسِ ثبت‌شده (isolate-the-real-path): یک مسیرِ جاافتاده کافی است تا تست روی
    `_octopus/` ِ زنده بنویسد. پس همه‌شان pin می‌شوند و بعد assert می‌شود که
    sandbox زیرِ درختِ زنده نیست."""
    sb = Path(tempfile.mkdtemp(prefix="octopus-mscan-honesty-")).resolve()
    assert _LIVE not in sb.parents and sb != _LIVE, f"sandbox داخلِ درختِ زنده: {sb}"
    oct_dir = sb / "_octopus"
    ms._OCTOPUS = oct_dir
    ms._MANIFEST_DIR = oct_dir / "manifests"
    ms._HISTORY_DIR = ms._MANIFEST_DIR / "history"
    ms._REPORTS_DIR = oct_dir / "reports" / "daily"
    ms._STATE_PATH = oct_dir / "state" / "metadata_scan.json"
    ms._AUDIT_PATH = oct_dir / "logs" / "audit.log"
    return sb


def _tree():
    """درختِ کوچکِ فیکسچر: دو پوشهٔ عادی + یک `.claude` که ادایِ worktree درمی‌آورد.

    شکلِ `.claude/worktrees/<branch>/...` عمداً همان شکلِ واقعیِ روی دیسک است —
    فیکسچرِ کوچک‌تر از واقعیت پوششِ کاذب می‌دهد."""
    sb = _sandbox()
    root = sb / "fakevault"
    (root / "03 - Projects").mkdir(parents=True)
    (root / "07 - Knowledge").mkdir(parents=True)
    (root / ".claude" / "worktrees" / "sess-a" / "03 - Projects").mkdir(parents=True)
    (root / ".claude" / "worktrees" / "sess-b").mkdir(parents=True)
    (root / ".git" / "objects").mkdir(parents=True)

    (root / "03 - Projects" / "one.md").write_text("# one", "utf-8")
    (root / "03 - Projects" / "two.md").write_text("# two", "utf-8")
    (root / "07 - Knowledge" / "note.md").write_text("# note", "utf-8")
    (root / "top-level.md").write_text("# root file", "utf-8")           # سطلِ "."
    (root / ".claude" / "settings.json").write_text("{}", "utf-8")
    (root / ".claude" / "worktrees" / "sess-a" / "03 - Projects" / "one.md").write_text(
        "# ghost copy", "utf-8")
    (root / ".claude" / "worktrees" / "sess-b" / "ghost.md").write_text("# ghost", "utf-8")
    (root / ".git" / "objects" / "deadbeef").write_bytes(b"\x00" * 16)
    return root


REAL_FILES = 4          # سه md در دو پوشهٔ عادی + یک فایلِ ریشه
GHOST_FILES = 4         # سه زیرِ .claude + یک زیرِ .git


# ─── ۱: پوشه‌های ارواح شمرده نمی‌شوند ─────────────────────────────────────────
def t_a_claude_dir_is_excluded_and_normal_dirs_are_counted():
    root = _tree()
    r = ms.scan_metadata(root, max_files=10_000, max_seconds=30)
    paths = [f["path"] for f in r["files"]]

    ghosts = [p for p in paths if p.startswith(".claude/") or p.startswith(".git/")]
    assert not ghosts, f".claude/.git شمرده شدند: {ghosts[:5]}"
    # و پوشه‌های عادی *واقعاً* شمرده شده‌اند (وگرنه «صفر فایل» هم این assert را پاس می‌کرد)
    assert "03 - Projects/one.md" in paths, f"نوتِ واقعی گم شد: {sorted(paths)}"
    assert "07 - Knowledge/note.md" in paths, f"نوتِ واقعی گم شد: {sorted(paths)}"
    assert "top-level.md" in paths, "فایلِ ریشه گم شد"
    assert r["summary"]["files"] == REAL_FILES, (
        f"باید دقیقاً {REAL_FILES} فایلِ واقعی باشد، شد {r['summary']['files']} "
        f"({GHOST_FILES} فایلِ روح در درخت هست)")


def t_b_exclude_dirs_declares_git_and_claude():
    """قاعده، نه نمونه: هر دو نام باید در خودِ مجموعه اعلام شده باشند."""
    assert ".git" in ms.EXCLUDE_DIRS, "`.git` از EXCLUDE_DIRS افتاد"
    assert ".claude" in ms.EXCLUDE_DIRS, (
        "`.claude` در EXCLUDE_DIRS نیست — ۴۹٬۹۳۹ رکوردِ worktreeِ کهنه برمی‌گردد")


def t_c_excluded_dirs_is_published_in_the_manifest():
    """manifest باید فیلترِ خودش را اعلام کند تا شکستنِ مقایسهٔ تاریخی آشکار باشد."""
    root = _tree()
    r = ms.scan_metadata(root, max_files=10_000, max_seconds=30)
    assert ".claude" in r["excluded_dirs"], "manifest استثنای .claude را اعلام نمی‌کند"


# ─── ۲: قطع‌شدگی درجه‌یک و دوجهته ─────────────────────────────────────────────
def t_d_truncated_is_true_when_cap_is_tiny():
    root = _tree()
    r = ms.scan_metadata(root, max_files=2, max_seconds=30)
    assert r["truncated"] is True, "سقفِ ۲ روی درختِ ۴ فایلی truncated نداد"
    assert r["truncated_reason"] == "max_files", (
        f"دلیلِ قطع اشتباه: {r['truncated_reason']}")
    assert r["summary"]["files"] == 2
    assert r["summary"]["truncated"] is True, "summary قطع‌شدگی را منتشر نمی‌کند"


def t_e_truncated_is_false_when_cap_is_generous():
    """جهتِ دوم — وگرنه یک `truncated = True` ِ ثابت هم تستِ بالا را پاس می‌کرد."""
    root = _tree()
    r = ms.scan_metadata(root, max_files=10_000, max_seconds=30)
    assert r["truncated"] is False, "درختِ ۴ فایلی با سقفِ ۱۰٬۰۰۰ نباید ناقص باشد"
    assert r["truncated_reason"] is None, f"دلیلِ قطعِ بی‌جا: {r['truncated_reason']}"


def t_f_capped_scan_renders_unknown_not_a_number():
    """«اسکنی که به سقف بخورد باید UNKNOWN رندر کند حتی اگر عدد تولید کرده باشد.»"""
    root = _tree()
    capped = ms.scan_metadata(root, max_files=2, max_seconds=30)
    full = ms.scan_metadata(root, max_files=10_000, max_seconds=30)

    assert ms.is_truncated(capped) is True, (
        "اسکنِ سقفِ‌۲ روی درختِ ۴ فایلی خودش را کامل اعلام کرد")
    assert ms.is_truncated(full) is False, (
        "اسکنِ سقفِ‌۱۰٬۰۰۰ روی درختِ ۴ فایلی خودش را ناقص اعلام کرد")
    assert ms.count_display(capped) == ms.UNKNOWN, (
        f"اسکنِ بریده عدد رندر کرد: {ms.count_display(capped)}")
    assert ms.count_display(full) == f"{REAL_FILES:,}", (
        f"اسکنِ کامل باید عدد بدهد، داد: {ms.count_display(full)}")
    assert ms.UNKNOWN in ms.summarize_manifest(capped), (
        f"خلاصهٔ اسکنِ بریده UNKNOWN نمی‌گوید: {ms.summarize_manifest(capped)}")
    assert ms.UNKNOWN not in ms.summarize_manifest(full)


def t_g_unknown_on_unreadable_result_never_zero():
    """نبودِ داده حکم نیست: ورودیِ خراب ⇒ UNKNOWN، هرگز «۰ فایل»."""
    for bad in (None, {}, {"summary": {}}, {"summary": {"files": 5}}):
        assert ms.count_display(bad) == ms.UNKNOWN, f"ورودیِ خراب عدد داد: {bad}"
        assert ms.is_truncated(bad) is True, f"ورودیِ خراب ادعای کامل کرد: {bad}"


# ─── ۳: شکستِ per-top-level-directory ────────────────────────────────────────
def t_h_by_top_dir_sums_to_files_seen():
    root = _tree()
    r = ms.scan_metadata(root, max_files=10_000, max_seconds=30)
    tops = r["by_top_dir"]
    assert sum(tops.values()) == r["summary"]["files"], (
        f"مجموعِ شکست {sum(tops.values())} ≠ files_seen {r['summary']['files']}")
    assert tops.get("03 - Projects") == 2, f"شکستِ اشتباه: {tops}"
    assert tops.get("07 - Knowledge") == 1, f"شکستِ اشتباه: {tops}"
    assert tops.get(".") == 1, f"فایلِ ریشه سطلِ خودش را ندارد: {tops}"
    assert ".claude" not in tops and ".git" not in tops, f"روح در شکست: {tops}"


def t_i_by_top_dir_sums_even_when_truncated():
    """ناوردیِ مجموع نباید فقط در مسیرِ خوش‌بینانه برقرار باشد."""
    root = _tree()
    r = ms.scan_metadata(root, max_files=2, max_seconds=30)
    assert sum(r["by_top_dir"].values()) == r["summary"]["files"] == 2, (
        f"شکست در اسکنِ بریده نمی‌خواند: {r['by_top_dir']}")


# ─── ۴: سقف فقط یک محلِ اعلام دارد ───────────────────────────────────────────
def _center_scan_calls():
    """همهٔ Call nodeهای `*.scan_metadata(...)` داخلِ center.py."""
    tree = ast.parse((_OPS / "telegram_center" / "center.py").read_text("utf-8"))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "scan_metadata":
            out.append(n)
    return out


def t_j_center_call_site_does_not_pass_max_files():
    calls = _center_scan_calls()
    assert calls, "هیچ فراخوانیِ scan_metadata در center.py نیست — تست تهی شد"
    for c in calls:
        kw = {k.arg for k in c.keywords}
        assert "max_files" not in kw, (
            "center.py باز هم max_files خودش را پاس می‌دهد — سقفِ ماژول بی‌اثر می‌شود")
        assert len(c.args) <= 1, (
            f"آرگومانِ موضعیِ اضافه در call site: {len(c.args)} (فقط root مجاز است)")


def t_k_center_call_site_keeps_the_sixty_second_cap():
    """max_seconds می‌ماند: دو آنتی‌ویروسِ لحظه‌ای، اسکنِ بازگشتی پاتولوژیک."""
    for c in _center_scan_calls():
        kw = {k.arg: k.value for k in c.keywords}
        assert "max_seconds" in kw, "سقفِ زمانی از call site حذف شد"
        v = kw["max_seconds"]
        assert isinstance(v, ast.Constant) and v.value == 60, (
            f"max_seconds دیگر ۶۰ نیست: {getattr(v, 'value', v)}")


def t_l_module_declares_exactly_one_file_cap():
    """یک نام، یک مقدار — دو سقفِ متفاوت همان تلهٔ ۵۰٬۰۰۰ در برابرِ ۲۰۰٬۰۰۰ است."""
    assert isinstance(ms.MAP_SCAN_MAX_FILES, int) and ms.MAP_SCAN_MAX_FILES > 0
    assert ms.DEFAULT_MAX_FILES == ms.MAP_SCAN_MAX_FILES, (
        f"دو سقفِ متفاوت اعلام شده: {ms.DEFAULT_MAX_FILES} و {ms.MAP_SCAN_MAX_FILES}")
    import inspect
    default = inspect.signature(ms.scan_metadata).parameters["max_files"].default
    assert default == ms.MAP_SCAN_MAX_FILES, (
        f"پیش‌فرضِ امضا ({default}) از ثابتِ ماژول ({ms.MAP_SCAN_MAX_FILES}) جدا افتاده")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_metadata_scan_honesty: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
