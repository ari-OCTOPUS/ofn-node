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
#: سهمِ مغز از سقفِ روزانهٔ تماسِ پولی.
#:
#: ⚠️ عددِ باربر، و امروز **موقت** است. رأیِ مالک (۰۸-۰۵): «واقعاً هر بیداری
#: یک تماس — سقف را بالا ببر». بیداریِ ۵ دقیقه‌ای = ۲۸۸ تماس در روز، و
#: ارگانیسم خودش ۵۵–۶۰ تا دارد ⇒ سقفِ لازم ~۳۵۰–۴۰۰.
#: ولی سقفِ **واقعیِ** پلنِ MAX از کد قابلِ فهم نیست (`_DEFAULT_CAP = 300` در
#: `fugu_quota.py` صریحاً «حدس، بعد از متری‌گیری کالیبره شود» است). مالک
#: داشبوردِ Sakana را نگاه می‌کند و عدد را می‌دهد. تا آن روز، این عدد
#: محافظه‌کارانه می‌ماند و تنزل **صدادار** است نه بی‌صدا.
#:
#: تنظیم: `OCTOPUS_BRAIN_CALL_SHARE` (کسر از سقفِ روزانه).
#: سقفِ کل: `FUGU_DAILY_CALL_CAP` — همان knob ِ موجودِ fugu_quota.
def _share() -> float:
    try:
        v = float(os.environ.get("OCTOPUS_BRAIN_CALL_SHARE", "") or 0)
        return v if 0 < v <= 1 else 0.6
    except (TypeError, ValueError):
        return 0.6


#: کفِ فاصلهٔ دو تماسِ پولی. با ریتمِ ۵ دقیقه‌ای و رأیِ «هر بیداری»، این
#: عدد کمی **زیرِ** ۵ دقیقه است تا جلوی بیداریِ عادی را نگیرد و فقط جلوی
#: رگبارِ ناشی از ری‌استارتِ پیاپی را بگیرد.
MIN_PAID_GAP_S = 240.0
#: ردهٔ مدل — رأیِ مالک (۰۸-۰۵): GLM. مغزِ اصلی (Fugu) برای کارهای سنگینِ
#: خودِ ارگانیسم آزاد می‌ماند.
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
# diff — چه چیزِ **مهمی** عوض شد؟ $۰ و قطعی
# ═════════════════════════════════════════════════════════════════════════
#: آستانه‌ها. عددِ کوچک‌تر از این «نوسان» است نه «تغییر» — و مغزی که هر
#: نوسان را حادثه بخواند، همان گاردِ گرگ‌گرگی است که خاموشش می‌کنی.
_THRESH = {"approvals": 1, "stalled_cards": 3, "paid_calls_today": 40,
           "month_aud": 5.0, "beats_spent": 200}
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
def may_spend(snapshot: dict, mem: dict, now: "float | None" = None) -> tuple:
    """(اجازه، دلیل). fail-closed: هر ابهامی ⇒ نه.

    سه گارد، به ترتیبِ ارزانی:
      ۱. کفِ فاصله — حتی وقتی همه‌چیز عوض شود، رگبار نه.
      ۲. سهمِ مغز از سقفِ روزانه (پیش‌فرض ۲۵٪).
      ۳. کشتارِ صریحِ Fugu، اگر مالک زده باشد.
    """
    t = time.time() if now is None else now
    last = mem.get("_paid_ts")
    if isinstance(last, (int, float)) and (t - last) < MIN_PAID_GAP_S:
        return False, f"کفِ فاصله ({int(MIN_PAID_GAP_S)}s) هنوز نگذشته"
    try:
        import fugu_quota
        if fugu_quota.killed():
            return False, "کشتارِ Fugu فعال است"
        cap = fugu_quota._cap()          # noqa: SLF001 — تکِ منبعِ حقیقتِ سقف
    except Exception:  # noqa: BLE001
        return False, "گاردِ سهمیه در دسترس نیست ⇒ fail-closed"
    used = snapshot.get("paid_calls_today")
    if used is None:
        return False, "مصرفِ امروز خوانده نشد ⇒ fail-closed"
    share = int(cap * _share())
    if used >= share:
        return False, f"سهمِ مغز تمام شد ({used}/{share} از سقفِ {cap})"
    return True, f"{used}/{share} از سهمِ مغز"


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


_FA = {"halted": "توقفِ ارگانیسم", "approvals": "صفِ تأیید",
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
    try:
        res = model_router.ask("summarize", prompt,
                               system="کوتاه، فارسی، بدون تعارف. عدد نساز.",
                               max_tokens=220, tier=BRAIN_TIER)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(res, dict) or not res.get("ok"):
        return None
    txt = str(res.get("text") or "").strip()
    # ⚠️ متنِ خالی با ok=True یک حالتِ واقعیِ دیده‌شده در این مخزن است.
    return ("🧠 " + txt) if txt else None


if __name__ == "__main__":   # پروبِ دستی — هرگز حرف نمی‌زند، هرگز خرج نمی‌کند
    sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[attr-defined]
    r = tick()
    print(json.dumps(r, ensure_ascii=False, indent=2)[:1400])
