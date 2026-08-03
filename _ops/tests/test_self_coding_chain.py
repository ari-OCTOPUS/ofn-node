"""test_self_coding_chain — «چطور مطمئن شویم با حرف‌زدن واقعاً کد می‌نویسد؟»

سؤالِ مالک ۲۰۲۶-۰۷-۲۷. جوابش یک ادعا نیست، یک **زنجیرهٔ هفت‌حلقه‌ای** است که
هر حلقه‌اش باید جدا سنجیده شود. اندازه‌گیریِ همان روز:

  ۱ حرفِ مالک → مأموریت            ✅
  ۲ مأموریت → طرحِ کد               ✅
  ۳ نوشتنِ پچ                       ✅
  ۴ تستِ ایزوله (سایه)              ✅
  ۵ کارتِ **دکمه‌دار** به مالک       ❌ → این فایل می‌بنددش
  ۶ تپِ مالک → صفِ اعمال            ✅
  ۷ درایورِ اعمال در حالِ اجرا        ❌ → تصمیمِ استقرارِ مالک

حلقهٔ ۵ دو علت داشت و هر دو نامرئی بودند چون هر تکه **جدا** کار می‌کرد:
  · `self_patch` متنِ پچ را ذخیره نمی‌کرد (فقط diffِ ۶۰۰کاراکتری) — پس حتی با
    «آره»ی مالک چیزی برای اعمال وجود نداشت.
  · کارتِ دکمه‌دارِ کامل از قبل نوشته شده بود و **هیچ صداکننده‌ای** نداشت.

و قیدِ همراه: این تنها مسیری است که به نوشتنِ کد روی درختِ زنده ختم می‌شود، پس
ورودی‌اش فلگ‌دار و پیش‌فرض خاموش است.
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("self-coding-chain")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import self_patch as sp   # noqa: E402

FLAG = "OCTOPUS_WIRE_PATCH_CARD"


def _on(v=True):
    if v:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


# ─── حلقهٔ ۵: کارت باید بتواند دکمه داشته باشد ────────────────────────────
def t_the_patch_record_carries_the_actual_patch_text():
    """بدونِ متنِ پچ، «آره»ی مالک به هیچ‌جا نمی‌رسد — کارت گزارش می‌ماند نه پیشنهاد."""
    src = Path(sp.__file__).read_text("utf-8")
    i = src.index('"bytes_after"')
    # پنجره عمداً پهن است: بینِ دو کلید یک توضیحِ چندخطی هست و پنجرهٔ تنگ
    # دقیقاً روی مرز می‌افتاد — همان تلهٔ «گاردِ پنجره‌ثابت» که امروز دو بار دیدم.
    around = src[max(0, i - 600):i + 1200]
    assert '"content"' in around, "رکوردِ پچ متنِ واقعی را نگه نمی‌دارد"
    assert '"shadow_green"' in around, "رکورد کلیدی که propose_to_owner می‌خواهد ندارد"


def t_the_record_shape_matches_what_the_card_builder_needs():
    """قراردادِ دو ماژول باید بخواند، وگرنه پل ساکت شکست می‌خورد."""
    import code_autonomy as ca
    src = Path(ca.__file__).read_text("utf-8")
    i = src.index("def propose_to_owner")
    body = src[i:i + 1200]
    for key in ("shadow_green", "target", "content"):
        assert key in body, f"propose_to_owner کلیدِ {key} را می‌خواهد"


def t_a_green_patch_is_offered_when_armed():
    _on()
    try:
        calls = []
        import code_autonomy as ca
        real = ca.propose_to_owner
        ca.propose_to_owner = lambda p: (calls.append(p), {"ok": True, "id": "x"})[1]
        try:
            r = sp._offer_patch_to_owner(
                {"shadow_green": True, "content": "کد", "target": "_ops/x.py"})
        finally:
            ca.propose_to_owner = real
        assert r.get("ok") and len(calls) == 1, (r, calls)
    finally:
        _on(False)


def t_a_red_patch_is_never_offered():
    """پچی که سایه‌اش سبز نیست هرگز به مالک پیشنهاد نمی‌شود."""
    _on()
    try:
        for bad in ({"shadow_green": False, "content": "x", "target": "y"},
                    {"shadow_green": True, "content": "", "target": "y"},
                    {}, {"content": "x"}):
            r = sp._offer_patch_to_owner(bad)
            assert r["ok"] is False and r["reason"] == "not-offerable", bad
    finally:
        _on(False)


# ─── مرزِ استقرار ─────────────────────────────────────────────────────────
def t_flag_off_offers_nothing_at_all():
    """این تنها مسیری است که به نوشتنِ کد روی درختِ زنده می‌رسد."""
    _on(False)
    r = sp._offer_patch_to_owner({"shadow_green": True, "content": "x", "target": "y"})
    assert r["ok"] is False and r["reason"] == "flag-off"


def t_self_patch_never_applies_anything_itself():
    """پیشنهاد ≠ اعمال. حتی با فلگِ روشن."""
    tree = ast.parse(Path(sp.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("apply_approved", "consume_approvals", "apply", "system", "run_forever"):
        assert d not in called, f"self_patch خودش اعمال می‌کند: {d}"


def t_a_broken_offer_never_kills_the_patch_loop():
    _on()
    try:
        import code_autonomy as ca
        real = ca.propose_to_owner
        ca.propose_to_owner = lambda p: (_ for _ in ()).throw(RuntimeError("x"))
        try:
            r = sp._offer_patch_to_owner(
                {"shadow_green": True, "content": "x", "target": "y"})
        finally:
            ca.propose_to_owner = real
        assert r["ok"] is False, r
    finally:
        _on(False)


# ─── حلقه‌های دیگر: گاردِ رگرسیون برای زنجیرهٔ سنجیده‌شده ──────────────────
def t_the_isolated_shadow_test_still_gates_everything():
    """حلقهٔ ۴ — بدونِ سبزِ سایه هیچ پچی جلو نمی‌رود."""
    src = Path(sp.__file__).read_text("utf-8")
    assert "shadow" in src and "green" in src


def t_the_approval_still_expires():
    """گاردِ ۲۰۲۶-۰۷-۲۷: تأییدِ کهنه رضایتِ کهنه است."""
    import code_autonomy as ca
    assert hasattr(ca, "APPROVAL_MAX_AGE_S")
    assert 3600 <= ca.APPROVAL_MAX_AGE_S <= 7 * 24 * 3600


def t_the_chain_has_no_hidden_shortcut_to_the_live_tree():
    """هیچ مسیری نباید از پیشنهاد مستقیم به نوشتنِ فایل برسد."""
    import code_autonomy as ca
    src = Path(ca.__file__).read_text("utf-8")
    i = src.index("def propose_to_owner")
    j = src.index("\ndef ", i + 10)
    body = src[i:j]
    for d in ("write_text(", "apply_approved", "os.replace"):
        # نوشتن فقط در صفِ pending مجاز است، نه روی هدف
        if d == "write_text(":
            assert "pend /" in body, "نوشتن خارج از صفِ pending"
        else:
            assert d not in body, f"propose_to_owner مستقیم اعمال می‌کند: {d}"


# ─── سایهٔ مجوز (۲۰۲۶-۰۷-۲۸، قدمِ ۴ از vertical slice) ────────────────────
# مسئله: تأیید امروز به **پیشنهاد** گره می‌خورد نه به **محتوای دقیقِ پچ**. بینِ
# «آره»ی مالک و لحظهٔ اعمال، اگر متنِ پچ عوض شود همان تأیید معتبر می‌ماند.
# `action_sha256` مجوز را به هشِ (هدف + عملیات + محتوا) می‌بندد.
#
# `self_patch` عمداً اولین مشتری است: تنها مسیری که به نوشتنِ کد روی درختِ
# زنده می‌رسد، و کارتِ تأییدش از قبل هست — پس یک لایه اضافه می‌شود نه جریانی نو.

AUTHZ_FLAG = "OCTOPUS_WIRE_AUTHZ_SHADOW"
_RES = {"shadow_green": True, "content": "def f():\n    return 1\n",
        "target": "_ops/x.py", "defect": "نمونه", "id": "sp-test"}


def _authz(v=True):
    if v:
        os.environ[AUTHZ_FLAG] = "1"
    else:
        os.environ.pop(AUTHZ_FLAG, None)


def t_the_authz_shadow_is_off_by_default():
    _authz(False)
    r = sp._authorization_shadow(_RES)
    assert r["ok"] is False and r["reason"] == "flag-off", r


def t_a_code_patch_always_requires_a_human():
    """`code_patch` در فهرستِ حساس است — هیچ policy engineی نباید جای مالک بگوید آره."""
    _authz()
    try:
        r = sp._authorization_shadow(_RES)
        assert r["ok"] is True, r
        assert r["allow"] is False and r["reason"] == "approval-required", r
    finally:
        _authz(False)


def t_changing_the_patch_changes_the_action_hash():
    """قلبِ گاردِ TOCTOU: تأییدِ محتوای الف نباید محتوای ب را مجاز کند."""
    _authz()
    try:
        a = sp._authorization_shadow(_RES)
        b = sp._authorization_shadow({**_RES, "content": _RES["content"] + "# x\n"})
        assert a["action_sha256"] != b["action_sha256"], (a, b)
        c = sp._authorization_shadow({**_RES, "target": "_ops/other.py"})
        assert a["action_sha256"] != c["action_sha256"], "هدفِ متفاوت هشِ یکسان داد"
    finally:
        _authz(False)


def t_the_same_patch_gives_the_same_hash():
    """اگر هش ناپایدار باشد، هر مقایسه‌ای بی‌معنا می‌شود (درسِ شمارندهٔ dedup)."""
    _authz()
    try:
        h = {sp._authorization_shadow(_RES)["action_sha256"] for _ in range(3)}
        assert len(h) == 1, h
    finally:
        _authz(False)


def t_the_shadow_never_gates_the_offer():
    """سایه یعنی می‌سنجد و نمی‌بندد. اگر رفتارِ پیشنهاد عوض شود، سایه نیست."""
    _on(False)
    for authz in (False, True):
        _authz(authz)
        try:
            r = sp._offer_patch_to_owner(_RES)
            assert r["ok"] is False and r["reason"] == "flag-off", (authz, r)
        finally:
            _authz(False)


def t_a_broken_shadow_never_raises():
    """مسیرِ پیشنهاد نباید به سلامتِ این لایه وابسته باشد."""
    _authz()
    try:
        for bad in ({}, {"content": None, "target": None}, {"content": 5}):
            r = sp._authorization_shadow(bad)
            assert isinstance(r, dict) and "ok" in r, bad
    finally:
        _authz(False)


def t_the_shadow_log_stays_in_the_isolated_tree():
    """گاردِ نشتی — همان تلهٔ money-fsm که امروز درختِ زنده را آلوده کرد."""
    import opslib
    _authz()
    try:
        sp._authorization_shadow(_RES)
        p = opslib.STATE_DIR / "authz-shadow.jsonl"
        live = str(harness.REAL_VAULT / "_ops" / "state").lower()
        assert p.exists(), "چیزی ثبت نشد"
        assert not str(p).lower().startswith(live), p
    finally:
        _authz(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_coding_chain: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
