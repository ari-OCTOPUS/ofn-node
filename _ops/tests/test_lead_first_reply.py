#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_first_reply — ماژول B: پاسخِ اولِ خودکار (فقط تولیدِ متن).

آنچه اثبات می‌شود (هر ادعا با سنجهٔ **مستقل**، نه با خودِ تابعِ ماژول):
  · flag خاموش / halt  → هیچ متنی.
  · قیمت هرگز: باتریِ ورودیِ متخاصم (دلار/یورو/متری/رقمِ فارسی/«5k») → بدنه پس از
    برداشتنِ شمارهٔ config صفر رقم و صفر نشانهٔ ارز دارد — با regex ِ خودِ تست.
  · کاندیدِ غیرِ consented_inbound (market_signal / basis=none / ارتقاء‌طلبِ کانالِ سیگنال)
    → **هیچ**؛ نه متنِ ناقص، نه نشتِ محتوا در reason.
  · شماره از config می‌آید: دو configِ متفاوت → دو شمارهٔ متفاوت؛ بی‌config → بی‌شماره؛
    و سورسِ ماژول هیچ literal ِ شماره‌مانند ندارد.
  · هرگز نمی‌فرستد (AST: صفر import ِ شبکه) و هرگز نمی‌نویسد (اسنپ‌شاتِ درختِ sandbox).
  · round-trip ِ تولیدی: submit_candidate واقعی → فایلِ inbox → همان فایل ورودیِ composer.
  · TEETH: بازسازیِ رفتارِ پیش‌از-فیکس (f-string ِ خام + شمارهٔ literal + بی‌گاردِ رضایت)
    و نشان‌دادنِ اینکه دقیقاً همین assertها رویش **می‌افتند**.

