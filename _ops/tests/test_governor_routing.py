#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_governor_routing.py — دو قاعده‌ای که اگر بشکنند یا **نشت** می‌کنند یا **پول** می‌سوزانند.

`_ops/budget/governor.py` یک آداپتور روی `model_router.ask()` است. تمامِ ارزشش در
دو جملهٔ منفی است، و این فایل فقط همان دو را می‌سنجد (بقیه سیاههٔ پشتیبان است):

  ۱. تماسِ secret-دار **هرگز** به ردهٔ راه‌دور نمی‌رسد.
  ۲. `allow_ultra=False` **هرگز** گران‌ترین رده را درخواست نمی‌کند.

چرا این فایل به جای «یک نمونه از هر قاعده»، ماتریسِ کامل می‌دود: قاعدهٔ secret
نقطهٔ اجرایش یک `if` است ولی سطحِ حمله‌اش کلِ فضای قرارداد است. یک تستِ تک‌نمونه
با `purpose="summary"` سبز می‌ماند در حالی که `purpose="deep_audit"` نشت می‌کند.

⚠️ نکتهٔ سنجش (درسِ «جهشِ سبز = خطِ نادیده»): قاعدهٔ secret **دو** قفلِ مستقل دارد
(`decide` و `delivery_allowed`). اگر هر دو را فقط از سرِ `ask()` بسنجیم، جهش روی
هرکدام را آن‌یکی می‌پوشاند و هر دو «SURVIVED» گزارش می‌شوند — یعنی هیچ‌کدام
سنجیده نشده. پس این‌جا هر قفل **جداگانه** و مستقیم سنجیده می‌شود.

صفر شبکه. صفر نوشتن روی درختِ زنده (harness اول از همه). صفر تماسِ مدلِ واقعی.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402

ENV = harness.setup("governor-routing")   # قبل از هر importی که state می‌نویسد

import governor as gv  # noqa: E402


# ── ابزارِ تست: مسیریابِ قلابیِ ضبط‌کننده ────────────────────────────────────
class FakeRouter:
    """امضای دقیقِ `model_router` که حاکم لمسش می‌کند — و هیچ کارِ دیگری."""

    TASK_TIERS = {"summarize": "local", "research": "secondary", "deep": "primary"}

    def __init__(self, scored=None, reply=None):
        self.calls = []
        self._scored = scored
        self._reply = reply if reply is not None else {"ok": True, "tier": "local",
                                                       "text": "پاسخ"}

    def _scored_tier(self, task):
        return self._scored

    def ask(self, task, prompt, system="", max_tokens=400,
            tier=None, opener=None, quality=None):
        self.calls.append({"task": task, "prompt": prompt, "system": system,
                           "max_tokens": max_tokens, "tier": tier,
                           "opener": opener, "quality": quality})
        return self._reply


ALL_PURPOSES = gv.PURPOSES
ALL_IMPORTANCES = gv.IMPORTANCES
ALL_RISKS = gv.RISKS
ALL_BASELINES = (gv.LOCAL_TIER, gv.MID_TIER, gv.ULTRA_TIER)


def _matrix(**over):
    """همهٔ ترکیب‌های purpose × importance × risk × allow_ultra × baseline."""
    for p in ALL_PURPOSES:
        for imp in ALL_IMPORTANCES:
            for rk in ALL_RISKS:
                for au in (True, False):
                    for base in ALL_BASELINES:
                        c = {"purpose": p, "importance": imp, "risk": rk,
                             "allow_ultra": au, "brain": "critic",
                             "expected_artifact": "x"}
                        c.update(over)
                        yield c, base


def setup_function(_=None):
    gv.cache_clear()


# ══ ۱) قاعدهٔ secret — نشت ═══════════════════════════════════════════════════

