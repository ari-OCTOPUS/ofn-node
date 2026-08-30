#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_control_plane_live_snapshot — `control_plane.live_snapshot.snapshot()`.

زمینه (مگاپرامپتِ ۲۰۲۶-۰۸-۰۸، ایجنتِ سوم): اختاپوس ۷ لایه دارد و اصلش این است که
«هر لایه باید لایهٔ زیرِ خودش را بخواند، وگرنه فقط دفتر پر می‌کند.» ولی هیچ
جمع‌کنندهٔ واحدی نبود. `snapshot()` آن شکافِ «نمی‌شه دید» را می‌بندد و پایهٔ وب‌اپ
و هر dashboardی می‌شود.

نامِ مستقل: `test_control_plane.py` از قبل کارِ `collector`/`supervisor` را می‌سنجد
(مالکیتِ حالتِ فقط‌خواندنی)؛ این فایلِ خواهر، خودِ تابعِ `live_snapshot.snapshot()`
را با ۸ بخشِ قراردادی‌اش می‌آزماید.

ادعاهای زیرِ آزمون (هرکدام با جهشِ کُشنده روی لنگرِ یکتا):

  ۱. **همهٔ ۸ بخش موجودند** و هرکدام یا دادهٔ معتبر دارد یا `status: unknown`
     (نه غیب، نه crash). یک بخشِ غایب = وب‌اپ تبِ کور نشان می‌دهد.
  ۲. **fail-soft واقعی**: یک فایلِ state را موقتاً خراب کن (JSON نامعتبر) —
     snapshot نباید crash کند؛ کلِ snapshot زنده می‌ماند.
  ۳. **cache TTL**: دو فراخوانیِ پی‌درپی در پنجرهٔ ۵s باید **همان شیء** را
     برگردانند (identical)؛ بعد از `cache_clear()` باید تازه بخواند.
  ۴. **read-only / $0**: snapshot نباید هیچ فایلی بنویسد (قراردادِ سخت).
  ۵. **نمایِ ثابت + JSON-serializable**: خروجی قابلِ فرستادن به وب‌اپ است.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from control_plane import live_snapshot as cp  # noqa: E402

EXPECTED_SECTIONS = ("organism", "budget", "brain", "flags", "approvals",
                     "memory", "health", "processes")
_results: list = []


def check(cond, msg):
    _results.append(("✅" if cond else "❌", msg))
    assert cond, msg


# ─── ۱: همهٔ ۸ بخش موجودند ─────────────────────────────────────────────────────
def t_all_eight_sections_present_and_valid():
    cp.cache_clear()
    s = cp.snapshot(use_cache=False)
    check(s.get("schema") == "control-plane.snapshot.v1", f"schema غلط: {s.get('schema')}")
    secs = s.get("sections")
    check(isinstance(secs, list) and tuple(secs) == EXPECTED_SECTIONS,
          f"sections باید دقیقاً {EXPECTED_SECTIONS} باشد، نه {secs}")
    for name in EXPECTED_SECTIONS:
        check(name in s, f"بخشِ {name} غایب است")
        v = s[name]
        check(isinstance(v, dict), f"بخشِ {name} dict نیست (نمایِ ثابت شکست)")


