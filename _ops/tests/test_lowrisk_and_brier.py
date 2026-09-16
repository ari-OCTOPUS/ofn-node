"""test_lowrisk_and_brier.py — WS-7 (تعریفِ «کم‌ریسک») + WS-8 (کارتِ هفتگیِ Brier).

WS-7: `code_autonomy.risk_report` یک تابعِ **خالص** است و گیتِ هشتمِ
`apply_approved` فقط روی تأییدِ **خودکار** (`by == auto-lowrisk`) می‌نشیند.
دندانِ آن با بازسازیِ رفتارِ پیش‌از-فیکس ثابت می‌شود: اگر طبقه‌بند را با
«همیشه کم‌ریسک» جایگزین کنیم (یعنی دقیقاً وضعِ دیروز، که تنها شرطش
`allowed_target` بود) همان پچِ ویرانگر **اعمال می‌شود**.

WS-8: `introspect_cmd.brier_stats/brier_card` توابعِ خالص‌اند و ساختاراً
نمی‌توانند عددی چاپ کنند که از جفت‌های واقعی درنیامده باشد.

صفر شبکه · صفر git · صفر ارسال · هیچ نوشتنی بیرونِ sandbox ِ harness.
"""
import io
import json
import re
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness                                    # noqa: E402
ENV = harness.setup("lowrisk-brier")              # ← اولین کار بعد از sys.path

from cortex import code_autonomy as CA            # noqa: E402
import introspect_cmd as IC                       # noqa: E402

_TMP = Path(tempfile.gettempdir()).resolve()


class _C:
    failed = 0


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


# ══════════════════════════════════════════════════════════════════════════
# WS-7 · risk_report — تابعِ خالص
# ══════════════════════════════════════════════════════════════════════════
_GOOD_BEFORE = (
    "import json\n"
    "\n"
    "def alpha(x):\n"
    "    assert x is not None\n"
    "    if x < 0:\n"
    "        raise ValueError('neg')\n"
    "    return json.dumps({'x': x})\n"
    "\n"
    "def beta():\n"
    "    return 2\n"
)
_TGT = "_ops/cortex/registry.py"


def _blockers(target, before, after):
    return CA.risk_report(target, before, after)["blockers"]


def t_a_a_tiny_comment_patch_is_low_risk():
    after = _GOOD_BEFORE + "\n# note: measured 2026-08-01\n"
    r = CA.risk_report(_TGT, _GOOD_BEFORE, after)
    check("۳خطیِ کامنت روی cortex = کم‌ریسک", r["low_risk"] and not r["blockers"])
    check("changed_lines شمرده می‌شود", r["changed_lines"] == 2)


def t_b_scope_is_cortex_only_not_telegram_center():
    """رأیِ ۰۷-۳۰ (VQ-SELFGOAL-005) بازگشایی نشد: telegram_center کم‌ریسک نیست."""
    after = _GOOD_BEFORE + "# c\n"
    check("telegram_center بیرونِ دامنهٔ کم‌ریسک",
          "outside-lowrisk-roots" in _blockers(
              "_ops/telegram_center/center.py", _GOOD_BEFORE, after))
    check("ریشهٔ بیرونی رد می‌شود",
          "outside-lowrisk-roots" in _blockers(
              "_ops/legs/lead_pipeline.py", _GOOD_BEFORE, after))
    check("غیرِ پایتون رد می‌شود",
          "not-python" in _blockers("_ops/cortex/notes.md", _GOOD_BEFORE, after))


def t_c_self_amendment_and_guard_files_stay_shut():
    after = _GOOD_BEFORE + "# c\n"
    for tgt in ("_ops/cortex/code_autonomy.py", "_ops/cortex/code_brain.py",
                "_ops/cortex/sigma_track.py"):
        check(f"deny-token در مسیر: {tgt}",
              "deny-token-in-path" in _blockers(tgt, _GOOD_BEFORE, after))
    check("فایلِ گارد کم‌ریسک نیست",
          "guard-file" in _blockers("_ops/cortex/reply_guard.py",
                                    _GOOD_BEFORE, after))
    check("فایلِ تست کم‌ریسک نیست",
          "test-file" in _blockers("_ops/cortex/test_x.py", _GOOD_BEFORE, after))