def t_a_secret_locks_every_contract_to_local():
    """قفلِ اول، روی **کلِ** فضای قرارداد نه یک نمونه.

    ۷۲۰ ترکیب: هیچ‌کدام حق ندارد چیزی جز `local` بدهد. `deep_audit` با
    `allow_ultra=True` و `importance=critical` و `baseline=primary` — یعنی
    گران‌ترین مسیرِ ممکن — هم باید به محلی قفل شود."""
    gv.cache_clear()
    n = 0
    for c, base in _matrix(contains_secrets=True):
        d = gv.decide(c, baseline=base)
        assert d["tier"] == gv.LOCAL_TIER, f"نشت: {c} baseline={base} → {d['tier']}"
        assert d["tier"] not in gv.REMOTE_TIERS, d
        assert d["redact"] is True, d
        n += 1
    # ۶ purpose × ۴ importance × ۳ risk × ۲ allow_ultra × ۳ baseline = ۴۳۲
    assert n == 432, f"ماتریس باید کامل باشد، نه یک نمونه: {n}"


def t_b_an_ambiguous_secret_flag_fails_towards_local():
    """`contains_secrets` مبهم = «بله دارد»، نه «نه ندارد».

    شکلِ کاملاً محتملِ صداکننده: فهرستِ **نامِ** متغیرها (نه مقدارشان).
    با `bool()`-ِ رشته‌ایِ ساده این می‌شد `"['FUGU_API_KEY']"` که در فهرستِ
    truthy نیست ⇒ False ⇒ همان تماس اجازهٔ ردهٔ راه‌دور می‌گرفت. برای پرچمی که
    کارش جلوگیری از نشت است، جهتِ خطا باید به سمتِ بسته باشد."""
    for val in (["FUGU_API_KEY"], "yes", "maybe", 1, {"k": "v"}, "TRUE"):
        d = gv.decide({"purpose": "deep_audit", "allow_ultra": True,
                       "contains_secrets": val}, baseline=gv.ULTRA_TIER)
        assert d["tier"] == gv.LOCAL_TIER, f"{val!r} → {d['tier']} (باید local باشد)"
    for val in (False, None, "", "0", "false", "no", "off"):
        d = gv.decide({"purpose": "deep_audit", "allow_ultra": True,
                       "contains_secrets": val}, baseline=gv.ULTRA_TIER)
        assert d["tier"] == gv.ULTRA_TIER, f"{val!r} نباید secret شمرده شود"


def t_c_the_delivery_guard_is_a_second_independent_lock():
    """قفلِ دوم، مستقیم — نه از پشتِ قفلِ اول.

    اگر این فقط از سرِ `ask()` سنجیده شود، `decide` هرگز نمی‌گذارد یک تصمیمِ
    secret-دارِ راه‌دور به این‌جا برسد، پس جهشِ روی این تابع زنده می‌ماند و ما
    خیال می‌کنیم گارد داریم."""
    for t in gv.REMOTE_TIERS:
        ok, why = gv.delivery_allowed({"contains_secrets": True, "tier": t})
        assert ok is False, f"tier={t} با secret باید رد شود"
        assert "secret" in why, why
    ok, _ = gv.delivery_allowed({"contains_secrets": True, "tier": gv.LOCAL_TIER})
    assert ok is True, "محلی + secret مجاز است — این‌که نکتهٔ ماجراست"
    ok, _ = gv.delivery_allowed({"contains_secrets": False, "tier": gv.ULTRA_TIER})
    assert ok is True, "بدونِ secret، ردهٔ راه‌دور مسئلهٔ این گارد نیست"


def t_d_a_secret_call_reaches_the_router_only_as_local():
    """سرتاسری: از `ask()` تا آرگومانی که واقعاً به مسیریاب می‌رسد."""
    import os
    os.environ[gv.FLAG] = "1"
    try:
        r = FakeRouter()
        out = gv.ask("deep", "متن", contract={
            "purpose": "deep_audit", "allow_ultra": True, "importance": "critical",
            "contains_secrets": True}, _router_mod=r)
        assert len(r.calls) == 1, r.calls
        assert r.calls[0]["tier"] == gv.LOCAL_TIER, r.calls[0]
        assert out.get("ok") is True
    finally:
        os.environ.pop(gv.FLAG, None)


