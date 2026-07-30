#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_code_brain_local — پلهٔ محلیِ مغزِ کد (اولاما، $0) و گاردهایش.

رأیِ مالک ۲۰۲۶-۰۷-۳۰: «خودشو بسازه با اولاما ۲۴ ساعت». تا آن روز نردبان
L1-SDK → L1-API(پولی) → L0(هیچ) بود، پس بدونِ کلیدِ پولی هیچ کدی تولید
نمی‌شد و حلقهٔ ۲۴ساعته ساختاراً ناممکن بود.

مهم‌ترین بندِ این فایل `t_a_patch_that_drops_a_definition_is_rejected` است:
یک پروبِ **واقعی** نشان داد مدلِ محلی `def add` را انداخت و در عوض متنِ
بیشتری تولید کرد — یعنی گاردِ نسبتِ بایت (خروجی ≥۶۰٪ ورودی) از آن رد می‌شد
و یک پچِ **مخرب** به صف می‌رفت. گارد حالا نحوی است.

هیچ تماسِ شبکه‌ای در این فایل: همه با تزریقِ متنِ پاسخ.
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("code-brain-local")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS / "cortex"), str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import code_brain as cb  # noqa: E402

BEFORE = 'def add(a, b):\n    """جمع."""\n    return a + b\n'


# ── استخراجِ کد: سه شکلِ سنجیده‌شده ─────────────────────────────────────────
def t_a_python_fence_is_extracted():
    got = cb._extract_code("توضیح\n```python\ndef f():\n    return 1\n```\nپایان")
    assert got.strip() == "def f():\n    return 1", repr(got)


def t_the_json_envelope_shape_is_also_accepted():
    """با system ِ tool-use، مدلِ کوچک پاکتِ JSON می‌دهد — پاسخِ معتبری است،
    نه خطا. (سنجیده شد: خروجیِ واقعیِ qwen2.5:1.5b همین بود.)"""
    txt = ('```json\n{"target": "_ops/x.py", "content": "def g():\\n    '
           'return 2\\n", "intent": "t"}\n```')
    got = cb._extract_code(txt)
    assert got.strip() == "def g():\n    return 2", repr(got)


def t_an_unlabelled_fence_with_code_is_accepted():
    got = cb._extract_code("```\nimport os\ndef h():\n    pass\n```")
    assert "def h" in got, repr(got)


def t_bare_prose_is_never_accepted_as_file_content():
    """مهم: نثرِ مدل به‌عنوانِ محتوای فایل، فاجعه است. بی‌فنس ⇒ رد."""
    for bad in ("من نمی‌توانم این کار را انجام دهم.",
                "def f(): ...",           # بدونِ فنس، حتی اگر شبیهِ کد باشد
                "", "   ", "```\nسلام دنیا\n```"):
        assert cb._extract_code(bad) == "", repr(bad)


# ── گاردِ ناوردیِ نحوی — قلبِ این tier ──────────────────────────────────────
def t_a_patch_that_drops_a_definition_is_rejected():
    """⚠️ از یک پروبِ واقعی آمد: مدل `add` را انداخت و `mul` را گذاشت، با
    **بایتِ بیشتر** از ورودی. گاردِ نسبتِ بایت از آن رد می‌شد."""
    after = 'def mul(a, b):\n    """ضرب."""\n    return a * b\n\n# توضیحِ اضافه\n'
    assert len(after) > len(BEFORE), "پایهٔ سنجه غلط است — باید بایتِ بیشتر باشد"
    lost = cb._defs_kept(BEFORE, after)
    assert lost == ["add"], lost


def t_a_patch_that_keeps_everything_and_adds_passes():
    after = BEFORE + '\ndef mul(a, b):\n    return a * b\n'
    assert cb._defs_kept(BEFORE, after) == [], cb._defs_kept(BEFORE, after)


