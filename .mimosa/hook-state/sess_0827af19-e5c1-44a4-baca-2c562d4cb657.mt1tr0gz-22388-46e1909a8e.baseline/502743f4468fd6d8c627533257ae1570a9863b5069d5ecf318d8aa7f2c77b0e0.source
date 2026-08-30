#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_c6_bench_honesty.py — C1: بنچِ C6 دیگر خودش را تأیید نمی‌کند.

باگِ بسته‌شده (c6_trigger.py:206-234 نسخهٔ قبل): `_default_bench` یک readِ ۷.۳KB را با
`time.time` می‌سنجید و با `baseline_ms=5.0`ِ **هاردکد داخلِ خودِ فرضیه** مقایسه می‌کرد →
gain ≈ ۴.۹ms هر روز، supported=True بی‌قید، و کارتِ «accepted» بدونِ ذره‌ای محتوا.
فرضیهٔ اعلامی («cache در برابرِ re-parse») هیچ‌وقت اندازه‌گیری نمی‌شد: بازوی دوم وجود نداشت.

این تست قفل می‌کند:
  ۱) NULL (دو بازوی **یکسان**) → supported=False  ← امروز True است، این تست قرمز می‌شود
  ۲) baselineِ اعلامیِ فرضیه هیچ اثری روی verdict ندارد (فقط شاهد ثبت می‌شود)
  ۳) کنترلِ مثبت (نامزد واقعاً کارِ کمتری می‌کند) → supported=True
  ۴) معیارِ پذیرش، اثرِ غیرقابلِ‌تمیز از نویز را رد می‌کند (واحد، بدونِ وابستگی به زمان)
  ۵) ادعای مکانیزمی قطعی است: parseِ هر اجرا شمرده می‌شود (مستقل از سخت‌افزار)
  ۶) طرحِ اندازه‌گیری: جفت‌شده/median+mean/IQR/کفِ نویزِ A/A/gc برگردانده‌شده
  ۷) گاردِ رگرسیون: baselineِ عددیِ هاردکد به سورس برنگردد
