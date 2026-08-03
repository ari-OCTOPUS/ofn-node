#!/usr/bin/env python3
"""governor.py — آداپتورِ مشترکِ بودجه/حاکمیت روی «درِ واحدِ مغز» (B5.1).

این ماژول یک **آداپتور** است، نه بازنویسیِ مسیریاب. تنها مسیرِ مدل در این ارگانیسم
`_ops/cortex/model_router.ask()` است (خطِ ۴۲۶) و این‌جا هیچ providerِ دومی ساخته
نمی‌شود، هیچ کلیدی خوانده نمی‌شود و هیچ تماسِ شبکه‌ای زده نمی‌شود. کارِ حاکم فقط
این است: از روی «قراردادِ» صریحِ صداکننده، **ردهٔ درخواستی** را انتخاب کند و
تصمیمش را ثبت کند — بعد همان `ask()` امروز را صدا بزند.

قراردادی که هر تماسِ مدل اعلام می‌کند (`normalize` همه را با پیش‌فرضِ امن پر می‌کند):
    task_id · brain · purpose · expected_artifact · risk · importance
    contains_secrets · allow_ultra · is_write · cache_key

قواعدِ مسیریابی (به ترتیب؛ اولین منطبق برنده است):
  ۱. is_write=True      → گیتِ تأییدِ مالکِ **موجود**. حاکم هرگز خودش مجوز نمی‌دهد.
  ۲. contains_secrets   → فقط محلی. هیچ ردهٔ راه‌دوری، تحتِ هیچ شرطی.
  ۳. cache hit          → اصلاً هیچ تماسِ مدلی زده نمی‌شود.
  ۴. purpose            → search→محلی · summary/classification/code_review→secondary
                          · deep_audit→ردهٔ بالا · security→محلی+redact
  ۵. allow_ultra=False  → ردهٔ بالا ممنوع؛ نزول به ردهٔ ارزان‌تر.
  ۶. سقفِ پایه          → ردهٔ انتخابی هرگز از ردهٔ **امروزِ** همان task بالاتر نمی‌رود.

⚠️ چهار صداقت دربارهٔ همین repo — همه با اجرا سنجیده شدند، نه با خواندنِ نقشه:
  · **ردهٔ «cyber» وجود ندارد.** در کلِ درخت هیچ مغز/tierِ cyber، هیچ مسیرِ
    redacted-remote و هیچ redactorِ خروجی نیست (grep: تنها وقوعِ «cyber» همین
    فایل است). پس قاعدهٔ «security → cyber با redaction» به سخت‌گیرانه‌ترین شکلِ
    **موجود** پیاده شد: `local` + پرچمِ `redact=True` در تصمیم (صفر egress).
    هیچ providerِ دومی ساخته نشد. `cyber` در `BRAINS` می‌ماند چون یک **برچسبِ
    صداکننده** است، نه یک رده.
  · **ردهٔ «ultra» به‌عنوان tier وجود ندارد.** `model_router._TIER_ROLE` فقط
    `secondary→glm` و `primary→orchestr` را می‌شناسد. نقشِ `premium`
    (`model: fugu-ultra-…`) در budgets.yaml **هست** ولی از `ask()` ساختاراً
    دست‌نیافتنی است (و همین‌طور `anthropic`/`econ`/`reason`). پس ultra =
    گران‌ترینِ *قابلِ‌دسترس* یعنی `primary`، و `allow_ultra=False` یعنی
    «هرگز primary درخواست نکن».
  · **مرزِ صادقانهٔ گاردِ ultra.** حاکم فقط ردهٔ **درخواستی** را تعیین می‌کند.
    `model_router._ask_impl` از قدیم یک fallbackِ key-aware دارد
    (`order = [want] + [t for t in ("primary","secondary") if t != want]`).
    اندازه‌گیریِ زنده (هر دو کلید ست، گیتِ پولی باز):
        tier=secondary → تلاش: secondary, primary, local
        tier=primary   → تلاش: primary, secondary, local
    یعنی **مجموعهٔ** ردهٔ قابلِ‌تلاش در هر دو حالت یکی است؛ فقط **ترتیب** فرق
    می‌کند. پس وقتی حاکم به‌جای primary، secondary می‌خواهد، هیچ ردهٔ تازه‌ای باز
    نمی‌کند — فقط ارزان را اول امتحان می‌کند. ادعای این ماژول دقیقاً همین است و
    نه یک کلمه بیشتر: «هرگز ultra **درخواست** نمی‌کند» + «اگر مسیریاب با
    fallbackِ از پیش موجودش بالا رفت، ثبت می‌شود» (`escalated`).
  · **`tier="local"` ساختاراً بی‌egress است.** اندازه‌گیری شد: با
    `tier="local"` شاخهٔ `want in ("secondary","primary")` اصلاً اجرا نمی‌شود و
    `_ask_paid` **هرگز** صدا نمی‌خورد. قفلِ ردهٔ محلی برای secretها روی همین
    واقعیت می‌نشیند، نه روی حسنِ نیت.

پیش‌فرض خاموش: `OCTOPUS_WIRE_GOVERNOR` (عمداً **بیرونِ** `wiring.PAPER_FULL_FLAGS`).
با فلگِ خاموش این ماژول یک passthroughِ بایت‌به‌بایت است: همان آرگومان‌ها به
`model_router.ask` و **همان شیءِ خروجی** برمی‌گردد — صفر تصمیم، صفر ثبت، صفر کش.

$۰ · فقط stdlib · بدونِ I/O در هستهٔ خالص (`decide`) · هر خطای ثبت fail-soft.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

# ── پرچم (پیش‌فرض خاموش) ─────────────────────────────────────────────────────
FLAG = "OCTOPUS_WIRE_GOVERNOR"
_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("", "0", "false", "no", "off", "none", "null")


def enabled() -> bool:
    """فقط env. نبود/خالی/«0» = خاموش. هیچ فایلی این را روشن نمی‌کند."""
    return str(os.environ.get(FLAG, "")).strip().lower() in _TRUTHY


# ── واژگانِ قرارداد ──────────────────────────────────────────────────────────
BRAINS = ("router", "planner", "memory", "critic", "omega", "cyber")
PURPOSES = ("search", "summary", "classification", "deep_audit",
            "security", "code_review")
RISKS = ("low", "medium", "high")
IMPORTANCES = ("low", "medium", "high", "critical")

# ردهٔ واقعیِ همین repo — هرچه غیر از این‌ها بیاید، وجود ندارد.
LOCAL_TIER = "local"
MID_TIER = "secondary"
ULTRA_TIER = "primary"          # گران‌ترینِ قابلِ‌دسترس از ask() — «ultra»ی این درخت
REMOTE_TIERS = (MID_TIER, ULTRA_TIER)
TIER_RANK = {None: -1, LOCAL_TIER: 0, MID_TIER: 1, ULTRA_TIER: 2}

# گیتِ نوشتن = همان گیتِ موجودِ `_ops/budget/capability_gate.py`.
# این یک **برچسب** نیست: `write_gate()` پایین واقعاً همین تابع را صدا می‌زند.
WRITE_GATE = "capability_gate.require"

# purpose → ردهٔ خامِ پیشنهادی (قبل از گاردها و سقف)
PURPOSE_TIER = {
    "search": LOCAL_TIER,           # جستجو/regex/diff/scan → محلیِ $۰
    "security": LOCAL_TIER,         # + redact (cyber در این درخت وجود ندارد)
    "summary": MID_TIER,
    "classification": MID_TIER,
    "code_review": MID_TIER,
    "deep_audit": ULTRA_TIER,       # فقط با allow_ultra=True به این‌جا می‌رسد
}


def _norm_choice(value, allowed, default):
    v = str(value or "").strip().lower()
    return v if v in allowed else default


def _as_bool(value) -> bool:
    """پیش‌فرضِ **بسته**: هرچه صریحاً truthy نباشد، False است.

    برای `allow_ultra` جهتِ درستِ خطا همین است — ندانستن یعنی «خرج نکن»."""
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in _TRUTHY


def _as_bool_leaky(value) -> bool:
    """پیش‌فرضِ **بدبین**: هرچه صریحاً falsy نباشد، True است.

    فقط برای `contains_secrets`. `_as_bool` این‌جا در جهتِ **غلط** خطا می‌کرد:
    `contains_secrets=["FUGU_API_KEY"]` (یک لیستِ نامِ متغیر — شکلِ کاملاً
    محتملِ صداکننده) با `str()` می‌شد `"['FUGU_API_KEY']"` که در `_TRUTHY`
    نیست ⇒ False ⇒ همان تماس اجازهٔ ردهٔ راه‌دور می‌گرفت. برای پرچمی که نشتِ
    secret را جلو می‌گیرد، شک باید به سمتِ «بله secret دارد» بیفتد."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() not in _FALSY