def t_d_size_is_a_bound_not_a_suggestion():
    small = _GOOD_BEFORE + "".join(f"# f{i}\n" for i in range(CA.LOWRISK_MAX_CHANGED_LINES))
    big = _GOOD_BEFORE + "".join(f"# f{i}\n" for i in range(CA.LOWRISK_MAX_CHANGED_LINES + 1))
    r_small = CA.risk_report(_TGT, _GOOD_BEFORE, small)
    r_big = CA.risk_report(_TGT, _GOOD_BEFORE, big)
    check("دقیقاً روی سقف = کم‌ریسک",
          r_small["low_risk"] and r_small["changed_lines"] == CA.LOWRISK_MAX_CHANGED_LINES)
    check("یک خط بالاتر از سقف = رد",
          (not r_big["low_risk"])
          and any(b.startswith("too-many-changed-lines") for b in r_big["blockers"]))


def t_e_removals_are_never_low_risk():
    no_beta = _GOOD_BEFORE.replace("def beta():\n    return 2\n", "")
    b = _blockers(_TGT, _GOOD_BEFORE, no_beta)
    check("حذفِ تابع = رد", any(x.startswith("defs-removed") for x in b))
    check("حذفِ تابع نامش را می‌گوید", any("beta" in x for x in b))

    no_assert = _GOOD_BEFORE.replace("    assert x is not None\n", "")
    check("برداشتنِ assert = رد",
          any(x.startswith("asserts-removed") for x in _blockers(_TGT, _GOOD_BEFORE, no_assert)))

    no_raise = _GOOD_BEFORE.replace("        raise ValueError('neg')\n", "        return 0\n")
    check("برداشتنِ raise = رد",
          any(x.startswith("raises-removed") for x in _blockers(_TGT, _GOOD_BEFORE, no_raise)))

    plus_test = _GOOD_BEFORE + "\ndef test_new():\n    assert True\n"
    check("افزودن/برداشتنِ تست = رد",
          any(x.startswith("tests-changed") for x in _blockers(_TGT, _GOOD_BEFORE, plus_test)))

    tiny = "def alpha(x):\n    return x\n"
    check("کوچک‌شدنِ فاحش = رد",
          any(x.startswith("shrink") for x in _blockers(_TGT, _GOOD_BEFORE, tiny)))


def t_f_new_outward_effects_are_never_low_risk():
    imp = _GOOD_BEFORE + "\nimport subprocess\n"
    check("importِ تازهٔ subprocess = رد",
          any(x.startswith("new-effect-import") for x in _blockers(_TGT, _GOOD_BEFORE, imp)))
    # `os` از قبل نبود ⇒ هم import و هم call تازه‌اند؛ سنجهٔ delta باید هر دو را ببیند
    call = _GOOD_BEFORE + "\nimport os\n\ndef gamma(p):\n    os.remove(p)\n"
    b = _blockers(_TGT, _GOOD_BEFORE, call)
    check("فراخوانیِ تازهٔ os.remove = رد", any(x.startswith("new-effect-call") for x in b))
    ev = _GOOD_BEFORE + "\ndef delta(s):\n    return eval(s)\n"
    check("eval ِ تازه = رد",
          any(x.startswith("new-effect-call") for x in _blockers(_TGT, _GOOD_BEFORE, ev)))
    # ضدِ مثبتِ کاذب: `.replace` روی رشته یک اثرِ بیرونی نیست
    strop = _GOOD_BEFORE + "\ndef eps(s):\n    return s.replace('a', 'b')\n"
    check("str.replace اثرِ بیرونی شمرده نمی‌شود",
          CA.risk_report(_TGT, _GOOD_BEFORE, strop)["low_risk"])


