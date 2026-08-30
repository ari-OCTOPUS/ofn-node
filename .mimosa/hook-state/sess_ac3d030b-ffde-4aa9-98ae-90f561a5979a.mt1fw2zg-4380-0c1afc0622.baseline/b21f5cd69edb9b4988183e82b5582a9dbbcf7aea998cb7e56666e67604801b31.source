#!/usr/bin/env python3
"""test_lead_property_extract.py — «ماشین نمی‌داند دارد برای چه چیزی قیمت می‌دهد».

زخمِ گزارشِ ۲۰۲۶-۰۸-۰۱ (دلایلِ ۸ و ۱۰، یک زخم با دو صورت):
  · `lead_email_intake.to_candidate` همیشه `"property": {}` می‌نوشت ⇒ suburb/lat/lng
    هرگز وجود نداشت ⇒ +۸ امتیازِ جغرافیایی ساختاراً دست‌نیافتنی ⇒ repaint ِ مسکونی
    ۶۸ در برابرِ آستانهٔ ۷۰ ⇒ `save` ⇒ برای همیشه پارک.
  · هیچ فیلدی برای متراژ نبود ⇒ `lead_quote` همیشه `size_m2=0.0` ⇒ کوتِ A$0.00.

پوشش (همه آفلاین، stdlib-only، $0، **هرگز سوکتی باز نمی‌شود** — transport تزریقی):
  (الف) فلگ خاموش = بایت‌به‌بایتِ دیروز: تنها دو فیلدِ ممکنِ تفاوت (`property` و
        `request.urgency`) دقیقاً مقادیرِ تاریخیِ `{}` و `"unknown"` را دارند، و
        هیچ کلیدِ دیگری فرق نمی‌کند.
  (ب) **پذیرش روی مسیرِ تولیدی**: متنِ واقعیِ استعلام → `beat()` با fetch تزریقی و
        `submit_candidate` ِ **واقعی** → رکوردِ روی دیسک `property` ِ پرشده دارد.
  (پ) پرچمِ assumption وقتی متراژ **استنتاج** شده روشن است، و وقتی مشتری خودش عدد
        داده خاموش — با کلیدِ جداگانهٔ `floor_area_m2_stated`.
  (ت) استعلامِ غیرقابلِ‌تجزیه به **تهی** تنزل می‌کند، نه به عددِ غلط.
  (ث) صداقتِ پول: هیچ عددِ حدس‌زده‌ای هرگز زیرِ کلیدِ «اعلام‌شده» نمی‌نشیند، و هر
        عددِ حدس‌زده بازه + confidence + جملهٔ hedge دارد.
  (ج) **دندان**: بازسازیِ رفتارِ پیش-از-فیکس (و دو بدلِ ناصادق) و اثباتِ اینکه هر
        سه در برابرِ همین assertها **قرمز** می‌شوند.
  (چ) مثبتِ کاذبِ جغرافیایی: «budget around 2000»، تاریخِ «Aug 2026»، امضای
        «Sydney NSW 2000»، و «12 Epping Road, Macquarie Park» هیچ‌کدام مختصاتِ
        غلط نمی‌سازند.
  (ح) ارزشِ واقعیِ مختصات: همان lat/lng که این ماژول تولید می‌کند، امتیازِ ۶۸ را
        به ۷۶ (=draft) می‌برد — سنجیده روی خودِ `lead_scorer`.
  (خ) خلوص + AST: `extract_property` هیچ فایلی نمی‌سازد، و صداکنندهٔ تولیدیِ
        واقعی دارد (خارج از `_ops/tests`).

اجرا: python -X utf8 _ops/tests/test_lead_property_extract.py
"""
import ast
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKTREE = _HERE.parents[1]
os.environ.setdefault("REAL_VAULT", str(_WORKTREE))
sys.path.insert(0, str(_HERE))

import harness                                    # noqa: E402
ENV = harness.setup("lead-property-extract")

_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import importlib                                  # noqa: E402
import opslib                                     # noqa: E402
import consent_firewall                           # noqa: E402
importlib.reload(consent_firewall)
import lead_candidate_inbox as lci                # noqa: E402
importlib.reload(lci)
import lead_scorer                                # noqa: E402
importlib.reload(lead_scorer)
import lead_email_intake as lei                   # noqa: E402
importlib.reload(lei)