def _task_id(contract: dict) -> str:
    try:
        raw = json.dumps(contract, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        raw = str(contract)
    return "gv-" + hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:8]


def normalize(contract) -> dict:
    """قرارداد را به شکلِ کامل و امن دربیاور. ورودیِ ناقص/آشغال هرگز کرش نمی‌کند.

    پیش‌فرض‌ها همه در جهتِ **کم‌خرج و بسته** انتخاب شده‌اند: purposeِ ناشناخته →
    `search` (محلی)، risk ناشناخته → بالاترین احتیاط، `allow_ultra` غایب →
    False (هرگز ردهٔ گران)، `contains_secrets` مبهم → True (نگاه کن به
    `_as_bool_leaky`).
    """
    c = contract if isinstance(contract, dict) else {}
    out = {
        "brain": _norm_choice(c.get("brain"), BRAINS, "router"),
        "purpose": _norm_choice(c.get("purpose"), PURPOSES, "search"),
        "expected_artifact": str(c.get("expected_artifact") or "")[:120],
        "risk": _norm_choice(c.get("risk"), RISKS, "high"),
        "importance": _norm_choice(c.get("importance"), IMPORTANCES, "medium"),
        "contains_secrets": _as_bool_leaky(c.get("contains_secrets")),
        "allow_ultra": _as_bool(c.get("allow_ultra")),
        "is_write": _as_bool(c.get("is_write")),
        "cache_key": (str(c["cache_key"])[:200]
                      if c.get("cache_key") not in (None, "") else None),
    }
    tid = c.get("task_id")
    out["task_id"] = str(tid)[:64] if tid else _task_id(out)
    return out


