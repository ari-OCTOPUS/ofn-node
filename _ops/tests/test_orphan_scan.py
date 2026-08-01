"""test_orphan_scan — ارگانیسم باید بداند کدام اندامش به بدن وصل نیست.

اسکنِ ۲۰۲۶-۰۷-۲۷ (شش ایجنت + راستی‌آزماییِ متخاصم) ۲۲ توانایی را تأیید کرد که
از تلگرام دست‌نیافتنی‌اند — و برای بخشِ بزرگی دلیل «فلگِ خاموش» نبود بلکه چیزِ
بدتری: **صفر صداکننده در کلِ مخزن**.

دو ناوردی:
  ۱) **دقت** — چیزی که این‌جا می‌آید باید واقعاً یتیم باشد. آشکارسازی که
     هشدارِ کاذب بدهد، خاموش می‌شود.
  ۲) **پوشش** — یتیمِ واقعی نباید جا بیفتد.

و یک قیدِ صداقت: روش عمداً محافظه‌کار است (هر ابهام → «وصل»). پس کارت **باید**
بگوید فهرست کف است نه سقف؛ ادعای کامل‌بودن این‌جا دروغ می‌شود.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("orphan-scan")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import orphan_scan as osc   # noqa: E402

_R = osc.scan()


# ── درختِ نحوی یک‌بار پارس می‌شود، نه به‌ازای هر یتیم ─────────────────────────
# ۲۰۲۶-۰۸-۰۱: بعد از بستنِ نقطهٔ کورِ اسکنر، شمارِ یتیم‌ها ۲۰ → ۷۱ شد و همین
# حلقه ۷۱ بار روی ~۴۵۰ فایل دوید — سوییت پیش از پایانش تایم‌اوت می‌گرفت.
# منطقِ سنجش دست‌نخورده است؛ فقط پارس یک‌بار انجام می‌شود.
_TREES: "dict | None" = None


def _trees() -> dict:
    global _TREES
    if _TREES is not None:
        return _TREES
    import warnings
    out = {}
    for f in _OPS.rglob("*.py"):
        if set(f.parts) & {"tests", "_code", "__pycache__"}:
            continue
        if f.name.startswith("test_"):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                out[f] = ast.parse(f.read_text("utf-8"))
        except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
            continue
    _TREES = out
    return out

def _bound(tree) -> set:
    """نام‌هایی که در این فایل با import بسته شده‌اند (با alias).

    تنها این نام‌ها می‌توانند در `X.attr` به یک **ماژول** اشاره کنند؛ هر نامِ
    دیگری متغیرِ محلی است."""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.asname or a.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                out.add(a.asname or a.name)
    return out


def _callers(stem: str) -> int:
    """شمارشِ مستقل — نه از کدِ زیرِ آزمون.

    ⚠️ نسخهٔ اول متن را گرپ می‌کرد (`f"{stem}." in src`) و **کامنت‌ها را هم
    می‌شمرد**: `arm_gate` دو ارجاع داشت که هر دو کامنت بودند، پس تست اسکنرِ
    درست را «هشدارِ کاذب» خواند. شمارشِ ارجاع باید از درختِ نحوی بیاید، نه از
    رشته — وگرنه یک جملهٔ توضیحی به‌اندازهٔ یک فراخوانِ واقعی وزن دارد.

    عمداً **سخت‌گیرتر** از اسکنر است: رشته‌های ثابت (importِ پویا) را شاهد
    نمی‌گیرد. پس اگر اختلافی باشد، در جهتِ امنِ «تست شاهدِ کمتری می‌بیند» است."""
    n = 0
    for f, tree in _trees().items():
        if f.stem == stem:
            continue
        hit = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.split(".")[-1] == stem for a in node.names):
                    hit = True
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[-1] == stem:
                    hit = True
            elif isinstance(node, ast.Attribute):
                v = node.value
                # ۰۸-۰۱ — `X.attr` فقط وقتی شاهد است که `X` را importی در همین
                # فایل بسته باشد. بدونِ این شرط یک پارامترِ هم‌نام کافی بود:
                # `action_boundary.py` پارامتری به نامِ `opportunity` دارد و
                # `opportunity.get(...)` صدا می‌زند، پس این شمارنده ماژولِ
                # `world_discovery/opportunity.py` را «صداشده» می‌دید و اسکنرِ
                # درست را «هشدارِ کاذب» می‌خواند. سایه‌اندازیِ نام ≠ ارجاع.
                if isinstance(v, ast.Name) and v.id == stem and stem in _bound(tree):
                    hit = True
            if hit:
                break
        n += 1 if hit else 0
    return n


# ─── ۱: دقت — هشدارِ کاذب ممنوع ───────────────────────────────────────────
def t_every_reported_orphan_really_has_no_caller():
    """آشکارسازی که هشدارِ کاذب بدهد، خاموش می‌شود. صفر تحمل."""
    false_alarms = []
    for o in _R["orphans"]:
        stem = Path(o["module"]).stem
        if _callers(stem) > 0:
            false_alarms.append(o["module"])
    assert not false_alarms, f"هشدارِ کاذب: {false_alarms}"


def t_a_clearly_wired_module_is_never_reported():
    """گاردِ سلامتِ عقل: ماژول‌هایی که همه‌جا صدا زده می‌شوند."""
    reported = {Path(o["module"]).stem for o in _R["orphans"]}
    for wired in ("opslib", "chrono", "wiring", "events", "cardiac"):
        assert wired not in reported, wired


def t_entry_points_are_not_called_orphans():
    """`organism.py` عمداً صداکننده ندارد — نقطهٔ ورود است، نه اندامِ رهاشده."""
    reported = {Path(o["module"]).stem for o in _R["orphans"]}
    for entry in ("organism", "owner_ping"):
        assert entry not in reported, entry


# ─── ۲: پوشش — یتیمِ واقعی جا نیفتد ───────────────────────────────────────
def t_the_three_independently_confirmed_orphans_are_found():
    """این سه‌تا را شش ایجنتِ مستقل و راستی‌آزماییِ متخاصم تأیید کردند.

    اگر اسکنر پیدایشان نکند، پوششش دروغ است."""
    reported = {Path(o["module"]).stem for o in _R["orphans"]}
    for known in ("watchdog_extension", "arm_gate", "drawdown_guard"):
        assert known in reported, f"«{known}» یتیمِ تأییدشده است ولی پیدا نشد"


def t_a_synthetic_orphan_would_be_caught():
    """گاردِ زندهٔ پوشش: هر ماژولِ بی‌صداکننده‌ای باید بیفتد داخلِ فهرست.

    به‌جای ساختنِ فایل (که درختِ زنده را لمس می‌کند)، منطق را روی یک نمونهٔ
    واقعیِ شناخته‌شده می‌سنجیم و شمارشِ مستقل را با ادعای اسکنر تطبیق می‌دهیم."""
    for o in _R["orphans"][:5]:
        assert _callers(Path(o["module"]).stem) == 0, o["module"]


def t_weighty_orphans_are_flagged_and_ranked_first():
    """یتیمِ مربوط به پول یا ایمنی باید اولِ فهرست باشد — نه قاطیِ بقیه."""
    ws = [o["weighty"] for o in _R["orphans"]]
    assert any(ws), "هیچ یتیمِ مهمی علامت نخورد"
    assert ws == sorted(ws, reverse=True), "مرتب‌سازی مهم‌ها را اول نگذاشت"


# ─── ۳: صداقتِ کارت ───────────────────────────────────────────────────────
def t_the_card_admits_the_list_is_a_floor_not_a_ceiling():
    """روش محافظه‌کار است؛ ادعای کامل‌بودن این‌جا دروغ می‌شود."""
    body = osc.card()
    assert "کف است نه سقف" in body, body
    assert "نکنی:" in body


def t_the_card_counts_the_dangerous_ones_separately():
    body = osc.card()
    if _R["weighty"]:
        assert "پول یا ایمنی" in body, body


# ─── ۴: مرزِ ماژول ────────────────────────────────────────────────────────
def t_the_scanner_imports_nothing_it_scans():
    """اسکنِ ۳۳۴ فایل با import یعنی اجرای هر اثرِ جانبیِ import-time."""
    before = set(sys.modules)
    osc.scan()
    new = set(sys.modules) - before - {"warnings"}
    leaked = [m for m in new if not m.startswith(("_", "encodings", "importlib"))]
    assert not leaked, leaked[:6]


def t_the_scanner_only_reads():
    tree = ast.parse(Path(osc.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("write_text", "unlink", "rmtree", "system", "run"):
        assert d not in called, f"اسکنرِ فقط‌خواندنی می‌نویسد: {d}"


def t_forbidden_paths_are_never_scanned():
    for bad in ("_code", ".git", "tests", "_Archive", "_Duplicates"):
        assert bad in osc._SKIP, bad
    assert not any("test" in o["module"] for o in _R["orphans"])


def t_the_scan_covers_the_whole_tree():
    assert _R["checked"] >= 200, _R["checked"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_orphan_scan: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