PFLAG = lei.PROPERTY_FLAG


# ── متنِ **واقعیِ** استعلام (شکلی که یک مشتریِ سیدنی واقعاً می‌نویسد) ──────────────
REAL_INQUIRY = (
    "Hi there,\n\n"
    "I'm after a quote to repaint the interior of my 3 bedroom house in "
    "Carlingford NSW 2118 — walls and ceilings throughout. We'd like to get "
    "it done as soon as possible.\n\n"
    "Thanks,\nSam"
)
REAL_INQUIRY_STATED_M2 = (
    "Hello, we need the exterior of our townhouse at 14 Windsor Road, "
    "Baulkham Hills NSW 2153 repainted. It's roughly 180 sqm. "
    "No rush on timing.\n"
)
UNPARSEABLE_INQUIRY = (
    "Hi, are you available to give me a painting quote? "
    "Let me know what you need from me. Cheers."
)
# استعلامِ **نیمه‌مشخص**: فقط یک واقعیت دارد (زمان‌بندی). باید دقیقاً همان را
# بدهد و نه یک ذره بیشتر — نه متراژ، نه مختصات.
PARTIAL_INQUIRY = "Hi, can I get a painting quote sometime? No rush at all."


def _msg(body: str, mid: str, subject: str = "Painting quote"):
    return {"message_id": mid, "from": "Sam Jones <sam.jones@resident.example>",
            "to": "info@business.example", "reply_to": "",
            "subject": subject, "date": "Sat, 01 Aug 2026 09:00:00 +1000",
            "body": body, "headers": {}}


def _cand(body: str, on: bool, channel: str = "other") -> dict:
    os.environ[PFLAG] = "1" if on else "0"
    try:
        return lei.to_candidate(_msg(body, "<m1@resident.example>"), channel, "k1")
    finally:
        os.environ[PFLAG] = "0"


def _flat(d, prefix=""):
    """dict تودرتو → {مسیرِ نقطه‌ای: مقدارِ json} — برای diff ِ دقیقِ کلید-به-کلید."""
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, key + "."))
        else:
            out[key] = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return out


def _red(fn, why: str) -> None:
    """دندان: `fn` **باید** شکست بخورد. سبزشدنش یعنی گارد کور است.

    KeyError/TypeError هم پذیرفته می‌شود چون بازسازیِ کدِ دیروز واقعاً کلید ندارد؛
    ولی assertهای بالا عمداً `.get` می‌زنند تا شکستِ **مورد انتظار** از خودِ گارد
    بیاید نه از تصادفِ دسترسی."""
    try:
        fn()
    except (AssertionError, KeyError, IndexError, TypeError, AttributeError):
        return
    raise AssertionError(f"گاردِ بی‌دندان — بدلِ ناصادق سبز شد: {why}")


def _files(root: Path) -> set:
    return {p for p in root.rglob("*") if p.is_file()}


# ── (الف) فلگ خاموش = بایت‌به‌بایتِ دیروز ────────────────────────────────────────
def t_a_flag_off_is_yesterday():
    for body in (REAL_INQUIRY, REAL_INQUIRY_STATED_M2, UNPARSEABLE_INQUIRY):
        off = _cand(body, on=False)
        on = _cand(body, on=True)
        # مقادیرِ تاریخی، عیناً
        assert off["property"] == {}, off["property"]
        assert off["request"]["urgency"] == "unknown", off["request"]
        # و **هیچ کلیدِ دیگری** با روشن‌شدنِ فلگ عوض نمی‌شود
        fo, fn = _flat(off), _flat(on)
        changed = {k for k in set(fo) | set(fn) if fo.get(k) != fn.get(k)}
        changed = {k for k in changed if not k.startswith("property")}
        assert changed <= {"request.urgency"}, f"نشتیِ فلگ به کلیدهای دیگر: {changed}"
        assert set(off.keys()) == set(on.keys()), (set(off) ^ set(on))
    assert lei.property_extract_on() is False, "پیش‌فرضِ فلگ باید خاموش باشد"


