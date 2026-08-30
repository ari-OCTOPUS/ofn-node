"""test_brain_cortisol.py — رأی مالک 2026-07-18 «سریع‌تر + هوشمندتر، بودجه داریم»:
(۱) گیتِ کیفیتِ محلی-اولِ روتر — جوابِ echo/تکراری دیگر Fugu را گرسنه نمی‌گذارد.
(۲) boot-think — چرخهٔ ۱ هم فکر می‌کند (نه ~۵۰ دقیقه بعد از restart).
(۳) ماشهٔ کورتیزولی — ورود به ترس = سنتزِ فوری با زمینهٔ هشدار + cooldown + قفلِ لِین.
(۴) سنتز — فیلترِ echo قالب، گیتِ کیفیتِ اختصاصی، alarm در sig/prompt (dedup خفه نکند).
(۵) cadence llm_learn تا فازِ ج دست‌نخورده (۲۴h). آفلاین: ollama با opener تزریقی fake می‌شود.
"""
import io
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "heart"))

os.environ["OCTOPUS_CORTISOL_EVENTS"] = "1"       # قبل از importِ cortex (ثابتِ ماژول)

import harness
ENV = harness.setup("brain_cortisol")

import importlib               # noqa: E402
import local_llm               # noqa: E402
import model_router            # noqa: E402
import synthesis               # noqa: E402
import cortex as cx            # noqa: E402
import work_pump               # noqa: E402
import opslib                  # noqa: E402
for _m in (local_llm, model_router, synthesis, cx, work_pump):
    importlib.reload(_m)

OPS = Path(ENV["ops"])


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_opener(payload: dict):
    def _open(req, timeout=None):
        return _FakeResp(json.dumps(payload).encode("utf-8"))
    return _open


_PROMPT = ("حداکثر ۳ پروپوزال بساز. هر پروپوزال یک خط: "
           "«عنوان | چرا (به کدام جهت/گپ وصل است) | قدمِ اول». فقط پیشنهاد.")
_ECHO_TEXT = ("عنوان | چرا (به کدام جهت/گپ وصل است) | قدم اول\n"
              "حداکثر ۳ پروپوزال بساز. هر پروپوزال یک خط: فقط پیشنهاد.")
_GOOD_TEXT = ("کاهشِ تایم‌اوتِ مغزِ محلی | سرعتِ پاسخِ روزمره | سنجشِ p95 روی ۲۰ فکر\n"
              "اتصالِ گپِ مدرسه به سنتز | یادگیریِ هدفمند | خواندنِ گپ در prompt سنتز")


def t_a_quality_gate_rejects_echo_and_degenerate():
    """گیتِ عمومی: echo قالب/prompt رد، خط‌های تکراری رد، جوابِ واقعی پاس، کوتاه رد."""
    q = model_router._local_quality_ok
    assert q(_GOOD_TEXT, _PROMPT, 80) is True
    assert q(_ECHO_TEXT, _PROMPT, 80) is False          # هر دو خط داخلِ prompt هستند
    assert q("سطر یکسان تکراری برای سنجش\n" * 6, _PROMPT, 80) is False
    assert q("کوتاه", _PROMPT, 80) is False
    assert q("", _PROMPT, 80) is False
    # اعراب/گیومه mismatch نباید echo را از قلم بیندازد («قدمِ اول» vs «قدم اول»)
    assert model_router._norm_echo("«قدمِ اول»") == model_router._norm_echo("قدم اول")
    # مشخصهٔ مالک: هم‌پوشانیِ توکنی >۰.۷ با prompt رد — حتی بدونِ echo عینیِ خطی
    shuffled = ("پروپوزال جهت گپ وصل هر خط\nعنوان قدم اول بساز یک عملی\n"
                "چرا کدام جهت گپ پیشنهاد مشخص")
    assert q(shuffled, _PROMPT + " پروپوزال جهت گپ وصل هر خط عنوان قدم اول بساز "
             "یک عملی چرا کدام مشخص پیشنهاد", 40) is False