def t_e_local_is_structurally_egress_free():
    """چرا «قفلِ محلی» یعنی «صفر egress» و نه یک آرزو.

    اندازه‌گیریِ زندهٔ `_ask_impl` (تستِ p پایین روی کدِ **واقعی** تکرارش می‌کند):
    با `tier="local"` شاخهٔ ردهٔ پولی اصلاً اجرا نمی‌شود، پس `_ask_paid` هرگز صدا
    نمی‌خورد. `paid_order` همان قاعده را ماشین‌خوان می‌کند."""
    assert gv.paid_order(gv.LOCAL_TIER) == [], gv.paid_order(gv.LOCAL_TIER)
    assert gv.paid_order(gv.MID_TIER) == [gv.MID_TIER, gv.ULTRA_TIER]
    assert gv.paid_order(gv.ULTRA_TIER) == [gv.ULTRA_TIER, gv.MID_TIER]


# ══ ۲) قاعدهٔ ultra — پول ════════════════════════════════════════════════════

def t_f_allow_ultra_false_never_requests_the_expensive_tier():
    """کلِ فضای قرارداد با `allow_ultra=False`: هیچ‌کدام حق ندارد primary بخواهد."""
    seen = set()
    for c, base in _matrix(allow_ultra=False):
        d = gv.decide(c, baseline=base)
        assert d["tier"] != gv.ULTRA_TIER, f"خرجِ ناخواسته: {c} baseline={base}"
        seen.add((c["purpose"], c["importance"], c["risk"], base))
    assert len(seen) == 216, f"ترکیبِ یکتا: {len(seen)}"   # ۶×۴×۳×۳


def t_g_deep_audit_reaches_ultra_only_with_explicit_permission():
    """و برعکسش هم باید درست باشد، وگرنه گارد فقط «همیشه نه» است.

    (درسِ «گاردِ بی‌دندان»: گاردی که هیچ‌وقت اجازه نمی‌دهد، گارد نیست — کلید
    نداشتن است. هر دو جهت باید سنجیده شود.)"""
    yes = gv.decide({"purpose": "deep_audit", "allow_ultra": True,
                     "importance": "critical"}, baseline=gv.ULTRA_TIER)
    assert yes["tier"] == gv.ULTRA_TIER, yes
    no = gv.decide({"purpose": "deep_audit", "allow_ultra": False,
                    "importance": "critical"}, baseline=gv.ULTRA_TIER)
    assert no["tier"] == gv.MID_TIER, no

    # `allow_ultra`ِ مبهم = «نه» — دقیقاً **برعکسِ** `contains_secrets`. جهتِ
    # درستِ خطا برای یک پرچمِ خرج این است: ندانستن یعنی خرج نکن.
    for val in ("maybe", ["yes"], {"a": 1}, 0.5, "hmm"):
        d = gv.decide({"purpose": "deep_audit", "importance": "critical",
                       "allow_ultra": val}, baseline=gv.ULTRA_TIER)
        assert d["tier"] != gv.ULTRA_TIER, f"allow_ultra={val!r} نباید خرج باز کند"

    # و اهمیتِ پایین حتی با اجازهٔ صریح خرج نمی‌تراشد (فقط نزول، هرگز صعود).
    low = gv.decide({"purpose": "deep_audit", "allow_ultra": True,
                     "importance": "low"}, baseline=gv.ULTRA_TIER)
    assert low["tier"] == gv.LOCAL_TIER, low


