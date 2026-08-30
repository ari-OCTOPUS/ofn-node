#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_target_guard — گاردِ مقصدِ پچ: resolve قبل از قضاوت.

این فایل **کورپوسِ فرارِ واقعی** را می‌سنجد — همان مسیرهایی که در ۲۰۲۶-۰۷-۳۰ روی
تابعِ زندهٔ `code_autonomy.allowed_target` سنجیده شدند و هر چهار `True` دادند.
اگر روزی این گارد وصل شود و کسی resolve را بردارد، این فایل قرمز می‌شود.

⚠️ این تست‌ها **درختِ زنده را لمس نمی‌کنند**: ریشه یک tmpdir واقعی است که
خودشان می‌سازند (resolve به فایلِ واقعی نیاز ندارد ولی به ریشهٔ واقعی بله —
روی ویندوز `resolve()` روی مسیرِ ناموجود هم `..` را می‌بندد).
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cortex"))

import target_guard as tg  # noqa: E402

_ROOT = Path(tempfile.mkdtemp(prefix="target-guard-")).resolve()
for _d in ("_ops/cortex", "_ops/state/pulse", "_ops/tests", "_ops/telegram_center",
           "PRE-0", "_ops/cortex-evil"):
    (_ROOT / _d).mkdir(parents=True, exist_ok=True)


def _ok(p):
    return tg.is_allowed(p, repo_root=_ROOT)


# ── کورپوسِ فرار — همان چهار موردی که گاردِ امروز رد می‌کند ─────────────────
def t_traversal_out_of_the_allow_root_is_rejected():
    """`..` نباید از allow-root بیرون بزند — این دقیقاً سوراخِ ۰۷-۳۰ است."""
    r = tg.check("_ops/cortex/../../PRE-0/governance.py", repo_root=_ROOT)
    assert r["ok"] is False, r
    assert r["reason"] in ("outside-allow-roots", "deny:pre-0/", "deny:governance"), r


def t_traversal_into_the_verifier_is_rejected():
    """سوییت = verifier؛ پچی که آن را عوض کند معیارِ پذیرش را عوض کرده."""
    r = tg.check("_ops/cortex/../tests/run_all.py", repo_root=_ROOT)
    assert r["ok"] is False, r


def t_the_guard_cannot_rewrite_itself():
    for p in ("_ops/cortex/code_autonomy.py",
              "_ops/cortex/../../_ops/cortex/code_autonomy.py",
              "_ops/cortex/target_guard.py",
              "_ops/cortex/code_brain.py"):
        assert _ok(p) is False, p


def t_the_kill_switch_is_never_writable():
    assert _ok("_ops/telegram_center/power.py") is False
    assert _ok("_ops/cortex/../telegram_center/power.py") is False


def t_the_evaluator_and_prereg_are_never_writable():
    """T18: اگر پچ بتواند ارزیاب یا پیش‌ثبت را عوض کند، آستانه پس از نتیجه جابه‌جا می‌شود."""
    for p in ("_ops/cortex/../held_out_evaluator.py",
              "_ops/cortex/../prereg.py",
              "_ops/cortex/../cycle_evaluator.py"):
        assert _ok(p) is False, p


# ── دام‌های ویندوزی ─────────────────────────────────────────────────────────
def t_case_variation_does_not_bypass_deny():
    """NTFS به حروف حساس نیست؛ گاردی که باشد، گارد نیست."""
    assert _ok("_OPS/CORTEX/../../PRE-0/GOVERNANCE.py") is False
    assert _ok("_ops/CORTEX/CODE_AUTONOMY.py") is False


def t_absolute_and_unc_and_drive_paths_are_rejected():
    for p in ("/etc/passwd", "//server/share/x.py", r"C:\Windows\System32\x.py",
              "C:/Windows/x.py"):
        r = tg.check(p, repo_root=_ROOT)
        assert r["ok"] is False, (p, r)
        assert r["reason"] in ("absolute-or-unc", "drive-letter"), (p, r)


def t_sibling_prefix_is_not_containment():
    """`_ops/cortex-evil` با startswith داخلِ `_ops/cortex` دیده می‌شود — نباید."""
    assert _ok("_ops/cortex-evil/x.py") is False


def t_empty_and_nul_are_fail_closed():
    for p in ("", "   ", None, "a\x00b.py"):
        assert tg.is_allowed(p, repo_root=_ROOT) is False, p


def t_a_directory_itself_is_not_a_target():
    """ریشه با خودش contained نیست (len(cp) > len(pp))."""
    assert _ok("_ops/cortex") is False
    assert _ok("_ops/cortex/") is False


# ── مسیرهای مجاز واقعاً مجازند (گاردِ ضدِ over-blocking) ─────────────────────
def t_legitimate_cortex_and_state_targets_pass():
    for p in ("_ops/cortex/improve.py", "_ops/cortex/synthesis.py",
              "_ops/state/pulse/work-plan.json"):
        r = tg.check(p, repo_root=_ROOT)
        assert r["ok"] is True, (p, r)
        assert r["rel"].startswith("_ops/"), r


def t_allow_roots_match_the_owner_vote_not_the_current_code():
    """رأیِ L3 = cortex + state. `telegram_center` عمداً نیست (VQ-SELFGOAL-005)."""
    assert tg.DEFAULT_ALLOW_ROOTS == ("_ops/cortex", "_ops/state")
    assert _ok("_ops/telegram_center/render.py") is False


def t_deny_is_evaluated_on_the_resolved_path_not_the_raw_string():
    """اگر deny روی رشتهٔ خام بنشیند، یک `..` دورش می‌زند."""
    r = tg.check("_ops/state/../cortex/code_autonomy.py", repo_root=_ROOT)
    assert r["ok"] is False and r["reason"].startswith("deny:"), r
    assert r["rel"] == "_ops/cortex/code_autonomy.py", r    # قضاوت روی resolve‌شده


# ── جهشِ قرمزکننده (mutation proof) ─────────────────────────────────────────
def t_mutation_removing_resolution_reopens_the_hole():
    """اثباتِ دندان‌داری: با گاردِ زیررشته‌ایِ *امروز*، کورپوسِ فرار عبور می‌کند.

    این بند خودِ پیاده‌سازیِ فعلیِ `code_autonomy` را بازتولید می‌کند تا نشان دهد
    این تست‌ها تزئینی نیستند — همان ورودی که این‌جا رد می‌شود، آن‌جا رد **نمی**‌شود.
    (اجرای واقعیِ جهش، نه ادعای آن.)"""
    _DENY = ("organism", "genome", ".git", ".env", "secret")
    _ALLOW = ("_ops/telegram_center/", "_ops/cortex/")

    def substring_guard(path):          # ← دقیقاً منطقِ code_autonomy.allowed_target
        p = str(path or "").replace("\\", "/").lower()
        if not p or any(d in p for d in _DENY):
            return False
        return any(r in p for r in _ALLOW)

    escapes = ("_ops/cortex/../../PRE-0/governance.py",
               "_ops/cortex/../tests/run_all.py",
               "_ops/telegram_center/power.py")
    for p in escapes:
        assert substring_guard(p) is True, f"جهش باید عبور بدهد: {p}"
        assert _ok(p) is False, f"گاردِ نو باید ببندد: {p}"


if __name__ == "__main__":
    import harness
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_target_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