def t_g_unparsable_or_empty_is_fail_closed():
    check("متنِ بعدِ غیرقابلِ‌پارس = رد",
          "after-unparsable" in _blockers(_TGT, _GOOD_BEFORE, _GOOD_BEFORE + "def (:\n"))
    check("متنِ قبلِ غیرقابلِ‌پارس = رد",
          "before-unparsable" in _blockers(_TGT, "def (:\n", _GOOD_BEFORE))
    check("محتوای خالی = رد", "empty-after" in _blockers(_TGT, _GOOD_BEFORE, "   "))
    check("فایلِ تازه (قبلِ خالی) = رد", "empty-before" in _blockers(_TGT, "", _GOOD_BEFORE))
    check("بی‌تغییر = رد", "no-change" in _blockers(_TGT, _GOOD_BEFORE, _GOOD_BEFORE))


def t_h_risk_report_is_pure_no_disk_no_clock():
    """خالص یعنی: مسیرِ ناموجود هم جواب می‌دهد، چیزی ساخته نمی‌شود، و دو
    فراخوانیِ پیاپی دقیقاً یک خروجی می‌دهند."""
    ghost = "_ops/cortex/__never_exists__.py"
    live = Path(CA._OPS).parent.joinpath(*ghost.split("/"))
    r1 = CA.risk_report(ghost, _GOOD_BEFORE, _GOOD_BEFORE + "# c\n")
    r2 = CA.risk_report(ghost, _GOOD_BEFORE, _GOOD_BEFORE + "# c\n")
    check("risk_report روی مسیرِ ناموجود هم حکم می‌دهد", r1["low_risk"] is True)
    check("risk_report چیزی روی دیسک نمی‌سازد", not live.exists())
    check("risk_report قطعی است (بی‌ساعت/بی‌تصادف)", r1 == r2)
    check("low_risk_patch روی هدفِ ناخوانا fail-closed است",
          CA.low_risk_patch({"target": ghost, "content": "# c\n"})["blockers"]
          == ["target-unreadable"])


# ══════════════════════════════════════════════════════════════════════════
# WS-7 · گیتِ هشتم در apply_approved — دندان
# ══════════════════════════════════════════════════════════════════════════
def _mood_ok():
    return {"mood": "🔥جریان", "verdict": "act", "arousal": 0.35,
            "in_fear": False, "sigma": None, "note": ""}


def _sandbox_guard():
    """هیچ فایلی بیرونِ tempdir نوشته نمی‌شود — گاردِ صریح، نه امید."""
    for p in (CA.ACTIVATION, CA.APPROVALS_DIR, CA.APPLIED_LOG):
        assert _TMP in Path(p).resolve().parents, f"harness ایزوله نکرد: {p}"


def _activate():
    _sandbox_guard()
    CA.ACTIVATION.parent.mkdir(parents=True, exist_ok=True)
    CA.ACTIVATION.write_text("owner", "utf-8")
    if CA.KILL.exists():
        CA.KILL.unlink()
    if CA.APPLIED_LOG.exists():
        CA.APPLIED_LOG.unlink()


def _approval(aid, by=None):
    _sandbox_guard()
    CA.APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
    import time
    rec = {"verdict": "ok", "id": aid, "epoch": time.time()}
    if by is not None:
        rec["by"] = by
    (CA.APPROVALS_DIR / f"{aid}.json").write_text(json.dumps(rec), "utf-8")


_LIVE_TARGET = "_ops/cortex/registry.py"
_DESTRUCTIVE = "def one():\n    return 1\n"     # حذفِ عملیِ کلِ ماژول


def _run(aid, by, content):
    _activate()
    _approval(aid, by=by)
    CA.heart_mood = _mood_ok
    calls = {"n": 0}

    def fake(_t, _c):
        calls["n"] += 1
        return {"applied": True, "green": True}

    r = CA.apply_approved({"target": _LIVE_TARGET, "content": content,
                           "shadow_green": True, "id": aid}, aid, apply_fn=fake)
    return r, calls["n"]


