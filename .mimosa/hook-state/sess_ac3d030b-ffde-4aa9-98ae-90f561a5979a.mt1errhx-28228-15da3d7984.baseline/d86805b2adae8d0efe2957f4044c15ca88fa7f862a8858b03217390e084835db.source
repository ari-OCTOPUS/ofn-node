"""test_control_plane — قاعدهٔ مالکیتِ حالت باید اجرا شود، نه توصیه.

مالک پروسهٔ مستقل را انتخاب کرد. ریسکِ شناخته‌شدهٔ آن «دو نویسنده روی یک فایلِ
حالت» است که در این ارگانیسم دو بار باگ ساخته. پس دو ناوردی این‌جا سنجیده
می‌شوند — و اگر روزی کسی آن‌ها را بشکند، این تست قرمز می‌شود نه اینکه در
مرورِ کد کشف شود.

  ۱) `collector` **هیچ‌چیز نمی‌نویسد** و **هیچ‌چیز اجرا نمی‌کند**.
  ۲) `supervisor` فقط داخلِ فضای‌نامِ خودش می‌نویسد.
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("control-plane")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "control_plane")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import collector as col        # noqa: E402
import supervisor as sup       # noqa: E402


def _tree(name):
    return ast.parse((_OPS / "control_plane" / name).read_text("utf-8"))


def _calls(tree):
    return {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            for n in ast.walk(tree) if isinstance(n, ast.Call)}


def _imports(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
    return out


# ─── ۱: جمع‌کننده فقط می‌خواند ─────────────────────────────────────────────
def t_collector_never_writes():
    """یک خواننده که بنویسد، دیگر خواننده نیست.

    ⚠️ نسخهٔ اولِ این گارد نامِ **برهنه** را می‌گرفت و روی `replace` قرمز شد —
    ولی آن `f.stem.replace("flags-loaded-", "")` بود، یک رشته. همان باگِ
    تصادمِ نام که این جلسه در `orphan_scan` بسته شد، این‌بار در گاردِ خودم.
    نام‌های یکتا (`write_text`…) بی‌گیرنده امن‌اند؛ `replace` گیرنده می‌خواهد."""
    tree = _tree("collector.py")
    bad = _calls(tree) & {
        "write_text", "write_bytes", "mkdir", "unlink", "rmtree", "touch",
        "rename", "makedirs", "remove"}
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        if (isinstance(fn, ast.Attribute) and fn.attr == "replace"
                and isinstance(fn.value, ast.Name) and fn.value.id == "os"):
            bad.add("os.replace")
    assert not bad, f"جمع‌کننده می‌نویسد: {sorted(bad)}"


def t_collector_never_executes_or_networks():
    """قراردادِ INV-7: نه subprocess، نه شبکه — هیچ اندامی اجرا نمی‌شود."""
    bad = _imports(_tree("collector.py")) & {
        "subprocess", "socket", "urllib", "requests", "http", "shutil"}
    assert not bad, f"جمع‌کننده اجرا/شبکه دارد: {sorted(bad)}"


def t_snapshot_reports_what_it_could_not_read():
    """عکسِ نیمه‌کور نباید سلامت خوانده شود — `degraded` باید وجود داشته باشد."""
    snap = col.snapshot()
    assert snap.get("schema") == col.SCHEMA
    assert isinstance(snap.get("degraded"), list), snap.keys()
    assert isinstance(snap.get("sections"), dict) and snap["sections"]


def t_every_section_declares_whether_it_knows():
    """هر بخش یا می‌داند یا صریحاً می‌گوید نمی‌داند. سکوت مجاز نیست."""
    for name, sec in col.snapshot()["sections"].items():
        assert isinstance(sec, dict), name
        assert "unknown" in sec, f"بخشِ «{name}» نمی‌گوید می‌داند یا نه"
        if sec.get("unknown"):
            assert sec.get("reason"), f"«{name}» نادانستنش را توضیح نمی‌دهد"


def t_process_liveness_is_three_valued():
    """غیابِ نبض ≠ مرگ. قرمزِ کاذب همان‌قدر بد است که سبزِ کاذب."""
    for item in col.processes().get("items", []):
        assert item["state"] in ("live", "stale", "unknown"), item


# ─── ۲: سوپروایزر فقط در فضای‌نامِ خودش می‌نویسد ───────────────────────────
def t_supervisor_writes_only_inside_its_own_namespace():
    """ریسکِ «نویسندهٔ دوم» با قاعده بسته می‌شود، نه با امید."""
    d = sup.owned_dir()
    assert d is not None, "فضای‌نام resolve نشد"
    assert d.name == sup._OWNED_DIRNAME, d
    assert d.parent.name == "state", d


def t_supervisor_refuses_to_write_outside_its_namespace(monkey=None):
    """اگر روزی مسیر عوض شود، نوشتن باید **متوقف** شود نه اینکه جای دیگر بنشیند."""
    import tempfile
    original = sup.owned_dir
    try:
        stray = Path(tempfile.mkdtemp(prefix="cp-stray-")) / "somewhere_else"
        sup.owned_dir = lambda: stray
        assert sup.write_snapshot() is None, "بیرونِ فضای‌نام نوشت"
        assert not stray.exists(), "پوشهٔ بیگانه ساخته شد"
    finally:
        sup.owned_dir = original


def t_flag_is_off_by_default():
    """قابلیتِ تازه پیش‌فرض خاموش است — رأیِ مالک، نه پیش‌فرضِ کد."""
    saved = os.environ.pop(sup.FLAG, None)
    try:
        assert sup.enabled() is False
    finally:
        if saved is not None:
            os.environ[sup.FLAG] = saved


def t_flag_on_is_explicit():
    saved = os.environ.get(sup.FLAG)
    try:
        os.environ[sup.FLAG] = "1"
        assert sup.enabled() is True
    finally:
        if saved is None:
            os.environ.pop(sup.FLAG, None)
        else:
            os.environ[sup.FLAG] = saved


def t_singleton_lock_blocks_the_second_instance():
    """دو مرکز روی یک توکن (۰۷-۲۹) دقیقاً از نبودِ همین قفل آمد."""
    port = 8779
    first = sup.acquire_singleton(port)
    assert first is not None, "نمونهٔ اول نتوانست قفل بگیرد"
    try:
        second = sup.acquire_singleton(port)
        assert second is None, "نمونهٔ دوم هم قفل گرفت — تک‌نمونگی نیست"
    finally:
        first.close()


def t_the_lock_socket_never_listens():
    """قفل نباید به سطحِ شبکه تبدیل شود — bind بله، listen/accept هرگز."""
    calls = _calls(_tree("supervisor.py"))
    for forbidden in ("listen", "accept", "serve_forever"):
        assert forbidden not in calls, f"سوکتِ قفل {forbidden} می‌کند"


def t_supervisor_binds_loopback_only():
    """«هیچ پورتِ عمومی روی لپ‌تاپ» — مرزِ غیرقابلِ مذاکرهٔ مالک."""
    src = (_OPS / "control_plane" / "supervisor.py").read_text("utf-8")
    assert "0.0.0.0" not in src, "bind روی همهٔ اینترفیس‌ها"
    assert '"127.0.0.1"' in src, "bind ِ loopback پیدا نشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_control_plane: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