def t_a_syntactically_broken_output_is_rejected_distinctly():
    """خروجیِ نحواً خراب باید از «حذفِ تعریف» تفکیک شود — دو نقصِ متفاوت."""
    assert cb._defs_kept(BEFORE, "def broken(:\n  pass") is None


def t_classes_are_protected_too_not_just_functions():
    before = "class A:\n    def m(self):\n        pass\n\ndef f():\n    pass\n"
    after = "def f():\n    pass\n"
    assert cb._defs_kept(before, after) == ["A"], cb._defs_kept(before, after)


def t_a_broken_input_never_blocks_a_good_patch():
    """ورودیِ خرابِ قبلی چیزی برای حفاظت ندارد — گارد نباید قفل شود."""
    assert cb._defs_kept("def x(:", "def y():\n    pass\n") == []


# ── مرزهای tier ────────────────────────────────────────────────────────────
def t_a_task_without_an_allowed_target_never_calls_the_model():
    """متن هرگز مسیر را انتخاب نمی‌کند: بدونِ مسیرِ مجاز در متن، صفر تماس."""
    os.environ["OCTOPUS_CODE_BRAIN"] = "1"
    try:
        calls = []
        import local_llm
        real = local_llm.ask
        local_llm.ask = lambda *a, **k: (calls.append(1), None)[1]
        try:
            assert cb._draft_via_local("یک کارِ مبهم بدونِ مسیر") is None
            assert cb._draft_via_local("PRE-0/CONSTITUTION.md را عوض کن") is None
            assert not calls, "برای هدفِ نامجاز مدل صدا زده شد"
        finally:
            local_llm.ask = real
    finally:
        os.environ.pop("OCTOPUS_CODE_BRAIN", None)


def t_the_local_tier_uses_its_own_knobs_and_restores_the_chat_settings():
    """مدل **و مهلتِ** چتِ روزمره نباید بعد از این tier عوض بمانند.

    ⚠️ مهلت از یک باگِ واقعی آمد: `TIMEOUT_S=90` ِ چت برای بازنویسیِ کاملِ یک
    فایلِ ۷۲خطی کافی نبود — پروب دقیقاً سرِ ۹۰ ثانیه با `chars=0` برگشت و
    شبیهِ «مدل امتناع کرد» به نظر رسید. با مهلتِ ۶۰۰ ثانیه همان کار در ۵۰۰
    ثانیه سبز شد. این tier یک daemon ِ ۵-دقیقه‌ای است، پس مهلتِ بلند هزینه
    ندارد — ولی نشتِ آن به چتِ روزمره **دارد**."""
    import local_llm
    before_model, before_timeout = local_llm.MODEL, local_llm.TIMEOUT_S
    os.environ["OCTOPUS_CODE_BRAIN"] = "1"
    seen = {}
    real = local_llm.ask
    real_avail = local_llm.available
    local_llm.available = lambda *a, **k: True

    def spy(*a, **k):
        seen["model"] = local_llm.MODEL
        seen["timeout"] = local_llm.TIMEOUT_S
        return {"text": "```python\n" + BEFORE + "```"}

    local_llm.ask = spy
    tgt = Path(ENV["ORG_ROOT"]) / "_ops" / "cortex" / "probe_t.py"
    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.write_text(BEFORE, "utf-8")
    try:
        got = cb._draft_via_local("در _ops/cortex/probe_t.py چیزی عوض کن")
        assert got and got["target"] == "_ops/cortex/probe_t.py", got
        # حینِ تماس: مدل و مهلتِ **مخصوصِ کد**
        assert seen["timeout"] >= 300, ("مهلتِ کوتاه ⇒ فایلِ متوسط قطع می‌شود",
                                       seen)
        assert seen["model"] != "" and seen["model"] is not None, seen
        # بعدِ تماس: هر دو برگشته
        assert local_llm.MODEL == before_model, ("مدلِ چت برنگشت", local_llm.MODEL)
        assert local_llm.TIMEOUT_S == before_timeout, ("مهلتِ چت برنگشت",
                                                       local_llm.TIMEOUT_S)
    finally:
        local_llm.ask = real
        local_llm.available = real_avail
        local_llm.MODEL, local_llm.TIMEOUT_S = before_model, before_timeout
        os.environ.pop("OCTOPUS_CODE_BRAIN", None)


