"""test_html_and_correction_safety.py — دو کلاس باگ از ممیزیِ ۲۰۲۶-۰۷-۲۷.

۱) **متنِ مدل بدونِ escape داخلِ `parse_mode=HTML`.** سه سطحِ ساخته‌شدهٔ همان روز
   (`ask_brain`، `mirror_room`، کارتِ `self_patch`) خروجیِ مدل و کدِ خام را مستقیم
   در HTML می‌گذاشتند. یک `<` کلِ پیام را ۴۰۰ می‌کند و چون `send_text` استثنا را
   می‌بلعد، کارت **بی‌هیچ ردی** گم می‌شود — همان الگویی که کارتِ C6 را یک شبانه‌روز
   خورد. بدترینش کارتِ self_patch است: diff تقریباً همیشه `<` و `>` دارد، یعنی
   خروجیِ کلِ حلقهٔ خودپچ‌زنی ساختاراً نامرئی بود.

۲) **تشخیصِ تصحیح با زیررشتهٔ خام.** `"نه "` هر کلمه‌ای را که به «نه» ختم شود
   می‌گرفت — «روزانه»، «خانه»، «چگونه»، «ماهانه». پس یک سؤالِ عادی به‌عنوانِ
   تصحیحِ **ماندگارِ** مالک ثبت می‌شد و برای همیشه در contextِ خودشناسی می‌ماند.
   مثبتِ کاذب اینجا یعنی مسمومیتِ دائمیِ حافظه، نه یک خطای گذرا.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness   # noqa: E402
ENV = harness.setup("html-correction-safety")

import ask_brain as ab      # noqa: E402
import mirror_room as mr    # noqa: E402
import self_patch as sp     # noqa: E402

HOSTILE = '<script>alert(1)</script> & "x" <b>bold</b>'


def _clean(body: str, label: str):
    assert "<script>" not in body, f"{label}: تگِ خام رد شد"
    assert "&lt;script&gt;" in body, f"{label}: escape نشد"
    # تگ‌های عمدیِ خودِ کارت باید بمانند
    assert "<b>" in body or "<i>" in body or "<code>" in body, \
        f"{label}: قالبِ خودِ کارت هم escape شد"


# ─── ۱: هر سطحی که متنِ مدل را نشان می‌دهد ──────────────────────────────────
def t_ask_brain_card_escapes_model_output():
    body, _ = ab.card(HOSTILE, model="fu<gu>")
    _clean(body, "ask_brain")
    assert "<gu>" not in body


def t_mirror_card_escapes_model_output():
    body, _ = mr.card(HOSTILE, model="fugu", corrected=True)
    _clean(body, "mirror")
    assert "ثبت شد" in body, "پیامِ تصحیح از بین رفت"


def t_self_patch_card_escapes_defect_and_diff():
    """بدترین مورد: diff تقریباً همیشه `<` دارد."""
    body = sp.card_text({"target": "_ops/x.py", "defect": HOSTILE,
                         "diff": "- if a < b:\n+ if a <= b:"})
    assert "<script>" not in body, "متنِ مدل خام رد شد"
    assert "a &lt; b" in body, "diff خام رد شد — پیام ۴۰۰ می‌شود"
    assert "<code>" in body and "<b>" in body, "قالبِ کارت خراب شد"


def t_the_know_card_escapes_the_self_model():
    body = mr.know_card()
    assert isinstance(body, str) and body
    # هر مقداری که از فایلِ خودشناسی می‌آید باید از escape رد شده باشد
    assert body.count("<b>") >= 1


def t_the_corrections_card_escapes_owner_text():
    mr.record_correction(HOSTILE)
    body = mr.corrections_card()
    assert "<script>" not in body, "متنِ خودِ مالک خام رد شد"
    assert "&lt;script&gt;" in body


def t_no_card_surface_interpolates_raw_model_text():
    """گاردِ کلاس: هر ماژولی که کارت می‌سازد باید escape داشته باشد."""
    for mod in (ab, mr, sp):
        src = Path(mod.__file__).read_text("utf-8")
        if "parse_mode" in src or "<b>" in src or "<code>" in src:
            assert "html" in src and "escape" in src, \
                f"{Path(mod.__file__).name}: کارتِ HTML بدونِ escape"


# ─── ۲: تشخیصِ تصحیح باید مرزِ کلمه داشته باشد ──────────────────────────────
def t_ordinary_persian_sentences_are_not_recorded_as_corrections():
    """مثبتِ کاذب اینجا یعنی نویزِ دائمی در فهمِ اختاپوس از خودش."""
    for s in ("برنامهٔ روزانه چیست؟", "خانه را چک کن", "چگونه کار می‌کنی؟",
              "هزینهٔ ماهانه چقدر شد", "گزارشِ هفتگی را بده",
              "وضعیت خوب است", "بهانه نیار", "سالانه چقدر خرج شد؟"):
        assert not mr.looks_like_correction(s), f"جملهٔ عادی تصحیح شمرده شد: {s}"


def t_real_corrections_are_still_detected():
    for s in ("نه، این اشتباه است", "نه این‌طور نیست", "برعکس، درآمد صفر است",
              "نخیر", "این غلط است", "تمرکزت اشتباه است",
              "واقعیت این است که پول درنیامده", "نه."):
        assert mr.looks_like_correction(s), f"تصحیحِ واقعی گرفته نشد: {s}"


def t_an_empty_or_whitespace_message_is_never_a_correction():
    for s in ("", "   ", "\n", None):
        assert not mr.looks_like_correction(s)


def t_the_detector_uses_a_word_boundary_not_a_bare_substring():
    """گاردِ ساختاری علیهِ بازگشتِ همان باگ."""
    src = Path(mr.__file__).read_text("utf-8")
    assert '_CORRECTION_HINTS' not in src, "تشخیصِ زیررشته‌ایِ قدیمی برگشت"
    assert "_CORRECTION_RX" in src, "الگوی مرزدار نیست"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_html_and_correction_safety: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