# ── (ب) پذیرش: متنِ واقعی از **مسیرِ تولیدی** تا رکوردِ روی دیسک ─────────────────
def _run_beat(bodies, *, extract_on: bool, consent: bool = False) -> tuple:
    """`beat()` با fetch تزریقی و `submit_candidate` ِ **واقعی** (بی‌تزریق).
    خروجی: (نتیجهٔ beat، لیستِ رکوردهای پایدارشده)."""
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    # ⛔ این تابع فایل **حذف** می‌کند. اگر harness روزی ایزوله نکند، همین خط
    # صندوقِ لیدِ زندهٔ یک کسب‌وکار را پاک می‌کرد. پس قبل از هر unlink ثابت کن
    # که مسیر داخلِ sandbox است — نه اینکه فرضش کن.
    sandbox = Path(ENV["root"]).resolve()
    resolved = box.resolve()
    assert sandbox in resolved.parents or resolved == sandbox, \
        f"⛔ STATE_DIR بیرونِ sandbox است ({resolved}) — حذف انجام نمی‌شود"
    assert _WORKTREE.resolve() not in resolved.parents, \
        f"⛔ STATE_DIR داخلِ درختِ زنده است ({resolved})"
    for sub in (box, box / "signals"):
        if sub.is_dir():
            for p in sub.glob("*.json"):
                p.unlink()
    seen = lei._seen_path()
    if seen.exists():
        seen.unlink()
    # ⚠️ لایهٔ دومِ dedup زیرِ `processed/` است، پس `box.glob("*.json")` آن را پاک
    # نمی‌کرد و اجرای دومِ همین تست «duplicate» می‌شد — یک no-op ِ بی‌صدا که
    # سبز به‌نظر می‌رسید. هر دو لایه باید پاک شوند.
    idem = lci._idem_index()
    if idem.exists():
        idem.unlink()
    env = {lei.FLAG: "1", lci.FLAG: "1", PFLAG: "1" if extract_on else "0",
           lei.INBOUND_CONSENT_FLAG: "1" if consent else "0"}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        msgs = [_msg(b, f"<beat-{i}@resident.example>") for i, b in enumerate(bodies)]
        res = lei.beat(fetch_fn=lambda **kw: list(msgs))
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    recs = []
    for p in sorted(box.glob("*.json")) + sorted((box / "signals").glob("*.json")):
        try:
            recs.append(json.loads(p.read_text("utf-8")))
        except (OSError, ValueError):
            pass
    return res, recs


def t_b_production_path_populates_property():
    res, recs = _run_beat([REAL_INQUIRY], extract_on=True)
    assert res["ok"] and res["fetched"] == 1 and res["inquiries"] == 1, res
    assert res["submitted"] + res["signals"] == 1, res
    assert recs, "هیچ رکوردی پایدار نشد — مسیرِ تولیدی به دیسک نرسید"
    prop = None
    for r in recs:
        prop = ((r.get("candidate") or {}).get("property")
                or (r.get("candidate") or {}).get("candidate", {}).get("property"))
        if prop is None and isinstance(r.get("candidate"), dict):
            prop = (r["candidate"].get("property")
                    or ((r.get("candidate") or {}).get("candidate") or {}).get("property"))
        if prop:
            break
    assert isinstance(prop, dict) and prop, f"property روی رکوردِ پایدار پر نشد: {recs}"
    assert prop.get("suburb") == "Carlingford", prop
    assert prop.get("postcode") == "2118", prop
    assert isinstance(prop.get("lat"), float) and isinstance(prop.get("lng"), float), prop
    assert prop.get("surfaces") == "interior" and prop.get("bedrooms") == 3, prop
    assert prop.get("timing") == "asap", prop
    assert prop.get("extracted_by"), "provenance غایب است"
    # نشانهٔ زمان باید تا `request.urgency` هم برسد — وگرنه فقط در `property`
    # می‌نشیند و هیچ مصرف‌کنندهٔ اولویت‌بندی آن را نمی‌بیند.
    req = None
    for r in recs:
        c = r.get("candidate")
        if isinstance(c, dict):
            req = (c.get("request")
                   or ((c.get("candidate") or {}).get("request") if
                       isinstance(c.get("candidate"), dict) else None))
        if req:
            break
    assert (req or {}).get("urgency") == "asap", f"urgency به رکورد نرسید: {req}"

    # و همان مسیر با فلگِ خاموش ⇒ رکورد هست ولی property تهی (رفتارِ دیروز).
    _res0, recs0 = _run_beat([REAL_INQUIRY], extract_on=False)
    blob0 = json.dumps(recs0, ensure_ascii=False)
    assert recs0 and '"property": {}' in blob0 or '"property":{}' in blob0, blob0[:400]
    assert "Carlingford" not in json.dumps(
        [(r.get("candidate") or {}).get("property") for r in recs0]), recs0