def t_i_auto_approval_of_a_destructive_patch_is_refused():
    r, n = _run("code-auto-1", CA.AUTO_APPROVAL_BY, _DESTRUCTIVE)
    check("تأییدِ خودکار + پچِ ویرانگر → رد", (not r["ok"]) and "not-low-risk" in r["reason"])
    check("تأییدِ خودکار + پچِ ویرانگر → صفر اعمال", n == 0)
    check("علتِ رد نام‌دار است", any(b.startswith("shrink") or b.startswith("defs-removed")
                                     for b in (r.get("risk") or {}).get("blockers", [])))


def t_j_TEETH_pre_fix_behaviour_applies_the_same_patch():
    """بازسازیِ رفتارِ دیروز: تنها شرطِ auto-apply در `code_brain` این بود که
    `allowed_target(target)` صادق باشد — هیچ سنجهٔ اندازه/حذف/اثر. آن وضع را
    با «طبقه‌بندِ همیشه-بله» بازمی‌سازیم؛ همان پچ باید **اعمال شود**. اگر این
    بند هم قرمز شود یعنی تست چیزی جز گیتِ تازه را می‌سنجد."""
    real = CA.low_risk_patch
    CA.low_risk_patch = lambda *_a, **_k: {"low_risk": True, "blockers": []}
    try:
        r, n = _run("code-auto-2", CA.AUTO_APPROVAL_BY, _DESTRUCTIVE)
    finally:
        CA.low_risk_patch = real
    check("پیش‌از-فیکس: همان پچِ ویرانگر اعمال می‌شد", r["ok"] and n == 1)
    # و حالا با گیتِ واقعی، همان ورودی رد می‌شود
    r2, n2 = _run("code-auto-3", CA.AUTO_APPROVAL_BY, _DESTRUCTIVE)
    check("پس-از-فیکس: همان ورودی رد می‌شود", (not r2["ok"]) and n2 == 0)


def t_k_the_human_path_is_untouched():
    """گیتِ هشتم فقط روی `by == auto-lowrisk` است. هر ۴۳ رکوردِ approvals ِ
    درختِ زنده `by` ندارند ⇒ مسیرِ HITL بایت‌به‌بایتِ دیروز."""
    r, n = _run("code-human-1", None, _DESTRUCTIVE)
    check("تأییدِ مالک (بی‌`by`) همان پچ را اعمال می‌کند", r["ok"] and n == 1)
    r2, n2 = _run("code-human-2", "owner-tap", _DESTRUCTIVE)
    check("`by` ِ غیرِ auto هم مسیرِ انسانی است", r2["ok"] and n2 == 1)


def t_l_a_genuinely_low_risk_auto_patch_still_applies():
    """گیت نباید همه‌چیز را ببندد — وگرنه قابلیت وجود ندارد (درسِ VQ-CANARY-001)."""
    live = Path(CA._OPS).parent.joinpath(*_LIVE_TARGET.split("/"))
    if not live.exists():
        check("هدفِ زندهٔ سنجش موجود است", False)
        return
    body = live.read_text("utf-8", errors="replace")
    r, n = _run("code-auto-4", CA.AUTO_APPROVAL_BY, body + "\n# measured 2026-08-01\n")
    check("پچِ واقعاً کم‌ریسک با تأییدِ خودکار اعمال می‌شود",
          r["ok"] and n == 1 and r.get("applied"))


# ══════════════════════════════════════════════════════════════════════════
# WS-8 · Brier — ساختاراً ناتوان از جعل
# ══════════════════════════════════════════════════════════════════════════
_NUM = re.compile(r"[0-9٠-٩۰-۹]")


def _brier_line_has_no_number(text):
    return not any(_NUM.search(ln) for ln in str(text).splitlines()
                   if IC.BRIER_LABEL in ln)