هیچ شبکه‌ای، هیچ IMAP/SMTP، هیچ نوشتنی بیرونِ sandbox ِ harness.
"""
import ast
import os
import re
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-first-reply")

# ماشینِ میزبان ممکن است config/flag ِ زنده داشته باشد — تست باید قطعی باشد.
for _k in ("OCTOPUS_WIRE_LEAD_FIRST_REPLY", "OCTOPUS_LEAD_REPLY_PHONE",
           "OCTOPUS_LEAD_REPLY_BUSINESS", "OCTOPUS_LEAD_REPLY_OWNER",
           "OCTOPUS_LEAD_REPLY_ABN", "OCTOPUS_WIRE_LEAD_CANDIDATES",
           "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE", "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE_LLM"):
    os.environ.pop(_k, None)

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lead_first_reply as lfr        # noqa: E402
import lead_candidate_inbox as lci    # noqa: E402

MODULE_SRC = Path(lfr.__file__).read_text("utf-8")

# شماره‌های **ساختگی** برای تست — هیچ شمارهٔ واقعیِ مالک در هیچ فیکسچری نیست.
FAKE_PHONE_A = "0400 000 111"
FAKE_PHONE_B = "0499 888 777"
FAKE_ABN = "11 222 333 444"
CFG_A = {"phone": FAKE_PHONE_A, "business_name": "Test Painting Co",
         "owner_name": "Ari", "abn": FAKE_ABN}

# سنجه‌های مستقلِ تست (عمداً از توابعِ ماژول استفاده نمی‌کنند).
RE_ANY_DIGIT = re.compile(r"[0-9٠-٩۰-۹０-９]")
RE_CURRENCY = re.compile(r"[$€£¥₹﷼₪₩¢]|\b(AUD|USD|NZD|dollars?|cents?|GST|grand)\b", re.I)
RE_PHONE_LITERAL = re.compile(r"(?:\+?61|0)[0-9 \-()]{7,}")


def _cand(scope, *, channel="website_form", basis="explicit", name="Sarah Nguyen",
          email=None, declared="consented_inbound"):
    c = {
        "candidate_type": declared,
        "source": {"channel": channel, "source_id": "test", "external_id": None},
        "consent": {"basis": basis, "evidence": "inbound_enquiry",
                    "compliance_reason": "replied to their own enquiry"},
        "contact": {"name": name},
        "property": {"suburb": "Marrickville"},
        "request": {"scope_text": scope, "service": "painting"},
    }
    if email:
        c["contact"]["email"] = email
    return c


def _on():
    os.environ["OCTOPUS_WIRE_LEAD_FIRST_REPLY"] = "1"


def _off():
    os.environ.pop("OCTOPUS_WIRE_LEAD_FIRST_REPLY", None)


def _digits_outside_config(body, cfg=CFG_A):
    """رقم‌هایی که **مقدارِ config نیستند** — سنجهٔ مستقلِ «قیمت هرگز»."""
    t = body
    for k in ("phone", "abn", "business_name", "owner_name"):
        v = cfg.get(k) or ""
        if v:
            t = t.replace(v, " ")
    return RE_ANY_DIGIT.findall(t)


# ── A. گیت و halt ───────────────────────────────────────────────────────────────
def t_a1_flag_off_produces_nothing():
    _off()
    r = lfr.compose_first_reply(_cand("Paint my hallway please"), config=CFG_A)
    assert r["ok"] is False and r["body"] is None and r["subject"] is None, r
    assert r["reason"] == "gate_off", r


def t_a2_halt_produces_nothing():
    _on()
    import opslib
    opslib.STOP_ORGANISM.parent.mkdir(parents=True, exist_ok=True)
    opslib.STOP_ORGANISM.write_text("test halt", "utf-8")   # داخلِ sandbox ِ harness
    try:
        r = lfr.compose_first_reply(_cand("Paint my hallway please"), config=CFG_A)
        assert r["ok"] is False and r["body"] is None, r
        assert r["reason"].startswith("halted:"), r
    finally:
        opslib.STOP_ORGANISM.unlink()
    r2 = lfr.compose_first_reply(_cand("Paint my hallway please"), config=CFG_A)
    assert r2["ok"] is True, r2      # halt برداشته شد → دوباره کار می‌کند


# ── B. مسیرِ خوشحال ─────────────────────────────────────────────────────────────
def t_b1_consented_inbound_produces_a_warm_reply():
    _on()
    r = lfr.compose_first_reply(
        _cand("Hi, we just bought a terrace in Marrickville and want the inside repainted "
              "before we move in. Are you around this month?"), config=CFG_A)
    assert r["ok"] is True, r
    b = r["body"]
    assert b.startswith("Hi Sarah,"), b[:40]
    assert "Test Painting Co" in b
    assert b.count("?") >= 3, "حداقل ۳ سوالِ واجد شرایط"           # property/scope/timing
    assert "house, a unit, or a commercial" in b                    # نوعِ ملک
    assert "interior, exterior" in b                                # داخلی/بیرونی
    assert "have the work done" in b and "access" in b              # زمان‌بندی و دسترسی
    assert "come and have a look at the place" in b                 # بازدیدِ حضوری
    assert FAKE_PHONE_A in b                                        # شمارهٔ تماس
    assert "will call you himself" in b                             # انتظارِ تماسِ انسانی
    assert "reply with the word STOP" in b                          # opt-out ِ کارآمد
    assert "ABN " + FAKE_ABN in b                                   # شناسهٔ فرستنده
    assert r["delivered"] is False and r["language"] == "en", r
    assert r["echo_used"] is True and "terrace" in b


def t_b2_echo_quotes_the_customer_back():
    _on()
    r = lfr.compose_first_reply(_cand("The weatherboards out the back are flaking badly"),
                                config=CFG_A)
    assert r["ok"] and "weatherboards out the back are flaking badly" in r["body"], r


def t_b4_suburb_personalises_when_the_echo_has_to_be_dropped():
    """پیامی که سراسر حرفِ قیمت است نقلِ‌قول نمی‌گیرد — ولی باید باز هم شخصی بماند."""
    _on()
    r = lfr.compose_first_reply(
        _cand("How much per square metre do you charge? Last painter quoted 38/sqm."),
        config=CFG_A)
    assert r["ok"] and r["echo_used"] is False, r
    assert "about your place in Marrickville" in r["body"], r["body"]
    assert not _digits_outside_config(r["body"]), r["body"]
    # کدپستیِ چسبیده به محله هرگز رقم وارد نمی‌کند
    c = _cand("How much do you charge?")
    c["property"]["suburb"] = "Marrickville 2204"
    r2 = lfr.compose_first_reply(c, config=CFG_A)
    assert r2["ok"] and "Marrickville" in r2["body"], r2["body"]
    assert not _digits_outside_config(r2["body"]), r2["body"]


def t_b3_no_name_still_reads_human():
    _on()
    r = lfr.compose_first_reply(_cand("Repaint two bedrooms", name=""), config=CFG_A)
    assert r["ok"] and r["body"].startswith("Hi there,"), r["body"][:30]


# ── C. قیمت هرگز (اصلی‌ترین قرارداد) ────────────────────────────────────────────
PRICE_BAIT = [
    "Our budget is $4,500 and we want three bedrooms done",
    "How much per square metre do you charge? Last painter quoted 38/sqm",
    "we paid €2000 last time, can you beat it",
    "Need a cheap job, around 5k, 120 sqm townhouse",
    "بودجه ما ۴۵۰۰ دلار است",                       # رقمِ فارسی + واژهٔ دلار
    "Quote for 3 bed 2 bath, GST inclusive please",
    "AUD 7,800 was the last quote. Can you do better?",
    "I have $$$ ready, just paint the 1st floor now!!!",
    "10% deposit ok? call me on 0412 345 678",       # شمارهٔ خودِ مشتری هم رقم است
    "Paint 4 rooms. Rate?",
    # رقم **بدونِ** حرفِ پول: جمله حذف نمی‌شود، پس پاک‌سازیِ رقم باید واقعاً کار کند.
    # (این مورد را جهش‌آزمایی پیدا کرد: بدونش M5 «حذفِ پاک‌سازیِ رقم» زنده می‌ماند.)
    "Paint 3 bedrooms and 2 bathrooms plus the 1st floor landing",
    "The place at 12 Smith St needs the trim done, we have 2 dogs",
    # عددِ ۳رقمیِ بدونِ حرفِ پول: نگاشتِ «۱..۱۲ → واژه» به آن نمی‌خورد، پس تنها چیزی که
    # جلویش را می‌گیرد فیلترِ توکنِ رقم‌دار است (بدونِ این مورد، جهشِ M5 زنده می‌ماند).
    "Paint the 120 window frames and the front door, plus 250 metres of skirting",
]


def t_c1_no_price_ever_across_the_adversarial_battery():
    _on()
    for scope in PRICE_BAIT:
        r = lfr.compose_first_reply(_cand(scope), config=CFG_A)
        assert r["ok"] is True, (scope, r)          # هرگز «هیچ» به‌خاطرِ طعمهٔ قیمت
        body = r["body"] + "\n" + r["subject"]
        stray = _digits_outside_config(body)
        assert not stray, (scope, "رقمِ غیرمجاز در بدنه:", stray)
        assert not RE_CURRENCY.search(body), (scope, "نشانهٔ ارز در بدنه")
        assert "sqm" not in body.lower() and "per square" not in body.lower(), scope


def t_c2_price_sentences_are_dropped_not_half_quoted():
    _on()
    r = lfr.compose_first_reply(
        _cand("We want the front fence and the garage door painted. "
              "Our budget is about $3,000 all up."), config=CFG_A)
    assert r["ok"], r
    assert "front fence and the garage door painted" in r["body"]
    assert "budget" not in r["body"].lower(), "جملهٔ قیمتی باید کامل حذف شود"


def t_c4_digits_are_scrubbed_from_a_sentence_that_survives():
    """جمله‌ای که حرفِ پول ندارد **می‌ماند** — پس رقم‌هایش باید واقعاً پاک شوند."""
    _on()
    r = lfr.compose_first_reply(
        _cand("Paint 3 bedrooms and 2 bathrooms plus the 1st floor landing"), config=CFG_A)
    assert r["ok"] and r["echo_used"] is True, r
    assert "bedrooms" in r["body"] and "bathrooms" in r["body"], r["body"]
    assert not _digits_outside_config(r["body"]), r["body"]
    assert "three bedrooms" in r["body"], r["body"]     # خوانا مانده، نه بریده
    # عددِ بزرگ‌تر از نگاشتِ واژه‌ای: توکنش باید حذف شود، نه اینکه رقم بماند
    r2 = lfr.compose_first_reply(
        _cand("Paint the 120 window frames and the front door"), config=CFG_A)
    assert r2["ok"] and r2["echo_used"] is True, r2
    assert "window frames" in r2["body"] and "120" not in r2["body"], r2["body"]
    assert not _digits_outside_config(r2["body"]), r2["body"]


def t_c3_customer_phone_never_leaks_into_the_reply():
    _on()
    r = lfr.compose_first_reply(_cand("call me on 0412 345 678 about the hallway"),
                                config=CFG_A)
    assert r["ok"], r
    assert "0412" not in r["body"] and "345 678" not in r["body"], r["body"]


# ── D. رضایت: هر چیزی جز consented_inbound → هیچ ────────────────────────────────
NON_CONSENTED = [
    ("nsw_da", "explicit", "consented_inbound"),        # کانالِ سیگنال، ارتقاءطلب
    ("facebook_group", "explicit", "consented_inbound"),
    ("domain_listing", "explicit", "consented_inbound"),
    ("other", "explicit", "consented_inbound"),         # «مطمئن نیستم» = سخت‌گیر
    ("made_up_channel", "explicit", "consented_inbound"),   # ناشناخته → fail-closed
    ("website_form", "none", "consented_inbound"),      # رضایتِ غایب
    ("website_form", "unknown", "consented_inbound"),
    ("website_form", "inferred_business", "consented_inbound"),   # نه explicit
    ("telegram_manual", "", "consented_inbound"),
]


def t_d1_non_consented_candidate_yields_nothing():
    _on()
    for channel, basis, declared in NON_CONSENTED:
        r = lfr.compose_first_reply(
            _cand("Please paint my whole house", channel=channel, basis=basis,
                  declared=declared), config=CFG_A)
        assert r["ok"] is False, (channel, basis, r)
        assert r["body"] is None and r["subject"] is None, (channel, basis, r)
        # privacy: reason فقط کدِ enum — هیچ محتوایی از پیام داخلش نیست
        assert "paint my whole house" not in r["reason"].lower(), r["reason"]
        assert "Sarah" not in r["reason"], r["reason"]


def t_d1b_outreach_allowed_b2b_still_gets_no_reply():
    """کلیدی‌ترین موردِ مرزی (جهش‌آزمایی پیدایش کرد): `escalated_b2b` با
    `basis=inferred_business` + evidence از نظرِ firewall **outreach_allowed=True** است —
    ولی آن‌ها هرگز به ما ننوشته‌اند. یک «پاسخ» به آن‌ها دقیقاً موردِ غیرقانونیِ Spam Act
    است. پس شرطِ `candidate_type == consented_inbound` مستقلاً لازم است، نه تزئینی."""
    _on()
    import consent_firewall as cf
    b2b = {"candidate_type": "public_b2b",
           "source": {"channel": "escalated_b2b"},
           "consent": {"basis": "inferred_business",
                       "evidence": "office_contact_published"},
           "contact": {"name": "Strata Manager"},
           "request": {"scope_text": "Manages twelve blocks in the inner west"}}
    v = cf.evaluate(b2b)
    assert v["candidate_type"] == "public_b2b" and v["outreach_allowed"] is True, v
    r = lfr.compose_first_reply(b2b, config=CFG_A)
    assert r["ok"] is False and r["body"] is None, r
    assert r["reason"] == "not_consented_inbound:public_b2b", r


def t_d2_missing_scope_yields_nothing():
    _on()
    r = lfr.compose_first_reply(_cand("   "), config=CFG_A)
    assert r["ok"] is False and r["reason"] == "no_scope_text", r
    assert lfr.compose_first_reply({}, config=CFG_A)["ok"] is False
    assert lfr.compose_first_reply(None, config=CFG_A)["ok"] is False


def t_d3_synthetic_is_stamped_not_disguised():
    _on()
    r = lfr.compose_first_reply(_cand("Paint the kitchen", channel="synthetic_test"),
                                config=CFG_A)
    assert r["ok"] is True and r["synthetic"] is True, r
    r2 = lfr.compose_first_reply(_cand("Paint the kitchen"), config=CFG_A)
    assert r2["synthetic"] is False, r2


# ── E. شماره از config، نه از کد ────────────────────────────────────────────────
def t_e1_phone_comes_from_config_two_different_values():
    _on()
    ra = lfr.compose_first_reply(_cand("Paint the deck"), config=dict(CFG_A))
    rb = lfr.compose_first_reply(_cand("Paint the deck"),
                                 config={**CFG_A, "phone": FAKE_PHONE_B})
    assert FAKE_PHONE_A in ra["body"] and FAKE_PHONE_B not in ra["body"], ra["body"]
    assert FAKE_PHONE_B in rb["body"] and FAKE_PHONE_A not in rb["body"], rb["body"]


def t_e2_no_phone_in_config_means_no_phone_and_no_digits():
    _on()
    r = lfr.compose_first_reply(_cand("Paint the deck"),
                                config={"business_name": "Test Painting Co",
                                        "owner_name": "Ari"})
    assert r["ok"] is True and r["phone_present"] is False, r
    assert "phone_missing_from_config" in r["warnings"], r
    assert not RE_ANY_DIGIT.findall(r["body"]), r["body"]
    assert "reply to this email" in r["body"], r["body"]


def t_e3_module_source_holds_no_phone_literal():
    hits = [h for h in RE_PHONE_LITERAL.findall(MODULE_SRC) if h.strip()]
    assert not hits, ("شمارهٔ literal در سورسِ ماژول:", hits)


def t_e4_config_precedence_overrides_beat_env_beat_profile():
    _on()
    os.environ[lfr.ENV_PHONE] = FAKE_PHONE_B
    os.environ[lfr.ENV_BUSINESS] = "Env Painting"
    try:
        r_env = lfr.compose_first_reply(_cand("Paint the deck"))
        assert FAKE_PHONE_B in r_env["body"] and "Env Painting" in r_env["body"], r_env
        r_ovr = lfr.compose_first_reply(_cand("Paint the deck"),
                                        config={"phone": FAKE_PHONE_A})
        assert FAKE_PHONE_A in r_ovr["body"] and FAKE_PHONE_B not in r_ovr["body"], r_ovr
    finally:
        os.environ.pop(lfr.ENV_PHONE, None)
        os.environ.pop(lfr.ENV_BUSINESS, None)


def t_e5_profile_file_is_a_config_source():
    """policy-profile ِ gitignored (همان منبعِ invoice.py) — در sandbox، نه فایلِ واقعی."""
    _on()
    import json
    prof = Path(ENV["root"]) / "03 - Projects" / "Accounting" / "personal" / "policy-profile.json"
    prof.parent.mkdir(parents=True, exist_ok=True)
    prof.write_text(json.dumps({
        "business_name": "Profile Painting", "business_phone": FAKE_PHONE_B,
        "owner_name": "Ari", "entities": [{"abn": FAKE_ABN}]}), "utf-8")
    try:
        r = lfr.compose_first_reply(_cand("Paint the deck"))
        assert r["ok"] and FAKE_PHONE_B in r["body"] and "Profile Painting" in r["body"], r
        assert r["abn_present"] is True and ("ABN " + FAKE_ABN) in r["body"], r
    finally:
        prof.unlink()


# ── F. بدونِ تعهد ───────────────────────────────────────────────────────────────
FORBIDDEN_COMMITMENT = [
    "guarantee", "within the hour", "within the day", "within the week",
    "no later than", "fixed price", "booked you in", "the job will take",
    "we will start", "we will finish", "by monday", "by friday",
]


def t_f1_no_commitment_to_date_duration_or_scope():
    _on()
    for scope in PRICE_BAIT + ["Can you start Monday and finish in two days?"]:
        r = lfr.compose_first_reply(_cand(scope), config=CFG_A)
        assert r["ok"], (scope, r)
        low = r["body"].lower()
        for bad in FORBIDDEN_COMMITMENT:
            assert bad not in low, (scope, bad)


def t_f2_template_is_english_only():
    _on()
    r = lfr.compose_first_reply(_cand("Paint the study"), config=CFG_A)
    assert not re.search(r"[؀-ۿ]", r["body"]), "بدنهٔ انگلیسی نباید فارسی داشته باشد"
    # اما نامِ خودِ مشتری اگر فارسی باشد مجاز است (مشتریِ ایرانیِ سیدنی)
    r2 = lfr.compose_first_reply(_cand("Paint the study", name="سارا"), config=CFG_A)
    assert r2["ok"] and r2["body"].startswith("Hi سارا,"), r2["body"][:20]


# ── G. هرگز نمی‌فرستد / هرگز نمی‌نویسد (ساختاری) ───────────────────────────────
BANNED_IMPORTS = {"smtplib", "socket", "ssl", "http", "urllib", "urllib2", "requests",
                  "httpx", "imaplib", "poplib", "ftplib", "telnetlib", "asyncio",
                  "subprocess", "email"}
# `replace` تنها به‌صورتِ **qualified** ممنوع است (`os.replace` = نوشتنِ اتمیک)؛
# `str.replace` بی‌گناه است و باید بماند وگرنه گارد دروغِ مثبت می‌دهد.
BANNED_WRITE_CALLS = {"write_text", "write_bytes", "mkdir", "touch", "unlink",
                      "append_jsonl", "alert", "heartbeat", "ledger_note", "system",
                      "rename", "rmtree", "makedirs", "dump", "writelines"}
BANNED_QUALIFIED = {"os.replace", "os.remove", "os.rename", "os.makedirs", "shutil.copy2",
                    "shutil.move", "json.dump", "opslib.append_jsonl", "opslib.alert"}


def t_g1_module_imports_nothing_that_can_reach_a_network():
    tree = ast.parse(MODULE_SRC)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    bad = found & BANNED_IMPORTS
    assert not bad, ("importِ شبکه/اجرا در ماژولی که فقط متن تولید می‌کند:", bad)


def t_g2_module_makes_no_write_call_at_all():
    tree = ast.parse(MODULE_SRC)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            qual = ""
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                qual = f"{fn.value.id}.{fn.attr}"
            if nm in BANNED_WRITE_CALLS or nm == "open" or qual in BANNED_QUALIFIED:
                bad.append(qual or nm)
    assert not bad, ("فراخوانیِ نوشتن در ماژولِ بی‌اثر:", sorted(set(bad)))


def t_g4_self_guard_catches_a_regression_upstream_of_it():
    """گاردِ نهاییِ قیمت پشتِ سه لایهٔ پاک‌سازی است، پس در مسیرِ عادی هرگز صدا نمی‌کند —
    یعنی «خطِ نادیده». با **تزریقِ نقص** (رگرسیونِ فرضی در پاک‌سازیِ نقلِ‌قول) ثابت می‌کنیم
    که واقعاً دندان دارد: بدنه‌ای با «$4,500» نباید تولید شود، باید **هیچ** شود."""
    _on()
    orig = lfr._echo_from_scope
    lfr._echo_from_scope = lambda s: str(s)[:180]     # رگرسیون: بدونِ هیچ پاک‌سازی
    try:
        r = lfr.compose_first_reply(
            _cand("Our budget is $4,500 for three bedrooms"), config=CFG_A)
        # گارد یا نقلِ‌قول را می‌اندازد یا کلاً «هیچ» می‌دهد — ولی **هرگز** متنِ قیمت‌دار.
        assert not (r["ok"] and _digits_outside_config(r["body"])), r
        assert not (r["ok"] and RE_CURRENCY.search(r["body"])), r
        fired = (r["reason"].startswith("self_guard_price:")
                 or "echo_dropped_price_signal" in (r.get("warnings") or []))
        assert fired, ("گارد باید صدا کرده باشد، نه اینکه تصادفاً تمیز باشد:", r)
    finally:
        lfr._echo_from_scope = orig
    r2 = lfr.compose_first_reply(_cand("Our budget is $4,500 for three bedrooms"),
                                 config=CFG_A)
    assert r2["ok"] is True and "echo_dropped_price_signal" not in r2["warnings"], r2


def t_g4b_price_detector_sees_each_family_of_signal():
    """خودِ آشکارساز (لایهٔ آخر) روی هر خانوادهٔ سیگنال — و اینکه allow کورش نمی‌کند."""
    assert lfr.price_signals("call 0400") == ["digit"]
    assert "currency_symbol" in lfr.price_signals("costs $$$")
    assert "currency_word" in lfr.price_signals("about two thousand dollars")
    assert "currency_word" in lfr.price_signals("GST inclusive")
    assert "digit" in lfr.price_signals("بودجه ۴۵۰۰")          # رقمِ فارسی
    assert lfr.price_signals("reach us on " + FAKE_PHONE_A, allow=(FAKE_PHONE_A,)) == []
    assert "digit" in lfr.price_signals("0400 000 111 and 4500", allow=(FAKE_PHONE_A,))


def t_g5_numeric_business_name_does_not_kill_the_reply():
    """نامِ تجاریِ رقم‌دار (مثلِ «Painting 4 U») از config می‌آید، قیمت نیست — پاسخ باید
    تولید شود و تنها رقم‌های بدنه همان مقادیرِ config باشند."""
    _on()
    cfg = {**CFG_A, "business_name": "Painting 4 U"}
    r = lfr.compose_first_reply(_cand("Paint the hallway"), config=cfg)
    assert r["ok"] is True and "Painting 4 U" in r["body"], r
    assert not _digits_outside_config(r["body"], cfg), r["body"]


def _snapshot(root: Path):
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            try:
                st = p.stat()
                out[str(p)] = (st.st_size, st.st_mtime_ns)
            except OSError:
                out[str(p)] = None
    return out


def t_g3_composing_writes_nothing_to_disk():
    _on()
    root = Path(ENV["root"])
    before = _snapshot(root)
    for scope in PRICE_BAIT:
        lfr.compose_first_reply(_cand(scope), config=CFG_A)
        lfr.compose_first_reply(_cand(scope, channel="nsw_da"), config=CFG_A)
    after = _snapshot(root)
    assert before == after, ("ماژول به دیسک نوشت:",
                             sorted(set(after) ^ set(before))[:5])


# ── H. round-trip ِ تولیدی (نه فیکسچر) ─────────────────────────────────────────
def t_h1_roundtrip_from_the_real_submit_candidate_file():
    """درسِ «خواننده و نویسنده را با هم بسنج»: composer باید دقیقاً همان فایلی را بخورد
    که `lead_candidate_inbox` می‌نویسد — نه یک dict ِ دست‌ساز."""
    _on()
    import json
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        res = lci.submit_candidate(
            _cand("Hi, our strata block in Marrickville needs the common areas repainted. "
                  "Who do we talk to?"), source_id="test-roundtrip")
        assert res["ok"] and res["status"] == "accepted", res
        path = Path(ENV["ops"]) / "state" / "legs" / "lead-inbox" / f"{res['lead_id']}.json"
        assert path.exists(), path
        lead_file = json.loads(path.read_text("utf-8"))
        r = lfr.compose_first_reply(lead_file, config=CFG_A)
        assert r["ok"] is True, r
        assert r["lead_id"] == res["lead_id"], r
        assert "common areas repainted" in r["body"], r["body"]
        assert not _digits_outside_config(r["body"]), r["body"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)


def t_h3_interface_pin_with_module_a_email_intake():
    """قفلِ **مرزِ بین دو ماژول** (درسِ «خواننده و نویسنده را با هم بسنج»).

    `lead_email_intake.classify` ایمیلِ مستقیمِ یک انسان را `channel="other"` +
    `basis="unknown"` می‌دهد (فقط اعلانِ فرمِ شناخته‌شده `website_form` می‌شود). سقفِ
    کانالِ `other` = market_signal ⇒ پاسخِ خودکار **تولید نمی‌شود**. این تست آن حقیقت را
    قفل می‌کند تا تصمیمش رویِ میزِ مالک باشد، نه یک سکوتِ کشف‌نشده در تولید.
    اگر روزی کانالِ صادقانهٔ تازه‌ای (مثلِ email_direct) به اسکیما اضافه شد، این تست
    عمداً می‌شکند و کسی مجبور می‌شود دوباره نگاه کند."""
    _on()
    try:
        import lead_email_intake as lei   # noqa: WPS433
    except Exception:                      # noqa: BLE001 — ماژولِ لِینِ دیگر؛ نبودش نمی‌کشد
        return
    msg = {"from": "Jane Doe <jane@example.com>", "subject": "Quote for painting",
           "body": "Hi, can you paint my terrace in Marrickville? Please call me.",
           "date": "2026-08-01T09:00:00", "message_id": "<abc@example.com>"}
    verdict = lei.classify(msg)
    if not verdict.get("is_inquiry"):
        return
    cand = lei.to_candidate(msg, verdict["channel"], "k1")
    r = lfr.compose_first_reply(cand, config=CFG_A)
    if verdict["channel"] == "website_form":
        assert r["ok"] is True, r
    else:
        assert verdict["channel"] == "other", verdict
        assert r["ok"] is False and r["body"] is None, r
        assert r["reason"] == "not_consented_inbound:market_signal", r


def t_h2_roundtrip_signal_file_never_yields_a_reply():
    """کانالِ سیگنال از همان مسیرِ تولیدی → فایلِ signals/ → composer هیچ نمی‌دهد."""
    _on()
    import json
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        res = lci.submit_candidate(
            _cand("DA lodged for a duplex", channel="nsw_da"), source_id="test-signal")
        assert res["status"] == "signal_recorded", res
        sig = Path(ENV["ops"]) / "state" / "legs" / "lead-inbox" / "signals" / f"{res['lead_id']}.json"
        assert sig.exists(), sig
        payload = json.loads(sig.read_text("utf-8"))
        r = lfr.compose_first_reply(payload.get("candidate"), config=CFG_A)
        assert r["ok"] is False and r["body"] is None, r
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)


# ── I. PII ──────────────────────────────────────────────────────────────────────
def t_i1_customer_email_never_appears_in_the_body():
    _on()
    r = lfr.compose_first_reply(
        _cand("Paint the laundry", email="sarah.nguyen@example.com"), config=CFG_A)
    assert r["ok"], r
    assert "@" not in r["body"], r["body"]


# ── J. TEETH: بازسازیِ رفتارِ پیش‌از-فیکس ───────────────────────────────────────
def _pre_fix_compose(cand, phone="0412 345 678"):
    """بازسازیِ «قبل از فیکس»: interpolation ِ خامِ متنِ مشتری + شمارهٔ literal +
    وعدهٔ زمانی + بدونِ هیچ گاردِ رضایت. (همان شکلی که speed_to_lead._fallback_draft دارد.)"""
    scope = (cand.get("request") or {}).get("scope_text") or ""
    name = (cand.get("contact") or {}).get("name") or "there"
    return {"ok": True, "body": (
        f"Hi {name}, thanks for your enquiry: \"{scope}\". "
        f"I'll come back within the hour with a price. Call me on {phone}.")}


def t_j1_teeth_pre_fix_fails_the_price_assertion():
    _on()
    scope = "Our budget is $4,500 and we want three bedrooms done"
    pre = _pre_fix_compose(_cand(scope))
    now = lfr.compose_first_reply(_cand(scope), config=CFG_A)
    # همان assert ِ t_c1، روی رفتارِ قدیمی:
    pre_stray = _digits_outside_config(pre["body"])
    assert pre_stray, "بازسازیِ پیش‌از-فیکس باید رقم نشت دهد وگرنه تست دندان ندارد"
    assert RE_CURRENCY.search(pre["body"]), "پیش‌از-فیکس باید نشانهٔ ارز داشته باشد"
    # و روی رفتارِ امروز:
    assert not _digits_outside_config(now["body"]), now["body"]
    assert not RE_CURRENCY.search(now["body"]), now["body"]


def t_j2_teeth_pre_fix_fails_the_commitment_and_config_assertions():
    _on()
    pre = _pre_fix_compose(_cand("Paint the hallway"))
    assert "within the hour" in pre["body"].lower(), "بازسازی باید تعهدِ زمانی داشته باشد"
    assert FAKE_PHONE_A not in pre["body"], "شمارهٔ literal ِ پیش‌از-فیکس به config گوش نمی‌دهد"
    now = lfr.compose_first_reply(_cand("Paint the hallway"), config=CFG_A)
    assert "within the hour" not in now["body"].lower(), now["body"]
    assert FAKE_PHONE_A in now["body"], now["body"]


def t_j3_teeth_pre_fix_replies_to_someone_who_never_wrote():
    _on()
    signal = _cand("DA lodged for a duplex in Ashfield", channel="nsw_da",
                   basis="none", declared="market_signal")
    pre = _pre_fix_compose(signal)
    assert pre["ok"] and "Ashfield" in pre["body"], "بازسازی باید به سیگنال هم جواب بدهد"
    now = lfr.compose_first_reply(signal, config=CFG_A)
    assert now["ok"] is False and now["body"] is None, now


def t_j4_the_in_repo_pre_fix_artifact_is_still_consent_blind():
    """`speed_to_lead.build_first_response` (صفر صداکنندهٔ تولیدی) امروز هیچ چکِ رضایتی
    ندارد. ادعا فقط دربارهٔ ماژولِ **خودم** است تا اگر آن یکی روزی فیکس شد نشکند."""
    _on()
    try:
        import speed_to_lead as stl    # noqa: WPS433
    except Exception:                  # noqa: BLE001 — نبودش تست را نمی‌کشد
        return
    os.environ["OCTOPUS_WIRE_LEAD_FIRST_RESPONSE"] = "1"
    try:
        signal = {"lead_id": "x1", "source": "nsw_da",
                  "request": {"scope_text": "DA lodged for a duplex"},
                  "contact": {"name": "Owner"}, "suburb": "Ashfield"}
        old = stl.build_first_response(signal)
        mine = lfr.compose_first_reply(
            _cand("DA lodged for a duplex", channel="nsw_da", basis="none",
                  declared="market_signal"), config=CFG_A)
        assert mine["ok"] is False, mine
        if old.get("ok"):
            assert mine["body"] is None, "قدیمی متن می‌دهد؛ جدید باید ساکت باشد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_FIRST_RESPONSE", None)


# ── K. پایداری ─────────────────────────────────────────────────────────────────
def t_k1_deterministic_and_never_raises():
    _on()
    junk = [None, 3, "string", [], {"source": 5}, {"request": {"scope_text": None}},
            {"source": {"channel": "website_form"}, "request": {"scope_text": "x" * 5000},
             "consent": {"basis": "explicit"}, "candidate_type": "consented_inbound"}]
    for j in junk:
        r = lfr.compose_first_reply(j, config=CFG_A)
        assert isinstance(r, dict) and "ok" in r, (j, r)
        assert r.get("delivered") in (False, None), r
    a = lfr.compose_first_reply(_cand("Paint the porch"), config=CFG_A, now="T")
    b = lfr.compose_first_reply(_cand("Paint the porch"), config=CFG_A, now="T")
    assert a == b, "خروجی باید قطعی باشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_first_reply: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