def t_a2_synth_gate_structural_completeness():
    """مشخصهٔ مالک: پروپوزالِ بدونِ «چرا» یا بدونِ قدمِ عملیِ چندواژه‌ای یا با
    عنوانِ تکراری، «معتبر» حساب نمی‌شود."""
    ok2 = ("الف عنوانی مستقل | چون سرعت می‌دهد | سنجشِ p95 روی بیست فکر\n"
           "ب عنوانی دیگر | چون خرج را کم می‌کند | افزودنِ کشِ جواب‌های تکراری")
    assert synthesis._synth_quality_ok(ok2) is True
    no_why = ("الف عنوانی مستقل |  | سنجشِ p95 روی بیست فکر\n"
              "ب عنوانی دیگر |  | افزودنِ کشِ جواب‌ها")
    assert synthesis._synth_quality_ok(no_why) is False
    lazy_step = ("الف عنوانی مستقل | چون سرعت می‌دهد | انجام\n"
                 "ب عنوانی دیگر | چون خرج کم می‌شود | بهبود")
    assert synthesis._synth_quality_ok(lazy_step) is False
    dup_title = ("عنوانِ یکسان | چون سرعت می‌دهد | سنجشِ p95 روی بیست فکر\n"
                 "عنوانِ یکسان | چون خرج کم می‌شود | افزودنِ کشِ جواب‌ها")
    assert synthesis._synth_quality_ok(dup_title) is False


def t_b_router_local_first_echo_falls_through():
    """CORTEX_LOCAL_FIRST=1: جوابِ echo از محلی → local_first نمی‌شود (مسیرِ پولی/امروز)؛
    جوابِ واقعی → local_first=True مثلِ قبل."""
    os.environ["CORTEX_LOCAL_FIRST"] = "1"
    try:
        local_llm._LAST_CALL["ts"] = 0.0
        r = model_router.ask("research", _PROMPT,
                             opener=_fake_opener({"response": _GOOD_TEXT}))
        assert r["ok"] is True and r.get("local_first") is True, r
        local_llm._LAST_CALL["ts"] = 0.0
        r2 = model_router.ask("research", _PROMPT,
                              opener=_fake_opener({"response": _ECHO_TEXT}))
        assert r2.get("local_first") is not True, r2     # گیت echo را رد کرد
        local_llm._LAST_CALL["ts"] = 0.0
        r3 = model_router.ask("research", _PROMPT, quality=lambda t: False,
                              opener=_fake_opener({"response": _GOOD_TEXT}))
        assert r3.get("local_first") is not True, r3     # چکِ تزریقیِ صداکننده حاکم است
    finally:
        os.environ.pop("CORTEX_LOCAL_FIRST", None)


def t_c_boot_think_via_every_n_flag():
    """پیش‌فرض N=5 = دقیقاً رفتارِ قدیم (چرخهٔ ۱ فکر نمی‌کند — گاردِ byte-identical)؛
    deploy با CORTEX_THINK_EVERY_N=1 → هر چرخه، از جمله خودِ چرخهٔ ۱ (boot-think)."""
    old = cx.THINK_EVERY_N
    try:
        cx.THINK_EVERY_N = 5
        assert cx._should_think(1) is False and cx._should_think(5) is True
        cx.THINK_EVERY_N = 1
        assert cx._should_think(1) is True and cx._should_think(2) is True
        cx.THINK_EVERY_N = 0                       # env خراب → هرگز کرش/تقسیم‌برصفر
        assert cx._should_think(1) is True
    finally:
        cx.THINK_EVERY_N = old