_PAIRS = [{"key": "a", "confidence": 0.9, "y": 1},
          {"key": "b", "confidence": 0.8, "y": 1},
          {"key": "c", "confidence": 0.3, "y": 0},
          {"key": "d", "confidence": 0.2, "y": 0}]
_EXACT = (0.01 + 0.04 + 0.09 + 0.04) / 4          # = 0.045


def t_m_brier_is_recomputed_from_pairs_not_read():
    st = IC.brier_stats({"n": 4, "brier": 0.045, "graded": _PAIRS})
    check("Brier دقیقاً از جفت‌ها بازمحاسبه می‌شود", abs(st["brier"] - _EXACT) < 1e-9)
    check("شمارِ جفت از خودِ فهرست می‌آید", st["n"] == 4)
    # نرخِ پایه = ۰.۵ ⇒ Brierِ حدسِ ثابت = ۰.۲۵
    check("حدسِ ثابتِ نرخِ پایه محاسبه می‌شود",
          st["base_rate"] == 0.5 and abs(st["baseline_brier"] - 0.25) < 1e-9)
    check("حکمِ مقایسه با حدسِ کور", st["verdict"] == "better")


def t_n_no_pairs_means_no_number_ever():
    for bad in (None, {}, {"n": 7, "brier": 0.2},                    # عدد بی‌جفت
                {"n": 7, "brier": 0.2, "graded": []},
                {"n": 1, "brier": 0.2, "graded": [{"confidence": 0.5, "y": 2}]},
                {"n": 1, "brier": 0.2, "graded": [{"confidence": 1.5, "y": 1}]},
                {"n": 1, "brier": 0.2, "graded": [{"confidence": None, "y": 1}]},
                {"n": 1, "brier": 0.2, "graded": ["not-a-dict"]}):
        st = IC.brier_stats(bad)
        txt = IC.brier_card(bad)
        ok = (st["has_data"] is False and st["brier"] is None
              and IC.NO_BRIER in txt and _brier_line_has_no_number(txt))
        check(f"بی‌جفت ⇒ بی‌عدد: {str(bad)[:44]}", ok)


def t_o_a_recorded_number_that_disagrees_is_refused():
    """دقیقاً الگوی سه ایجنتِ ۲۴ ساعتِ گذشته: عددِ ثبت‌شده بدونِ پشتوانه."""
    bad = {"n": 4, "brier": 0.001, "graded": _PAIRS}      # ۰.۰۰۱ ≠ ۰.۰۴۵
    st = IC.brier_stats(bad)
    txt = IC.brier_card(bad)
    check("عددِ ثبت‌شدهٔ ناهم‌خوان → امتناع", st["has_data"] is False
          and st["reason"] == "mismatch" and st["brier"] is None)
    check("کارت به‌جای عدد، اختلاف را می‌گوید",
          IC.NO_BRIER in txt and _brier_line_has_no_number(txt))


def t_p_trend_and_baseline_are_labelled_and_bounded():
    hist = [{"ts": "2026-07-25T00:00:00", "n": 3, "brier": 0.20},
            {"ts": "2026-07-30T00:00:00", "n": 5, "brier": 0.10},
            {"ts": "2026-07-31T00:00:00", "n": 0, "brier": None}]   # بی‌جفت → نادیده
    st = IC.brier_stats({"n": 4, "brier": _EXACT, "graded": _PAIRS,
                         "ts": "2026-08-01T00:00:00"}, hist)
    check("روند از تازه‌ترین اسنپ‌شاتِ **دارای جفت** می‌آید", st["prev_brier"] == 0.10)
    check("روند علامت‌دار است", abs(st["trend"] - (_EXACT - 0.10)) < 1e-9)
    txt = IC.brier_card({"n": 4, "brier": _EXACT, "graded": _PAIRS,
                         "ts": "2026-08-01T00:00:00"}, hist)
    check("کارت عدد، تعدادِ جفت و حدسِ کور را با هم می‌گوید",
          "0.0450" in txt and "4 جفت" in txt and "حدسِ ثابت" in txt)
    st0 = IC.brier_stats({"n": 4, "brier": _EXACT, "graded": _PAIRS}, [])
    check("بی‌تاریخچه ⇒ ادعای روند نمی‌کند", st0["trend"] is None)
    check("و کارت صریح می‌گوید اولین اندازه‌گیری است",
          "اولین اندازه‌گیری" in IC.brier_card({"n": 4, "brier": _EXACT,
                                                 "graded": _PAIRS}, []))