# ── (پ) پرچمِ assumption ────────────────────────────────────────────────────────
def t_c_assumption_flag_tracks_reality():
    # `.get` عمدی (نه `[]`): بازسازیِ پیش-از-فیکس باید AssertionError بدهد نه
    # KeyError — وگرنه «قرمز» بودنش تصادفی است، نه به‌خاطرِ خودِ گارد.
    inferred = lei.extract_property(REAL_INQUIRY)
    assert inferred.get("area_is_assumption") is True, inferred
    assert inferred.get("area_basis") == "assumed_from_bedrooms", inferred
    assert "floor_area_m2_stated" not in inferred, \
        "عددِ حدس‌زده زیرِ کلیدِ «اعلام‌شده» نشست — دقیقاً همان چیزی که ممنوع بود"
    assert 0.0 < float(inferred.get("area_confidence") or 0.0) < 1.0, inferred
    rng = inferred.get("floor_area_range_m2") or [0.0, 0.0]
    assert rng[0] < float(inferred.get("floor_area_m2") or 0.0) < rng[1], inferred

    stated = lei.extract_property(REAL_INQUIRY_STATED_M2)
    assert stated.get("area_is_assumption") is False, stated
    assert stated.get("area_basis") == "stated_m2", stated
    assert stated.get("floor_area_m2_stated") == 180.0, stated
    # سطحِ رنگ‌شونده **همیشه** مشتق است، حتی وقتی کف اعلام‌شده بود
    assert stated.get("paint_area_is_derived") is True, stated
    assert inferred.get("paint_area_is_derived") is True, inferred


# ── (ت) غیرقابلِ‌تجزیه ⇒ تهی، نه عددِ غلط ────────────────────────────────────────
def t_d_unparseable_degrades_to_empty():
    p = lei.extract_property(UNPARSEABLE_INQUIRY)
    assert p == {}, f"استعلامِ بی‌نشانه باید تهی بدهد، داد: {p}"
    for key in ("floor_area_m2", "floor_area_m2_stated", "paint_area_m2",
                "lat", "lng", "suburb", "postcode"):
        assert key not in p, key
    # نیمه‌مشخص: دقیقاً همان یک واقعیتِ موجود، نه یک ذره بیشتر
    q = lei.extract_property(PARTIAL_INQUIRY)
    assert q.get("timing") == "flexible", q
    for key in ("floor_area_m2", "floor_area_m2_stated", "paint_area_m2",
                "lat", "lng", "suburb", "postcode", "bedrooms", "room_count"):
        assert key not in q, f"از هیچ، «{key}» ساخته شد: {q}"
    # و از مسیرِ تولیدی هم همان: رکورد ساخته می‌شود ولی هیچ عددی جعل نمی‌شود
    _res, recs = _run_beat([UNPARSEABLE_INQUIRY], extract_on=True)
    blob = json.dumps(recs, ensure_ascii=False)
    assert recs, "لیدِ بی‌مشخصات نباید گم شود — فقط بی‌عدد بماند"
    for token in ("floor_area", "paint_area", '"lat"'):
        assert token not in blob, f"عددِ جعلی در رکوردِ استعلامِ بی‌نشانه: {token}"


