"""test_code_apply_wiring — حلقهٔ ۷ وصل شد؛ این تست ثابت می‌کند قفل‌هایش تیغ دارند.

رأیِ صریحِ مالک ۲۰۲۶-۰۷-۲۸: «بله، وصل کن». تا آن لحظه `code_autonomy.run_forever`
**هیچ صداکننده‌ای نداشت** — و کامنتِ خودِ آن ماژول این وضع را «امنیتِ تصادفی» می‌نامید،
چون فایلِ ACTIVATION از قبل باز بود و تنها چیزی که جلوی اعمال را گرفته بود **نبودِ سیم**
بود نه **بودنِ قفل**. تفاوتشان این است که سیم را هر کسی ممکن است روزی وصل کند.

حالا سیم هست. پس قفل باید سنجیده شود، نه ادعا:

  ۱ فلگ  — `OCTOPUS_WIRE_CODE_APPLY` نباشد، ماژول حتی import نمی‌شود.
  ۲ فعال‌سازی — `active()` = ACTIVATION هست و STOP-CODE-AUTONOMY نیست.
  ۳ کیل   — ساختنِ STOP-CODE-AUTONOMY حلقه را می‌بندد، بدونِ ری‌استارت.
  ۴ مرز   — خودِ organism هرگز پچی را اعمال نمی‌کند؛ فقط درایور را استارت می‌کند.

⚠️ این تست عمداً فایلِ کیل می‌سازد. اولین چکش ثابت می‌کند آن فایل **در درختِ موقت**
ساخته می‌شود نه زنده — همان تلهٔ `test_tg_power` که سوئیتِ کامل را روی ارگانیسمِ
در حالِ اجرا خطرناک می‌کند.
"""
import ast
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("code-apply-wiring")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import code_autonomy as ca   # noqa: E402

FLAG = "OCTOPUS_WIRE_CODE_APPLY"
_ORGANISM = _OPS / "organism.py"


def _wiring_block():
    """گرهِ ASTِ بلوکِ سیم‌کشی — با جستجوی نحوی، نه با شمارهٔ خط (خط جابه‌جا می‌شود)."""
    tree = ast.parse(_ORGANISM.read_text("utf-8"))
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        if FLAG in ast.dump(n):
            return n
    return None


# ─── ۰: خودِ تست نباید به درختِ زنده دست بزند ─────────────────────────────
def t_this_test_never_touches_the_live_tree():
    """اگر ایزوله‌سازی نشت کند، بقیهٔ چک‌ها ارگانیسمِ واقعی را می‌خوابانند."""
    live = str(harness.REAL_VAULT / "_ops").lower()
    for p in (ca.KILL, ca.ACTIVATION):
        assert not str(p).lower().startswith(live), f"مسیرِ زنده: {p}"


# ─── ۱: فلگ ──────────────────────────────────────────────────────────────
def t_the_flag_is_read_before_the_driver_is_imported():
    """نبودِ فلگ باید حتی از importِ ماژول جلوگیری کند، نه فقط از استارت."""
    blk = _wiring_block()
    assert blk is not None, f"بلوکِ {FLAG} در organism.py پیدا نشد"
    imported = [a.name for s in ast.walk(blk) if isinstance(s, ast.Import) for a in s.names]
    assert "code_autonomy" in imported, "importِ درایور داخلِ گاردِ فلگ نیست"


def t_the_flag_defaults_to_off():
    """`environ.get(FLAG, "")` — پیش‌فرضِ خالی یعنی غایب = خاموش."""
    blk = _wiring_block()
    src = ast.dump(blk)
    assert "'1'" in src or '"1"' in src, "الگوی روشن‌بودن تعریف نشده"
    got = ast.parse(_ORGANISM.read_text("utf-8"))
    txt = ast.unparse(blk) if hasattr(ast, "unparse") else ""
    if txt:
        assert f"environ.get('{FLAG}', '')" in txt or f'environ.get("{FLAG}", "")' in txt, txt[:200]
    assert got is not None


