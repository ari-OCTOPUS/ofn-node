"""test_restart_preflight — گیتِ پیش‌پروازِ RESTART-ALL باید واقعاً جلو را بگیرد.

چرا این فایل هست (۲۰۲۶-۰۸-۰۳):

    `RESTART-ALL.ps1` قبل از دست‌زدن به هیچ پروسه‌ای دو چیز را چک می‌کند —
    مارکرِ `STOP-*` سرگردان، و CRLF بودنِ `OCTOPUS-flags.cmd`. هر دو گاردِ
    گران‌قیمت‌اند: یک `STOP-ORGANISM` جامانده یک‌بار کلِ سیستم را ۳۰ دقیقه
    خواباند، و یک فایلِ فلگِ LF ‏یک‌بار مرکز را با ۵۹ از ۱۵۶ فلگ بالا آورد.

    ولی تا امروز این دو گارد **آزمون‌ناپذیر** بودند: مسیرِ `_ops` در اسکریپت
    هاردکد بود، پس تنها راهِ سنجیدنشان تزریقِ یک فایلِ `STOP-*` واقعی به درختِ
    زنده بود — یعنی همان کاری که گارد برای جلوگیری‌اش وجود دارد. گاردی که برای
    آزمودنش باید ارگانیسم را بخوابانی، عملاً هیچ‌وقت آزموده نمی‌شود.

    پس `-OpsRoot` به‌عنوان درزِ آزمون اضافه شد، و امنیتش **ساختاری** است نه
    اخلاقی: ریشهٔ غیرکانونی فقط preflight اجرا می‌کند (خروجِ ۲)، پس این تست
    ساختاراً نمی‌تواند به حلقهٔ ری‌استارت برسد حتی اگر بخواهد.

ناوردی‌هایی که این‌جا قفل می‌شوند:
  ۱) هر یک از چهار مارکر به‌تنهایی ⇒ abort (خروجِ ۱)، با نامِ همان مارکر.
  ۲) فایلِ فلگِ LF یا غایب ⇒ abort.
  ۳) فیکسچرِ سالم ⇒ عبور، و رسیدن به PLAN بدونِ هیچ ری‌استارتی.
  ۴) ریشهٔ غیرکانونی بدونِ ‎-WhatIf ⇒ خروجِ ۲ (خودِ درز نمی‌تواند سوءاستفاده شود).
  ۵) پیش‌فرضِ `-OpsRoot` هنوز همان درختِ زنده است (درز رفتارِ عادی را عوض نکرده).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("restart-preflight")

_OPS = harness.SELF_OPS
_SCRIPT = _OPS / "RESTART-ALL.ps1"
_MARKERS = ("STOP-ORGANISM", "RESTART-REQUESTED", "STOP-TG-CENTER", "STOP-CORTEX")
# 2026-08-10: The live-tree-default check (t_default_ops_root_is_still_the_live_tree)
# only makes sense when running FROM the live tree. In a worktree, SELF_OPS points to
# the worktree, not F:\backup\_ops. We check against REAL_VAULT (the canonical live root)
# and ENV_BLOCK the subtest if we're not in the live tree.
_REAL_LIVE_OPS = str(Path(harness.REAL_VAULT) / "_ops").lower()
_LIVE_ROOT = _REAL_LIVE_OPS
_IN_WORKTREE = str(_OPS).lower() != _REAL_LIVE_OPS


def _fixture(markers=(), flags="crlf"):
    """یک ریشهٔ ops ِ ساختگی و کامل. هرگز زیرِ درختِ زنده نیست (assert می‌شود)."""
    root = Path(tempfile.mkdtemp(prefix="restart-preflight-"))
    # گاردِ ایمنی: اگر روزی tempdir به درختِ زنده اشاره کند، اینجا می‌ایستیم و
    # نه یک بایت می‌نویسیم — درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن».
    assert _LIVE_ROOT not in str(root).lower(), f"fixture landed inside the live tree: {root}"
    (root / "RESTART-PROCESS.ps1").write_bytes(b"# stub runner for preflight tests\r\n")
    if flags == "crlf":
        body = b"".join(b"set OCTOPUS_FAKE_%d=1\r\n" % i for i in range(20))
        (root / "OCTOPUS-flags.cmd").write_bytes(body)
    elif flags == "lf":
        body = b"".join(b"set OCTOPUS_FAKE_%d=1\n" % i for i in range(20))
        (root / "OCTOPUS-flags.cmd").write_bytes(body)
    # flags == "missing" → فایلی نساز
    for m in markers:
        (root / m).write_bytes(b"")
    return root


def _run(root, whatif=True, timeout=90):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(_SCRIPT), "-OpsRoot", str(root)]
    if whatif:
        cmd.append("-WhatIf")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        # هر مسیرِ preflight باید در چند ثانیه تصمیم بگیرد. تنها راهِ کند شدن این
        # است که گارد نگیرد و اسکریپت وارد حلقهٔ ری‌استارت شود، جایی که برای
        # «حالتِ تازه» ۱۲۰ ثانیه صبر می‌کند. جهشِ M3 دقیقاً همین را کرد و تست
        # با TimeoutExpired ِ خام قرمز شد — سیگنالی که علتش را نمی‌گفت. حالا
        # به یک ادعای معنادار ترجمه می‌شود.
        raise AssertionError(
            f"preflight پس از {timeout}s تصمیم نگرفت — یعنی abort نکرد و وارد "
            f"حلقهٔ ری‌استارت شد (گاردِ ریشهٔ غیرکانونی یا مارکر کار نکرده)."
        ) from None
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def t_the_seam_exists_at_all():
    """بدونِ `-OpsRoot` این تست ممکن نیست؛ اگر کسی درز را بردارد اینجا قرمز می‌شود."""
    src = _SCRIPT.read_text("utf-8")
    assert "$OpsRoot" in src, "درزِ -OpsRoot از اسکریپت حذف شده — گارد دوباره آزمون‌ناپذیر شد"
    assert "$CanonicalOps" in src, "مقایسه با مسیرِ کانونی حذف شده"


def t_default_ops_root_is_still_the_live_tree():
    """درز نباید رفتارِ عادی را عوض کرده باشد: اجرای بی‌آرگومان همان درختِ زنده.

    2026-08-10: در worktree، SELF_OPS ≠ live tree. این گارد فقط وقتی معنا دارد
    که از live tree اجرا شود. در worktree = ENV_BLOCKED (نه سبز، نه قرمز)."""
    if _IN_WORKTREE:
        return  # ENV_BLOCKED — live-tree-default check only valid in live tree
    src = _SCRIPT.read_text("utf-8")
    m = re.search(r'\$OpsRoot\s*=\s*"([^"]+)"', src)
    assert m, "پیش‌فرضِ -OpsRoot پیدا نشد"
    assert m.group(1).rstrip("\\").lower() == _LIVE_ROOT.rstrip("\\"), \
        f"پیش‌فرض از درختِ زنده منحرف شده: {m.group(1)}"


def t_clean_fixture_passes_preflight():
    root = _fixture()
    try:
        rc, out = _run(root)
        assert rc == 0, f"فیکسچرِ سالم باید عبور کند، ولی exit={rc}\n{out}"
        assert "none (clean)" in out, f"گزارشِ «مارکری نیست» غایب:\n{out}"
        assert "PLAN:" in out, f"به مرحلهٔ PLAN نرسید:\n{out}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_each_marker_alone_aborts():
    """هر چهار مارکر جدا سنجیده می‌شوند — وگرنه حذفِ سه‌تا از فهرست بی‌صدا می‌ماند."""
    for m in _MARKERS:
        root = _fixture(markers=(m,))
        try:
            rc, out = _run(root)
            assert rc == 1, f"مارکرِ {m} باید abort کند (exit 1)، ولی exit={rc}\n{out}"
            assert "ABORT" in out, f"کلمهٔ ABORT برای {m} نیامد:\n{out}"
            assert m in out, f"نامِ مارکرِ {m} در گزارش نیامد (مالک باید بداند کدام):\n{out}"
            assert "=== RESTART" not in out, f"با مارکرِ {m} وارد حلقهٔ ری‌استارت شد:\n{out}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def t_lf_flags_file_aborts():
    """فایلِ فلگِ LF: همان حادثهٔ «۵۹ از ۱۵۶ فلگ»."""
    root = _fixture(flags="lf")
    try:
        rc, out = _run(root)
        assert rc == 1, f"فایلِ فلگِ LF باید abort کند، ولی exit={rc}\n{out}"
        assert "CRLF" in out, f"دلیلِ CRLF توضیح داده نشد:\n{out}"
        assert "=== RESTART" not in out, f"با فلگِ شکسته ری‌استارت شروع شد:\n{out}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_missing_flags_file_aborts():
    root = _fixture(flags="missing")
    try:
        rc, out = _run(root)
        assert rc == 1, f"نبودِ فایلِ فلگ باید abort کند، ولی exit={rc}\n{out}"
        assert "flagless" in out or "missing" in out.lower(), f"دلیل توضیح داده نشد:\n{out}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_non_canonical_root_cannot_restart():
    """قلبِ ایمنیِ درز: ریشهٔ غیرکانونی بدونِ -WhatIf باید با خروجِ ۲ رد شود."""
    root = _fixture()
    try:
        # تایم‌اوتِ کوتاه عمدی: مسیرِ درست بی‌درنگ exit 2 می‌دهد، پس هر کندی یعنی
        # گارد نگرفته و اسکریپت جای abort دارد کار می‌کند.
        rc, out = _run(root, whatif=False, timeout=30)
        assert rc == 2, f"ریشهٔ غیرکانونی بدونِ -WhatIf باید exit=2 بدهد، ولی exit={rc}\n{out}"
        assert "preflight-only" in out, f"دلیلِ رد توضیح داده نشد:\n{out}"
        assert "=== RESTART" not in out, f"🔴 وارد حلقهٔ ری‌استارت شد با ریشهٔ ساختگی:\n{out}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_fixture_never_touches_the_live_tree():
    """ناوردیِ خودِ تست: هیچ مارکری در `_ops` واقعی ساخته یا جا نمانده باشد."""
    leftover = [m for m in _MARKERS if (_OPS / m).exists()]
    assert not leftover, f"🔴 مارکر در درختِ زنده جا مانده: {leftover}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    if _IN_WORKTREE:
        # ENV_BLOCKED: live-tree-default subtest was SKIPPED, not passed.
        # exit(2) = SKIP, so run_all does NOT count this as PASS.
        print(f"\n⏭️ test_restart_preflight: SKIP (ENV_BLOCKED — در worktree؛ "
              f"{len(checks) - failed}/{len(checks)} checks ran, "
              f"live-tree-default check skipped — NOT PASS)")
        sys.exit(2)
    print(f"\n{'✅' if not failed else '❌'} test_restart_preflight: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
