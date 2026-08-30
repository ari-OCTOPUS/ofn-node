#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 (۲۰۲۶-۰۸-۰۳) — رأیِ مالک باید در گیت رد داشته باشد، نه فقط در یک فایلِ ignored.

‏`_ops/OCTOPUS-flags.cmd` عمداً gitignore است (ممکن است secret بگیرد)، پس هر
رأیی که به فلگ تبدیل می‌شد **در هیچ کامیتی نبود** — تمدیدِ ۰۸-۰۳ ِ دو استثنا فقط
روی یک ماشین زندگی می‌کرد. حالا `_ops/owner-verdicts.yaml` ِ tracked همان
knobهای غیرمحرمانه را نگه می‌دارد و خواننده‌ها وقتی env غایب است از آن می‌خوانند.

سنجهٔ پذیرشِ پلن: «حذفِ آزمایشیِ فلگ‌های تاریخ‌دار → همان مقادیر از فایل خوانده
شوند» ⇒ `t_the_window_survives_a_missing_flags_file` و خواهرش برای سهمیه.

سه ناوردا که عمداً قفل شده‌اند:
  • **env برنده است** — وگرنه این فایل یک منبعِ رقیب می‌شد و رفتارِ امروز عوض.
  • **واگرایی ساکت نیست** — `drift()` نام‌به‌نام می‌گوید.
  • **fail-soft مطلق** — این ماژول در مسیرِ پول صدا زده می‌شود؛ فایلِ خراب یعنی
    برگشت به رفتارِ env-only، نه استثنا.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

import owner_verdicts as ov  # noqa: E402

KNOBS = ("OCTOPUS_SPEND_CAP_USD", "OCTOPUS_SPEND_CAP_UNTIL",
         "OCTOPUS_GOAL_MAX_CIRCULAR", "OCTOPUS_GOAL_MAX_CIRCULAR_UNTIL",
         "OCTOPUS_NEURAL_LEARNED_APPLY", "OCTOPUS_WIRE_CHRONO_RHYTHM")


def _clear():
    for k in KNOBS:
        os.environ.pop(k, None)


def _load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tmp_yaml(body: str) -> str:
    p = Path(tempfile.mkdtemp(prefix="verdicts-")) / "owner-verdicts.yaml"
    p.write_text(body, encoding="utf-8")
    return str(p)


# ── فایلِ زندهٔ والت ────────────────────────────────────────────────────────

def t_the_live_file_declares_both_dated_knobs():
    """۲۰۲۶-۰۸-۰۴ — دامنه باریک شد، دندان نه.

    نسخهٔ اول روی **هر** رأی حلقه می‌زد و `until`/`until_env` می‌خواست، چون وقتی
    نوشته شد هر دو رأیِ موجود پنجرهٔ تاریخ‌دار بودند. با آمدنِ `fugu_weekly_share`
    (سیاستِ ماندگارِ درصدی، بدونِ انقضا) آن فرض شکست. گذاشتنِ تاریخِ جعلی یعنی
    بودجهٔ مالک یک روزِ دلخواه بی‌صدا به پیش‌فرض برگردد — بدتر از قرمزِ تست.

    پس: رأیِ تاریخ‌دار همان قرارداد را کامل نگه می‌دارد، و رأیِ ماندگار **باید
    صریح** خودش را `standing: yes` اعلام کند. حذفِ `until` بدونِ آن اعلام همچنان
    قرمز است — یعنی «فراموش کردم تاریخ بگذارم» از «عمداً ماندگار است» تفکیک
    می‌شود و گارد بی‌دندان نمی‌شود."""
    v = ov.load()
    assert set(v) >= {
        "spend_cap", "goal_max_circular", "neural_learned_apply",
        "chrono_rhythm_cr_b0",
    }, sorted(v)
    for name, spec in v.items():
        for key in ("env", "value", "decided", "reader"):
            assert spec.get(key), (name, key, spec)
        if str(spec.get("standing") or "").lower() in ("yes", "true", "1"):
            assert not spec.get("until"), (
                name, "رأیِ ماندگار نباید تاریخِ انقضا داشته باشد", spec)
            continue
        for key in ("until_env", "until"):
            assert spec.get(key), (
                name, key,
                "رأیِ تاریخ‌دار باید انقضا اعلام کند، یا صریح `standing: yes` شود",
                spec)


def t_the_live_file_carries_no_secret_looking_keys():
    """گاردِ ساختاری: این فایل tracked است؛ secret آن‌جا ابدی می‌شود."""
    banned = ("token", "secret", "key", "password", "seed", "wallet", "api")
    text = Path(ov.path()).read_text(encoding="utf-8").lower()
    for spec in ov.load().values():
        for k in spec:
            assert not any(b in k.lower() for b in banned), (k, spec)
    assert "sk-" not in text and "bearer " not in text


