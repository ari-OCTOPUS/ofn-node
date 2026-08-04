#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cockpit_brain.py — مغزِ حافظه‌دارِ کنترل‌پنل.

    خواستهٔ مالک (۲۰۲۶-۰۸-۰۵): «یک مغز هوشمند حافظه‌دار که این کنترل‌پنل را
    چک کند، با من هماهنگ کند، با خودِ اختاپوس، و کمکم کند به تغییرِ سریع و
    بهبود و عملگراییِ واقعی.»

    رأی‌های مالک که این طرح از آن‌ها ساخته شده:
      · بیداری هر **۵ دقیقه**.
      · فقط وقتی حرف بزند که **کاری با مالک دارد** — سکوت یعنی سالم.
      · اولین کارها: خودآگاهی/خودترمیمیِ مداوم · کارهای گیرکرده ·
        دروغ‌های کاکپیت · پول و بودجه.

    ── چرا تماسِ پولی **مشروط** است ──────────────────────────────────────
    مالک گفت «هر ضربان یک تماسِ واقعی»، ولی بعد گفت بودجه را دقیق تحقیق کنم.
    تحقیق (paid-calls.jsonl، ۵۴۷ تماس) این را داد:
      · ارگانیسم امروز ۵۵–۶۰ تماسِ پولی در روز می‌زند (~۱۹٪ سقفِ ۳۰۰).
      · میانگین ۴٬۷۷۵ توکن در هر تماس.
    بیداریِ ۵ دقیقه‌ای = ۲۸۸ بیداری در روز. تماسِ بی‌قید یعنی ۳۴۳ تماس ⇒ از
    سقف رد می‌شود و توکن ~۶ برابر. و `budgets.yaml` می‌گوید `system_share:
    0.5` — نصفِ اشتراک سهمِ سیستم است (رأیِ خودِ مالک، ۰۷-۱۰).

    پس: بیدارشدن هر ۵ دقیقه (رأیِ مالک، دست‌نخورده) ولی تماسِ پولی فقط وقتی
    پاسِ **محلیِ رایگان** بگوید چیزی مهم عوض شده. «هر ضربانی که حرفی برای
    فکرکردن دارد».

    ── معماری ────────────────────────────────────────────────────────────
      observe()  — فقط خواندن. هر رقم منبعِ نام‌بردهٔ روی دیسک دارد.
      recall()   — حافظهٔ ماندگار: آخرین چیزی که دیدم و آخرین چیزی که گفتم.
      diff()     — چه چیزِ **مهمی** عوض شد؟ ($۰، قطعی، بی‌مدل)
      think()    — فقط روی diff ِ غیرِ خالی، و فقط اگر سهمیه اجازه دهد.
      speak()    — حداکثر یک کارتِ زنده. تکرارِ حرفِ قبلی = سکوت.

    ⚠️ این ماژول **هیچ‌وقت خودش اقدام نمی‌کند**. پیشنهاد می‌دهد و مالک تپ
    می‌زند. دلیل: منشور، §۰ و §۱۰ — پول/ارسال/حذف گیتِ انسانی دارند.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex"),
           str(_HERE / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib
    STATE = opslib.STATE_DIR
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    STATE = _HERE / "state"

BRAIN_DIR = STATE / "cockpit_brain"
MEMORY = BRAIN_DIR / "memory.jsonl"
LATEST = BRAIN_DIR / "latest.json"

#: فلگ — پیش‌فرض خاموش. روشن‌کردن یک تصمیمِ مالک است، نه پیش‌فرضِ من.
FLAG = "OCTOPUS_COCKPIT_BRAIN"
#: کفِ فاصلهٔ دو تماسِ پولی. با ریتمِ ۵ دقیقه‌ای و رأیِ «هر بیداری»، این
#: عدد کمی **زیرِ** ۵ دقیقه است تا جلوی بیداریِ عادی را نگیرد و فقط جلوی
#: رگبارِ ناشی از ری‌استارتِ پیاپی را بگیرد.
MIN_PAID_GAP_S = 240.0
#: ردهٔ مدل — رأیِ مالک (۰۸-۰۵): GLM.
#:
#: ⚠️ تصحیحِ ۰۸-۰۵ با شاهدِ زنده. کامنتِ قبلی نوشته بود «Fugu آزاد می‌ماند»
#: و **دروغ بود**. در `model_router._ask_impl` ترتیب این است:
#:     order = [want] + [t for t in ("primary","secondary") if t != want]
#: یعنی `tier="secondary"` معنایش «اول GLM، بعد Fugu» است نه «فقط GLM».
#: شاهد در paid-calls.jsonl:
#:     01:16:51  tier=secondary role=glm  ok=False (HTTPError)
#:     01:17:01  tier=primary   role=fugu ok=True     ← همان پرامپتِ مغز
#: ده ثانیه بعد. با بیداریِ ۵ دقیقه‌ای، هر قطعیِ GLM کلِ دیده‌بان را بی‌صدا
#: روی سهمیهٔ Fugu می‌برد.
#: پس `think()` حالا نتیجه‌ای را که از ردهٔ دیگری آمده **رد می‌کند**.
BRAIN_TIER = "secondary"


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


# ═════════════════════════════════════════════════════════════════════════
# observe — فقط خواندن، و هر عدد یک منبعِ نام‌برده دارد
# ═════════════════════════════════════════════════════════════════════════
def _j(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def observe(state_dir: "Path | None" = None) -> dict:
    """عکسِ لحظه‌ایِ ارگانیسم از روی دیسک.

    هر کلید یا مقدارِ واقعی دارد یا `None` — **هرگز صفرِ جعلی**. `None` یعنی
    «نخواندم»، و مغز باید بتواند آن را از «صفر است» جدا کند، وگرنه همان
    اشتباهی را می‌کند که کاکپیت می‌کرد.
    """
    sd = Path(state_dir) if state_dir else STATE
    out: dict = {"ts": time.time(), "sources": {}}

    def put(key, value, source):
        out[key] = value
        out["sources"][key] = source

    org = _j(sd / "ORGANISM-STATE.json") or {}
    put("halted", bool(org.get("halted") or org.get("stop_organism"))
        if org else None, "state/ORGANISM-STATE.json")
    put("beat", org.get("beat") if org else None, "state/ORGANISM-STATE.json")
    put("conflicts", org.get("conflicts") if org else None, "state/ORGANISM-STATE.json")
    put("germline_alert", org.get("germline_alert") if org else None,
        "state/ORGANISM-STATE.json")
    month = (org.get("month") or {}) if org else {}
    put("month_aud", month.get("aud"), "state/ORGANISM-STATE.json:month")

    car = _j(sd / "cardiac-budget.json") or {}
    today = time.strftime("%Y-%m-%d")
    # ⚠️ گاردِ کهنگی: عددِ دیروز از نبودِ عدد بدتر است.
    fresh = str(car.get("date") or "") == today
    put("beats_spent", car.get("spent") if (car and fresh) else None,
        "state/cardiac-budget.json")

    fq = _j(sd / "fugu-quota.json") or {}
    put("paid_calls_today", fq.get("used_total") if (
        fq and str(fq.get("day") or "") == today) else None,
        "state/fugu-quota.json")

    # چرخهٔ عمرِ کارت‌ها — «چه چیزی گیر کرده» مستقیماً از این می‌آید.
    #
    # ⚠️ اول خودم `pending-cards.json` را می‌خواندم و `stage=="STALLED"` را
    # می‌شمردم: نتیجه **صفر** شد در حالی که همان لحظه `/api/lifecycle`
    # می‌گفت ۲۷. یعنی دو عدد برای یک حقیقت — دقیقاً همان «دروغِ کاکپیت» که
    # قرار است این مغز بگیرد. پس از **همان** خواننده‌ای می‌پرسم که کاکپیت
    # می‌پرسد؛ یک منبع، یک عدد. تفسیرِ موازی = تناقضِ فردا.
    stalled = None
    try:
        import miniapp_state as _ms2
        _sv = _ms2.STATE_DIR
        _ms2.STATE_DIR = sd
        try:
            lc = _ms2.get_lifecycle_state()
        finally:
            _ms2.STATE_DIR = _sv
        by = lc.get("by_stage") if isinstance(lc, dict) else None
        val = by.get("value") if isinstance(by, dict) else None
        if isinstance(val, dict):
            stalled = val.get("STALLED")
    except Exception:  # noqa: BLE001
        stalled = None
    put("stalled_cards", stalled, "miniapp_state.get_lifecycle_state:by_stage")

    # صفِ تأیید — از همان خوانندهٔ کاکپیت، تا مغز و صفحه یک حقیقت بگویند
    try:
        import miniapp_state as _ms
        _saved = _ms.STATE_DIR
        _ms.STATE_DIR = sd
        try:
            ap = _ms.get_approvals_state()
        finally:
            _ms.STATE_DIR = _saved
        put("approvals", ap.get("count") if ap.get("status") == "ok" else None,
            "miniapp_state.get_approvals_state")
        put("approvals_status", ap.get("status"), "miniapp_state.get_approvals_state")
    except Exception as exc:  # noqa: BLE001
        put("approvals", None, f"unavailable:{type(exc).__name__}")
        put("approvals_status", None, f"unavailable:{type(exc).__name__}")

    return out


# ═════════════════════════════════════════════════════════════════════════
# خودآگاهی — سه اندامِ موجود که هیچ‌کس صدایشان نمی‌زد
# ═════════════════════════════════════════════════════════════════════════
# ⚠️ این بخش هیچ اسکنرِ تازه‌ای نمی‌سازد. اختاپوس از قبل پنج اندامِ خودآگاهی
# دارد — orphan_scan · dark_capabilities · capability_registry · flag_drift ·
# self_scan — و **هیچ‌کدام صداکنندهٔ تولیدی نداشت**. تنها ارجاع‌ها یک فهرستِ
# تست بود و ارجاعِ متقابل در docstring ِ همدیگر.
#
# یعنی ابزارهایی که ساخته شده بودند تا «قابلیتِ تاریک» را پیدا کنند، خودشان
# تاریک بودند. این بازگشتی‌ترین شکلِ همان بیماری است، و رفعش ماژولِ ششم
# نیست — وصل‌کردنِ همان حس‌ها به تنها صدایی است که حالا به مالک می‌رسد.
#
# ریتم از روی **هزینهٔ اندازه‌گیری‌شده** (روی همین لپ‌تاپ، دیسکِ ۵۴۰۰ دور):
#     dark_capabilities   ۴.۵ ثانیه
#     orphan_scan         ۷.۸ ثانیه
#     self_scan          ۴۶.۲ ثانیه   ← گران، پس روزانه
# بیداریِ ارزان هر ۵ دقیقه است (~۰.۳ث)، پس این‌ها روی همان ریتم نمی‌نشینند.
_TIERS = {
    # نام: (ماژول، فاصلهٔ ثانیه، آرگومان)
    "dark":   ("dark_capabilities", 3600.0),
    "orphan": ("orphan_scan", 3600.0),
    "self":   ("self_scan", 86400.0),
}


def _run_scan(mod: str, timeout_s: float = 120.0) -> "dict | None":
    """اسکنر را در **زیرپروسه** می‌دواند، نه با import.

    دو دلیل: (۱) این ماژول‌ها در سطحِ ماژول کار می‌کنند و import کردنشان
    داخلِ مغز می‌تواند حالت را آلوده کند؛ (۲) اسکنی که ۴۶ ثانیه طول می‌کشد
    اگر هنگ کند نباید مغز را با خودش ببرد — زیرپروسه timeout دارد.
    """
    import subprocess
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(_HERE / f"{mod}.py"), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout_s, cwd=str(_HERE.parent),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONIOENCODING": "utf-8"})
    except Exception:  # noqa: BLE001 — اسکن هرگز بیداری را نمی‌کشد
        return None
    txt = (r.stdout or "").strip()
    i = txt.find("{")
    if i < 0:
        return None
    # ⚠️ `orphan_scan` بعد از خطِ JSON، فهرستِ خوانا هم چاپ می‌کند، پس
    # `json.loads` روی کلِ خروجی «Extra data» می‌دهد. `raw_decode` فقط
    # اولین شیء را می‌خواند و بقیه را نادیده می‌گیرد — پس هر سه اسکنر با
    # یک مسیر کار می‌کنند، بی‌آنکه لازم باشد خروجیِ آن‌ها را عوض کنم.
    try:
        return json.JSONDecoder().raw_decode(txt, i)[0]
    except (ValueError, TypeError):
        return None


def _summarise(name: str, d: dict) -> dict:
    """از خروجیِ پرحجمِ اسکن فقط چند **عدد** نگه می‌دارد.

    عمداً نه فهرستِ نام‌ها: حافظهٔ مغز باید کوچک بماند و diff باید روی عدد
    باشد. نامِ چیزِ تازه را وقتی لازم شد از خودِ اسکن می‌شود گرفت.
    """
    # ⚠️ کلیدها **خوانده** شدند نه حدس زده. نسخهٔ اولِ این تابع کلیدهای
    # حدسی داشت (`summary`، `dark`، `total`) و نتیجه‌اش این شد که فهرستِ
    # خامِ ۱۲۸ دیکشنری داخلِ حافظهٔ مغز نشست — چند صد کیلوبایت به‌جای یک
    # عدد، و diff روی فهرست بی‌معنا. شکلِ واقعی با `--json` گرفته شد.
    def _num(v):
        """فقط عدد. اگر فهرست بود، طولش. وگرنه None — نه صفرِ جعلی."""
        if isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, (list, tuple, dict)):
            return len(v)
        return None

    if name == "orphan":
        return {"orphans": _num(d.get("total")),
                "weighty": _num(d.get("weighty")),
                "modules_checked": _num(d.get("checked"))}
    if name == "dark":
        # شکلِ واقعی: n_dark / n_partial / n_flags / n_live_on (سطحِ بالا)
        return {"dark_gates": _num(d.get("n_dark")),
                "partial_gates": _num(d.get("n_partial")),
                "flags_seen": _num(d.get("n_flags")),
                "flags_live_on": _num(d.get("n_live_on"))}
    # self_scan: همهٔ اعداد در `headline` نشسته‌اند
    h = d.get("headline") if isinstance(d.get("headline"), dict) else {}
    return {"read_undefined": _num(h.get("dark_flags_read_unarmed")),
            "orphan_state": _num(h.get("orphan_state")),
            "untested": _num(h.get("untested_modules")),
            "dead_symbols": _num(h.get("dead_symbols")),
            "unfinished": _num(h.get("unfinished_markers")),
            "checks_failed": _num(h.get("checks_failed"))}


def self_awareness(mem: dict, now: "float | None" = None,
                   force: str = "") -> dict:
    """هر اندام را فقط وقتی می‌دواند که فاصله‌اش گذشته باشد.

    خروجی فقط چند عدد است؛ `diff()` روی همان‌ها کار می‌کند و اگر چیزی عوض
    نشد، مالک هیچ نمی‌شنود.
    """
    t = time.time() if now is None else now
    out, ran = {}, []
    for key, (mod, every) in _TIERS.items():
        last = mem.get(f"_scan_{key}_ts")
        due = force == key or not isinstance(last, (int, float)) or (t - last) >= every
        if not due:
            # مقدارِ قبلی را نگه دار تا diff آن را «ناپدید شد» نخواند.
            prev = mem.get(f"_scan_{key}") or {}
            for k, v in prev.items():
                out[k] = v
            # ⚠️ باگی که دیباگِ ۰۸-۰۵ گرفت: فقط **مقادیر** کپی می‌شد و
            # کلیدهای دفترداری (`_scan_<key>` و `_scan_<key>_ts`) نه. پس
            # `remember()` حافظه‌ای بی‌آن‌ها می‌نوشت، و از آن به بعد:
            #   · `/api/selfmap` این اسکن را **خالی** نشان می‌داد،
            #   · و `last` ِ دفعهٔ بعد `None` می‌شد ⇒ اسکن بی‌دلیل زودتر
            #     از فاصله‌اش دوباره می‌دوید.
            # نتیجه در عمل: `dark` و `orphan` در کاکپیت همیشه خالی بودند
            # در حالی که واقعاً دویده بودند. حافظه‌ای که خودش را پاک کند،
            # از نداشتنِ حافظه بدتر است — چون شبیهِ «هرگز نبود» دیده می‌شود.
            if prev:
                out[f"_scan_{key}"] = prev
                out[f"_scan_{key}_ts"] = last
            continue
        d = _run_scan(mod, timeout_s=150.0 if key == "self" else 60.0)
        if d is None:
            ran.append(f"{key}:failed")
            continue
        s = _summarise(key, d)
        out.update(s)
        out[f"_scan_{key}"] = s
        out[f"_scan_{key}_ts"] = t
        ran.append(key)
    out["_scans_ran"] = ran
    return out


# ═════════════════════════════════════════════════════════════════════════
# diff — چه چیزِ **مهمی** عوض شد؟ $۰ و قطعی
# ═════════════════════════════════════════════════════════════════════════
#: آستانه‌ها. عددِ کوچک‌تر از این «نوسان» است نه «تغییر» — و مغزی که هر
#: نوسان را حادثه بخواند، همان گاردِ گرگ‌گرگی است که خاموشش می‌کنی.
_THRESH = {"approvals": 1, "stalled_cards": 3, "paid_calls_today": 40,
           "month_aud": 5.0, "beats_spent": 200,
           # خودآگاهی: یک یتیمِ تازه یا یک دروازهٔ تاریکِ تازه خبر است.
           # آستانهٔ ۱ عمدی است — این اعداد آرام حرکت می‌کنند، پس هر
           # حرکتی معنا دارد و رگبار نمی‌سازد.
           "orphans": 1, "weighty": 1, "dark_gates": 1,
           "read_undefined": 5, "dead_symbols": 10, "unfinished": 2}
#: تغییرِ این‌ها همیشه مهم است، هر قدر کوچک.
_ALWAYS = ("halted", "germline_alert", "approvals_status")


def diff(now: dict, before: "dict | None") -> list:
    """فهرستِ تغییرهای مهم. خالی = سکوت = هیچ تماسِ پولی."""
    if not before:
        return [{"key": "first_run", "from": None, "to": None,
                 "why": "اولین بیداری — هنوز حافظه‌ای نیست"}]
    out = []
    for k in _ALWAYS:
        a, b = before.get(k), now.get(k)
        if a != b:
            out.append({"key": k, "from": a, "to": b, "why": "وضعِ باربر عوض شد"})
    for k, th in _THRESH.items():
        a, b = before.get(k), now.get(k)
        if a is None and b is None:
            continue
        # ⚠️ ظهور و ناپدیدشدنِ داده خودش خبر است: «نخواندم» ⇄ «خواندم».
        if (a is None) != (b is None):
            out.append({"key": k, "from": a, "to": b,
                        "why": "دیده‌شدن/گم‌شدنِ منبعِ داده"})
            continue
        try:
            if abs(float(b) - float(a)) >= th:
                out.append({"key": k, "from": a, "to": b,
                            "why": f"تغییرِ بیش از آستانه ({th})"})
        except (TypeError, ValueError):
            if a != b:
                out.append({"key": k, "from": a, "to": b, "why": "مقدار عوض شد"})
    return out


# ═════════════════════════════════════════════════════════════════════════
# memory — ماندگار، و عمداً append-only
# ═════════════════════════════════════════════════════════════════════════
def recall() -> dict:
    """آخرین چیزی که دیدم و آخرین چیزی که گفتم."""
    d = _j(LATEST)
    return d if isinstance(d, dict) else {}


def remember(snapshot: dict, said: "str | None", changes: list,
             paid: bool) -> None:
    """یک ردیفِ ماندگار. ⚠️ هرگز محتوای پرامپت یا کلید ثبت نمی‌شود."""
    try:
        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": snapshot.get("ts"), "changes": changes,
               "said_digest": (said or "")[:200] or None, "paid": bool(paid)}
        with MEMORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        LATEST.write_text(json.dumps(
            {**snapshot, "_said": said, "_paid_ts": (time.time() if paid
                                                     else recall().get("_paid_ts"))},
            ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001 — حافظه هرگز بیداری را نمی‌کشد
        pass


# ═════════════════════════════════════════════════════════════════════════
# سهمیه — مغز نباید ارگانیسم را گرسنه کند
# ═════════════════════════════════════════════════════════════════════════
#: شمارندهٔ **خودِ مغز**، جدا از سهمیهٔ ارگانیسم.
BRAIN_QUOTA = BRAIN_DIR / "calls.json"


def _brain_cap() -> int:
    """سقفِ روزانهٔ تماسِ مغز — **مشتق از سقفِ واقعیِ مشترک**، نه عددِ مستقل.

    ⚠️ بازنویسیِ کامل، ۲۰۲۶-۰۸-۰۵. نسخهٔ قبلی ۳۲۰ برمی‌گرداند و سه ادعا
    داشت که هر سه با شاهدِ زنده غلط از آب درآمد:

      ۱. «سقف ۳۰۰ است» — **غلط**. `OCTOPUS-flags.cmd` مقدارِ
         `FUGU_DAILY_CALL_CAP=60` را ست می‌کند و هر چهار پروسهٔ زنده آن را
         بار کرده‌اند. من فقط `_DEFAULT_CAP = 300` را از کد خواندم و ندیدم
         تولید چه چیزی بار می‌کند — ششمین بارِ همین خطا در یک شب.
      ۲. «مغز به سهمیهٔ Fugu دست نمی‌زند» — **غلط**. `model_router` هر
         تماسِ پولی را از `fugu_quota.reserve` رد می‌کند، رده هرچه باشد.
      ۳. «سقفِ مستقل امن است» — **غلط و خطرناک**. سقفِ ۳۲۰ روی سقفِ مشترکِ
         ۶۰ می‌نشست، پس هرگز نمی‌بست: `fugu_quota` اول می‌بست و **کلِ کارِ
         پولیِ ارگانیسم** را هم با خودش می‌برد.

    عددِ واقعی: دیروز ارگانیسم به‌تنهایی ۵۵ از ۶۰ زد (۹۲٪). پس مغز سهمِ
    کوچکی می‌گیرد و بقیه برای خودِ ارگانیسم می‌ماند.
    """
    try:
        import fugu_quota
        shared = int(fugu_quota._cap())      # noqa: SLF001 — تکِ منبعِ حقیقت
    except Exception:  # noqa: BLE001
        return 0                              # fail-closed: نمی‌دانم ⇒ خرج نکن
    try:
        share = float(os.environ.get("OCTOPUS_BRAIN_CALL_SHARE", "") or 0)
    except (TypeError, ValueError):
        share = 0
    if not (0 < share <= 1):
        share = 0.25
    return max(1, int(shared * share))


def _brain_used(now: "float | None" = None) -> int:
    d = _j(BRAIN_QUOTA) or {}
    today = time.strftime("%Y-%m-%d", time.localtime(now) if now else time.localtime())
    return int(d.get("n") or 0) if str(d.get("day") or "") == today else 0


def _brain_count(now: "float | None" = None) -> None:
    """شمارنده **قبل از** تماس بالا می‌رود — اندپوینتِ خراب هم باید بسوزاند،
    وگرنه یک حلقهٔ شکست بی‌نهایت تماس می‌زند و سقف هرگز نمی‌بندد."""
    try:
        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        today = time.strftime("%Y-%m-%d", time.localtime(now) if now else time.localtime())
        BRAIN_QUOTA.write_text(json.dumps(
            {"day": today, "n": _brain_used(now) + 1}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def may_spend(snapshot: dict, mem: dict, now: "float | None" = None) -> tuple:
    """(اجازه، دلیل). fail-closed: هر ابهامی ⇒ نه.

    سه گارد، به ترتیبِ ارزانی:
      ۱. کفِ فاصله — جلوی رگبارِ ناشی از ری‌استارتِ پیاپی.
      ۲. سقفِ **مستقلِ** مغز (بالا) — نه سهمیهٔ ارگانیسم.
      ۳. کشتارِ صریح، اگر مالک زده باشد. مغز پولی است، پس باید همان
         کلیدِ کشتاری را که بقیهٔ مسیرهای پولی دارند احترام بگذارد.
    """
    t = time.time() if now is None else now
    last = mem.get("_paid_ts")
    if isinstance(last, (int, float)) and (t - last) < MIN_PAID_GAP_S:
        return False, f"کفِ فاصله ({int(MIN_PAID_GAP_S)}s) هنوز نگذشته"
    try:
        import fugu_quota
        if fugu_quota.killed():
            return False, "کلیدِ کشتارِ پولی فعال است"
    except Exception:  # noqa: BLE001
        return False, "گاردِ کشتار در دسترس نیست ⇒ fail-closed"
    used, cap = _brain_used(t), _brain_cap()
    if used >= cap:
        return False, f"سقفِ روزانهٔ مغز تمام شد ({used}/{cap})"
    return True, f"{used}/{cap} تماسِ مغز امروز"


# ═════════════════════════════════════════════════════════════════════════
# tick — یک بیداری
# ═════════════════════════════════════════════════════════════════════════
def tick(state_dir: "Path | None" = None, speak_fn=None,
         think_fn=None) -> dict:
    """یک بیداریِ کامل. خروجی = گزارشِ صادقِ آنچه واقعاً شد.

    `speak_fn`/`think_fn` تزریقی‌اند تا تست هرگز شبکه نزند و هرگز به
    تلگرامِ زنده پیام ندهد.
    """
    snap = observe(state_dir)
    mem = recall()
    # اندام‌های خودآگاهی: هرکدام فقط وقتی فاصله‌اش گذشته باشد می‌دود.
    # روی درختِ تست (state_dir تزریقی) اصلاً نمی‌دود — وگرنه هر تست
    # ۴۶ ثانیه اسکنِ کلِ مخزن می‌شود.
    if state_dir is None:
        try:
            snap.update(self_awareness(mem))
        except Exception as exc:  # noqa: BLE001
            snap["_scans_ran"] = [f"error:{type(exc).__name__}"]
    before = {k: v for k, v in mem.items() if not k.startswith("_")}
    changes = diff(snap, before or None)

    report = {"ts": snap["ts"], "changes": changes, "spoke": False,
              "paid": False, "reason": None}

    if not changes:
        report["reason"] = "هیچ تغییرِ مهمی نبود — سکوت"
        remember(snap, None, [], False)
        return report

    allow, why = may_spend(snap, mem)
    report["quota"] = why
    text = None
    if allow and think_fn is not None:
        try:
            text = think_fn(snap, changes)
            report["paid"] = True
        except Exception as exc:  # noqa: BLE001
            report["reason"] = f"فکرکردن شکست: {type(exc).__name__}"
    if text is None:
        # مسیرِ محلی/رایگان: خودِ تغییرها را به فارسیِ ساده می‌گوید.
        # ⚠️ این fallback عمداً کامل است — اگر مدل هرگز جواب ندهد، مغز
        # همچنان مفید است. قابلیتی که فقط با مدل کار کند، شکننده است.
        text = describe(snap, changes)

    # تکرارِ حرفِ قبلی = سکوت. وگرنه همان کارتِ تکراری ساخته می‌شود که
    # مالک را یک بار به «هیچ‌کس گوش نمی‌دهد» رساند.
    if text and text.strip() == str(mem.get("_said") or "").strip():
        report["reason"] = "همان حرفِ قبلی — دوباره نمی‌گویم"
        remember(snap, mem.get("_said"), changes, report["paid"])
        return report

    if speak_fn is not None and text:
        try:
            speak_fn(text)
            report["spoke"] = True
        except Exception as exc:  # noqa: BLE001
            report["reason"] = f"گفتن شکست: {type(exc).__name__}"
    report["text"] = text
    remember(snap, text, changes, report["paid"])
    return report


_FA = {"orphans": "ماژولِ یتیم", "weighty": "یتیمِ سنگین",
       "dark_gates": "دروازهٔ تاریک", "read_undefined": "فلگِ تعریف‌نشده",
       "dead_symbols": "نمادِ مرده", "unfinished": "کارِ ناتمام",
       "halted": "توقفِ ارگانیسم", "approvals": "صفِ تأیید",
       "approvals_status": "خوانایی صفِ تأیید", "stalled_cards": "کارتِ راکد",
       "paid_calls_today": "تماسِ پولیِ امروز", "month_aud": "خرجِ ماه",
       "beats_spent": "ضربانِ خرج‌شده", "germline_alert": "هشدارِ ژرم‌لاین",
       "first_run": "اولین بیداری"}


def describe(snap: dict, changes: list) -> str:
    """گزارشِ محلیِ $۰ — هر خط با منبعش."""
    lines = ["🧠 چیزی عوض شد:"]
    for c in changes[:5]:
        k = c["key"]
        nm = _FA.get(k, k)
        if k == "first_run":
            lines.append("• اولین بیداری — از حالا تغییرها را دنبال می‌کنم.")
            continue
        a, b = c.get("from"), c.get("to")
        fa = lambda v: "نامعلوم" if v is None else str(v)  # noqa: E731
        lines.append(f"• {nm}: {fa(a)} ← {fa(b)}")
    src = snap.get("sources", {})
    named = [src.get(c["key"]) for c in changes[:3] if src.get(c["key"])]
    if named:
        lines.append("منبع: " + " · ".join(dict.fromkeys(named)))
    return "\n".join(lines)


def think(snapshot: dict, changes: list) -> "str | None":
    """پاسِ پولی — ردهٔ GLM. برمی‌گرداند متن، یا None تا محلی جواب بدهد.

    ⚠️ چه چیزی **نمی‌رود**: هیچ متنِ کارت، هیچ شناسهٔ لید، هیچ مسیرِ فایل،
    هیچ کلید. فقط نامِ سنجه و دو عدد. دلیل: منشور §۱۰، و اینکه این پرامپت
    از مرزِ دستگاه بیرون می‌رود.
    """
    # ── دو سرعته ─────────────────────────────────────────────────────────
    # مالک (۰۸-۰۵): «مدلِ معمولی زود جواب می‌دهد، اولترا دیرتر و بهتر».
    # بیداری هر ۵ دقیقه است، پس مسیرِ عادی **باید** سریع باشد وگرنه
    # بیداری‌ها روی هم می‌افتند و صف می‌شود.
    #
    # و اولترا عمداً خودکار صدا زده نمی‌شود: در `budgets.yaml` نقشِ
    # `premium` (fugu-ultra) صریحاً `human_gated: true` است. پس وقتی چیزی
    # واقعاً سنگین باشد، مغز **پیشنهاد می‌دهد** «می‌خواهی عمیق فکر کنم؟»
    # نه اینکه خودش گران‌ترین مسیر را باز کند. سقفِ خرج تصمیمِ مالک است،
    # نه قضاوتِ لحظه‌ایِ یک دیده‌بان.
    try:
        import model_router
    except Exception:  # noqa: BLE001
        return None
    facts = []
    for c in changes[:6]:
        facts.append(f"{_FA.get(c['key'], c['key'])}: {c.get('from')} -> {c.get('to')}")
    prompt = (
        "وضعِ یک سیستمِ عملیاتی تغییر کرده. تغییرها:\n"
        + "\n".join(facts)
        + "\n\nدر حداکثر سه جملهٔ کوتاهِ فارسی بگو: آیا این مالک را لازم دارد "
          "یا خودش می‌گذرد؟ اگر لازم دارد، دقیقاً چه کاری باید بکند؟ "
          "اگر مطمئن نیستی، بگو نامعلوم — حدس نزن.")
    # ⚠️ شمارنده **قبل از** شبکه بالا می‌رود (همان اصلِ attempt-counted که
    # fugu_quota دارد): اگر بعد از موفقیت بشماریم، یک اندپوینتِ خراب که
    # همیشه استثنا می‌دهد بی‌نهایت تماس می‌زند و سقف هرگز نمی‌بندد.
    _brain_count()
    try:
        res = model_router.ask("summarize", prompt,
                               system="کوتاه، فارسی، بدون تعارف. عدد نساز.",
                               max_tokens=220, tier=BRAIN_TIER)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(res, dict) or not res.get("ok"):
        return None
    # ⚠️ گاردِ فرار به Fugu. `tier="secondary"` یعنی «اول GLM، بعد Fugu»؛
    # `res["tier"]` می‌گوید واقعاً کدام جواب داد. اگر ردهٔ دیگری بود، متن را
    # **دور می‌ریزم** و مغز به گزارشِ محلیِ رایگان می‌افتد.
    # هزینه‌اش یک تماسِ هدررفته است — ولی جایگزینش این بود که هر قطعیِ GLM
    # کلِ دیده‌بانِ ۵ دقیقه‌ای را بی‌صدا روی سهمیهٔ Fugu ببرد.
    used = str(res.get("tier") or "")
    if used and used != BRAIN_TIER:
        try:
            import opslib as _o
            _o.alert([f"cockpit_brain: پاسخ از ردهٔ {used} آمد نه {BRAIN_TIER} — "
                      "دور ریخته شد تا سهمیهٔ Fugu محافظت شود"])
        except Exception:  # noqa: BLE001
            pass
        return None
    txt = str(res.get("text") or "").strip()
    # ⚠️ متنِ خالی با ok=True یک حالتِ واقعیِ دیده‌شده در این مخزن است.
    return ("🧠 " + txt) if txt else None


if __name__ == "__main__":   # پروبِ دستی — هرگز حرف نمی‌زند، هرگز خرج نمی‌کند
    sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[attr-defined]
    r = tick()
    print(json.dumps(r, ensure_ascii=False, indent=2)[:1400])