hermetic: ORG_ROOT به tempdir پین می‌شود؛ صفر شبکه/پول/apply؛ < ۲ ثانیه.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("c6-bench-honesty")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "memory"), str(_OPS.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gc  # noqa: E402
import opslib  # noqa: E402
import c6_trigger as c6  # noqa: E402

_GC_BEFORE = gc.isenabled()

# payloadِ بنچ داخلِ STATE_DIRِ موقت (hermetic) — هم‌اندازهٔ ORGANISM-STATE واقعی (~۷KB)
_PAYLOAD = Path(str(opslib.STATE_DIR)) / "ORGANISM-STATE.json"
_PAYLOAD.parent.mkdir(parents=True, exist_ok=True)
_PAYLOAD.write_text(json.dumps(
    {"organs": {f"organ-{i}": {"state": "ok", "beat": i, "notes": "n" * 60}
                for i in range(80)}}, ensure_ascii=False), encoding="utf-8")


def _derive(h):
    """با هر دو امضا کار می‌کند تا شکستِ این تست روی کدِ قدیمی **محتوایی** باشد،
    نه یک ValueErrorِ unpack."""
    r = c6._derive_fns(h, {})
    return tuple(r) + ({},) if len(r) == 2 else tuple(r)


def _mk_arm(work: int):
    """بازوی مصنوعیِ قابلِ‌کنترل: در هر tick یک read و `work` بار parse، با شمارنده."""
    def arm(path, n, ops):
        obj = None
        for _ in range(n):
            raw = path.read_bytes()
            ops["read_calls"] += 1
            ops["bytes_read"] += len(raw)
            for _w in range(work):
                obj = json.loads(raw.decode("utf-8"))
                ops["parse_calls"] += 1
        return obj
    return arm


def t_null_rejected():
    """فرضِ صفر: **همان** بازو در برابرِ خودش، با baselineِ مسمومِ ۵.۰ms در فرضیه."""
    arm = _mk_arm(1)
    h = {"kind": "micro_benchmark", "baseline_ms": 5.0,
         "_arms": (arm, arm), "bench_pairs": 9, "bench_inner": 4}
    exp, ver, _box = _derive(h)
    res = exp({})
    v = ver({}, res)
    assert v["supported"] is False, f"NULL پذیرفته شد: {v}"
    assert float(v["benchmark_gain"]) == 0.0, v
    assert float(res.get("parse_calls_saved_per_run", -1)) == 0.0, res
    assert res.get("declared_baseline_ms_ignored") == 5.0, \
        "baselineِ اعلامی باید فقط **ثبت** شود، نه مصرف"
    json.dumps(res, ensure_ascii=False)   # research_loop آرتیفکت را سریالایز می‌کند


def t_declared_baseline_is_inert():
    """دو NULLِ یکسان با baselineِ اعلامیِ ۵ و ۵۰۰۰ باید **دقیقاً** یک نتیجه بدهند."""
    arm = _mk_arm(1)
    outs = []
    for b in (5.0, 5000.0):
        exp, ver, _ = _derive({"baseline_ms": b, "_arms": (arm, arm),
                               "bench_pairs": 9, "bench_inner": 4})
        v = ver({}, exp({}))
        outs.append((v["supported"], float(v["benchmark_gain"])))
    assert outs[0] == outs[1] == (False, 0.0), f"baselineِ اعلامی روی verdict اثر دارد: {outs}"


def t_positive_control_accepted():
    """نامزد واقعاً کارِ کمتری می‌کند (۳۲ parse در برابرِ ۱) → باید پذیرفته شود."""
    h = {"_arms": (_mk_arm(32), _mk_arm(1)), "bench_pairs": 15, "bench_inner": 6}
    exp, ver, _ = _derive(h)
    res = exp({})
    v = ver({}, res)
    assert v["supported"] is True, f"کنترلِ مثبت رد شد: {v['evidence']}"
    assert 0.0 < float(v["benchmark_gain"]) <= 1.0, v
    assert float(res["parse_calls_saved_per_run"]) > 0.0, res
    assert res["same_output"] is True, res


def t_acceptance_rejects_noise():
    """معیارِ پذیرش، واحد و قطعی — بدونِ هیچ وابستگی به ساعتِ ماشین."""
    good = {"same_output": True, "parse_calls_saved_per_run": 5.0, "sign_test_p": 0.001,
            "delta_median_ms": 1.0, "delta_mean_ms": 1.02, "delta_iqr_ms": 0.2,
            "noise_floor_ms": 0.05, "baseline_median_ms": 2.0, "n": 15, "wins": 15}
    a = c6._accept_bench(good)
    assert a["supported"] is True, a
    assert abs(a["benchmark_gain"] - 0.5) < 1e-9, a          # بی‌بعد: ۱.۰/۲.۰
    for tweak, label in (
            ({"delta_iqr_ms": 0.9}, "اثر < ۱.۵×IQR"),
            ({"noise_floor_ms": 0.5}, "اثر < ۳× کفِ نویزِ A/A"),
            ({"sign_test_p": 0.2}, "علامتِ ناپایدار (شانس)"),
            ({"parse_calls_saved_per_run": 0.0}, "مکانیزمِ صفر"),
            ({"delta_median_ms": 0.0}, "میانهٔ ≤ ۰"),
            ({"same_output": False}, "خروجیِ متفاوت")):
        r = c6._accept_bench({**good, **tweak})
        assert r["supported"] is False, f"{label} پذیرفته شد: {r}"
        assert r["inconclusive"] is False, f"{label} باید ابطال باشد نه نامعلوم: {r}"
    sk = c6._accept_bench({**good, "delta_mean_ms": 9.0})
    assert sk["supported"] is False and sk["inconclusive"] is True, sk
    er = c6._accept_bench({"error": "no-payload", "parse_calls_saved_per_run": 0.0})
    assert er["supported"] is False and er["inconclusive"] is True, er


def t_sign_test_exact():
    assert abs(c6._sign_test_p(15, 15) - 1.0 / 32768.0) < 1e-15
    assert c6._sign_test_p(8, 15) > c6.SIGN_ALPHA          # ۸/۱۵ = شیر یا خط
    assert c6._sign_test_p(12, 15) > c6.SIGN_ALPHA         # آستانه دقیقاً اینجاست
    assert c6._sign_test_p(13, 15) <= c6.SIGN_ALPHA
    assert c6._sign_test_p(0, 0) == 1.0


def t_real_arms_mechanism_is_deterministic():
    """بازوهای **تولیدی** روی payloadِ واقعی: ادعای مکانیزمی مستقل از سخت‌افزار است
    و همیشه همان عدد را می‌دهد (به همین دلیل ادعای اصلی همین است، نه ساعتِ دیواری)."""
    exp, _ver, _ = _derive({"bench_pairs": 9, "bench_inner": 6})
    res = exp({})
    assert res.get("error") is None, res
    assert res["parse_calls_per_run_a"] == 6.0, res     # re-parse: هر tick یک parse
    assert res["parse_calls_per_run_b"] == 1.0, res     # cache: فقط missِ اول
    assert res["stat_calls_per_run_b"] == 6.0, res      # اعتبارسنجی با stat در هر tick
    assert res["parse_calls_saved_per_run"] == 5.0, res
    assert res["bytes_read_per_run_b"] < res["bytes_read_per_run_a"], res
    assert res["same_output"] is True, res
    assert res["payload_bytes"] > 1000, res


def t_design_is_paired_and_restores_gc():
    exp, _ver, _ = _derive({"bench_pairs": 9, "bench_inner": 4})
    res = exp({})
    assert res["n_pairs"] == 9 and res["n"] == 9, res
    assert res["n_pairs"] % 3 == 0, "چرخشِ ترتیب توازن ندارد"
    for k in ("baseline_median_ms", "baseline_mean_ms", "candidate_median_ms",
              "candidate_mean_ms", "delta_median_ms", "delta_mean_ms",
              "delta_iqr_ms", "noise_floor_ms", "sign_test_p", "wins", "same_output"):
        assert k in res, f"کلیدِ {k} در رکوردِ اندازه‌گیری نیست"
    assert res["baseline_median_ms"] > 0.0, "baseline اندازه‌گیری نشد"
    assert res["gc_disabled_during_timing"] is True and res["clock"] == "perf_counter_ns"
    assert gc.isenabled() == _GC_BEFORE, "gc بعد از بنچ برنگشت"
    # ترتیبِ برعکس (نامزد کندتر) هرگز پذیرفته نمی‌شود
    exp2, ver2, _ = _derive({"_arms": (_mk_arm(1), _mk_arm(24)),
                             "bench_pairs": 9, "bench_inner": 4})
    assert ver2({}, exp2({}))["supported"] is False


def t_no_hardcoded_baseline_in_source():
    src = (_OPS / "c6_trigger.py").read_text("utf-8")
    assert re.search(r"[\"']baseline_ms[\"']\s*:\s*[0-9]", src) is None, \
        "baselineِ عددیِ هاردکد به c6_trigger.py برگشت"
    assert "perf_counter_ns" in src, "ساعتِ monotonic حذف شد"
    assert "_paired_bench" in src and "_accept_bench" in src
    assert "_default_bench" not in src, "بنچِ تک‌بازوی قدیمی هنوز هست"


def t_missing_payload_is_inconclusive_not_supported():
    """payloadِ غایب هرگز نباید gainِ ساختگی بسازد (fail-closed)."""
    exp, ver, _ = _derive({"bench_path": "does-not-exist.json"})
    res = exp({})
    v = ver({}, res)
    assert res.get("error") == "no-payload", res
    assert v["supported"] is False and float(v["benchmark_gain"]) == 0.0, v
    # مسیرِ بیرون از STATE_DIR هم fail-closed است
    exp2, ver2, _ = _derive({"bench_path": "../../etc/hosts"})
    assert ver2({}, exp2({}))["supported"] is False


print("── C6 bench honesty (C1) ─────────────────────────────────────────")
fails = harness.run([
    ("NULL (دو بازوی یکسان) رد می‌شود", t_null_rejected),
    ("baselineِ اعلامیِ فرضیه بی‌اثر است", t_declared_baseline_is_inert),
    ("کنترلِ مثبت پذیرفته می‌شود", t_positive_control_accepted),
    ("معیارِ پذیرش نویز را رد می‌کند", t_acceptance_rejects_noise),
    ("آزمونِ علامتِ دقیق", t_sign_test_exact),
    ("ادعای مکانیزمی قطعی است", t_real_arms_mechanism_is_deterministic),
    ("طرحِ جفت‌شده + بازگشتِ gc", t_design_is_paired_and_restores_gc),
    ("باگِ baselineِ هاردکد برنگشته", t_no_hardcoded_baseline_in_source),
    ("payloadِ غایب = نامعلوم، نه پذیرفته", t_missing_payload_is_inconclusive_not_supported),
])
print("=" * 66)
print(("❌ " if fails else "✅ ") + f"test_c6_bench_honesty: {fails} failure(s)")
sys.exit(1 if fails else 0)


