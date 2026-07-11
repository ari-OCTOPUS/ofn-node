#!/usr/bin/env python3
"""تستِ standalone برای human_append_guard (E16).
اجرا: python3 test_human_append_guard.py
بدونِ pytest و بدونِ importِ هستهٔ ارگانیسم (فایل‌های هسته در این checkout بریده‌اند)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "budget"))
import human_append_guard as G  # noqa: E402

# ایزولاسیونِ تست: هرگز به alertِ زندهٔ opslib دست نزن (این تست standalone است، بدونِ harness).
G._emit_shadow_alert = lambda msg: None


class _C:
    failed = 0


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


secret = b"test-secret-abc-123"
g = G.HumanAppendGuard(secret, ttl_s=100)

# ۱) human-append قانونی → مجاز
tok = g.mint("appr-1", "VERDICT")
ok, r = g.authorize("VERDICT", True, token=tok, approval_id="appr-1")
check("legit human-append authorized", ok and r == "ok")

# ۲) replay (همان token دوباره) → رد
ok2, r2 = g.authorize("VERDICT", True, token=tok, approval_id="appr-1")
check("replay rejected", (not ok2) and r2 == "replay")

# ۳) بدونِ token → رد
ok3, r3 = g.authorize("VERDICT", True, token=None)
check("missing token rejected", (not ok3) and r3 == "missing-token")

# ۴) tamperِ event_type (token برای VERDICT، استفاده برای PAYMENT) → رد
tok2 = g.mint("appr-2", "VERDICT")
ok4, r4 = g.authorize("PAYMENT", True, token=tok2, approval_id="appr-2")
check("event_type tamper rejected", (not ok4) and r4 == "bad-signature")

# ۵) tamperِ امضا → رد
tok3 = g.mint("appr-3", "VERDICT")
bad = tok3[:-1] + ("0" if tok3[-1] != "0" else "1")
ok5, r5 = g.authorize("VERDICT", True, token=bad, approval_id="appr-3")
check("signature tamper rejected", (not ok5) and r5 == "bad-signature")

# ۶) منقضی → رد
g_exp = G.HumanAppendGuard(secret, ttl_s=-1)
tok4 = g_exp.mint("appr-4", "VERDICT")
ok6, r6 = g_exp.authorize("VERDICT", True, token=tok4, approval_id="appr-4")
check("expired token rejected", (not ok6) and r6 == "expired")

# ۷) گاردِ disabled → passthrough (backward-compat)
g_off = G.HumanAppendGuard(None)
ok7, r7 = g_off.authorize("VERDICT", True, token=None)
check("disabled guard passthrough", ok7 and r7 == "guard-disabled-passthrough")

# ۸) append غیرِ انسانی → دست‌نخورده (چیزی برای authorize نیست)
ok8, r8 = g.authorize("NOTE", False)
check("non-human append untouched", (not ok8) and r8 == "not-human-append")

# ۹) عدمِ تطابقِ approval_id → رد
tok5 = g.mint("appr-5", "VERDICT")
ok9, r9 = g.authorize("VERDICT", True, token=tok5, approval_id="WRONG")
check("approval-id mismatch rejected", (not ok9) and r9 == "approval-id-mismatch")

# ۱۰) mint وقتی گارد disabled است → خطا (نمی‌تواند راز جعل کند)
try:
    g_off.mint("x", "VERDICT")
    check("disabled guard cannot mint", False)
except G.HumanAppendError:
    check("disabled guard cannot mint", True)

# ۱۱) strict + بی‌سکرت → DENY (fail-closed، default-deny) — رفعِ #۱ سند ۲۰۲۷، رأی مالک «برو»
g_strict = G.HumanAppendGuard(None, strict=True)
ok11, r11 = g_strict.authorize("VERDICT", True, token=None)
check("strict fail-closed denies (no secret)", (not ok11) and r11 == "fail-closed-no-secret")

# ۱۲) strict + سکرتِ واقعی → مسیرِ HMAC دست‌نخورده (strict فقط شاخهٔ بی‌سکرت را می‌بندد)
g_strict_sec = G.HumanAppendGuard(secret, strict=True)
tokS = g_strict_sec.mint("appr-s", "VERDICT")
ok12, r12 = g_strict_sec.authorize("VERDICT", True, token=tokS, approval_id="appr-s")
check("strict + secret keeps HMAC path", ok12 and r12 == "ok")

# ۱۳) shadow_alert + بی‌سکرت → همان passthrough (رفتار عوض نمی‌شود)
g_shadow = G.HumanAppendGuard(None, shadow_alert=True)
ok13, r13 = g_shadow.authorize("VERDICT", True, token=None)
check("shadow-alert keeps passthrough (no behavior change)",
      ok13 and r13 == "guard-disabled-passthrough")

# ۱۴) default (نه strict) + بی‌سکرت → passthrough (byte-identical با امروز)
ok14, r14 = G.HumanAppendGuard(None).authorize("VERDICT", True, token=None)
check("default still passthrough (backward-compat)",
      ok14 and r14 == "guard-disabled-passthrough")

# ۱۵) guard_from_env: با فلگ → deny؛ بدونِ فلگ → passthrough
os.environ[G._ENV_STRICT] = "1"
oke, re_ = G.guard_from_env(None).authorize("VERDICT", True, token=None)
os.environ.pop(G._ENV_STRICT, None)
okf, rf = G.guard_from_env(None).authorize("VERDICT", True, token=None)
check("guard_from_env flag->deny, unset->passthrough",
      (not oke) and re_ == "fail-closed-no-secret"
      and okf and rf == "guard-disabled-passthrough")

print("\n== %d failure(s) ==" % _C.failed)
sys.exit(1 if _C.failed else 0)