def t_h_the_governor_never_enlarges_what_the_router_may_try():
    """«این لایه هم‌قدر یا کمتر خرج می‌کند، هرگز بیشتر» — ماشین‌خوان.

    دو سنجه، چون یکی‌شان به‌تنهایی دروغ می‌گوید:
      · ردهٔ **درخواستی** هرگز از ردهٔ امروزِ همان task بالاتر نیست.
      · **مجموعهٔ** ردهٔ قابلِ‌تلاش بزرگ‌تر نمی‌شود. (مسیریاب یک fallbackِ
        key-aware از قدیم دارد؛ حاکم فقط ترتیب را ارزان-اول می‌کند.)"""
    r = FakeRouter()
    for task, today in r.TASK_TIERS.items():
        for c, _ in _matrix():
            d = gv.decide(c, baseline=gv.router_want(task, None, router_mod=r))
            assert gv.TIER_RANK[d["tier"]] <= gv.TIER_RANK[today], \
                f"task={task} امروز={today} حاکم={d['tier']} · {c}"
            assert set(gv.paid_order(d["tier"])) <= set(gv.paid_order(today)), \
                f"مجموعهٔ ردهٔ قابلِ‌تلاش بزرگ شد: {task} {d['tier']} vs {today}"


def t_i_the_ceiling_follows_the_router_not_a_stale_copy():
    """سقف باید همان چیزی باشد که مسیریاب **امروز** حساب می‌کند.

    باگی که این قفل می‌کند: نسخهٔ اول فقط `TASK_TIERS` را می‌خواند و شاخهٔ
    `CORTEX_ROUTE_SCORER` را نمی‌دید. آن پرچم روشن ⇒ `route_scorer` می‌تواند
    ردهٔ پایین‌تری بدهد ⇒ سقفِ کپی‌شده از خرجِ واقعی **بالاتر** می‌شد و حاکم
    اجازه می‌داد بیشتر خرج شود. دقیقاً کاری که این لایه نباید بکند."""
    import os
    r = FakeRouter(scored=gv.LOCAL_TIER)          # مشاور می‌گوید محلی…
    assert r.TASK_TIERS["deep"] == gv.ULTRA_TIER  # …ولی نگاشتِ ایستا می‌گوید primary
    os.environ.pop("CORTEX_ROUTE_SCORER", None)
    assert gv.router_want("deep", None, router_mod=r) == gv.ULTRA_TIER
    os.environ["CORTEX_ROUTE_SCORER"] = "1"
    try:
        assert gv.router_want("deep", None, router_mod=r) == gv.LOCAL_TIER, \
            "با پرچمِ روشن، سقف باید نظرِ مشاور باشد نه نگاشتِ ایستا"
    finally:
        os.environ.pop("CORTEX_ROUTE_SCORER", None)
    assert gv.router_want("deep", gv.MID_TIER, router_mod=r) == gv.MID_TIER, \
        "tierِ صریحِ صداکننده خودش سقف است"

    # tierِ صریحِ **ناشناخته**: مسیریاب آن را مثلِ محلی رفتار می‌کند و صفر ردهٔ
    # پولی لمس می‌کند (تستِ p همین را روی کدِ واقعی می‌سنجد). پس سقف هم باید
    # محلی باشد. اگر به‌جایش از `TASK_TIERS` بیاید، سقف از خرجِ **امروز** بالاتر
    # می‌رود و حاکم اجازه می‌دهد بیشتر خرج شود. `tier="think"` در همین درخت
    # به‌عنوان آرگومانِ پیش‌فرض وجود دارد — این یک حالتِ فرضی نیست.
    for unknown in ("think", "premium", "econ", "reason"):
        assert gv.router_want("deep", unknown, router_mod=r) == gv.LOCAL_TIER, \
            f"tier={unknown!r} امروز صفر خرجِ پولی دارد؛ سقف نباید بالاتر برود"
    assert gv.router_want("deep", "", router_mod=r) == gv.ULTRA_TIER, \
        "tierِ falsy را مسیریاب «نداده» می‌شمارد — سقف باید محاسبه شود"

    # مسیریابِ غایب/خراب = سخت‌گیرانه‌ترین سقف، نه بازترین.
    class NoRouter:
        pass

    assert gv.router_want("deep", None, router_mod=NoRouter()) == gv.LOCAL_TIER, \
        "ندانستنِ سقف باید پایین‌ترین سقف باشد، نه بالاترین"


# ══ ۳) بقیهٔ قواعدِ مسیریابی ════════════════════════════════════════════════