# ── کشِ درون-پروسه‌ای (بدونِ دیسک، بدونِ state جدید) ──────────────────────────
# عمداً فقط حافظه: کشِ روی دیسک یک فایلِ حالتِ نو و یک سطحِ نشتِ نو می‌سازد، و
# هیچ‌کدام برای «hit ⇒ صفر تماس» لازم نیست. هرگز پاسخِ secret-دار یا writeِ
# تأییدشده کش نمی‌شود.
_CACHE_MAX = 128
_CACHE: "OrderedDict[str, dict]" = OrderedDict()


def cache_clear() -> None:
    _CACHE.clear()


def cache_get(key):
    if not key:
        return None
    hit = _CACHE.get(key)
    if hit is not None:
        _CACHE.move_to_end(key)
    return hit


def cache_put(key, value) -> None:
    if not key or not isinstance(value, dict):
        return
    _CACHE[key] = value
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


# ── ردهٔ «امروز» (سقفِ خرج) ──────────────────────────────────────────────────
def _router():
    here = Path(__file__).resolve().parent
    cx = str(here.parent / "cortex")
    if cx not in sys.path:
        sys.path.insert(0, cx)
    import model_router  # noqa: WPS433
    return model_router


def router_want(task: str, tier: str | None = None, router_mod=None) -> str:
    """ردهٔ همین taskِ **بدونِ** حاکم — دقیقاً همان‌طور که `_ask_impl` حسابش می‌کند.

    نسخهٔ قبلی فقط `TASK_TIERS` را می‌خواند و شاخهٔ `CORTEX_ROUTE_SCORER` را
    نمی‌دید. اگر آن پرچم روشن باشد `route_scorer` می‌تواند ردهٔ **پایین‌تری** از
    نگاشتِ ایستا بدهد (سنجیده شد: `research`→secondary، `summarize`→local) — و
    آن‌وقت سقفی که از `TASK_TIERS` می‌آمد از خرجِ واقعیِ امروز **بالاتر** بود،
    یعنی حاکم اجازه می‌داد بیشتر خرج شود. همان چیزی که این لایه نباید بکند.

    importِ ناموفق → `local` یعنی سخت‌گیرانه‌ترین سقف (خطا در جهتِ کم‌خرجی).
    """
    if tier:
        # tierِ صریح = همان چیزی که امروز اجرا می‌شود — ولی «امروز» را باید از
        # خودِ مسیریاب پرسید، نه از نگاشت. سنجیده شد: `_ask_impl` هر tierِ
        # بیرونِ ("secondary","primary") را مثلِ محلی رفتار می‌کند و **صفر**
        # ردهٔ پولی لمس می‌کند (tier="think"/"premium" → tried=[]). اگر این‌جا
        # برای چنین tierی سقف از `TASK_TIERS` بیاید، سقف از خرجِ واقعیِ امروز
        # **بالاتر** می‌رود و حاکم اجازه می‌دهد بیشتر خرج شود — دقیقاً کاری که
        # این لایه نباید بکند. (`tier`ِ falsy — None/"" — را خودِ مسیریاب
        # «نداده» می‌شمارد، پس از این شاخه رد می‌شویم.)
        return tier if tier in TIER_RANK else LOCAL_TIER
    try:
        r = router_mod if router_mod is not None else _router()
        want = None
        if os.environ.get("CORTEX_ROUTE_SCORER"):
            want = r._scored_tier(task)          # همان مشاورِ خودِ مسیریاب
        want = want or r.TASK_TIERS.get(str(task), LOCAL_TIER)
        return want if want in TIER_RANK else LOCAL_TIER
    except Exception:  # noqa: BLE001 — ندانستنِ سقف = پایین‌ترین سقف
        return LOCAL_TIER


