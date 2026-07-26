"""test_self_patch.py — پلِ «نقص پیدا کردم» → «پچ نوشتم و تستش کردم».

رأیِ مالک ۲۰۲۶-۰۷-۲۶: «خودشو بهتر کنه، نه الکی فقط نگاه». مرزِ الف: می‌نویسد و
ایزوله تست می‌کند؛ اعمال همیشه یک کلیکِ جداست.

سخت‌ترین قیدها این‌جا **آن‌هایی‌اند که نباید اتفاق بیفتند**:
  · هیچ پچی بدونِ سوییتِ سبز به کارت تبدیل نشود (`t_a_red_shadow_never_becomes_a_card`)
  · allowlist هرگز این‌جا بازتعریف نشود — از code_autonomy قرض گرفته می‌شود
  · هرگز چیزی به درختِ زنده نوشته نشود
اگر این سه سبز بمانند و بقیه بشکنند، هنوز ایمن است؛ برعکسش نه.

صفر شبکه: مغز و شادو-تستر هر دو تزریقی‌اند.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("self-patch")

sys.path.insert(0, str(_HERE.parent / "cortex"))
import self_patch as sp      # noqa: E402
import code_autonomy as ca   # noqa: E402

ALLOWED = "_ops/telegram_center/live_commands.py"
DENIED = "_ops/budget/approval_channel.py"


def _flag(on):
    if on:
        os.environ[sp.FLAG] = "1"
    else:
        os.environ.pop(sp.FLAG, None)


def _brain(text):
    def fn(task, prompt, system="", max_tokens=4000, tier=None):
        assert tier == "primary", "نوشتنِ کد باید به لایهٔ سنگین برود"
        return {"ok": True, "tier": "primary", "text": text}
    return fn


def _shadow(green, **extra):
    def fn(target, content):
        return {"ok": True, "green": green, "target": target,
                "diff": " 1 file changed, 2 insertions(+)", **extra}
    return fn


# ─── گیت‌ها ─────────────────────────────────────────────────────────────────
def t_flag_off_does_nothing():
    _flag(False)
    r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain("y"),
                   shadow_fn=_shadow(True))
    assert r == {"ok": False, "reason": "flag-off"}


def t_allowlist_is_borrowed_not_redefined():
    """این ماژول نباید allowlist خودش را بسازد — یک حقیقت، یک نگهبان."""
    import inspect
    src = inspect.getsource(sp)
    assert "allowed_target" in src, "باید از code_autonomy.allowed_target استفاده کند"
    for banned in ("_ALLOW_ROOTS", "_DENY = ", "allowlist = ["):
        assert banned not in src, f"allowlist این‌جا بازتعریف شده: {banned!r}"


def t_a_denied_target_is_refused_before_the_brain_is_asked():
    _flag(True)
    asked = []

    def spy(task, prompt, system="", max_tokens=4000, tier=None):
        asked.append(task)
        return {"ok": True, "text": "x"}
    try:
        r = sp.propose(target_rel=DENIED, defect="x", ask_fn=spy,
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "target-not-allowed", r
        assert asked == [], "مغز نباید برای هدفِ ممنوع اصلاً صدا زده شود"
    finally:
        _flag(False)


def t_money_and_secret_paths_stay_denied():
    """گاردِ صریح روی مسیرهایی که هرگز نباید خودتغییر شوند."""
    for p in ("_ops/budget/budgets.yaml", "_ops/.env", "_ops/genome/x.py",
              "_ops/state/ledger.jsonl", "_ops/money_effector.py", ".git/config"):
        assert not ca.allowed_target(p), f"{p} نباید مجاز باشد"


# ─── قیدِ اصلی: قرمز هرگز کارت نمی‌شود ──────────────────────────────────────
def t_a_red_shadow_never_becomes_a_card():
    """قلبِ ایمنیِ مرزِ الف. پچی که سوییت را نمی‌گذراند نباید توجهِ مالک را بخورد."""
    _flag(True)
    try:
        r = sp.propose(target_rel=ALLOWED, defect="یک نقص",
                       ask_fn=_brain("# changed\nprint(1)\n"),
                       shadow_fn=_shadow(False))
        assert r["ok"] is False and r["reason"] == "shadow-red", r
        assert r["green"] is False
    finally:
        _flag(False)


def t_a_green_shadow_produces_a_proposal():
    _flag(True)
    try:
        r = sp.propose(target_rel=ALLOWED, defect="یک نقصِ واقعی", fix_hint="کوتاهش کن",
                       ask_fn=_brain("# fixed\nprint(1)\n"),
                       shadow_fn=_shadow(True))
        assert r["ok"] is True and r["green"] is True, r
        assert r["target"] == ALLOWED and r["id"].startswith("sp-")
        assert r["bytes_after"] > 0 and r["bytes_before"] > 0
    finally:
        _flag(False)


def t_an_unchanged_candidate_is_honesty_not_success():
    """سیستم‌پرامپت می‌گوید اگر مطمئن نیستی فایل را دست‌نخورده برگردان.
    آن حالت نباید به‌عنوان پچ جا زده شود."""
    _flag(True)
    src = (Path(sp._HERE).parent / ALLOWED).read_text("utf-8")
    try:
        r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain(src),
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "no-change-proposed", r
    finally:
        _flag(False)


def t_brain_silence_is_not_a_patch():
    _flag(True)
    try:
        for empty in ("", "   ", "```\n```"):
            r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain(empty),
                           shadow_fn=_shadow(True))
            assert r["ok"] is False and r["reason"] == "brain-no-answer", r
    finally:
        _flag(False)


def t_code_fences_are_stripped():
    assert sp._strip_fences("```python\nprint(1)\n```") == "print(1)"
    assert sp._strip_fences("print(1)") == "print(1)"


# ─── سقفِ روزانه و بی‌اثری روی درختِ زنده ───────────────────────────────────
def t_daily_cap_protects_owner_attention():
    _flag(True)
    d = sp._dir()
    d.mkdir(parents=True, exist_ok=True)
    made = []
    try:
        for i in range(sp.DAILY_CAP):
            p = d / f"cap-{i}.json"
            p.write_text("{}", encoding="utf-8")
            made.append(p)
        r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=_brain("print(1)"),
                       shadow_fn=_shadow(True))
        assert r["ok"] is False and r["reason"] == "daily-cap", r
    finally:
        for p in made:
            try:
                p.unlink()
            except OSError:
                pass
        _flag(False)


def t_it_never_writes_to_the_live_tree():
    """قیدِ سخت: تنها اثرِ جانبیِ مجاز، رکوردِ پیشنهاد در state است."""
    _flag(True)
    target = Path(sp._HERE).parent / ALLOWED
    before = target.read_bytes()
    try:
        sp.propose(target_rel=ALLOWED, defect="x",
                   ask_fn=_brain("# مهاجم\nprint('pwned')\n"),
                   shadow_fn=_shadow(True))
        assert target.read_bytes() == before, "فایلِ زنده عوض شد — نقضِ مرزِ الف"
    finally:
        _flag(False)


def t_the_card_says_what_happens_if_ignored():
    """طبق دکترین D1 — کارتِ بی‌پیامدِ بی‌عملی ساخته نمی‌شود."""
    txt = sp.card_text({"target": "x.py", "defect": "d", "diff": "1 file changed"})
    assert "نکنی" in txt, "کارت نمی‌گوید اگر کاری نکنی چه می‌شود"
    assert "x.py" in txt and "سبز" in txt


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_patch: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
