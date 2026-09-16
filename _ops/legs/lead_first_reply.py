#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_first_reply.py — ماژول B: پاسخِ **اولِ خودکار** به یک لیدِ inbound (فقط تولیدِ متن).

چرا (۲۰۲۶-۰۸-۰۱، رأیِ مالک): در خدماتِ خانگی سرعتِ پاسخِ اول تعیین‌کنندهٔ برد است و مالک
معمولاً بالای نردبان است. پس پاسخِ **اول** خودکار می‌شود — ولی هیچ عددی بی‌تپِ او بیرون
نمی‌رود. این ماژول یک کاندیدِ لید را می‌گیرد و یک متنِ کوتاهِ گرمِ **انگلیسی** برمی‌گرداند.

مرزهای غیرقابل‌مذاکره (هر کدام در تست قفل است):
  · **هرگز نمی‌فرستد.** خروجی فقط dict با `body`/`subject`؛ صفر import ِ شبکه
    (smtplib/socket/urllib/requests)، صفر transport، `delivered=False` ساختاری.
  · **هرگز چیزی نمی‌نویسد.** نه فایل، نه لاگ، نه state، نه متریک. تابعِ خالص + خواندنِ
    config. (privacy: هیچ محتوایِ مشتری هرگز به دیسک/لاگ نشت نمی‌کند.)
  · **هیچ قیمتی.** نه عدد، نه بازه، نه «from $X»، نه نرخِ متری، نه «حدوداً». تنها عددهای
    مجاز در متن = شمارهٔ تماس و ABN، و هر دو **از config** می‌آیند نه literal ِ کد.
    گاردِ تولیدی: بدنه قبل از برگشت اسکن می‌شود؛ سیگنالِ قیمت → متن **تولید نمی‌شود**.
  · **هیچ تعهدی** به تاریخ/مدت/scope. فقط قرارِ گفت‌وگو می‌گذارد.
  · **رضایت، ساختاری**: تصمیم فقط از `consent_firewall` (fail-closed). هر چیزی که
    `consented_inbound` + `outreach_allowed` نباشد → **هیچ** (نه متنِ ناقص، نه پیش‌نویس).
    Spam Act 2003: پاسخ به یک استعلامِ inbound قانونی است؛ «پاسخ» به کسی که هرگز ننوشته
    دقیقاً همان موردِ غیرقانونی است. مرجع: `03 - Projects/Lead-نقاشی/Outreach Compliance.md`.
  · انگلیسی برای مشتری (مالک فارسی‌زبان، مشتری انگلیسی‌زبان) + امضای هویتِ فرستنده +
    ABN (اگر در config باشد) + راهِ کارآمدِ opt-out («reply with STOP») که transport ِ
    موجود (`lead_outbound_transport` → `consent_store`) از قبل احترامش را می‌گذارد.

Flag: OCTOPUS_WIRE_LEAD_FIRST_REPLY (پیش‌فرض OFF = no-op ِ بایت‌به‌بایت).
config (به ترتیبِ تقدم): overrides ِ تزریقی → env → policy-profile ِ gitignored.
stdlib-only. هرگز استثنا پرتاب نمی‌کند؛ همیشه dict.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib                    # noqa: E402
import consent_firewall as cf    # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_FIRST_REPLY"

# ── config: نامِ متغیرها (مقدار هرگز در کد نیست) ────────────────────────────────
ENV_PHONE = "OCTOPUS_LEAD_REPLY_PHONE"
ENV_BUSINESS = "OCTOPUS_LEAD_REPLY_BUSINESS"
ENV_OWNER = "OCTOPUS_LEAD_REPLY_OWNER"
ENV_ABN = "OCTOPUS_LEAD_REPLY_ABN"

MAX_ECHO_CHARS = 180
MIN_ECHO_CHARS = 12
_MAX_CFG_CHARS = 60
_MAX_NAME_CHARS = 24

# ── آشکارسازِ سیگنالِ قیمت (هم گاردِ تولیدی، هم ابزارِ تست) ─────────────────────
# رقم‌های فارسی/عربی/تمام‌عرض هم رقم‌اند — وگرنه «۴۵۰۰» از فیلتر رد می‌شد.
_DIGIT_CLASS = "0-9٠-٩۰-۹０-９"
_RE_DIGIT = re.compile("[" + _DIGIT_CLASS + "]")
_RE_CURRENCY_SYM = re.compile("[$€£¥₹﷼₪₩¢]")
_RE_CURRENCY_WORD = re.compile(
    r"\b(aud|a\.u\.d|usd|nzd|dollar|dollars|buck|bucks|cent|cents|grand|gst)\b", re.I)

