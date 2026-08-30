#!/usr/bin/env python3
"""test_denylist_bilingual.py — گاردهای denylist باید فارسی هم بفهمند (لِین B · 2026-08-03).

چرا این فایل هست:
همهٔ denylist/scrubهای این ونچر تطبیقِ **substring روی `.lower()`** می‌کنند، و
`str.lower()` روی فارسی بی‌اثر است. نتیجه: «Sydney» بلاک می‌شد ولی «سیدنی» از
همان فیلتر رد می‌شد — یعنی قاعدهٔ قفل‌شدهٔ #۶ (هیچ فکتِ جغرافیایی در حدِ شهر،
هیچ سیگنالِ متنیِ قومی) در برابرِ ورودیِ فارسی بی‌دندان بود. مالکِ این سیستم و
خالقِ محتوا هر دو فارسی‌زبان‌اند، پس ورودیِ فارسی حالتِ **عادی** است نه لبه.

پوشش (۸ لایه، هر کدام از مسیرِ واقعیِ خودش):
  brain/dual_brain_v3.py     _guard_text        ← FORBIDDEN_TERMS
  brain/acquisition_pipeline AcquisitionPipeline._copy_ok / auto_plan  ← _BANNED_COPY
  brain/dm_pipeline.py       DmPipeline._copy_ok / draft               ← _BANNED_DM
  langar/vault_admin.py      _is_clean / handle_vault                  ← _BANNED
  studio/creator_brain.py    GuardLayer.filter_output                  ← FORBIDDEN_TERMS
  pf_os/bridge.py            _scrub_summary                            ← _PII_TERMS
  pf_os/brain.py             scrub_for_cortex                          ← _SCRUB_TERMS
  pf_os/event_bus.py         _scrub                                    ← _BANNED_ECHO

و یک گاردِ **ضدِ over-blocking**: «Aussie / Australia / استرالیایی» طبقِ
VOICE-AND-STYLE و قاعدهٔ #۶ مجازند و هرگز نباید بلاک شوند — وگرنه این فیکس
خودش یک رگرسیون است.

بدونِ شبکه، بدونِ توکن، state در tmp_path.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
for _p in [str(_PROJ), str(_PROJ / "brain"), str(_PROJ / "studio"),
           str(_PROJ / "langar")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import vault_admin  # noqa: E402  — langar/
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402
from creator_brain import GuardLayer  # noqa: E402
from dm_pipeline import DmPipeline  # noqa: E402
from dual_brain_v3 import _guard_text  # noqa: E402
from pf_os import brain as pf_brain  # noqa: E402
from pf_os import bridge as pf_bridge  # noqa: E402
from pf_os import event_bus  # noqa: E402

# ── نمونه‌های فارسیِ واقعی (همان چیزی که مالک/خالق تایپ می‌کند) ───────────────
FA_CITY = "امروز از سیدنی عکس گرفتم"
FA_CITY_AR_YEH = "امروز از سيدني عکس گرفتم"      # ی/ک عربی — کیبوردِ عربی/کپی از وب
FA_ETHNIC = "یه ست با تمِ ایرانی بزنیم"
FA_LANG = "کپشن رو فارسی بنویس"
FA_PLATFORM = "لینکِ فنسلی رو بفرست"
FA_PAYPAL = "پولش رو پی‌پال بفرست برام"
FA_CARD = "کارت به کارت کن راحت‌تره"
FA_MELBOURNE = "غروبِ ملبورن قشنگ بود"

# ── نمونه‌هایی که **نباید** بلاک شوند (گاردِ over-blocking) ───────────────────
OK_AUSSIE = "Aussie arch of the day, soft light"
OK_AUSTRALIAN_FA = "حال‌وهوای استرالیایی این هفته خوب جواب داد"
OK_PLAIN_FA = "این هفته دو ست جدید آماده کردم"


# ════════════════════════════════════════════════════════════════════════════
# ۱. brain/dual_brain_v3.py — FORBIDDEN_TERMS
# ════════════════════════════════════════════════════════════════════════════
def test_dual_brain_blocks_persian_city():
    ok, violations = _guard_text(FA_CITY)
    assert ok is False, "«سیدنی» فارسی باید مثلِ Sydney بلاک شود (rule #6)"
    assert violations, "باید حداقل یک violation گزارش شود"


def test_dual_brain_blocks_persian_city_arabic_yeh():
    ok, _ = _guard_text(FA_CITY_AR_YEH)
    assert ok is False, "شکلِ ی/ک عربیِ «سيدني» هم باید بلاک شود"


def test_dual_brain_blocks_persian_ethnicity():
    assert _guard_text(FA_ETHNIC)[0] is False, "«ایرانی» باید مثلِ iranian بلاک شود"
    assert _guard_text(FA_LANG)[0] is False, "«فارسی» باید مثلِ persian بلاک شود"


def test_dual_brain_blocks_persian_offplatform_payment():
    assert _guard_text(FA_PAYPAL)[0] is False, "«پی‌پال» باید مثلِ paypal بلاک شود"
    assert _guard_text(FA_CARD)[0] is False, "«کارت به کارت» = مسیرِ پرداختِ خارج‌پلتفرم"


def test_dual_brain_allows_country_level_and_plain_persian():
    assert _guard_text(OK_AUSSIE)[0] is True, "Aussie کشوری است و مجاز (VOICE-AND-STYLE)"
    assert _guard_text(OK_AUSTRALIAN_FA)[0] is True, "«استرالیایی» کشوری است و مجاز"
    assert _guard_text(OK_PLAIN_FA)[0] is True, "جملهٔ فارسیِ بی‌خطر نباید بلاک شود"


# ════════════════════════════════════════════════════════════════════════════
# ۲. brain/acquisition_pipeline.py — _BANNED_COPY
# ════════════════════════════════════════════════════════════════════════════
def _acq(tmp_path):
    return AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None)


def test_acq_copy_guard_blocks_persian_terms():
    assert AcquisitionPipeline._copy_ok(FA_ETHNIC) is False, "«ایرانی» در کپی ممنوع"
    assert AcquisitionPipeline._copy_ok(FA_MELBOURNE) is False, "«ملبورن» = شهرِ ممنوع"
    assert AcquisitionPipeline._copy_ok(FA_PLATFORM) is False, "«فنسلی» = نامِ پلتفرم"
    assert AcquisitionPipeline._copy_ok(FA_CITY_AR_YEH) is False, "ی/ک عربی هم باید گرفته شود"


def test_acq_copy_guard_allows_country_level():
    assert AcquisitionPipeline._copy_ok(OK_AUSSIE) is True
    assert AcquisitionPipeline._copy_ok(OK_AUSTRALIAN_FA) is True
    assert AcquisitionPipeline._copy_ok(OK_PLAIN_FA) is True


def test_acq_all_clean_rejects_when_any_field_persian_dirty(tmp_path):
    """گارد روی هر سه فیلد است — hookِ فارسیِ ناپاک کلِ آیتم را flag می‌کند."""
    acq = _acq(tmp_path)
    assert acq._all_clean("caption تمیز", "عکس پا از سیدنی", "tag") is False
    assert acq._all_clean("caption تمیز", OK_AUSSIE, "arch") is True


# ════════════════════════════════════════════════════════════════════════════
# ۳. brain/dm_pipeline.py — _BANNED_DM (rule #3: پرداخت فقط درون‌پلتفرم)
# ════════════════════════════════════════════════════════════════════════════
def test_dm_guard_blocks_persian_p2p_payment_paths():
    for bad in ("پولش رو پی‌پال بفرست", "پیپال دارم", "کارت به کارت کن",
                "شمارهٔ شبا رو بدم؟", "با رمزارز حساب کن", "بیت‌کوین قبول می‌کنم",
                "تتر بفرست", "حواله می‌کنم"):
        assert DmPipeline._copy_ok(bad) is False, f"مسیرِ پرداختِ P2P رد شد: {bad!r}"


def test_dm_guard_blocks_persian_identity_and_geo():
    assert DmPipeline._copy_ok(FA_CITY) is False
    assert DmPipeline._copy_ok(FA_ETHNIC) is False
    assert DmPipeline._copy_ok(FA_PLATFORM) is False


def test_dm_guard_allows_safe_persian_and_aussie():
    assert DmPipeline._copy_ok(OK_AUSSIE) is True
    assert DmPipeline._copy_ok(OK_AUSTRALIAN_FA) is True
    assert DmPipeline._copy_ok(OK_PLAIN_FA) is True


def test_dm_draft_flags_persian_paypal_end_to_end(tmp_path):
    """مسیرِ واقعیِ تولید: draft() باید flagged=True بدهد و متنِ ناپاک persist نشود."""
    dm = DmPipeline(store_path=tmp_path / "dm.json")
    r = dm.draft(channel="of", kind="general", body=FA_PAYPAL)
    assert r["ok"] is True
    assert r["flagged"] is True, "DMِ حاوی «پی‌پال» باید flag شود (rule #3)"
    item = dm.pending()[0]
    assert "پی‌پال" not in item["body"], "متنِ ناپاک هرگز نباید persist شود"


def test_dm_draft_does_not_flag_clean_persian(tmp_path):
    dm = DmPipeline(store_path=tmp_path / "dm.json")
    r = dm.draft(channel="of", kind="welcome", body=OK_PLAIN_FA)
    assert r["flagged"] is False, "جملهٔ فارسیِ بی‌خطر نباید flag شود (over-blocking)"


# ════════════════════════════════════════════════════════════════════════════
# ۴. langar/vault_admin.py — _BANNED
# ════════════════════════════════════════════════════════════════════════════
class _FakeBank:
    """bankِ ساختگی — تستِ گارد نباید به store/فایلِ تولیدی دست بزند."""

    def __init__(self):
        self.added = []

    def add(self, tag, hook, caption="", channel="reddit"):
        self.added.append((tag, hook, channel))
        return {"id": "V-test"}


def test_vault_is_clean_blocks_persian():
    assert vault_admin._is_clean("pedicure", "تمِ ایرانی", "reddit") is False
    assert vault_admin._is_clean("sunset", FA_CITY, "reddit") is False
    assert vault_admin._is_clean("sunset", FA_PLATFORM, "reddit") is False


def test_vault_is_clean_allows_country_level():
    assert vault_admin._is_clean("arch", OK_AUSSIE, "reddit") is True
    assert vault_admin._is_clean("arch", OK_AUSTRALIAN_FA, "reddit") is True


def test_vault_add_rejects_persian_dirty_hook():
    bank = _FakeBank()
    out = vault_admin.handle_vault("/vault_add", 'pedicure "عکس پا از سیدنی" reddit',
                                   bank=bank)
    assert "flagged" in out, f"assetِ حاویِ شهرِ ممنوع باید رد شود، خروجی: {out!r}"
    assert bank.added == [], "asset ناپاک نباید به vault نوشته شود"


def test_vault_add_accepts_clean_aussie_hook():
    bank = _FakeBank()
    out = vault_admin.handle_vault("/vault_add", 'arch "Aussie arch of the day" reddit',
                                   bank=bank)
    assert "flagged" not in out, f"هوکِ مجاز نباید رد شود، خروجی: {out!r}"
    assert len(bank.added) == 1


# ════════════════════════════════════════════════════════════════════════════
# ۵. studio/creator_brain.py — GuardLayer.FORBIDDEN_TERMS (خروجیِ LLM)
# ════════════════════════════════════════════════════════════════════════════
def test_guardlayer_blocks_persian_llm_output():
    g = GuardLayer()
    assert g.filter_output(FA_CITY)[0] is False, "خروجیِ LLM با «سیدنی» باید بلاک شود"
    assert g.filter_output(FA_ETHNIC)[0] is False
    assert g.filter_output(FA_PAYPAL)[0] is False, "پیشنهادِ پرداختِ خارج‌پلتفرم به فارسی"


def test_guardlayer_allows_warm_persian_reply():
    g = GuardLayer()
    ok, text = g.filter_output(OK_PLAIN_FA)
    assert ok is True, "پاسخِ گرمِ فارسیِ بی‌خطر باید رد شود (سیستم فارسی حرف می‌زند)"
    assert text == OK_PLAIN_FA
    assert g.filter_output(OK_AUSTRALIAN_FA)[0] is True


# ════════════════════════════════════════════════════════════════════════════
# ۶. pf_os/bridge.py — _PII_TERMS (هیچ PII به saba-bridge.jsonl)
# ════════════════════════════════════════════════════════════════════════════
def test_bridge_scrubs_persian_geo_summary():
    assert pf_bridge._scrub_summary("draft جدید از سیدنی") == "[scrubbed]"
    assert pf_bridge._scrub_summary("خلاصهٔ " + FA_ETHNIC) == "[scrubbed]"


def test_bridge_keeps_clean_summary():
    clean = "draft submitted by creator"
    assert pf_bridge._scrub_summary(clean) == clean
    assert pf_bridge._scrub_summary(OK_PLAIN_FA) == OK_PLAIN_FA


# ════════════════════════════════════════════════════════════════════════════
# ۷. pf_os/brain.py — scrub_for_cortex (هیچ محتوای raw به cortex)
# ════════════════════════════════════════════════════════════════════════════
def test_scrub_for_cortex_rejects_persian_pii():
    assert pf_brain.scrub_for_cortex(FA_CITY) == "", "شهرِ فارسی نباید به cortex برود"
    assert pf_brain.scrub_for_cortex(FA_ETHNIC) == ""
    assert pf_brain.scrub_for_cortex(FA_CITY_AR_YEH) == "", "ی/ک عربی هم باید reject شود"


def test_scrub_for_cortex_keeps_clean_persian():
    assert pf_brain.scrub_for_cortex(OK_PLAIN_FA) == OK_PLAIN_FA
    assert pf_brain.scrub_for_cortex(OK_AUSTRALIAN_FA) == OK_AUSTRALIAN_FA


# ════════════════════════════════════════════════════════════════════════════
# ۸. pf_os/event_bus.py — _BANNED_ECHO (هیچ نامِ پلتفرم در لاگ)
# ════════════════════════════════════════════════════════════════════════════
def test_event_bus_scrubs_persian_platform_name():
    out = event_bus._scrub("پستِ فنسلی منتشر شد")
    assert "فنسلی" not in out, "نامِ پلتفرم به فارسی نباید در لاگ echo شود"
    assert "▇" in out


def test_event_bus_scrubs_arabic_yeh_platform_name():
    out = event_bus._scrub("کارتِ اونلي آماده شد")   # ی عربی
    assert "اونلي" not in out, "شکلِ ی عربیِ نامِ پلتفرم هم باید scrub شود"


def test_event_bus_keeps_clean_text_byte_for_byte():
    clean = "queue depth 3, aussie batch ok"
    assert event_bus._scrub(clean) == clean
    assert event_bus._scrub(OK_PLAIN_FA) == OK_PLAIN_FA