def t_d_cortisol_fires_on_fear_entry_with_alarm_context():
    """ورود به ترس + گیتِ باز → synthesis با extra.alarm صدا می‌خورد و state ثبت می‌شود."""
    calls = []
    real = synthesis.run_and_persist

    def _fake_rp(ask=None, extra=None):
        calls.append(extra)
        return {"ok": True, "tier": "primary", "n_proposals": 2, "cost_usd": 0.0}

    synthesis.run_and_persist = _fake_rp
    try:
        # قدم ۰: اولین مشاهده (state تازه) حتی وسطِ ترسِ مزمن = فقط baseline، هیچ شلیک —
        # وگرنه هر بوتِ state-تازه یک تماسِ پولیِ خودکار می‌شد (بازبینی 07-18).
        out0 = cx.cortisol_tick(0, {"level": "🔴 ترس", "organism_stress": 1.0,
                                    "in_fear": ["legs"]})
        assert out0 is None and calls == [], out0
        # قدم ۱: گیتِ لِین بسته (هیچ flagی در ops تست) → fired=False با دلیلِ صادق
        out = cx.cortisol_tick(1, {"level": "🔴 ترس", "organism_stress": 1.0,
                                   "in_fear": ["legs", "spine"]})
        assert out and out["fired"] is False and "live-locked" in out["reason"], out
        assert calls == []                               # قفل بسته = هیچ خرجی
        # قدم ۱.۵: لِین باز ولی دروازهٔ پولیِ روتر هنوز بسته → شلیکِ بی‌فایده ممنوع
        (OPS / "ACTIVATION-GO-LIVE.flag").write_text("test", "utf-8")
        (OPS / "ACTIVATION-WORK-LLM.flag").write_text("test", "utf-8")
        out15 = cx.cortisol_tick(1, {"level": "🔴 ترس", "organism_stress": 1.0,
                                     "in_fear": ["legs", "spine", "eye"]})
        assert out15 and out15["fired"] is False and "paid-gate" in out15["reason"], out15
        assert calls == []
        # قدم ۲: دروازهٔ پولی هم باز → عضوِ تازهٔ ترس → شلیک با زمینهٔ هشدار
        (OPS / "ACTIVATION-CORTEX-PAID.flag").write_text("test", "utf-8")
        out2 = cx.cortisol_tick(2, {"level": "🔴 ترس", "organism_stress": 1.0,
                                    "in_fear": ["legs", "spine", "eye", "heart"]})
        assert out2 and out2["fired"] is True and out2["tier"] == "primary", out2
        assert len(calls) == 1 and "heart" in calls[0]["alarm"], calls
        st = json.loads((OPS / "state" / "cortex" / "cortisol-state.json")
                        .read_text("utf-8"))
        assert st["last_fire_ts"] > 0 and "heart" in st["in_fear"]
        # قدم ۳: عضوِ تازهٔ دیگر بلافاصله → cooldown جلوی طوفانِ خرج را می‌گیرد
        out3 = cx.cortisol_tick(3, {"level": "🔴 ترس", "organism_stress": 1.0,
                                    "in_fear": ["legs", "spine", "eye", "heart",
                                                "governor"]})
        assert out3 and out3["fired"] is False and "cooldown" in out3["reason"], out3
        assert len(calls) == 1                           # شلیکِ دوم نشد
        # قدم ۴: بدونِ تغییرِ ترس → None (هیچ رویدادی)
        out4 = cx.cortisol_tick(4, {"level": "🔴 ترس", "organism_stress": 1.0,
                                    "in_fear": ["legs", "spine", "eye", "heart",
                                                "governor"]})
        assert out4 is None
        # قدم ۵ (ضدِ رگبارِ بودجه): اگر ثبتِ slotِ cooldown شکست بخورد → هیچ شلیکی.
        st_path = OPS / "state" / "cortex" / "cortisol-state.json"
        st = json.loads(st_path.read_text("utf-8"))
        st["last_fire_ts"] = 0.0                         # cooldown آزاد
        st_path.write_text(json.dumps(st), "utf-8")

        class _Boom:
            def __init__(self, *a, **k):
                pass

            def __enter__(self):
                raise OSError("locked-by-av")

            def __exit__(self, *a):
                return False

        real_lj = cx.opslib.LockedJson
        cx.opslib.LockedJson = _Boom
        try:
            out5 = cx.cortisol_tick(5, {"level": "🔴 ترس", "organism_stress": 1.0,
                                        "in_fear": ["legs", "spine", "eye", "heart",
                                                    "governor", "sigma"]})
        finally:
            cx.opslib.LockedJson = real_lj
        assert out5 and out5["fired"] is False and "state-write-failed" in out5["reason"]
        assert len(calls) == 1                           # پول خرج نشد
    finally:
        synthesis.run_and_persist = real


def t_e_cortisol_flag_off_is_noop():
    """flag خاموش → دقیقاً رفتارِ امروز (None)، حتی وسطِ ورود به ترس."""
    old = cx.CORTISOL_EVENTS
    cx.CORTISOL_EVENTS = False
    try:
        assert cx.cortisol_tick(1, {"level": "🔴 ترس", "in_fear": ["زِ-تازه"]}) is None
    finally:
        cx.CORTISOL_EVENTS = old


def t_f_parse_skips_template_echo():
    """خطِ echo قالب پروپوزال حساب نمی‌شود؛ واقعی‌ها می‌مانند (باگِ synthesis 07-17)."""
    raw = ("عنوان | چرا (به کدام جهت/گپ وصل است) | قدم اول\n"
           "ارگانیسم خود تحلیل بدهد | بهبود عملکرد | لینک‌های تحلیلِ خودکار\n"
           "حافظهٔ ماندگار بماند | امنیت داده‌ها | ذخیره‌سازیِ چندنقطه‌ای")
    props = synthesis._parse_proposals(raw)
    assert len(props) == 2 and props[0]["title"].startswith("ارگانیسم"), props
    assert synthesis._synth_quality_ok(raw) is True      # ۲ پروپوزالِ واقعی
    assert synthesis._synth_quality_ok(
        "عنوان | چرا (به کدام جهت/گپ وصل است) | قدم اول") is False
    # سبکِ رایجِ label-as-prefix محتوای واقعی است و نباید فیلتر شود (بازبینی 07-18)
    styled = ("کاهشِ تایم‌اوتِ محلی | چرا (به کدام جهت/گپ وصل است): سرعتِ روزمره | "
              "قدم اول: سنجشِ p95 روی بیست فکر\n"
              "کشِ جوابِ تکراری | چرا (به کدام جهت/گپ وصل است): کاهشِ خرج | "
              "قدم اول: افزودنِ کش با کلیدِ امضا")
    sp = synthesis._parse_proposals(styled)
    assert len(sp) == 2 and sp[0]["title"].startswith("کاهش"), sp
    assert synthesis._synth_quality_ok(styled) is True