# واژه‌های «حرفِ پول» — در متنِ **خودم** ممنوع (Tier-2)؛ در نقلِ‌قولِ مشتری فقط باعثِ
# حذفِ همان جمله می‌شود (نه ردِ کلِ پاسخ).
_RE_PRICE_TALK = re.compile(
    r"\b(price|prices|priced|pricing|cost|costs|costing|rate|rates|fee|fees|"
    r"charge|charges|charged|deposit|discount|cheap|cheaper|cheapest|budget|budgets|"
    r"afford|paid|pay|spend|spent|sqm|sq\.?m|m2|per\s+square\s+met(re|er))\b", re.I)
_RE_MONEY_WORD = re.compile(
    r"\b(quote|quotes|quoted|quotation|estimate|estimates|estimated|invoice|"
    r"payment|payments)\b", re.I)

# تعهدِ تاریخ/مدت/scope — در متنِ خودم ممنوع.
_RE_COMMITMENT = re.compile(
    r"\b(guarantee[ds]?|guaranteed|promise[ds]?|we will (start|begin|finish|complete)|"
    r"no later than|by (monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"within the (hour|day|week)|fixed (price|quote|fee)|book(ed)? you in|"
    r"the job will take|it will take|commit(ted|ment)? to)\b", re.I)

# فارسی/عربی در متنِ **قالب** ممنوع (مشتری انگلیسی‌زبان). نامِ خودِ مشتری استثناست.
_RE_PERSIAN = re.compile(r"[؀-ۿ]")

_NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
    "7": "seven", "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve",
}
_DIGIT_FOLD = {}
for _base in (0x0660, 0x06F0, 0xFF10):
    for _i in range(10):
        _DIGIT_FOLD[chr(_base + _i)] = str(_i)


def enabled() -> bool:
    """flag خاموش (پیش‌فرض) = no-op مطلق."""
    return os.environ.get(FLAG, "0") == "1"


# ── آشکارسازها (public: تست دقیقاً همین‌ها را می‌خواند) ─────────────────────────
def price_signals(text: str, *, allow: tuple = ()) -> list:
    """سیگنالِ قیمتِ **سخت** در متن. خروجی فقط *کدِ الگو*، هرگز خودِ متن (privacy).

    `allow` = رشته‌هایی که مجازند رقم داشته باشند (شمارهٔ تماس و ABN ِ config). قبل از
    اسکن حذف می‌شوند — پس نامتغیر این است: «تنها رقم‌های بدنه، مقادیرِ configاند»."""
    t = str(text or "")
    for a in allow or ():
        a = str(a or "").strip()
        if a:
            t = t.replace(a, " ")
    out = []
    if _RE_DIGIT.search(t):
        out.append("digit")
    if _RE_CURRENCY_SYM.search(t):
        out.append("currency_symbol")
    if _RE_CURRENCY_WORD.search(t):
        out.append("currency_word")
    return out


def template_signals(text: str) -> list:
    """سیگنالِ ممنوعِ متنِ **خودم**: حرفِ پول، تعهد، فارسی. کدِ الگو، نه متن."""
    t = str(text or "")
    out = []
    if _RE_PRICE_TALK.search(t):
        out.append("price_talk")
    if _RE_MONEY_WORD.search(t):
        out.append("money_word")
    if _RE_COMMITMENT.search(t):
        out.append("commitment")
    if _RE_PERSIAN.search(t):
        out.append("non_english")
    return out


# ── پاکسازیِ متنِ مشتری برای نقلِ‌قول ────────────────────────────────────────────
def _fold_digits(s: str) -> str:
    return "".join(_DIGIT_FOLD.get(ch, ch) for ch in s)


def _clean_ws(s: str) -> str:
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def _scrub_digits(s: str) -> str:
    """رقم‌ها را از متن بردار: ۱..۱۲ → واژه (خوانا می‌ماند)، بقیه → توکن حذف می‌شود."""
    s = _fold_digits(s)
    s = re.sub(r"(?<![" + _DIGIT_CLASS + r"])([0-9]{1,2})(?![" + _DIGIT_CLASS + r"])",
               lambda m: _NUM_WORDS.get(m.group(1).lstrip("0") or "0", " "), s)
    s = " ".join(tok for tok in s.split(" ")
                 if not _RE_DIGIT.search(tok) and not _RE_CURRENCY_SYM.search(tok))
    return _clean_ws(s)