def t_q_card_is_byte_identical_when_the_flag_is_off():
    import os
    os.environ.pop(IC.BRIER_FLAG, None)
    off = IC.card()
    check("فلگ خاموش ⇒ کارتِ خودنگری دقیقاً همان دیروز",
          off == ("🔎 خودنگری\n"
                  "  /flags    مسلح در برابرِ بارگذاری‌شده\n"
                  "  /trace    پیام‌ها کجا نشستند\n"
                  "  /scan     نقاطِ کور\n"
                  "  /insight  فرضیه‌ها + نمرهٔ اجرای قبل"))
    check("فلگ خاموش ⇒ هیچ اشاره‌ای به Brier", IC.BRIER_LABEL not in off)
    os.environ[IC.BRIER_FLAG] = "1"
    try:
        on = IC.card()
    finally:
        os.environ.pop(IC.BRIER_FLAG, None)
    check("فلگ روشن ⇒ کارت رشد می‌کند و Brier را نام می‌برد",
          on.startswith(off) and IC.BRIER_LABEL in on and len(on) > len(off))
    check("و روی دادهٔ واقعیِ امروز عددی نمی‌سازد", _brier_line_has_no_number(on))


def t_r_the_module_must_not_declare_a_module_level_FLAG():
    """`capability_registry._zero_arg_card` هر `FLAG` ِ سطحِ ماژول را می‌خواند و
    کلِ کارت را «خاموش» برچسب می‌زند — یعنی چهار فرمانِ موجود هم خاموش دیده
    می‌شدند. این یک رگرسیونِ واقعی است، پس بند دارد."""
    import ast
    tree = ast.parse((_HERE.parent / "telegram_center" / "introspect_cmd.py")
                     .read_text("utf-8"))
    names = {t.id for n in tree.body if isinstance(n, ast.Assign)
             for t in n.targets if isinstance(t, ast.Name)}
    check("ماژول `FLAG` ِ سطحِ بالا ندارد", "FLAG" not in names)
    check("و به‌جایش نامِ اختصاصی دارد", "BRIER_FLAG" in names)
    import capability_registry as CR
    row = next((r for r in CR.discover() if r["module"] == "introspect_cmd"), None)
    check("رجیستری هنوز کارت را روشن می‌بیند",
          row is not None and row["flag"] == "" and row["flag_on"] is True)


def t_s_live_data_today_has_no_brier():
    """سنجهٔ امروز روی دادهٔ زنده: `self-claims.jsonl` نیست ⇒ صفر جفت ⇒ بی‌عدد.
    کارت باید همین را بگوید، نه عددی از هوا."""
    txt = IC.brier_text()
    check("کارتِ زنده رشته برمی‌گرداند (بی‌استثنا)", isinstance(txt, str) and txt)
    check("کارتِ زنده امروز عددی چاپ نمی‌کند", _brier_line_has_no_number(txt))
    check("و علتش را نام می‌برد", IC.NO_BRIER in txt and "علت" in txt)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(checks)
    total_failed = failed + _C.failed
    print(f"\n{'✅' if not total_failed else '❌'} test_lowrisk_and_brier: "
          f"{len(checks) - failed}/{len(checks)}"
          + (f" · +{_C.failed} soft-check failure(s)" if _C.failed else ""))
    sys.exit(1 if total_failed else 0)