# ── سنجهٔ پذیرش: بدونِ flags.cmd هم رأی زنده است ────────────────────────────

def t_the_window_survives_a_missing_flags_file():
    _clear()
    bg = _load_module("bg_a2", "04 - Architect System/scripts/budget_gate.py")
    r = bg.spend_cap_now(30.0, 1.5, 500.0, today="2026-08-07")
    assert r["window_open"] and r["value_aud"] == 300.0, r
    gone = bg.spend_cap_now(30.0, 1.5, 500.0, today="2026-08-14")
    assert gone["value_aud"] == 30.0 and gone.get("expired"), gone


def t_the_quota_survives_a_missing_flags_file():
    _clear()
    if str(OPS / "cortex") not in sys.path:
        sys.path.insert(0, str(OPS / "cortex"))
    gd = _load_module("gd_a2", "_ops/cortex/goal_directed.py")
    assert gd.max_circular_now("2026-08-07")["value"] == 6
    assert gd.max_circular_now("2026-08-14")["value"] == 2


def t_apply_and_rhythm_survive_a_missing_flags_file():
    _clear()
    assert ov.get("OCTOPUS_NEURAL_LEARNED_APPLY") == "1"
    assert ov.get("OCTOPUS_WIRE_CHRONO_RHYTHM") == "1"


def t_explicit_zero_overrides_tracked_arming():
    _clear()
    env = {
        "OCTOPUS_NEURAL_LEARNED_APPLY": "0",
        "OCTOPUS_WIRE_CHRONO_RHYTHM": "0",
    }
    assert ov.get("OCTOPUS_NEURAL_LEARNED_APPLY", environ=env) == "0"
    assert ov.get("OCTOPUS_WIRE_CHRONO_RHYTHM", environ=env) == "0"
    drift = ov.drift(env)
    assert len(drift) == 2 and all("≠" in item for item in drift), drift


# ── تقدم و رانش ────────────────────────────────────────────────────────────

def t_the_environment_still_wins():
    """رفتارِ امروز نباید عوض شود: flags.cmd همچنان حرفِ آخر را می‌زند."""
    _clear()
    os.environ["OCTOPUS_SPEND_CAP_USD"] = "50"
    try:
        assert ov.get("OCTOPUS_SPEND_CAP_USD") == "50"
    finally:
        _clear()


def t_an_empty_environment_value_falls_through():
    _clear()
    os.environ["OCTOPUS_SPEND_CAP_USD"] = "   "
    try:
        assert ov.get("OCTOPUS_SPEND_CAP_USD") == "200"
    finally:
        _clear()


def t_divergence_is_reported_not_swallowed():
    d = ov.drift({"OCTOPUS_SPEND_CAP_USD": "50"})
    assert len(d) == 1 and "≠" in d[0], d


def t_agreement_is_not_reported_as_drift():
    assert ov.drift({"OCTOPUS_SPEND_CAP_USD": "200"}) == []


def t_an_absent_environment_is_not_drift():
    assert ov.drift({}) == []


# ── fail-soft: هیچ ورودیِ بدی نباید مسیرِ پول را بشکند ──────────────────────

def t_a_missing_file_is_silence_not_an_exception():
    assert ov.load("__no_such_file__.yaml") == {}
    assert ov.env_map("__no_such_file__.yaml") == {}
    assert ov.get("OCTOPUS_SPEND_CAP_USD", environ={}, p="__nope__.yaml") == ""


def t_a_broken_file_is_silence_not_an_exception():
    for junk in ("", "«»\x00\x01", "verdicts:\n  bad indentation here\n",
                 "no verdicts section at all: true\n"):
        assert ov.load(_tmp_yaml(junk)) == {}


def t_a_key_outside_the_verdicts_section_is_ignored():
    body = ("other:\n  x:\n    env: NOPE\n    value: '1'\n"
            "verdicts:\n  real:\n    env: YES_ENV\n    value: '7'\n")
    m = ov.env_map(_tmp_yaml(body))
    assert m == {"YES_ENV": "7"}, m


def t_the_money_path_survives_a_dead_verdicts_module():
    """اگر ماژول اصلاً نبود، budget_gate باید env-only کار کند نه crash."""
    _clear()
    bg = _load_module("bg_a2_dead", "04 - Architect System/scripts/budget_gate.py")
    saved = bg._verdicts
    try:
        bg._verdicts = None
        r = bg.spend_cap_now(30.0, 1.5, 500.0, today="2026-08-07")
        assert r["value_aud"] == 30.0 and r["reason"] == "default", r
    finally:
        bg._verdicts = saved


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            _clear()
            fn()
            print(f"  ✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {fn.__name__}: {e}", file=sys.stderr)
    _clear()
    ok = len(tests) - failed
    print(f"{'✅' if not failed else '❌'} test_owner_verdicts: {ok}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