def _echo_from_scope(scope: str) -> str:
    """نقلِ‌قولِ امنِ خواستهٔ مشتری: جمله‌های «حرفِ پول» حذف، رقم‌ها پاک، کوتاه‌شده.

    اگر چیزی نماند → رشتهٔ خالی و caller نقلِ‌قول را کنار می‌گذارد (پاسخِ عمومی می‌ماند)."""
    # ⚠️ آدرسِ ایمیل **قبل از** هر کارِ دیگری حذف می‌شود.
    # چرا: بدنهٔ تقریباً هر فرمِ سایت خطی مثل `Email: sam@gmail.com` دارد؛ آن
    # آدرس داخلِ نقلِ‌قول می‌آمد و گاردِ PII ِ پایین‌دست کلِ پاسخ را رد می‌کرد
    # (`self_guard_pii_email`). یعنی قابلیت برای **همان مسیری که ساخته شده**
    # ساکت بود: فرمِ سایت. گارد درست عمل می‌کرد، ولی «هیچ پاسخی» جوابِ درستِ
    # یک لیدِ سالم نیست. پس منبع پاک می‌شود و گارد به‌عنوان لایهٔ آخر می‌ماند.
    raw = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", " ", str(scope or ""))
    raw = _clean_ws(_fold_digits(raw))
    if not raw:
        return ""
    kept = []
    for sent in re.split(r"(?<=[.!?;\n])\s+", raw):
        s = sent.strip()
        if not s:
            continue
        if _RE_CURRENCY_SYM.search(s) or _RE_CURRENCY_WORD.search(s) or _RE_PRICE_TALK.search(s):
            continue          # جملهٔ قیمتی کامل حذف — نه نصفه‌نقل‌قولِ بی‌معنی
        kept.append(_scrub_digits(s))
    out = _clean_ws(" ".join(k for k in kept if k))
    out = out.replace('"', "'").replace("“", "'").replace("”", "'")
    if len(out) > MAX_ECHO_CHARS:
        cut = out[:MAX_ECHO_CHARS]
        sp = cut.rfind(" ")
        out = (cut[:sp] if sp > 40 else cut).rstrip(" ,.;:") + "..."
    return out if len(out) >= MIN_ECHO_CHARS else ""


def _safe_name(raw: str) -> str:
    """نامِ کوچکِ مشتری برای سلام. رقم/نشانه حذف؛ حروفِ غیرلاتین مجازند (نامِ خودشان)."""
    s = _clean_ws(_fold_digits(raw))
    s = re.sub(r"[^\w'\- ]", " ", s, flags=re.UNICODE)
    s = " ".join(tok for tok in s.split(" ") if tok and not _RE_DIGIT.search(tok))
    first = s.split(" ")[0] if s else ""
    first = first.strip("-'")
    return first[:_MAX_NAME_CHARS]


def _safe_place(raw: str) -> str:
    """نامِ محله برای شخصی‌کردنِ حالتِ بی‌نقلِ‌قول. رقم (کدپستی) حذف؛ حرفِ پول = دور بریز."""
    s = _clean_ws(_fold_digits(raw))
    s = re.sub(r"[^\w'\- ]", " ", s, flags=re.UNICODE)
    s = " ".join(tok for tok in s.split(" ") if tok and not _RE_DIGIT.search(tok))
    s = _clean_ws(s)[:_MAX_NAME_CHARS]
    if _RE_PRICE_TALK.search(s) or _RE_CURRENCY_WORD.search(s):
        return ""
    return s


def _clean_cfg(raw) -> str:
    return _clean_ws(raw)[:_MAX_CFG_CHARS]


# ── config ──────────────────────────────────────────────────────────────────────
def _profile() -> dict:
    """policy-profile ِ **gitignored** (همان منبعِ invoice.py). fail-soft → {}.

    شمارهٔ تماس عمداً از این فایل خوانده می‌شود نه از فایلِ tracked — تا هرگز واردِ
    تاریخچهٔ git نشود (درسِ `_profile_business` در invoice.py)."""
    try:
        import ledger_core   # noqa: WPS433 — هم‌پوشه، بدونِ I/O شبکه
        return ledger_core.load_profile() or {}
    except Exception:  # noqa: BLE001 — نبودِ profile هرگز مسیر را نمی‌کشد
        return {}