def t_the_chat_settings_are_restored_even_when_the_model_raises():
    """مسیرِ استثنا هم باید برگرداند — وگرنه یک خطا چتِ روزمره را برای همیشه
    روی مدل/مهلتِ سنگین می‌گذارد."""
    import local_llm
    before_model, before_timeout = local_llm.MODEL, local_llm.TIMEOUT_S
    os.environ["OCTOPUS_CODE_BRAIN"] = "1"
    real, real_avail = local_llm.ask, local_llm.available
    local_llm.available = lambda *a, **k: True
    local_llm.ask = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    tgt = Path(ENV["ORG_ROOT"]) / "_ops" / "cortex" / "probe_t2.py"
    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.write_text(BEFORE, "utf-8")
    try:
        assert cb._draft_via_local("در _ops/cortex/probe_t2.py عوض کن") is None
        assert local_llm.MODEL == before_model, local_llm.MODEL
        assert local_llm.TIMEOUT_S == before_timeout, local_llm.TIMEOUT_S
    finally:
        local_llm.ask, local_llm.available = real, real_avail
        local_llm.MODEL, local_llm.TIMEOUT_S = before_model, before_timeout
        os.environ.pop("OCTOPUS_CODE_BRAIN", None)


def t_the_ladder_prefers_paid_then_local_then_nothing():
    """ترتیب عمدی است: پولی بهتر کد می‌نویسد؛ محلی جایگزینِ **سکوت** است."""
    src = Path(cb.__file__).read_text("utf-8")
    i_api = src.index("_draft_via_api(task, max_turns)")
    i_loc = src.index("_draft_via_local(task)")
    assert i_api < i_loc, "پلهٔ محلی قبل از پولی امتحان می‌شود"
    assert "no-tier-produced" in src, "شکستِ هر دو پله ثبت نمی‌شود"


def t_the_local_drafter_itself_never_applies_anything():
    """⚠️ نسخهٔ اولِ این بند بیش از حد پهن بود و قرمز شد — و **کد درست بود**:
    `code_brain` یک مسیرِ auto-apply دارد که `apply_approved` را صدا می‌زند،
    ولی پشتِ فلگِ رأی‌خوردهٔ `OCTOPUS_CODE_AUTOAPPLY_LOWRISK` (پیش‌فرض خاموش)
    و از همان ۷ گیتِ `apply_approved` می‌گذرد. ناوردیِ درست باریک‌تر است:
    **خودِ تولیدکنندهٔ محلی** هیچ اعمالی ندارد."""
    import ast
    src = Path(cb.__file__).read_text("utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_draft_via_local":
            called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                      for n in ast.walk(node) if isinstance(n, ast.Call)}
            for bad in ("apply_approved", "consume_approvals", "tick",
                        "_git_apply_canary", "commit", "merge", "write_text"):
                assert bad not in called, f"تولیدکنندهٔ محلی {bad} می‌کند"
            return
    raise AssertionError("_draft_via_local پیدا نشد")


def t_the_auto_apply_path_stays_behind_its_owner_flag():
    """و ناوردیِ دوم: مسیرِ auto-apply بدونِ فلگ باز نشود."""
    src = Path(cb.__file__).read_text("utf-8")
    i_flag = src.index("_autoapply_lowrisk()")
    i_apply = src.index("code_autonomy.apply_approved(")
    assert i_flag < i_apply, "اعمالِ خودکار قبل از گیتِ فلگ می‌آید"
    assert cb.AUTOAPPLY_FLAG == "OCTOPUS_CODE_AUTOAPPLY_LOWRISK"
    assert cb._autoapply_lowrisk() is False, "فلگِ auto-apply در تست روشن است!"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_code_brain_local: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