def t_j_purpose_routes_to_the_tier_the_owner_asked_for():
    base = gv.ULTRA_TIER
    assert gv.decide({"purpose": "search"}, baseline=base)["tier"] == gv.LOCAL_TIER
    for p in ("summary", "classification", "code_review"):
        assert gv.decide({"purpose": p}, baseline=base)["tier"] == gv.MID_TIER, p
    sec = gv.decide({"purpose": "security"}, baseline=base)
    assert sec["tier"] == gv.LOCAL_TIER and sec["redact"] is True, sec
    assert "cyber" not in gv.TIER_RANK, "ردهٔ cyber در این درخت وجود ندارد"
    unknown = gv.decide({"purpose": "چیزِ ناشناخته"}, baseline=base)
    assert unknown["tier"] == gv.LOCAL_TIER, "ناشناخته = ارزان‌ترین، نه گران‌ترین"
    # قراردادِ غایب/آشغال هم همان‌طور: هرگز به گران‌ترین پیش‌فرض نمی‌افتد.
    for bad in (None, "یک رشته", 42, [1, 2]):
        d = gv.decide(bad, baseline=base)
        assert d["tier"] == gv.LOCAL_TIER, f"قراردادِ {bad!r} → {d['tier']}"


def t_k_a_cache_hit_makes_zero_model_calls():
    import os
    os.environ[gv.FLAG] = "1"
    gv.cache_clear()
    try:
        r = FakeRouter(reply={"ok": True, "tier": "secondary", "text": "تازه"})
        c = {"purpose": "summary", "cache_key": "k-۱", "importance": "high"}
        gv.ask("research", "س", contract=c, _router_mod=r)
        assert len(r.calls) == 1, "بارِ اول باید واقعاً بپرسد"
        out = gv.ask("research", "س", contract=c, _router_mod=r)
        assert len(r.calls) == 1, f"cache hit نباید هیچ تماسی بزند: {r.calls}"
        assert out.get("cached") is True and out.get("text") == "تازه", out
        assert out.get("tier") == "secondary", "ردهٔ کش‌شده باید صادقانه برگردد"
    finally:
        gv.cache_clear()
        os.environ.pop(gv.FLAG, None)


def t_l_a_secret_answer_is_never_cached():
    import os
    os.environ[gv.FLAG] = "1"
    gv.cache_clear()
    try:
        r = FakeRouter(reply={"ok": True, "tier": "local", "text": "محرمانه"})
        c = {"purpose": "security", "cache_key": "k-secret",
             "contains_secrets": True}
        gv.ask("triage", "س", contract=c, _router_mod=r)
        assert gv.cache_get("k-secret") is None, "پاسخِ secret-دار نباید کش شود"
    finally:
        gv.cache_clear()
        os.environ.pop(gv.FLAG, None)


def t_m_is_write_reaches_the_real_gate_and_the_governor_never_grants():
    """`is_write` باید به گیتِ **واقعی** برسد، نه به نامِ گیت.

    نسخهٔ اول فقط رشتهٔ `"capability_gate.require"` را در تصمیم می‌گذاشت و هیچ
    گیتی صدا نمی‌خورد — برچسب، نه سیم."""
    import os
    seen = []

    class FakeGate:
        def require(self, action_id, amount_aud, channel=None):
            seen.append((action_id, amount_aud))
            return {"allow": True, "reason": "fake-open"}

    d = gv.decide({"purpose": "code_review", "is_write": True,
                   "task_id": "T-42"}, baseline=gv.ULTRA_TIER)
    assert d["route"] == "approval_gate" and d["tier"] is None, d
    assert d["granted"] is False, "حاکم به خودش مجوز نمی‌دهد"

    res = gv.write_gate(d, gate_mod=FakeGate())
    assert seen and seen[0][1] == 0.0, f"گیت واقعاً صدا نخورد: {seen}"
    assert "T-42" in seen[0][0], seen
    assert res["allow"] is True, res

    os.environ[gv.FLAG] = "1"
    try:
        r = FakeRouter()
        out = gv.ask("plan", "س", contract={"purpose": "code_review",
                                            "is_write": True}, _router_mod=r)
        assert r.calls == [], "مسیرِ نوشتن نباید به مدل برسد"
        assert out["ok"] is False and out["reason"] == "owner-approval-required", out
        assert out["gate"] == gv.WRITE_GATE, out
    finally:
        os.environ.pop(gv.FLAG, None)