def load_config(overrides: "dict | None" = None) -> dict:
    """هویتِ فرستنده. تقدم: overrides ِ تزریقی > env > policy-profile. هرگز literal.

    کلیدها: phone · business_name · owner_name · abn. غایب = رشتهٔ خالی (نه حدس،
    نه شمارهٔ ساختگی) — متن آن بخش را حذف می‌کند و warning می‌دهد."""
    cfg = {"phone": "", "business_name": "", "owner_name": "", "abn": ""}
    try:
        prof = _profile()
        cfg["phone"] = _clean_cfg(prof.get("business_phone") or prof.get("phone"))
        cfg["business_name"] = _clean_cfg(prof.get("business_name"))
        cfg["owner_name"] = _clean_cfg(prof.get("owner_name") or prof.get("operator_name"))
        for ent in (prof.get("entities") or []):
            if isinstance(ent, dict) and ent.get("abn"):
                cfg["abn"] = _clean_cfg(ent.get("abn"))
                break
    except Exception:  # noqa: BLE001
        pass
    for key, env in (("phone", ENV_PHONE), ("business_name", ENV_BUSINESS),
                     ("owner_name", ENV_OWNER), ("abn", ENV_ABN)):
        val = _clean_cfg(os.environ.get(env, ""))
        if val:
            cfg[key] = val
    if isinstance(overrides, dict):
        for key in ("phone", "business_name", "owner_name", "abn"):
            if key in overrides and str(overrides[key] or "").strip():
                cfg[key] = _clean_cfg(overrides[key])
    return cfg


# ── نرمال‌سازیِ رکورد ────────────────────────────────────────────────────────────
def _as_candidate(record) -> dict:
    """هر دو شکل را می‌پذیرد: کاندیدِ canonical ِ `submit_candidate`، یا فایلِ inbox ِ
    نوشتهٔ `lead_candidate_inbox._to_lead_sense_file` (که در آن `source` رشته است).
    هم‌الگوی `lead_pipeline._rebuild_candidate` — یک شکلِ داده، دو نویسنده."""
    if not isinstance(record, dict):
        return {}
    inner = record.get("candidate")
    if isinstance(inner, dict) and not isinstance(record.get("source"), dict):
        return {
            "lead_id": record.get("lead_id"),
            "source": {"channel": record.get("source")},
            "candidate_type": inner.get("candidate_type"),
            "consent": inner.get("consent") or {},
            "request": inner.get("request") or {},
            "contact": inner.get("contact") or {},
            "property": {"address": record.get("address"), "suburb": record.get("suburb")},
            "description": record.get("description"),
        }
    return record