# نامِ قدیمی حفظ شد (هر صداکننده‌ای که به آن اشاره دارد نشکند).
baseline_tier = router_want


def paid_order(want: str) -> list:
    """ترتیبِ تلاشِ ردهٔ پولی در `_ask_impl` — بازتابِ مو‌به‌موی خطِ ۳۷۰ مسیریاب.

    این‌جا فقط برای این است که ادعای «حاکم مجموعهٔ ردهٔ قابلِ‌تلاش را **بزرگ‌تر**
    نمی‌کند» ماشین‌خوان و آزمون‌پذیر باشد، نه یک جملهٔ اطمینان‌بخش در docstring.
    """
    if want not in REMOTE_TIERS:
        return []                        # محلی = هیچ تلاشِ پولی‌ای (سنجیده شد)
    return [want] + [t for t in (ULTRA_TIER, MID_TIER) if t != want]


def _min_tier(a, b):
    return a if TIER_RANK.get(a, -1) <= TIER_RANK.get(b, -1) else b


# ── هستهٔ خالص: تصمیم (بدونِ I/O، بدونِ تماس، بدونِ اثرِ جانبی) ────────────────
def decide(contract, baseline: str | None = None, cache_lookup=None) -> dict:
    """قرارداد → تصمیمِ مسیریابی. نه فایل می‌نویسد، نه مدل صدا می‌زند، نه گیت.

    تنها وابستگیِ بیرونی `cache_lookup` است (پیش‌فرض: کشِ درون-پروسه‌ای) و
    تزریق‌پذیر است تا آزمون بتواند hit/miss را قطعی بسازد.

    خروجی: {route, tier, redact, gate, granted, baseline, clamped, reasons, …}
      route = "approval_gate" | "cache" | "model"
      tier  = None (بدونِ تماس) | "local" | "secondary" | "primary"
    """
    c = normalize(contract)
    look = cache_lookup if cache_lookup is not None else cache_get
    base = baseline if baseline in TIER_RANK and baseline is not None else ULTRA_TIER
    reasons: list[str] = []
    d = dict(c)
    d.update({"baseline": base, "route": "model", "tier": None, "redact": False,
              "gate": None, "granted": False, "cacheable": False,
              "clamped": False, "escalated": False, "reasons": reasons})

    # ۱) نوشتن: حاکم هرگز خودش مجوز نمی‌دهد — فقط به گیتِ موجود ارجاع می‌دهد.
    #    خودِ صدازدنِ گیت در `ask()` است تا این تابع خالص بماند.
    if c["is_write"]:
        d.update(route="approval_gate", tier=None, gate=WRITE_GATE, granted=False)
        reasons.append("is_write → گیتِ تأییدِ مالک؛ حاکم مجوزِ نوشتن صادر نمی‌کند")
        return d

    # ۲) گاردِ secret (قفلِ اول): هیچ ردهٔ راه‌دوری، تحتِ هیچ شرطی.
    if c["contains_secrets"]:
        d.update(tier=LOCAL_TIER, redact=True, cacheable=False)
        reasons.append("contains_secrets → قفلِ محلی؛ ردهٔ راه‌دور ممنوع (صفر egress)")
        return d

    # ۳) کش: hit یعنی اصلاً هیچ تماسی زده نمی‌شود.
    if c["cache_key"] and look(c["cache_key"]) is not None:
        d.update(route="cache", tier=None, cacheable=True)
        reasons.append("cache hit → صفر تماسِ مدل")
        return d

    # ۴) نوعِ کار → ردهٔ خام
    tier = PURPOSE_TIER.get(c["purpose"], LOCAL_TIER)
    reasons.append(f"purpose={c['purpose']} → {tier}")
    if c["purpose"] == "security":
        d["redact"] = True
        reasons.append("security → محلی + redact (ردهٔ cyber در این درخت وجود ندارد)")

    # ۵) گاردِ ultra (نقطهٔ اجرای یکتا): گران‌ترین رده فقط با اجازهٔ صریح.
    if tier == ULTRA_TIER and not c["allow_ultra"]:
        tier = MID_TIER
        reasons.append("allow_ultra=false → ردهٔ ultra ممنوع؛ نزول به " + MID_TIER)

    # ۶) اهمیتِ پایین هرگز خرج نمی‌تراشد (فقط نزول، هرگز صعود).
    if c["importance"] == "low":
        tier = _min_tier(tier, LOCAL_TIER)
        reasons.append("importance=low → کفِ محلی")

    # ۷) سقفِ پایه: تصمیمِ حاکم هرگز از ردهٔ **امروزِ** همین task بالاتر نمی‌رود.
    clamped = _min_tier(tier, base)
    if clamped != tier:
        reasons.append(f"سقفِ پایه ({base}) → نزول از {tier} به {clamped}")
        d["clamped"] = True
    d["tier"] = clamped
    d["cacheable"] = bool(c["cache_key"])
    return d