def t_g_synthesize_alarm_changes_sig_and_prompt_and_passes_quality():
    """alarm واردِ prompt/sig/digest می‌شود؛ askِ قدیمی بدونِ quality هم کار می‌کند؛
    askِ روترنما quality=چکِ سنتز را می‌گیرد."""
    seen = {}

    def _old_style_ask(task, prompt, system="", max_tokens=400, tier=None):
        seen["prompt"], seen["tier"] = prompt, tier
        return {"ok": True, "tier": "primary", "model": "fake", "cost_usd": 0.0,
                "text": _GOOD_TEXT}

    r1 = synthesis.synthesize(ask=_old_style_ask)
    assert r1["ok"] and "زنگِ خطر" not in seen["prompt"]
    assert seen["tier"] is None                          # تایمری = محلی-اولِ ارزان
    r2 = synthesis.synthesize(ask=_old_style_ask, extra={"alarm": "ورود به ترس: heart"})
    assert r2["ok"] and "زنگِ خطر" in seen["prompt"] and "heart" in seen["prompt"]
    assert seen["tier"] == "primary"                     # کورتیزول = مستقیم مغزِ بزرگ
    assert r2["digest"]["alarm"].startswith("ورود به ترس")
    # sig بدونِ alarm — دو نویسندهٔ synthesis-latest (پمپ/کورتیزول) هم‌سیگ می‌مانند
    # تا بعد از شلیک، پمپِ تایمری تماسِ پولیِ بی‌سیگنالِ اضافه نزند (بازبینی 07-18).
    assert r1["digest"]["input_sig"] == r2["digest"]["input_sig"]

    got = {}

    def _router_like_ask(task, prompt, system="", max_tokens=400, tier=None,
                         opener=None, quality=None):
        got["quality"] = quality
        return {"ok": True, "tier": "local", "model": "fake", "cost_usd": 0.0,
                "text": _GOOD_TEXT}

    r3 = synthesis.synthesize(ask=_router_like_ask)
    assert r3["ok"] and callable(got["quality"])         # چکِ اختصاصی پاس داده شد
    assert got["quality"](_GOOD_TEXT) is True
    assert got["quality"](_ECHO_TEXT) is False


def t_h_event_driven_dedup_skips_same_sig_but_not_alarm():
    """OCTOPUS_SYNTH_EVENT_DRIVEN=1: ورودیِ بی‌تغییر skip؛ همان ورودی + alarm → اجرا."""
    def _ask(task, prompt, system="", max_tokens=400, tier=None):
        return {"ok": True, "tier": "primary", "model": "fake", "cost_usd": 0.0,
                "text": _GOOD_TEXT}

    first = synthesis.run_and_persist(ask=_ask)
    assert first["ok"] and first["n_proposals"] == 2, first
    os.environ["OCTOPUS_SYNTH_EVENT_DRIVEN"] = "1"
    try:
        again = synthesis.run_and_persist(ask=_ask)
        assert again.get("skipped") == "no-new-signal", again
        fired = synthesis.run_and_persist(ask=_ask, extra={"alarm": "ترسِ تازه"})
        assert fired.get("skipped") is None and fired["ok"] is True, fired
        # بعد از شلیکِ کورتیزولی، پمپِ تایمری با ورودیِ بی‌تغییر باید هنوز skip کند —
        # نه یک تماسِ پولیِ «بی‌سیگنال» فقط چون alarm سیگ را عوض کرده بود.
        pump_after = synthesis.run_and_persist(ask=_ask)
        assert pump_after.get("skipped") == "no-new-signal", pump_after
    finally:
        os.environ.pop("OCTOPUS_SYNTH_EVENT_DRIVEN", None)


def t_i_llm_learn_cadence_untouched_until_phase_c():
    """فازبندی مالک 2026-07-18: تایمرِ llm_learn تا فازِ ج (event-driven) دست‌نخورده."""
    tpl = {t["kind"]: t for t in work_pump.DEFAULT_PLAN["templates"]}
    assert tpl["llm_learn"]["every_s"] == 86400
    assert tpl["llm_learn"]["paid"] is True
    assert tpl["search"]["every_s"] == 86400


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_brain_cortisol: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