def _halt_reason() -> "str | None":
    """halt مقدم بر همه‌چیز. هر خطا → fail-closed (سکوت، نه متنِ مشکوک)."""
    try:
        return (opslib.master_halted() or opslib.halted()
                or ("STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None)
                or ("FREEZE" if opslib.frozen() else None))
    except Exception:  # noqa: BLE001
        return "halt_check_failed"


def _nothing(reason: str) -> dict:
    """«هیچ» = هیچ متنی. reason فقط کدِ enum است، هرگز محتوای مشتری (privacy)."""
    return {"ok": False, "reason": str(reason)[:80], "subject": None, "body": None,
            "delivered": False}


# ── ساختِ متن ───────────────────────────────────────────────────────────────────
SUBJECT = "Thanks for your enquiry - a couple of quick questions"


def _build_parts(ctx: dict, use_echo: bool) -> list:
    """بدنه به‌صورتِ قطعه‌های برچسب‌دار: ("tpl") متنِ من · ("cust") متنِ مشتری/config.

    چرا برچسب: گاردِ رقم/ارز روی **کلِ** بدنه اجرا می‌شود، ولی گاردِ حرفِ‌پول/تعهد/فارسی
    فقط روی متنِ خودم — وگرنه واژهٔ خودِ مشتری کلِ پاسخ را می‌کشت."""
    name = ctx["name"]
    business = ctx["business_name"]
    owner = ctx["owner_name"]
    phone = ctx["phone"]
    abn = ctx["abn"]
    suburb = ctx["suburb"]
    echo = ctx["echo"] if use_echo else ""
    p = []

    p.append(("Hi ", "tpl"))
    p.append((name or "there", "cust"))
    p.append((",\n\n", "tpl"))

    if business:
        p.append(("Thanks for getting in touch with ", "tpl"))
        p.append((business, "cust"))
    else:
        p.append(("Thanks for getting in touch", "tpl"))
    # وقتی نقلِ‌قولِ امنی نمانده (مثلاً کلِ پیام حرفِ قیمت بوده)، محله جای آن را می‌گیرد
    # تا پاسخ باز هم شخصی بماند، نه یک قالبِ بی‌روح.
    if not echo and suburb:
        p.append((" about your place in ", "tpl"))
        p.append((suburb, "cust"))
    p.append((".", "tpl"))

    if echo:
        p.append((" You wrote:\n\n  \"", "tpl"))
        p.append((echo, "cust"))
        p.append(("\"\n\nWe've got your message and wanted to get back to you straight "
                  "away rather than leave you waiting.\n\n", "tpl"))
    else:
        p.append((" We've got your message and wanted to get back to you straight "
                  "away rather than leave you waiting.\n\n", "tpl"))

    p.append(("So we can turn up with the right gear and give you a proper answer in "
              "person, could you let us know:\n\n"
              "  - Is it a house, a unit, or a commercial space?\n"
              "  - Which rooms or areas are we looking at, and is it interior, exterior, "
              "or both?\n"
              "  - When were you hoping to have the work done, and is there anything "
              "about access we should know (stairs, tenants, pets, parking)?\n\n"
              "The easiest next step is for us to come and have a look at the place, at "
              "a time that suits you.\n\n", "tpl"))

    if phone:
        if owner:
            p.append(("If it's quicker to talk it through, you can reach ", "tpl"))
            p.append((owner, "cust"))
            p.append((" on ", "tpl"))
        else:
            p.append(("If it's quicker to talk it through, you can reach us on ", "tpl"))
        p.append((phone, "cust"))
        p.append((".\n\n", "tpl"))
    else:
        p.append(("If it's quicker to talk it through, just reply to this email and it "
                  "comes straight to us.\n\n", "tpl"))

    if owner:
        p.append((owner, "cust"))
        p.append((" will call you himself to arrange a time - usually the same day, and "
                  "always as soon as he's off the tools.\n\n", "tpl"))
    else:
        p.append(("One of us will call you to arrange a time - usually the same day, and "
                  "always as soon as we're off the tools.\n\n", "tpl"))

    p.append(("Kind regards,\n", "tpl"))
    if owner:
        p.append((owner, "cust"))
        p.append(("\n", "tpl"))
    if business:
        p.append((business, "cust"))
        p.append(("\n", "tpl"))
    if abn:
        p.append(("ABN ", "tpl"))
        p.append((abn, "cust"))
        p.append(("\n", "tpl"))
    p.append(("\nIf you'd rather not hear from us again, just reply with the word STOP "
              "and we won't contact you again.\n", "tpl"))
    return p


def _join(parts: list, only: "str | None" = None) -> str:
    return "".join(t for t, kind in parts if only is None or kind == only)


def compose_first_reply(record, *, config: "dict | None" = None, now=None) -> dict:
    """کاندیدِ لید → متنِ پاسخِ اول (انگلیسی). **هرگز نمی‌فرستد، هرگز نمی‌نویسد.**

    خروجی: {ok, reason, subject, body, delivered:False, ...} — همیشه dict، هرگز استثنا.
    `ok=False` یعنی **هیچ متنی** (body=None): flag خاموش · halt · غیرِ consented_inbound ·
    بدونِ scope · یا تریپ‌شدنِ گاردِ خودم.
    """
    try:
        if not enabled():
            return _nothing("gate_off")
        kill = _halt_reason()
        if kill:
            return _nothing("halted:" + str(kill)[:40])

        cand = _as_candidate(record)
        if not cand:
            return _nothing("bad_record")

        # رضایت: تنها مرجع، consent_firewall (fail-closed). «پاسخ» به کسی که ننوشته = غیرقانونی.
        verdict = cf.evaluate(cand)
        ctype = str(verdict.get("candidate_type") or "")
        if ctype != "consented_inbound":
            return _nothing("not_consented_inbound:" + (ctype or "unknown"))
        if not verdict.get("outreach_allowed"):
            return _nothing("consent_basis_not_explicit:"
                            + str(verdict.get("consent_basis") or "unknown"))

        req = cand.get("request") if isinstance(cand.get("request"), dict) else {}
        scope_raw = str(req.get("scope_text") or cand.get("description") or "").strip()
        if not scope_raw:
            return _nothing("no_scope_text")

        cfg = load_config(config)
        contact = cand.get("contact") if isinstance(cand.get("contact"), dict) else {}
        warnings = []
        if not cfg["phone"]:
            warnings.append("phone_missing_from_config")
        if not cfg["abn"]:
            warnings.append("abn_missing_from_config")   # Spam Act: شناسهٔ فرستنده
        if not cfg["business_name"]:
            warnings.append("business_name_missing_from_config")

        prop = cand.get("property") if isinstance(cand.get("property"), dict) else {}
        ctx = {
            "name": _safe_name(contact.get("name") or cand.get("applicant") or ""),
            "business_name": cfg["business_name"], "owner_name": cfg["owner_name"],
            "phone": cfg["phone"], "abn": cfg["abn"],
            "suburb": _safe_place(prop.get("suburb") or cand.get("suburb") or ""),
            "echo": _echo_from_scope(scope_raw),
        }
        if not ctx["echo"]:
            warnings.append("echo_omitted_no_safe_text")

        # مقادیرِ config مجازند رقم داشته باشند (شماره، ABN، و نامِ تجاریِ رقم‌دار مثل
        # «Painting 4 U») — قیمت نیستند. سقفِ ۳ کاراکتر تا یک نامِ تک‌رقمی کلِ اسکن را
        # کور نکند. نامتغیر: **هر رقمِ دیگری در بدنه = پاسخ تولید نمی‌شود**.
        allow = tuple(v for v in (cfg["phone"], cfg["abn"], cfg["business_name"],
                                  cfg["owner_name"]) if v and len(v) >= 3)
        use_echo = bool(ctx["echo"])
        parts = _build_parts(ctx, use_echo)
        body = _join(parts)

        # گاردِ سختِ ۱: تنها رقم/ارزِ مجاز، مقادیرِ config. اگر نقلِ‌قول تریپ کرد → بی‌نقلِ‌قول.
        hard = price_signals(body, allow=allow)
        if hard and use_echo:
            warnings.append("echo_dropped_price_signal")
            use_echo = False
            parts = _build_parts(ctx, False)
            body = _join(parts)
            hard = price_signals(body, allow=allow)
        if hard:
            return _nothing("self_guard_price:" + ",".join(sorted(set(hard))))

        # گاردِ سختِ ۲: متنِ خودم — حرفِ پول، تعهد، غیرانگلیسی.
        bad = template_signals(_join(parts, only="tpl") + " " + SUBJECT)
        if bad:
            return _nothing("self_guard_template:" + ",".join(sorted(set(bad))))
        if price_signals(SUBJECT, allow=allow):
            return _nothing("self_guard_subject")

        # گاردِ PII: آدرسِ ایمیلِ مشتری هرگز داخلِ متن interpolate نمی‌شود.
        email = str(contact.get("email") or "").strip()
        if email and email.lower() in body.lower():
            return _nothing("self_guard_pii_email")

        return {
            "ok": True, "reason": "composed", "subject": SUBJECT, "body": body,
            "delivered": False,            # ساختاری: این ماژول transport ندارد
            "lead_id": str(cand.get("lead_id") or "") or None,
            "candidate_type": ctype,
            "consent_basis": verdict.get("consent_basis"),
            "synthetic": (str((cand.get("source") or {}).get("channel") or "").strip()
                          == "synthetic_test"),
            "phone_present": bool(cfg["phone"]), "abn_present": bool(cfg["abn"]),
            "echo_used": use_echo, "warnings": warnings, "chars": len(body),
            "composed_at": _now_iso(now), "language": "en",
        }
    except Exception as e:  # noqa: BLE001 — fail-soft مطلق؛ هرگز مسیرِ لید را نمی‌کشد
        return _nothing("exception:" + type(e).__name__)


def _now_iso(now) -> str:
    try:
        if callable(now):
            return str(now())
        if now:
            return str(now)
        return opslib.now_iso()
    except Exception:  # noqa: BLE001
        return ""


if __name__ == "__main__":
    import json
    os.environ.setdefault(FLAG, "0")   # عمداً OFF: اجرای مستقیم چیزی تولید نمی‌کند
    print(json.dumps({"enabled": enabled(), "flag": FLAG,
                      "note": "produces text only; never sends, never writes"},
                     ensure_ascii=False))