# ── (ث) صداقتِ پول ──────────────────────────────────────────────────────────────
def t_e_no_guess_ever_reads_as_firm():
    cases = (REAL_INQUIRY, REAL_INQUIRY_STATED_M2, UNPARSEABLE_INQUIRY,
             "repaint five rooms in Epping, exterior",
             "interior repaint of my studio apartment in Ryde",
             "we need our 400 m2 warehouse in Seven Hills painted inside")
    for text in cases:
        p = lei.extract_property(text)
        if not p:
            continue
        # ── ناوردیِ **مستقل از پرچم** ─────────────────────────────────────────
        # اگر فقط `if p["area_is_assumption"]` را چک کنیم، بدلی که پرچم را
        # False می‌کند و حدس را داخلِ کلیدِ «اعلام‌شده» می‌گذارد از گارد رد
        # می‌شود — یعنی گارد دقیقاً همان دروغی را که وظیفه‌اش گرفتنِ آن است
        # نمی‌بیند. پس شاهد را از **متنِ خودِ مشتری** می‌گیریم، نه از رکورد:
        # متنی که هیچ توکنِ متراژ ندارد، اجازه ندارد عددِ «اعلام‌شده» بسازد.
        said_m2 = bool(re.search(r"\d\s*(?:m2|m²|sqm|sq\.?\s?m|square\s+met)",
                                 text, re.I))
        if not said_m2:
            assert "floor_area_m2_stated" not in p, \
                f"متن هیچ متراژی نگفته ولی عددِ «اعلام‌شده» ساخته شد: {text!r} → {p}"
            if "floor_area_m2" in p:
                assert p.get("area_is_assumption") is True, \
                    f"عددِ بی‌منبع به‌عنوانِ قطعی علامت خورد: {text!r} → {p}"
        if p.get("area_is_assumption"):
            assert "floor_area_m2_stated" not in p, (text, p)
            # هر حدس باید بازه + confidence + جملهٔ hedge داشته باشد
            assert isinstance(p.get("floor_area_range_m2"), list), (text, p)
            notes = [a for a in p.get("assumptions", [])
                     if a.get("field") == "floor_area_m2"]
            assert notes and notes[0]["note"], (text, p)
            assert 0.0 < notes[0]["confidence"] < 1.0, (text, p)
        if "paint_area_m2" in p:
            assert p.get("paint_area_is_derived") is True, (text, p)
            pl, ph = p["paint_area_range_m2"]
            assert pl <= p["paint_area_m2"] <= ph and pl > 0, (text, p)
            assert any(a.get("field") == "paint_area_m2" and a.get("note")
                       for a in p.get("assumptions", [])), (text, p)
        # هرگز عددِ صفر/منفی به‌عنوانِ متراژ
        for k in ("floor_area_m2", "floor_area_m2_stated", "paint_area_m2"):
            if k in p and p[k] is not None:
                assert float(p[k]) > 0.0, (text, k, p[k])
    # انبار/strata: عمداً هیچ سطحِ رنگ‌شونده‌ای ساخته نمی‌شود (نسبتش پایدار نیست)
    wh = lei.extract_property("interior repaint of our 400 m2 warehouse in Seven Hills")
    assert wh["property_type"] == "commercial", wh
    assert "paint_area_m2" not in wh, "برای انبار عددِ سطح جعل شد"
    assert wh.get("paint_area_unavailable_reason"), wh


# ── (ج) دندان: بازسازیِ پیش-از-فیکس و دو بدلِ ناصادق ────────────────────────────
def t_f_teeth_pre_fix_and_dishonest_fakes():
    real = lei.extract_property

    # ۱ رفتارِ **دقیقِ** پیش-از-فیکس: `to_candidate` همیشه `"property": {}`.
    _red(lambda: _with(lambda _t: {}, t_c_assumption_flag_tracks_reality),
         "کدِ دیروز (property همیشه تهی) — گاردِ assumption")
    _red(lambda: _with(lambda _t: {}, t_b_production_path_populates_property),
         "کدِ دیروز روی مسیرِ تولیدی")

    # ۲ بدلِ ناصادق: متراژِ پیش‌فرض برای استعلامِ بی‌نشانه (همان خطای پولی).
    _red(lambda: _with(lambda t: ({"floor_area_m2_stated": 120.0,
                                   "floor_area_m2": 120.0,
                                   "area_is_assumption": False}
                                  if "quote sometime" in t else real(t)),
                       t_d_unparseable_degrades_to_empty),
         "متراژِ پیش‌فرضِ ۱۲۰ برای استعلامِ بی‌نشانه")

    # ۳ بدلِ ناصادق: حدس زیرِ کلیدِ «اعلام‌شده» با پرچمِ خاموش.
    def _liar(t):
        p = dict(real(t))
        if p.get("area_is_assumption"):
            p["area_is_assumption"] = False
            p["area_basis"] = "stated_m2"
            p["floor_area_m2_stated"] = p.get("floor_area_m2")
        return p
    _red(lambda: _with(_liar, t_c_assumption_flag_tracks_reality),
         "حدس به‌عنوانِ عددِ اعلام‌شدهٔ مشتری")
    _red(lambda: _with(_liar, t_e_no_guess_ever_reads_as_firm),
         "حدس به‌عنوانِ عددِ اعلام‌شده (گاردِ صداقتِ پول)")

    assert lei.extract_property is real, "بازگردانیِ تابعِ واقعی انجام نشد"


