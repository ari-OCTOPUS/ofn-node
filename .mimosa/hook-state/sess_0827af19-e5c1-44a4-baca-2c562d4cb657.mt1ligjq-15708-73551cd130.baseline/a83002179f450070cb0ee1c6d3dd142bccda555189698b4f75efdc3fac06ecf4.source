"""test_self_patch_quota.py — سهمِ self_patch از سقفِ سراسریِ فوگو (۲۰۲۶-۰۸-۰۵).

رأیِ مالک (اجازهٔ کاملِ امشب): «همیشه ... سهمِ توکنش رو بگیره». این سهم
عیناً الگوی cockpit_brain._brain_cap/_brain_used/_brain_count است، فقط برای
self_patch — تا مرورِ روزانه یا پچ‌نویسیِ self_patch هرگز توسطِ بقیهٔ ارگانیسم
(که همان سقفِ مشترکِ fugu_quota را می‌خورد) بی‌صدا گرسنه نماند.

سخت‌ترین قیدها این‌جا:
  · گارد باید **قبل از** تماسِ پولی رد کند — مغز اصلاً نباید صدا زده شود
    (t_propose_never_calls_the_brain_once_quota_is_spent /
     t_review_never_calls_the_brain_once_quota_is_spent).
  · شمارندهٔ سهمِ self_patch نباید با شمارندهٔ DAILY_CAP (رکوردهای propose در
    همان `_dir()`) قاطی شود — وگرنه یک گارد، گاردِ دیگر را کور می‌کند
    (t_quota_counter_is_isolated_from_daily_cap_records).
  · اتمام‌شدنِ سهم باید **گذرا** شمرده شود، نه شکستِ نهاییِ نقص
    (t_drive_treats_self_patch_quota_as_transient_not_a_final_failure).

صفر شبکه: مغز همیشه تزریقی است.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("self-patch-quota")

sys.path.insert(0, str(_HERE.parent / "cortex"))
import self_patch as sp   # noqa: E402

ALLOWED = "_ops/cortex/local_llm.py"


def _flag(on):
    if on:
        os.environ[sp.FLAG] = "1"
    else:
        os.environ.pop(sp.FLAG, None)


def _reset():
    """صفرکردنِ کاملِ حالتِ سهمیه/صف/روز بینِ تست‌ها — یک تست نباید بعدی را
    از طریقِ فایل‌های مشترکِ state آلوده کند."""
    for p in (sp.SELF_PATCH_CALLS, sp.QUEUE_PATH, sp.REVIEW_STATE):
        try:
            p.unlink()
        except OSError:
            pass
    d = sp._dir()
    if d.exists():
        for f in d.glob("*.json"):
            try:
                f.unlink()
            except OSError:
                pass
    for k in (sp.SELF_PATCH_SHARE_ENV, "FUGU_DAILY_CALL_CAP"):
        os.environ.pop(k, None)


def _mk_ask(answer="patched content"):
    """ask_fn جاسوس — ضبط می‌کند چند بار و با چه چیزی صدا زده شد."""
    calls = []

    def ask(task, prompt, system="", max_tokens=400, tier=None, **kw):
        calls.append({"task": task, "tier": tier})
        return {"ok": True, "text": answer, "tier": "primary"}

    ask._calls = calls
    return ask


def _write_used(n, day=None):
    import time as _t
    day = day or _t.strftime("%Y-%m-%d")
    sp.SELF_PATCH_CALLS.parent.mkdir(parents=True, exist_ok=True)
    sp.SELF_PATCH_CALLS.write_text(json.dumps({"day": day, "n": n}), encoding="utf-8")


# ─── _self_patch_cap: مشتق از سقفِ سراسری، نه عددِ مستقل ────────────────────
def t_cap_derives_from_shared_fugu_cap_and_share_env():
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "60"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.12"
    try:
        assert sp._self_patch_cap() == max(1, int(60 * 0.12)) == 7
    finally:
        _reset()


def t_cap_falls_back_to_default_share_on_garbage_env():
    """سهمِ نامعتبر (خارج از (۰,۱]) یا غیرِعددی ⇒ پیش‌فرضِ ماژول، نه صفر و نه نامحدود."""
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "60"
    try:
        for bad in ("abc", "2", "0", "-0.5", ""):
            os.environ[sp.SELF_PATCH_SHARE_ENV] = bad
            assert sp._self_patch_cap() == max(1, int(60 * sp._SELF_PATCH_DEFAULT_SHARE)), bad
    finally:
        _reset()


def t_cap_is_at_least_one_even_with_a_tiny_share():
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "5"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.01"
    try:
        assert sp._self_patch_cap() == 1
    finally:
        _reset()


def t_cap_fails_closed_when_fugu_quota_is_unavailable():
    """اگر fugu_quota اصلاً import نشود، سقف باید ۰ باشد — نمی‌دانم یعنی خرج نکن،
    نه اینکه نامحدود فرض کنم."""
    _reset()
    real = sys.modules.get("fugu_quota")
    sys.modules["fugu_quota"] = None   # import fugu_quota → ImportError تضمینی
    try:
        assert sp._self_patch_cap() == 0
    finally:
        if real is not None:
            sys.modules["fugu_quota"] = real
        else:
            sys.modules.pop("fugu_quota", None)
        _reset()


# ─── _self_patch_used/_count: شمارندهٔ روزمحور، count-before-call ───────────
def t_used_is_scoped_to_today_and_ignores_other_days():
    _reset()
    _write_used(5, day="2000-01-01")
    assert sp._self_patch_used() == 0, "روزِ کهنه نباید امروز حساب شود"
    _write_used(3)
    assert sp._self_patch_used() == 3
    _reset()


def t_count_increments_before_any_network_attempt():
    _reset()
    assert sp._self_patch_used() == 0
    sp._self_patch_count()
    assert sp._self_patch_used() == 1
    sp._self_patch_count()
    assert sp._self_patch_used() == 2
    _reset()


def t_quota_counter_is_isolated_from_daily_cap_records():
    """رگرسیونِ حیاتی: calls.json نباید توسطِ `_today_count()` (که DAILY_CAP را
    می‌بندد) شمرده شود — چون آن یکی با `glob("*.json")` هر json ِ کنارش را
    می‌بلعد و DAILY_CAP را کاذب زودتر می‌بندد."""
    _reset()
    sp._self_patch_count()
    sp._self_patch_count()
    assert sp._today_count() == 0, "شمارندهٔ سهمیه با شمارندهٔ DAILY_CAP قاطی شد"
    _reset()


# ─── _self_patch_may_spend ──────────────────────────────────────────────────
def t_may_spend_blocks_once_the_cap_is_reached():
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.2"   # cap = 2
    try:
        assert sp._self_patch_cap() == 2
        allow, why = sp._self_patch_may_spend()
        assert allow and "0/2" in why
        _write_used(2)
        allow, why = sp._self_patch_may_spend()
        assert not allow and "self-patch-quota" in why, why
    finally:
        _reset()


# ─── سیمِ propose(): گاردِ سهمیه قبل از تماسِ پولی ───────────────────────────
def t_propose_never_calls_the_brain_once_quota_is_spent():
    _flag(True)
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.1"   # cap = 1
    try:
        _write_used(1)
        spy = _mk_ask()
        r = sp.propose(target_rel=ALLOWED, defect="x", ask_fn=spy,
                       shadow_fn=lambda t, c: {"green": True})
        assert r["ok"] is False and r["reason"] == "self-patch-quota", r
        assert spy._calls == [], "مغز نباید صدا زده شود — سهمِ self_patch تمام شده بود"
    finally:
        _flag(False)
        _reset()


def t_propose_proceeds_normally_while_quota_has_room():
    _flag(True)
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.5"   # cap = 5, plenty
    try:
        spy = _mk_ask("# fixed\nprint(1)\n")
        r = sp.propose(target_rel=ALLOWED, defect="نقصِ واقعی", ask_fn=spy,
                       shadow_fn=lambda t, c: {"green": True})
        assert r["ok"] is True, r
        assert len(spy._calls) == 1, "دقیقاً یک تماس باید بشود"
        assert sp._self_patch_used() == 1, "شمارنده باید قبل/همراهِ تماس بالا رفته باشد"
    finally:
        _flag(False)
        _reset()


# ─── سیمِ review_and_queue(): گاردِ سهمیه قبل از سوزاندنِ روز ────────────────
def t_review_never_calls_the_brain_once_quota_is_spent():
    _flag(True)
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.1"   # cap = 1
    try:
        _write_used(1)
        spy = _mk_ask("CLEAN")
        r = sp.review_and_queue(ask_fn=spy, targets=[ALLOWED])
        assert r["ok"] is False and r["reason"] == "self-patch-quota", r
        assert spy._calls == [], "مغز نباید صدا زده شود"
        assert not sp.REVIEW_STATE.exists(), \
            "روز نباید سوخته شود — تلاشِ واقعی اصلاً نیفتاد"
    finally:
        _flag(False)
        _reset()


def t_review_proceeds_normally_while_quota_has_room():
    _flag(True)
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.5"   # cap = 5
    try:
        spy = _mk_ask("CLEAN")
        r = sp.review_and_queue(ask_fn=spy, targets=[ALLOWED])
        assert r["ok"] is True, r
        assert len(spy._calls) == 1
        assert sp.REVIEW_STATE.exists()
    finally:
        _flag(False)
        _reset()


# ─── drive(): اتمامِ سهمیه گذرا است، نه شکستِ نهایی ─────────────────────────
def t_drive_treats_self_patch_quota_as_transient_not_a_final_failure():
    _flag(True)
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "10"
    os.environ[sp.SELF_PATCH_SHARE_ENV] = "0.1"   # cap = 1
    try:
        _write_used(1)
        sp._queue_append({"id": "sp-q1", "ts": "2026-01-01T00:00:00Z", "target": ALLOWED,
                          "defect": "d", "hint": "", "status": "open"})
        r = sp.drive(channel=None, ask_fn=_mk_ask(), shadow_fn=lambda t, c: {"green": True})
        assert not r.get("ok") and r.get("reason") == "self-patch-quota", r
        eff = sp._queue_effective()["sp-q1"]
        assert eff["status"] == "open", f"سهمیهٔ تمام‌شده باید گذرا باشد، نه failed: {eff}"
        assert eff["attempts"] == 1
    finally:
        _flag(False)
        _reset()


# ─── مستندسازیِ قفل‌شده: پیش‌فرض باید داخلِ بازهٔ توصیه‌شده بماند ─────────────
def t_default_share_is_within_the_recommended_band():
    assert 0.10 <= sp._SELF_PATCH_DEFAULT_SHARE <= 0.15, sp._SELF_PATCH_DEFAULT_SHARE


def t_default_share_comfortably_covers_self_patchs_real_daily_ceiling():
    """self_patch روزی حداکثر ۱ مرور + DAILY_CAP=۳ پیشنهاد = ۴ تماس می‌زند.
    سهمِ پیش‌فرض روی سقفِ زندهٔ ۶۰ باید این ۴ تا را با حاشیه پوشش دهد."""
    _reset()
    os.environ["FUGU_DAILY_CALL_CAP"] = "60"
    os.environ.pop(sp.SELF_PATCH_SHARE_ENV, None)   # پیش‌فرضِ ماژول
    try:
        real_daily_ceiling = 1 + sp.DAILY_CAP
        assert sp._self_patch_cap() >= real_daily_ceiling, \
            f"سهمِ پیش‌فرض ({sp._self_patch_cap()}) از سقفِ واقعیِ روزانه ({real_daily_ceiling}) کمتر است"
    finally:
        _reset()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_patch_quota: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