def t_n_the_write_gate_fails_closed_when_it_is_unavailable():
    class Broken:
        def require(self, *a, **k):
            raise RuntimeError("گیت در دسترس نیست")

    class Weird:
        def require(self, *a, **k):
            return "yes"

    for mod in (Broken(), Weird()):
        res = gv.write_gate({"task_id": "T"}, gate_mod=mod)
        assert res["allow"] is False, f"ندانستن باید «رد» باشد: {res}"


# ══ ۴) فلگِ خاموش = رفتارِ امروز، بایت‌به‌بایت ══════════════════════════════

def t_o_flag_off_is_a_byte_identical_passthrough():
    """با فلگِ خاموش: همان آرگومان‌ها، **همان شیءِ** خروجی، صفر تصمیم، صفر ثبت.

    «صفر تصمیم» با ترکاندنِ `decide`/`record` سنجیده می‌شود، نه با اعتماد."""
    import os
    os.environ.pop(gv.FLAG, None)
    sentinel = {"ok": True, "tier": "primary", "text": "امروز"}
    r = FakeRouter(reply=sentinel)
    _decide, _record = gv.decide, gv.record

    def boom(*a, **k):
        raise AssertionError("با فلگِ خاموش نباید صدا زده شود")

    gv.decide, gv.record = boom, boom
    try:
        marker = object()
        out = gv.ask("research", "پرسش", "سیستم", 123, tier="primary",
                     opener=marker, quality=None,
                     contract={"purpose": "deep_audit", "allow_ultra": True},
                     _router_mod=r)
        assert out is sentinel, "خروجی باید **همان شیء** باشد، نه یک کپی"
        assert r.calls == [{"task": "research", "prompt": "پرسش",
                            "system": "سیستم", "max_tokens": 123,
                            "tier": "primary", "opener": marker,
                            "quality": None}], r.calls
    finally:
        gv.decide, gv.record = _decide, _record


def t_o2_an_escalation_by_the_routers_own_fallback_is_recorded():
    """اگر fallbackِ از پیش موجودِ مسیریاب از ردهٔ درخواستی بالاتر رفت، باید **دیده** شود.

    این تنها جای صادقانه‌ای است که حاکم می‌تواند دربارهٔ گاردِ ultra حرف بزند:
    جلوگیری از پسِ `ask()` ممکن نیست (پول خرج شده)، ولی سکوت یعنی مالک هرگز
    نفهمد `allow_ultra=false` در عمل چقدر نگه داشته. «ثبت همیشه»."""
    import os
    os.environ[gv.FLAG] = "1"
    seen = []
    _record = gv.record
    gv.record = lambda d, event="decision": seen.append((event, d.get("escalated")))
    try:
        # حاکم secondary می‌خواهد؛ مسیریاب با fallbackِ خودش primary برمی‌گرداند.
        r = FakeRouter(reply={"ok": True, "tier": "primary", "text": "ت"})
        gv.ask("research", "س", contract={"purpose": "summary",
                                          "allow_ultra": False}, _router_mod=r)
        assert r.calls[0]["tier"] == gv.MID_TIER, r.calls[0]
        assert ("escalated", True) in seen, f"صعودِ رده ثبت نشد: {seen}"

        # و وقتی صعودی نبوده، نباید ردِ دروغین بسازد.
        seen.clear()
        r2 = FakeRouter(reply={"ok": True, "tier": "secondary", "text": "ت"})
        gv.ask("research", "س", contract={"purpose": "summary",
                                          "allow_ultra": False}, _router_mod=r2)
        assert not [e for e in seen if e[0] == "escalated"], seen
    finally:
        gv.record = _record
        os.environ.pop(gv.FLAG, None)