# ─── ۲: فعال‌سازی ─────────────────────────────────────────────────────────
def t_active_is_checked_before_the_thread_starts():
    """فلگِ روشن کافی نیست؛ ACTIVATION هم باید باشد."""
    blk = _wiring_block()
    calls = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
             for n in ast.walk(blk) if isinstance(n, ast.Call)}
    assert "active" in calls, "بدونِ چکِ active() استارت می‌شود"


def t_without_activation_the_gate_is_closed():
    """رفتارِ واقعی، نه ساختار: بدونِ فایلِ فعال‌سازی هیچ‌چیز مجاز نیست."""
    if ca.ACTIVATION.exists():
        ca.ACTIVATION.unlink()
    assert ca.active() is False


def t_the_consume_call_sits_under_the_active_guard():
    """ناوردیِ حلقه: مصرفِ تأیید فقط زیرِ active() اتفاق می‌افتد."""
    tree = ast.parse(Path(ca.__file__).read_text("utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "run_forever")
    guarded = False
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and "active" in ast.dump(node.test):
            if "consume_approvals" in ast.dump(node):
                guarded = True
    assert guarded, "consume_approvals بیرونِ گاردِ active() صدا زده می‌شود"


# ─── ۳: کیل‌سوئیچ ─────────────────────────────────────────────────────────
def t_the_kill_file_stops_the_driver_immediately():
    """رفتارِ واقعی: با فایلِ کیل، حلقه باید فوراً برگردد نه بعد از every_s."""
    ca.KILL.parent.mkdir(parents=True, exist_ok=True)
    ca.KILL.write_text("test", "utf-8")
    try:
        t0 = time.monotonic()
        ca.run_forever(every_s=3600.0)      # اگر کیل کار نکند، اینجا آویزان می‌شود
        assert time.monotonic() - t0 < 5.0, "کیل‌سوئیچ فوری نبود"
    finally:
        ca.KILL.unlink(missing_ok=True)


def t_the_kill_file_beats_activation():
    """اگر هر دو باشند، کیل برنده است — وگرنه خاموشیِ اضطراری معنا ندارد."""
    ca.ACTIVATION.parent.mkdir(parents=True, exist_ok=True)
    ca.ACTIVATION.write_text("1", "utf-8")
    ca.KILL.write_text("stop", "utf-8")
    try:
        assert ca.active() is False
    finally:
        ca.KILL.unlink(missing_ok=True)
        ca.ACTIVATION.unlink(missing_ok=True)


# ─── ۴: مرز ──────────────────────────────────────────────────────────────
def t_organism_starts_the_driver_but_never_applies_anything():
    """organism فقط سیم است. اگر خودش اعمال کند، همهٔ گیت‌های درایور دور زده می‌شوند."""
    tree = ast.parse(_ORGANISM.read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for banned in ("apply_approved", "consume_approvals"):
        assert banned not in called, f"organism خودش اعمال می‌کند: {banned}"


def t_the_thread_is_a_daemon():
    """غیرdaemon یعنی خاموشیِ ارگانیسم پشتِ این حلقه گیر می‌کند."""
    blk = _wiring_block()
    thread_calls = [n for n in ast.walk(blk) if isinstance(n, ast.Call)
                    and (getattr(n.func, "attr", None) == "Thread"
                         or getattr(n.func, "id", None) == "Thread")]
    assert thread_calls, "threadی استارت نمی‌شود"
    for c in thread_calls:
        kw = {k.arg: k.value for k in c.keywords}
        assert "daemon" in kw and getattr(kw["daemon"], "value", None) is True, "daemon=True نیست"


def t_a_broken_driver_never_kills_boot():
    """بلوک باید داخلِ try باشد — وگرنه یک ImportError بوتِ کلِ ارگانیسم را می‌کشد."""
    tree = ast.parse(_ORGANISM.read_text("utf-8"))
    blk = _wiring_block()
    for n in ast.walk(tree):
        if isinstance(n, ast.Try) and FLAG in ast.dump(n):
            assert n.handlers, "try بدونِ except"
            return
    raise AssertionError(f"بلوکِ {FLAG} داخلِ try نیست (blk={blk is not None})")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_code_apply_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