def _with(fake, fn):
    """`fn` را با `extract_property` ِ جعلی اجرا کن، بعد اصل را برگردان."""
    real = lei.extract_property
    lei.extract_property = fake
    try:
        fn()
    finally:
        lei.extract_property = real


# ── (چ) مثبتِ کاذبِ جغرافیایی ───────────────────────────────────────────────────
def t_g_no_false_geography():
    no_geo = (
        ("Hi, looking to repaint. Budget around 2000 dollars.", "عددِ بودجه"),
        ("Sent Fri 01 Aug 2026. Can you paint my place?", "تاریخ"),
        ("Please quote a repaint.\n--\nJane\nSydney NSW 2000", "امضای سیدنی"),
    )
    for text, why in no_geo:
        p = lei.extract_property(text)
        assert "lat" not in p and "lng" not in p, f"مختصاتِ کاذب از {why}: {p}"
    # نامِ خیابان ≠ نامِ حومه. حالتِ **بدونِ کدپستی** عمداً هست: با کدپستی، لنگرِ
    # هم‌جواری خودش کار را درست می‌کند و جهشِ «حذفِ جریمهٔ نامِ خیابان» زنده می‌ماند
    # — یعنی این فیکسچرِ تنها یک گاردِ کور می‌ساخت.
    for text, want in (
            ("We're at 12 Epping Road, Macquarie Park NSW 2113. Exterior repaint.",
             "Macquarie Park"),
            ("We're at 12 Epping Road, Macquarie Park. Exterior repaint please.",
             "Macquarie Park"),
            ("Repaint at 5 Castle Hill Road, Cherrybrook. Interior.", "Cherrybrook")):
        p = lei.extract_property(text)
        assert p.get("suburb") == want, f"نامِ خیابان حومه شد: {text!r} → {p}"
        assert isinstance(p.get("lat"), float), p
    # واژه‌های تله: زیررشتهٔ خام این‌ها را غلط طبقه‌بندی می‌کرد
    assert "property_type" not in lei.extract_property(
        "Repaint of a community facility hall, interior."), "«unit» داخلِ «community»"
    assert "address" not in lei.extract_property(
        "Quote for a 3 bed terrace repaint please."), "«3 bed terrace» نشانی شد"
    assert "floor_area_m2_stated" not in lei.extract_property(
        "Do you charge $45 sqm? Interior repaint."), "نرخِ هر متر متراژ شد"


# ── (ح) ارزشِ واقعیِ مختصات — سنجیده روی خودِ scorer ─────────────────────────────
def t_h_coordinates_are_worth_the_eight_points():
    old = os.environ.get("OCTOPUS_LEAD_DIRECT_RESIDENTIAL")
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    try:
        p = lei.extract_property(REAL_INQUIRY)
        base = {"description": "quote to repaint the interior of my 3 bedroom house",
                "address": p["address"]}
        without = lead_scorer.score_lead(dict(base))
        with_geo = lead_scorer.score_lead({**base, "lat": p["lat"], "lng": p["lng"]})
        assert without.action == "save" and without.score == 68, without.as_dict()
        assert with_geo.score == without.score + 8, (without.score, with_geo.score)
        assert with_geo.action == "draft", with_geo.as_dict()
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_LEAD_DIRECT_RESIDENTIAL", None)
        else:
            os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = old
    # و آنچه امروز واقعاً به scorer می‌رسد را **می‌سنجیم** (نه فرض):
    # `lead_candidate_inbox._to_lead_sense_file` فقط address/suburb را عبور می‌دهد.
    cand = _cand(REAL_INQUIRY, on=True)
    verdict = {"candidate_type": "consented_inbound", "consent_basis": "explicit",
               "outreach_allowed": True, "retention_class": "standard",
               "compliance_reason": "x"}
    sense = lci._to_lead_sense_file("LID", cand, verdict)
    assert sense["suburb"] == "Carlingford" and sense["address"], sense
    print(f"     ↳ عبورِ پایین‌دست: lat در فایلِ sense = {'lat' in sense} "
          f"(اگر False، آن +۸ هنوز به scorer نمی‌رسد — یک خط در "
          f"lead_candidate_inbox._to_lead_sense_file)")