# ── قفلِ دوم: گاردِ تحویل (مستقل از `decide`) ────────────────────────────────
def delivery_allowed(decision: dict) -> tuple:
    """آیا این تصمیم اجازهٔ رفتن به `model_router.ask` را دارد؟

    عمداً یک تابعِ **جدا** است، نه یک `if` توی `ask`. دلیلش آزمون‌پذیری است:
    قفلِ اول (`decide`) و قفلِ دوم (این‌جا) باید هرکدام جداگانه **کشته** شوند تا
    ثابت شود هر دو واقعاً دندان دارند. وقتی هر دو در یک تابع باشند، جهشِ روی
    یکی را آن‌یکی می‌پوشاند و هر دو «SURVIVED» گزارش می‌شوند — یعنی هیچ‌کدام
    سنجیده نشده.
    """
    if decision.get("contains_secrets") and decision.get("tier") in REMOTE_TIERS:
        return False, "secret-bearing call refused: remote tier"
    return True, "ok"


# ── گیتِ نوشتن: صداکردنِ گیتِ **واقعی**، نه اشاره به نامش ────────────────────
def write_gate(decision: dict, gate_mod=None) -> dict:
    """`capability_gate.require` را واقعاً صدا می‌زند. حاکم هرگز خودش grant نمی‌کند.

    مبلغ ۰.۰ است چون این‌جا خرجِ نقدی نیست؛ چیزی که لازم داریم همان سه‌قفلهٔ
    `capability ∧ LIVE_ENABLED ∧ per-action approval` است. هر خطا (نبودِ ماژول،
    import شکسته، …) = **رد**، نه عبور: fail-closed.
    """
    try:
        g = gate_mod
        if g is None:
            here = str(Path(__file__).resolve().parent)
            if here not in sys.path:
                sys.path.insert(0, here)
            import capability_gate as g  # noqa: WPS433
        res = g.require(f"governor-write:{decision.get('task_id', '?')}", 0.0)
        if not isinstance(res, dict):
            return {"allow": False, "gate": WRITE_GATE, "reason": "gate returned non-dict"}
        return res
    except Exception as e:  # noqa: BLE001 — ندانستن = بسته
        return {"allow": False, "gate": WRITE_GATE,
                "reason": f"gate unavailable: {type(e).__name__}"}