def t_p_the_measured_router_facts_are_still_true():
    """لنگرِ واقعیت: ادعاهای این ماژول را روی کدِ **واقعیِ** مسیریاب بسنج.

    بدونِ این، `paid_order` فقط رونویسیِ من از خطِ ۳۷۰ است و روزی که آن خط عوض
    شود، این سوئیت سبز می‌ماند و حاکم دربارهٔ جهانی حرف می‌زند که دیگر وجود
    ندارد. صفر شبکه: هم `_ask_paid` هم مغزِ محلی هم `keys_present` قلابی‌اند
    (تا هیچ فایلِ `.env`ای هم خوانده نشود)."""
    import os
    sys.path.insert(0, str(_HERE.parent / "cortex"))
    import model_router as mr
    import local_llm

    saved = (mr._ask_paid, local_llm.ask, mr.keys_present)
    tried = []
    try:
        mr._ask_paid = lambda t, p, s, m: tried.append(t) or None
        local_llm.ask = lambda p, system="", max_tokens=400, opener=None: \
            {"text": "x" * 200, "tier": "local"}
        mr.keys_present = lambda: {"fugu": True, "glm": True, "deepseek": False}
        mr.ACT_CORTEX_PAID.parent.mkdir(parents=True, exist_ok=True)
        mr.ACT_CORTEX_PAID.write_text("test", "utf-8")   # sandboxِ harness
        assert mr.paid_gate()[0] is True, mr.paid_gate()

        # (الف) ردهٔ محلی ساختاراً بی‌egress است — پایهٔ قفلِ secret.
        tried.clear()
        mr._ask_impl("هرچه", "س", tier=gv.LOCAL_TIER)
        assert tried == [], f"tier=local نباید هیچ ردهٔ پولی‌ای را لمس کند: {tried}"
        assert tried == gv.paid_order(gv.LOCAL_TIER), tried

        # (ب) fallbackِ key-aware از پیش موجود است و **متقارن** — پس درخواستِ
        #     secondary به‌جای primary مجموعهٔ ردهٔ قابلِ‌تلاش را بزرگ نمی‌کند.
        for want in gv.REMOTE_TIERS:
            tried.clear()
            mr._ask_impl("هرچه", "س", tier=want)
            assert tried == gv.paid_order(want), \
                f"paid_order({want}) با مسیریابِ واقعی نمی‌خواند: {tried}"

        # (ج) «ultra» به‌عنوان رده از این در دست‌نیافتنی است.
        assert set(mr._TIER_ROLE) == set(gv.REMOTE_TIERS), mr._TIER_ROLE
        assert gv.ULTRA_TIER in mr._TIER_ROLE, "ULTRA_TIER باید ردهٔ واقعی باشد"

        # (د) tierِ ناشناختهٔ صریح در **خودِ مسیریاب** صفر ردهٔ پولی می‌زند، پس
        #     سقفِ `router_want` هم باید محلی باشد. بدونِ این لنگر، حاکم برای
        #     `tier="think"` سقف را از `TASK_TIERS` می‌گرفت (=primary) و یک
        #     تماسِ **پولی** می‌ساخت جایی که امروز $۰ خرج می‌شود.
        for unknown in ("think", "premium"):
            tried.clear()
            mr._ask_impl("هرچه", "س", tier=unknown)
            assert tried == [], f"tier={unknown!r} نباید ردهٔ پولی لمس کند: {tried}"
            assert gv.router_want("deep", unknown, router_mod=mr) == gv.LOCAL_TIER, \
                f"سقفِ tier={unknown!r} باید محلی باشد (مثلِ خودِ مسیریاب)"
    finally:
        mr._ask_paid, local_llm.ask, mr.keys_present = saved
        try:
            mr.ACT_CORTEX_PAID.unlink()
        except OSError:
            pass
        os.environ.pop("CORTEX_ROUTE_SCORER", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_governor_routing: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