# ── (خ) خلوص + صداکنندهٔ تولیدی (AST) ───────────────────────────────────────────
def t_i_purity_and_ast_callers():
    root = Path(ENV["root"])
    before = _files(root)
    for text in (REAL_INQUIRY, REAL_INQUIRY_STATED_M2, UNPARSEABLE_INQUIRY, "", "x" * 9000):
        lei.extract_property(text)
    assert _files(root) == before, "تابعِ «خالص» فایل ساخت/عوض کرد"
    # قطعی و مستقل از env
    a = lei.extract_property(REAL_INQUIRY)
    os.environ["OCTOPUS_LEAD_PROPERTY_EXTRACT"] = "1"
    b = lei.extract_property(REAL_INQUIRY)
    os.environ["OCTOPUS_LEAD_PROPERTY_EXTRACT"] = "0"
    assert a == b, "خروجی به env وابسته شد — تابع دیگر خالص نیست"

    src = (_OPS / "legs" / "lead_email_intake.py").read_text("utf-8")
    tree = ast.parse(src)
    # `to_candidate` باید هم فلگ را بپرسد هم استخراج‌گر را صدا بزند
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "to_candidate")
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert {"extract_property", "property_extract_on"} <= called, called
    # و هیچ‌کدام یتیم نیستند: شمارشِ صداکننده در کدِ **تولیدی** (بیرونِ _ops/tests)
    n_calls = 0
    for p in (_OPS / "legs").glob("lead_*.py"):
        for n in ast.walk(ast.parse(p.read_text("utf-8"))):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id in ("extract_property", "property_extract_on"):
                n_calls += 1
    assert n_calls >= 2, f"صداکنندهٔ تولیدی کم است ({n_calls}) — ماژولِ یتیم"
    # هیچ سطحِ شبکه/ارسالی اضافه نشده
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top.add(node.module.split(".")[0])
    assert not (top & {"smtplib", "socket", "urllib", "http", "requests"}), top
    # جدولِ جغرافیا سالم است
    assert len(lei._SUBURBS) >= 40, len(lei._SUBURBS)
    assert "sydney" not in lei._SUBURBS, "«Sydney» در جدول = +۸ کاذب از هر امضا"
    for name, (pc, lat, lng) in lei._SUBURBS.items():
        assert pc.isdigit() and len(pc) == 4 and "2000" <= pc <= "2999", (name, pc)
        assert -34.5 < lat < -33.0 and 150.0 < lng < 152.0, (name, lat, lng)


CHECKS = [
    ("الف — فلگ خاموش = بایت‌به‌بایتِ دیروز", t_a_flag_off_is_yesterday),
    ("ب — مسیرِ تولیدی: property روی دیسک پر شد", t_b_production_path_populates_property),
    ("پ — پرچمِ assumption با واقعیت می‌خواند", t_c_assumption_flag_tracks_reality),
    ("ت — استعلامِ بی‌نشانه ⇒ تهی، نه عددِ غلط", t_d_unparseable_degrades_to_empty),
    ("ث — صداقتِ پول: حدس هرگز قطعی نمی‌شود", t_e_no_guess_ever_reads_as_firm),
    ("ج — دندان: پیش-از-فیکس و دو بدلِ ناصادق قرمز", t_f_teeth_pre_fix_and_dishonest_fakes),
    ("چ — صفر مختصاتِ کاذب", t_g_no_false_geography),
    ("ح — همان مختصات ۶۸ را ۷۶ می‌کند", t_h_coordinates_are_worth_the_eight_points),
    ("خ — خلوص + صداکنندهٔ تولیدی (AST)", t_i_purity_and_ast_callers),
]

if __name__ == "__main__":
    print("=== test_lead_property_extract ===")
    failed = harness.run(CHECKS)
    print(f"\n{'❌' if failed else '✅'} {len(CHECKS) - failed}/{len(CHECKS)} سبز")
    sys.exit(1 if failed else 0)