# ── ثبت (فقط با فلگِ روشن؛ محتوا-آزاد؛ هرگز prompt/secret) ────────────────────
def _decisions_log() -> Path:
    try:
        here = str(Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import opslib  # noqa: WPS433
        return Path(opslib.STATE_DIR) / "governor" / "decisions.jsonl"
    except Exception:  # noqa: BLE001
        return Path(__file__).resolve().parent.parent / "state" / "governor" / "decisions.jsonl"


def record(decision: dict, event: str = "decision") -> None:
    """«ثبت همیشه، گیت فقط روی تحویل»: هر تصمیم — عبور یا رد — ثبت می‌شود.

    فقط برچسب/رده/دلیل. هیچ promptی، هیچ متنِ پاسخی، هیچ cache_keyِ خام (هش شده).
    fail-soft مطلق: دفتر هرگز مسیرِ مدل را نمی‌کشد.
    """
    try:
        rec = {k: decision.get(k) for k in
               ("task_id", "brain", "purpose", "risk", "importance", "route",
                "tier", "baseline", "clamped", "redact", "gate", "granted",
                "contains_secrets", "allow_ultra", "is_write", "escalated")}
        rec["event"] = event
        ck = decision.get("cache_key")
        rec["cache_key_h"] = (hashlib.sha1(str(ck).encode("utf-8", "replace"))
                              .hexdigest()[:12] if ck else None)
        rec["why"] = " · ".join(decision.get("reasons") or [])[:400]
        try:
            import opslib  # noqa: WPS433
            rec["ts"] = opslib.now_iso()
            opslib.append_jsonl(_decisions_log(), rec)
            return
        except ImportError:
            pass
        p = _decisions_log()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


# ── آداپتور ──────────────────────────────────────────────────────────────────
def ask(task: str, prompt: str, system: str = "", max_tokens: int = 400,
        tier: str | None = None, opener=None, quality=None,
        contract=None, _router_mod=None) -> dict:
    """امضایِ `model_router.ask` + یک `contract` اختیاری.

    فلگِ خاموش **یا** قراردادِ غایب ⇒ passthroughِ بایت‌به‌بایت: همان آرگومان‌ها،
    همان شیءِ خروجی، صفر تصمیم، صفر ثبت، صفر کش. (رفتارِ امروز دست‌نخورده.)

    فلگِ روشن + قرارداد ⇒ تصمیم گرفته و ثبت می‌شود، بعد **همان** `ask` با ردهٔ
    تصمیم‌گرفته‌شده صدا زده می‌شود. مسیرهای cache و approval_gate اصلاً صداش
    نمی‌زنند.
    """
    r = _router_mod if _router_mod is not None else _router()
    if not enabled() or contract is None:
        return r.ask(task, prompt, system, max_tokens,
                     tier=tier, opener=opener, quality=quality)

    want_today = router_want(task, tier, router_mod=r)
    d = decide(contract, baseline=want_today)
    record(d)                       # ثبت **قبل** از هر اقدام: کرش هم رد می‌گذارد

    # ۱) نوشتن → گیتِ واقعی. حاکم فقط منتقل می‌کند؛ نه grant می‌سازد نه گیت را دور می‌زند.
    if d["route"] == "approval_gate":
        g = write_gate(d)
        d["granted"] = bool(g.get("allow"))
        record(d, event="write-gate")
        return {"ok": False, "reason": "owner-approval-required",
                "gate": d["gate"], "gate_result": g, "governor": d}

    # ۲) کش → صفر تماسِ مدل.
    if d["route"] == "cache":
        hit = cache_get(d["cache_key"]) or {}
        return {"ok": True, "tier": hit.get("tier", LOCAL_TIER), "cached": True,
                "text": hit.get("text", ""), "governor": d}

    # ۳) قفلِ دوم، مستقل از `decide`: پاسخِ secret-دار هرگز از این‌جا به یک ردهٔ
    #    راه‌دور نمی‌رود، حتی اگر بالادست خراب شده باشد.
    allowed, why = delivery_allowed(d)
    if not allowed:
        d["reasons"].append("delivery-guard: " + why)
        record(d, event="refused")
        return {"ok": False, "reason": why, "governor": d}

    out = r.ask(task, prompt, system, max_tokens,
                tier=d["tier"], opener=opener, quality=quality)

    # ۴) اگر fallbackِ **از پیش موجودِ** مسیریاب از ردهٔ درخواستی بالاتر رفت، این
    #    را نمی‌شود جلو گرفت (پولش خرج شده) ولی می‌شود دید. سکوت این‌جا یعنی
    #    مالک هرگز نفهمد allow_ultra=false در عمل چقدر نگه داشته.
    if isinstance(out, dict):
        got = out.get("tier")
        if TIER_RANK.get(got, -1) > TIER_RANK.get(d["tier"], -1):
            d["escalated"] = True
            d["reasons"].append(f"router fallback: {d['tier']} → {got}")
            record(d, event="escalated")

    if (d.get("cacheable") and d["cache_key"] and isinstance(out, dict)
            and out.get("ok") and not d["contains_secrets"]):
        cache_put(d["cache_key"], {"text": out.get("text", ""),
                                   "tier": out.get("tier")})
    return out


if __name__ == "__main__":
    demo = [
        {"purpose": "search", "importance": "medium"},
        {"purpose": "deep_audit", "importance": "critical", "allow_ultra": True},
        {"purpose": "deep_audit", "importance": "critical", "allow_ultra": False},
        {"purpose": "summary", "contains_secrets": True},
        {"purpose": "code_review", "is_write": True},
    ]
    print(json.dumps({"flag": FLAG, "enabled": enabled(),
                      "decisions": [{"in": c,
                                     "route": decide(c)["route"],
                                     "tier": decide(c)["tier"],
                                     "why": decide(c)["reasons"]} for c in demo]},
                     ensure_ascii=False, indent=2))