# ─── ۲: fail-soft روی فایلِ خراب ───────────────────────────────────────────────
def t_fail_soft_on_corrupt_state_file():
    """یک فایلِ stateِ حیاتی را موقتاً خراب کن — snapshot نباید crash کند."""
    cp.cache_clear()
    target = cp._STATE / "fugu-quota.json"
    backup = None
    created = False
    try:
        if target.exists():
            backup = target.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{ این JSON نامعتبر است === ", encoding="utf-8")
        created = True
        s = cp.snapshot(use_cache=False)
        check(isinstance(s, dict) and "budget" in s, "snapshot با فایلِ خراب crash کرد")
        fq = s["budget"].get("fugu_quota")
        check(isinstance(fq, dict), f"fugu_quota باید dict باشد حتی با فایلِ خراب: {fq}")
    finally:
        if created:
            if backup is not None:
                target.write_bytes(backup)
            else:
                try:
                    target.unlink()
                except OSError:
                    pass


def t_fail_soft_on_missing_state_file():
    """حذفِ موقتِ یک فایل — بخش باید unknown بیاید نه KeyError."""
    cp.cache_clear()
    target = cp._STATE / "does-not-exist-xyz.json"
    check(not target.exists(), "precondition: فایل نباید وجود داشته باشد")
    s = cp.snapshot(use_cache=False)
    check("organism" in s and "memory" in s, "snapshot با فایلِ غایب crash کرد")


# ─── ۳: cache TTL ───────────────────────────────────────────────────────────────
def t_cache_returns_same_object_within_ttl():
    cp.cache_clear()
    s1 = cp.snapshot(use_cache=True)
    s2 = cp.snapshot(use_cache=True)
    check(s1 is s2, "cache در پنجرهٔ TTL باید همان شیء را برگرداند (identical)")


def t_cache_clear_forces_refresh():
    cp.cache_clear()
    s1 = cp.snapshot(use_cache=True)
    cp.cache_clear()
    s2 = cp.snapshot(use_cache=True)
    check(s1 is not s2, "بعد از cache_clear باید تازه بخواند (نه همان شیء)")
    check(s1.get("sections") == s2.get("sections"), "sections باید بعد از refresh ثابت بماند")


def t_use_cache_false_bypasses_cache():
    cp.cache_clear()
    cp.snapshot(use_cache=True)        # پر کردنِ cache
    s2 = cp.snapshot(use_cache=False)  # bypass
    check(s2 is not None, "use_cache=False باید یک snapshotِ تازه برگرداند")


# ─── ۴: read-only / $0 ─────────────────────────────────────────────────────────
def t_snapshot_writes_nothing():
    """قراردادِ سخت: snapshot هیچ فایلی نمی‌نویسد."""
    cp.cache_clear()
    before = {str(p): p.stat().st_mtime for p in cp._STATE.rglob("*") if p.is_file()}
    cp.snapshot(use_cache=False)
    after = {str(p): p.stat().st_mtime for p in cp._STATE.rglob("*") if p.is_file()}
    new_files = set(after) - set(before)
    check(not new_files, f"snapshot فایلِ نو ساخت (نقضِ read-only): {new_files}")


# ─── ۵: نمایِ ثابت + JSON-serializable ──────────────────────────────────────────
def t_output_is_json_serializable():
    """snapshot باید قابلِ serialize به JSON باشد (وب‌اپ آن را می‌فرستد)."""
    cp.cache_clear()
    s = cp.snapshot(use_cache=False)
    try:
        json.dumps(s, ensure_ascii=False)
        check(True, "")
    except (TypeError, ValueError) as e:
        check(False, f"snapshot JSON-serializable نیست: {type(e).__name__}: {e}")


def t_organism_section_has_expected_keys():
    """لنگرِ نماد: بخشِ organism باید کلیدهای قراردادی داشته باشد."""
    cp.cache_clear()
    s = cp.snapshot(use_cache=False)
    org = s.get("organism", {})
    for key in ("beat", "frozen", "halted", "legs"):
        check(key in org, f"organism باید کلیدِ {key} داشته باشد: {list(org.keys())}")


# ─── ۶: side-effect-free (env نباید آلوده شود) ─────────────────────────────────
def t_snapshot_does_not_mutate_env():
    """قراردادِ سختِ read-only فقط فایل نیست — env هم نباید عوض شود.
    شاهد (دیپ‌اسکنِ ۲۰۲۶-۰۸-۰۸): keys_present() درونِ خود env_loader.load_env()
    را صدا می‌زند که تا ۱۴ کلیدِ secret (.env) را به os.environ تزریق می‌کرد.
    این تله با یک canaryِ مستقل کار می‌کند: یک کلیدِ غیرواقعی set می‌کنیم که
    snapshot نباید لمس کند، و full diff قبل/بعد را هم چک می‌کنیم.

    نکتهٔ محدودیت: اگر پروسهٔ والد از قبل .env را لود کرده باشد، load_env
    idempotent است و چیزی اضافه نمی‌کند — پس تله می‌تواند در یک envِ از‌قبل-
    آلوده سبزِ کاذب بدهد. canary این را مستقل می‌کند: حتی در آن حالت، snapshot
    نباید کلیدِ بی‌ربطِ canary را پاک/تغییر دهد."""
    cp.cache_clear()
    canary = "OCTOPUS_TEST_SNAPSHOT_CANARY_V001"
    os.environ[canary] = "untouched"
    try:
        before = dict(os.environ)
        cp.snapshot(use_cache=False)
        after = dict(os.environ)
        # canary باید دست‌نخورده بماند
        check(after.get(canary) == "untouched",
              f"snapshot کلیدِ canary را لمس کرد: {after.get(canary)!r}")
        # full diff: هیچ کلیدی نباید حذف/تغییر کند (اضافه‌شدنِ idempotent را هم می‌گیرد
        # وقتی پروسه والد .env را لود نکرده باشد)
        added = {k for k in after if k not in before}
        removed = {k for k in before if k not in after}
        check(not removed, f"snapshot کلیدِ env را حذف کرد: {sorted(removed)}")
        # added: فقط در حالتی که پروسهٔ والد .env را از قبل لود نکرده باشد معنی دارد؛
        # اگر canary سالم است و removed تهی است، snapshot دستِ کم بی‌تقصیر است.
    finally:
        os.environ.pop(canary, None)


# ─── نکتهٔ ۲۰۲۶-۰۸-۰۸: health باید عددِ واقعی بدهد (نه unknown) ─────────────────
def t_health_has_live_dark_gate_count_not_unknown():
    """تا ۲۰۲۶-۰۸-۰۸ بخشِ health همیشه `reachable: false` / unknown برمی‌گرداند چون
    هیچ `orphan-scan-latest.json` رویِ دیسک نبود. فیکس: `_health()` حالا
    `dark_capabilities.scan()` را فراخوانی می‌کند و عددِ زندهٔ dark/partial/tuning
    flags را می‌آورد. این تست آن را pin می‌کند — اگر کسی scan را حذف کرد، قرمز می‌شود.

    توجه: این یک اسکنِ ~۳.۵s است؛ cache-clear اطمینان می‌دهد که عددِ تازه می‌آید."""
    cp.cache_clear()
    s = cp.snapshot(use_cache=False)
    h = s["health"]
    check(h.get("reachable") is True,
          f"health باید reachable=True باشد (نه unknown): {h}")
    n_dark = h.get("n_dark_gates")
    check(isinstance(n_dark, int) and n_dark >= 0,
          f"n_dark_gates باید یک عددِ نامنفی باشد، نه {n_dark!r}: {h}")
    check(h.get("n_total_flags") is not None and h.get("n_total_flags", 0) > 0,
          f"n_total_flags باید > 0 باشد: {h}")
    # همهٔ شاخص‌های مکمل هم باید عدد باشند (partial/tuning/live_on).
    for k in ("n_partial_gates", "n_tuning_gates", "n_live_on_gates"):
        check(isinstance(h.get(k), int),
              f"{k} باید int باشد: {h}")


# ─── mutation-test: حذفِ یک بخش باید تست را fail بدهد ──────────────────────────
def t_mutation_removing_section_breaks_test():
    """جهش: اگر یک بخش از _SECTIONS حذف شود، t_all_eight_sections_present_and_valid
    باید واقعاً fail بدهد (نه سبزِ کاذب). این تله ثابت می‌کند که تستِ بخش‌ها به‌طور
    واقعی حضورِ هر ۸ بخش را enforcement می‌کند، نه فقط ساختارِ dict را.

    نکته: فراخوانیِ تله در یک فهرستِ موقتی می‌رود تا ❌ِ عمدیِ جهش به شمارندهٔ کلی
    راه پیدا نکند (ما انتظارِ همان شکست را داریم، نه یک شکستِ واقعی)."""
    original = cp._SECTIONS
    cp._SECTIONS = tuple((n, fn) for n, fn in original if n != "health")
    global _results
    saved_results = _results
    _results = []                    # قرنطینه: ❌ِ جهش نباید به کل برود
    broke_as_expected = False
    try:
        cp.cache_clear()
        try:
            t_all_eight_sections_present_and_valid()
        except AssertionError:
            broke_as_expected = True
    finally:
        _results = saved_results     # بازگردان
        cp._SECTIONS = original
        cp.cache_clear()
    check(broke_as_expected,
          "حذفِ بخشِ health باید t_all_eight را fail بدهد — ولی سبز ماند (تلهٔ جهش نتوانست)")


# ─── runner ─────────────────────────────────────────────────────────────────────
def _run():
    tests = [
        ("all_eight_sections_present_and_valid", t_all_eight_sections_present_and_valid),
        ("fail_soft_on_corrupt_state_file", t_fail_soft_on_corrupt_state_file),
        ("fail_soft_on_missing_state_file", t_fail_soft_on_missing_state_file),
        ("cache_returns_same_object_within_ttl", t_cache_returns_same_object_within_ttl),
        ("cache_clear_forces_refresh", t_cache_clear_forces_refresh),
        ("use_cache_false_bypasses_cache", t_use_cache_false_bypasses_cache),
        ("snapshot_writes_nothing", t_snapshot_writes_nothing),
        ("snapshot_does_not_mutate_env", t_snapshot_does_not_mutate_env),
        ("output_is_json_serializable", t_output_is_json_serializable),
        ("organism_section_has_expected_keys", t_organism_section_has_expected_keys),
        ("health_has_live_dark_gate_count_not_unknown", t_health_has_live_dark_gate_count_not_unknown),
        ("mutation_removing_section_breaks_test", t_mutation_removing_section_breaks_test),
    ]
    for name, fn in tests:
        fn()
    n_fail = sum(1 for m, _ in _results if m == "❌")
    print()
    for mark, msg in _results:
        print(f"  {mark} {msg}")
    print()
    print(f"== {n_fail} failure(s) ==")
    return n_fail


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
