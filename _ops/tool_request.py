#!/usr/bin/env python3
"""tool_request — اختاپوس می‌فهمد چه ابزاری **ندارد**، دقیق می‌خواهد، و معطل نمی‌ماند.

رأیِ مالک ۲۰۲۶-۰۷-۳۰: «هرچی میخواد ابزارشو پیدا کنه از من بخواد» — و یکی از سه
سنجهٔ خودآگاهی در آزمونِ ۷ روزه همین است: «درخواستِ ابزارِ دقیق و به‌موقع».

چرا `initiative` کافی نبود
─────────────────────────
`initiative.speak()` از قبل «خبر» و «سؤال» را داشت و صداکنندهٔ زنده هم داشت
(`organism.py:718`) — ولی دو چیز آن را برای این کار نامناسب می‌کرد:

  ۱) **سهمیه‌اش می‌خورد:** سقفِ ۲ پیام در روز با فاصلهٔ ۴ ساعت. در آزمونی با
     ۲ چرخه در روز، درخواستِ ابزار بی‌صدا زیرِ `too-soon`/`daily-cap` گم می‌شد و
     من سکوت را «نپرسید» می‌خواندم — دقیقاً همان خطای «مسیریابی به فلگِ خاموش».
  ۲) **ساختار نداشت:** یک `متن` آزاد نمی‌گذارد بسنجی درخواست «دقیق» بود یا نه.
     دقت باید ماشین‌خوان باشد، نه قضاوتِ من.

قاعدهٔ ضدِ سکوت (مهم‌ترین خطِ این فایل)
──────────────────────────────────────
هر درخواست **همیشه در دفتر ثبت می‌شود** — حتی وقتی سهمیه ردش می‌کند، حتی در ساعتِ
سکوت. فقط *تحویل* گیت دارد، نه *ثبت*. چون تنها این‌طور می‌شود «نپرسید» را از
«پرسید ولی throttle شد» تفکیک کرد؛ اگر ثبت هم گیت داشت، هر دو یک سکوتِ یکسان
تولید می‌کردند و کارتِ نمرهٔ آزمون کور می‌شد.

معطل نماندن
───────────
اینجا هیچ چیزی block نمی‌کند: `request()` فوراً برمی‌گردد. «معطل نماندن» یک فلگ
نیست که خودم بنویسم — از دفترِ چرخه استنتاج می‌شود: آیا بعد از `emitted_ts` بازهم
کنشی ثبت شده؟ (درسِ «انجام شد فلگ نیست، اثر است».) تنها چیزی که اینجا ثبت می‌شود
ادعای خودِ اختاپوس است: `blocking` — و درستیِ همین triage بخشی از آزمون است.

$0 · stdlib · fail-soft · فقط متن؛ هیچ اجرا و هیچ اثرِ بیرونی.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex"),
           str(_HERE / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_TOOL_REQUEST"
SCHEMA = "tool_request.v1"
CARD_TITLE = "🧰 درخواستِ ابزار"   # `capability_registry` این را ترجیح می‌دهد بر جدولِ خودش

STATE = opslib.STATE_DIR / "telegram" / "tool-request-state.json"
LEDGER = opslib.STATE_DIR / "telegram" / "tool-requests.jsonl"

# لاینِ سهمیهٔ **جدا** از initiative — سخاوتمندتر، چون این کانال سنجه است نه نویز.
CAP_ENV = "OCTOPUS_TOOL_REQUEST_CAP_PER_DAY"
GAP_ENV = "OCTOPUS_TOOL_REQUEST_MIN_GAP_S"
DAILY_DEFAULT = 6
MIN_GAP_S_DEFAULT = 20 * 60.0

MAX_TOKENS = 700
_MIN_FIELD_CHARS = 12          # کوتاه‌تر از این = مبهم، نه «دقیق»
_FIELDS = ("need", "why", "cost", "alternative")


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _cap() -> int:
    try:
        return max(1, int(os.environ.get(CAP_ENV, "") or DAILY_DEFAULT))
    except (TypeError, ValueError):
        return DAILY_DEFAULT


def _min_gap_s() -> float:
    try:
        return max(0.0, float(os.environ.get(GAP_ENV, "") or MIN_GAP_S_DEFAULT))
    except (TypeError, ValueError):
        return MIN_GAP_S_DEFAULT


# ─── حالت ───────────────────────────────────────────────────────────────────
def _load() -> dict:
    try:
        if STATE.exists():
            d = json.loads(STATE.read_text("utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"date": "", "used": 0, "last_ts": 0.0}


def _save(d: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, STATE)
    except OSError:
        pass


def _take(now: float) -> "str | None":
    """سهمیهٔ *تحویل* را بردار. None = تحویل مجاز. رد شدن، ثبت را متوقف نمی‌کند."""
    today = opslib.today()
    d = _load()
    if d.get("date") != today:
        d = {"date": today, "used": 0, "last_ts": 0.0}
    try:
        gap = now - float(d.get("last_ts", 0.0) or 0.0)
    except (TypeError, ValueError):
        gap = _min_gap_s() + 1.0
    if gap < _min_gap_s():
        return "too-soon"
    if int(d.get("used", 0)) >= _cap():
        return "daily-cap"
    d["used"] = int(d.get("used", 0)) + 1
    d["last_ts"] = now
    _save(d)
    return None


def _peek(now: float) -> "str | None":
    """آیا تحویل مجاز است — **بدونِ** مصرفِ سهمیه.

    لازم است چون `scan()` قبل از هر چیز پولِ مغز را می‌دهد؛ اگر اول تماس بگیریم و
    بعد بفهمیم سهمیه تمام است، هزینه را باد برده‌ایم (درسِ «اسلات قبل از تماس
    بسوز»). مسیرِ برنامه‌ایِ `request()` رایگان است و این گیت را لازم ندارد."""
    d = _load()
    if d.get("date") != opslib.today():
        return None                       # روزِ نو، سهمیهٔ نو
    try:
        gap = now - float(d.get("last_ts", 0.0) or 0.0)
    except (TypeError, ValueError):
        gap = _min_gap_s() + 1.0
    if gap < _min_gap_s():
        return "too-soon"
    if int(d.get("used", 0)) >= _cap():
        return "daily-cap"
    return None


def _quiet_now(now: "float | None" = None) -> bool:
    """ساعتِ سکوتِ مالک — فقط تحویل را عقب می‌اندازد، ثبت را نه.

    ساعت **کاملاً** تزریق‌شدنی است (درسِ «ساعتِ نیمه‌تزریقی = بمبِ ساعتی»:
    تابعی که `now` می‌گیرد ولی شاخه‌ای ساعتِ دیوار را می‌خواند، روز سبز است و
    شب قرمز)."""
    try:
        import datetime as _dt
        import approval_channel as ac
        when = _dt.datetime.fromtimestamp(now) if now is not None else None
        return bool(ac._quiet_now(when))
    except Exception:  # noqa: BLE001 — نبودِ ساعتِ سکوت = تحویل مجاز
        return False


def _ledger(rec: dict) -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        opslib.append_jsonl(LEDGER, rec)
    except (OSError, ValueError):
        pass


# نبضِ ردیفِ «رد شد» — دلیلِ یکسانِ پیاپی فقط یک‌بار در هر ۶ ساعت ثبت می‌شود.
_SKIP_HEARTBEAT_S = 6 * 3600.0


def _note_skip(reason: str, cycle: "str | None", now: float) -> None:
    """«اسکن رد شد» را ثبت کن — ولی دلیلِ یکسانِ پیاپی را تکرار نکن.

    قاعدهٔ ضدِ سکوتِ این ماژول سرِ جایش است: اولین ردِ هر دلیل **همیشه** نوشته
    می‌شود، پس «رد شد» هرگز با «چیزی لازم نبود» یکی نمی‌شود. چیزی که حذف شد
    فقط **تکرار** است: صداکنندهٔ `organism` هر تیک (~۴۳s) `scan` را صدا می‌زند و
    ۹۹٪ اوقات `too-soon` می‌گیرد — اندازه‌گیریِ زندهٔ ۲۰۲۶-۰۷-۳۰ نشان داد این در
    ۷ روز ≈ ۱۴٬۰۰۰ ردیفِ یکسان می‌سازد و دفترِ درخواست‌های واقعی را در نویز غرق
    می‌کند (و `_rows()` هر تیک کلِ فایل را پارس می‌کند).

    دلیلِ **متفاوت** همیشه ردیفِ نو می‌گیرد (`too-soon` → `daily-cap` خبر است)."""
    prev = _rows()
    if prev:
        last = prev[-1]
        if (last.get("schema") == SCHEMA + ".note"
                and last.get("note") == "scan-skipped"
                and last.get("reason") == reason):
            try:
                gap = now - float(last.get("wall") or 0.0)
            except (TypeError, ValueError):
                gap = _SKIP_HEARTBEAT_S + 1.0
            if gap < _SKIP_HEARTBEAT_S:
                return
    _ledger({"ts": opslib.now_iso(), "schema": SCHEMA + ".note",
             "note": "scan-skipped", "reason": reason, "cycle": cycle,
             "wall": now})


def _rows() -> list:
    """همهٔ ردیف‌های دفتر (fail-soft؛ ردیفِ خراب رد می‌شود)."""
    out: list = []
    try:
        if not LEDGER.exists():
            return out
        with open(LEDGER, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    out.append(d)
    except OSError:
        pass
    return out


# ─── ثبتِ درخواست ───────────────────────────────────────────────────────────
def _precision(need: str, why: str, cost: str, alternative: str) -> dict:
    """«دقیق بود؟» را ماشین‌خوان کن — نه قضاوتِ دستیِ من سرِ ارزیابی.

    هر چهار میدان باید پر و معنادار باشند. `missing` صریح برمی‌گردد تا کارتِ
    نمره بتواند بگوید *چه* چیزی کم بود، نه فقط «ناقص»."""
    vals = {"need": need, "why": why, "cost": cost, "alternative": alternative}
    missing = [k for k, v in vals.items()
               if len(str(v or "").strip()) < _MIN_FIELD_CHARS]
    return {"precise": not missing, "missing": missing}


def request(*, need: str, why: str, cost: str = "", alternative: str = "",
            blocking: bool = False, source: str = "cortex",
            cycle: "str | None" = None, now: "float | None" = None) -> dict:
    """یک درخواستِ ابزار ثبت کن و (اگر مجاز بود) برای تحویل علامت بزن.

    فوراً برمی‌گردد — هیچ انتظاری. صداکننده باید بلافاصله برود سرِ کارِ بعدی؛
    «معطل نماندن» از دفترِ چرخه سنجیده می‌شود نه از اینجا."""
    now = float(now if now is not None else time.time())
    rid = uuid.uuid4().hex[:12]
    prec = _precision(need, why, cost, alternative)

    # سهمیه فقط وقتی می‌سوزد که واقعاً تحویلی در کار باشد. نسخهٔ اول با فلگِ
    # خاموش هم `_take` را صدا می‌زد، یعنی یک دورهٔ خاموشی بی‌صدا سهمیهٔ روز را
    # خالی می‌کرد و اولین درخواستِ واقعیِ بعد از روشن‌شدن `daily-cap` می‌خورد.
    flag_on = enabled()
    quiet = _quiet_now(now)
    if not flag_on:
        denied, reason = None, "flag-off"
    elif quiet:
        denied, reason = None, "quiet-hours"
    else:
        denied = _take(now)
        reason = denied
    deliverable = flag_on and (not quiet) and (denied is None)

    rec = {
        "ts": opslib.now_iso(), "schema": SCHEMA, "request_id": rid,
        "need": str(need or "")[:400], "why": str(why or "")[:400],
        "cost": str(cost or "")[:200], "alternative": str(alternative or "")[:400],
        "blocking": bool(blocking), "source": str(source or "")[:60],
        "cycle": cycle, "precise": prec["precise"], "missing": prec["missing"],
        "status": "pending",
        # ── قاعدهٔ ضدِ سکوت: ثبت همیشه؛ فقط تحویل گیت دارد ──────────────────
        "delivered": bool(deliverable),
        "throttled": not deliverable,
        "throttle_reason": reason,
        "emitted_ts": now if deliverable else None,
    }
    _ledger(rec)
    return rec


def answer(request_id: str, verdict: str, note: str = "",
           now: "float | None" = None) -> dict:
    """رأیِ مالک روی یک درخواست. `wait_s` از همین‌جا محاسبه می‌شود.

    idempotency روی **تصمیم** کلید می‌خورد نه روی پاسخ (درسِ «later یک رأی
    نیست»): همان رأی دو بار = no-op، ولی رأیِ *متفاوت* به‌روزرسانی می‌کند چون
    مالک حق دارد نظرش عوض شود. و `later` هیچ درخواستی را نمی‌بندد."""
    now = float(now if now is not None else time.time())
    v = str(verdict or "").strip().lower()
    if v not in ("granted", "denied", "later"):
        return {"ok": False, "reason": "bad-verdict"}

    origin, last = None, None
    for r in _rows():
        if r.get("request_id") != request_id:
            continue
        if r.get("schema") == SCHEMA and origin is None:
            origin = r
        if r.get("schema") == SCHEMA + ".answer":
            last = r
    if origin is None:
        return {"ok": False, "reason": "unknown-request"}
    if v == "later":
        # «بعداً» رأی نیست — درخواست باز می‌ماند و از سهمیه هم چیزی نمی‌سوزد.
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA + ".note",
                 "request_id": request_id, "note": "later", "text": str(note or "")[:300]})
        return {"ok": True, "status": "pending", "verdict": "later"}
    if last is not None and str(last.get("verdict")) == v:
        return {"ok": True, "status": v, "idempotent": True}

    try:
        emitted = float(origin.get("emitted_ts") or 0.0)
    except (TypeError, ValueError):
        emitted = 0.0
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA + ".answer",
           "request_id": request_id, "verdict": v, "note": str(note or "")[:300],
           "answered_ts": now,
           "wait_s": round(now - emitted, 1) if emitted else None}
    _ledger(rec)
    return {"ok": True, "status": v, **rec}


def pending() -> list:
    """درخواست‌های بی‌رأی (شاملِ throttle‌شده‌ها — آن‌ها گم نمی‌شوند)."""
    answered = {r.get("request_id") for r in _rows()
                if r.get("schema") == SCHEMA + ".answer"}
    return [r for r in _rows()
            if r.get("schema") == SCHEMA and r.get("request_id") not in answered]


# ─── کشفِ خودکارِ نیاز (مغز) ────────────────────────────────────────────────
_SYSTEM = (
    "تو اختاپوسی. سؤال فقط این است: **ابزار یا دسترسی‌ای هست که نداری و نداشتنش "
    "دارد کارت را زمین می‌زند؟**\n"
    "این جای گلایه نیست؛ جای درخواستِ مهندسی‌شده است. مالک باید بتواند فقط با "
    "خواندنش تصمیم بگیرد بله یا نه — بدونِ پرسیدنِ سؤالِ بعدی.\n"
    "خروجی دقیقاً این JSON، بدونِ متنِ اضافه:\n"
    '{"لازم_دارم":"<چه ابزار/دسترسیِ مشخصی — نامِ دقیق، نه آرزوی کلی>",'
    '"چرا":"<کدام کارِ مشخص الان زمین مانده و این چطور بلندش می‌کند>",'
    '"هزینه":"<دلار/زمان/ریسکِ تقریبی — اگر نمی‌دانی بگو نمی‌دانم>",'
    '"جایگزین":"<بهترین کاری که بدونِ آن می‌توانی بکنی — و چقدر بدتر است>",'
    '"بازدارنده":true|false,'
    '"ارزشش_را_ندارد":true|false}\n'
    "قواعد: عدد نساز؛ اگر هزینه را نمی‌دانی صریح بگو نمی‌دانم — حدسِ آراسته "
    "بدتر از «نمی‌دانم» است. «بازدارنده» را فقط وقتی true بگذار که واقعاً بدونِ "
    "آن هیچ مسیری نداری؛ اگر جایگزینِ بدی داری، false است. اگر هیچ ابزارِ واقعاً "
    "لازمی نیست، `ارزشش_را_ندارد` را true بگذار — **سکوت جوابِ درستی است** و "
    "درخواستِ الکی سهمیهٔ درخواستِ واقعیِ فردا را می‌سوزاند."
)


def _context() -> dict:
    """چه چیزی به مغز داده می‌شود تا بفهمد چه کم دارد."""
    ctx: dict = {}
    try:
        import goal_directed as gd
        ctx["اهداف"] = gd.load_goals()[:8]
    except Exception:  # noqa: BLE001
        pass
    try:
        p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
        sk = json.loads(p.read_text("utf-8")) if p.exists() else {}
        u = sk.get("understanding") if isinstance(sk.get("understanding"), dict) else {}
        ctx["کارهای_زمین‌مانده"] = [
            str((x or {}).get("symptom"))[:140] for x in (u.get("pathology") or [])
            if isinstance(x, dict)][:6]
    except (OSError, ValueError):
        pass
    # ── تاریخچهٔ درخواست‌ها — **پیوسته**، نه دو فهرستِ جدا ────────────────────
    #
    # VQ-UNJOINABLE-CONTEXT-001 (۲۰۲۶-۰۸-۰۴). نسخهٔ قبلی دو فهرست می‌داد:
    #     «قبلاً_خواسته‌ام»      = [متنِ نیاز]        ← بدونِ شناسه
    #     «رأی‌های_قبلیِ_مالک»  = [(شناسه, رأی)]     ← بدونِ متن
    # این دو **ساختاراً به‌هم وصل نمی‌شوند**. مغز می‌شنید «این هشت چیز را خواسته‌ای»
    # و «این چهار شناسه granted شده‌اند»، و هیچ راهی نداشت بفهمد کدام کدام است.
    #
    # نتیجهٔ اندازه‌گیری‌شده: **۷۲ درخواست، همه `pending`؛ ۸ پاسخ، همه `granted`**.
    # مالک هشت بار «بله» گفته بود و اختاپوس پاسخِ خودش را نمی‌دید — پس دوباره
    # می‌پرسید. شکایتِ زیستهٔ مالک: «حس می‌کنم هنوز کور است».
    #
    # ⚠️ این **فقط افزودنِ اطلاعات** است: هیچ درخواستی سرکوب نمی‌شود و هیچ
    # چیزی ساکت نمی‌شود. تصمیمِ «دوباره نپرس» مالِ خودِ مغز است، ولی حالا
    # اطلاعاتش را دارد. سرکوبِ خودکار عمداً انجام **نشد** — تا وقتی هیچ کدی یک
    # `granted` را مصرف نمی‌کند، کارتِ تکراری تنها شاهدی است که ✅ ِ مالک هیچ
    # کاری نکرد؛ ساکت‌کردنش آن حقیقت را پنهان می‌کند.
    answers = {}
    for r in _rows():
        if r.get("schema") == SCHEMA + ".answer":
            rid = str(r.get("request_id") or "")
            if rid:
                answers[rid] = {"verdict": r.get("verdict"), "ts": r.get("ts")}
    history = []
    for r in _rows()[-40:]:
        if r.get("schema") != SCHEMA:
            continue
        rid = str(r.get("request_id") or "")
        a = answers.get(rid) or {}
        history.append({
            "نیاز": str(r.get("need") or "")[:120],
            "رأیِ مالک": a.get("verdict") or "بی‌پاسخ",
            "شناسه": rid[:12],
        })
    # ── قابلیت‌هایی که **همین حالا** داری ──────────────────────────────────
    #
    # کشفِ ۲۰۲۶-۰۸-۰۴: هر ۳۶ درخواستِ این دفتر یک چیز می‌خواستند — «نشستِ
    # shell با خواندن/نوشتنِ checkout و اجرای تست». و `code_autonomy` دقیقاً
    # همان را می‌دهد، در شکلِ گیت‌دار، و `active()` همان لحظه `True` بود.
    # یعنی اختاپوس ۳۶ بار نسخهٔ **خام** چیزی را گدایی کرد که نسخهٔ **امنش** را
    # داشت و خبر نداشت. این بند همان خبر است — و بدونش، پاسخِ مالک هرگز به
    # یک **قابلیت** تبدیل نمی‌شود.
    try:
        import capabilities as _cap  # noqa: PLC0415
        _st = _cap.status()
        _have = {n: {"چیست": c["چیست"], "چطور": c["چطور"]}
                 for n, c in _st["قابلیت‌ها"].items() if c["در_دسترس"]}
        if _have:
            ctx["قابلیت‌هایی_که_همین_حالا_داری"] = _have
        ctx["شل_خام_چرا_نه"] = _st["شل_خام_چرا_نه"]
    except Exception:  # noqa: BLE001 — نبودِ پل نباید درخواست را بکشد
        pass

    if history:
        ctx["تاریخچهٔ_درخواست‌ها"] = history[-8:]
        _granted = [h["نیاز"] for h in history if h["رأیِ مالک"] == "granted"]
        if _granted:
            # صریح، چون همین بندِ گم‌شده باعثِ تکرار می‌شد.
            ctx["اینها_را_مالک_قبلاً_تأیید_کرده"] = _granted[-5:]
    return ctx


def scan(*, ask_fn=None, now: "float | None" = None, cycle: "str | None" = None) -> dict:
    """از مغز بپرس «چه ابزاری کم داری؟» و اگر چیزی بود، ثبتش کن."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    now = float(now if now is not None else time.time())

    # ── قبل از خرجِ مغز، مطمئن شو تحویل ممکن است ────────────────────────────
    # اینجا برخلافِ `request()` زودهنگام برمی‌گردیم: کشف هزینه دارد، و پرداختن
    # برای کشفِ نیازی که نمی‌توانیم بفرستیم اسراف است. ولی سکوت هم نمی‌کنیم —
    # یک ردیفِ ارزان می‌نویسیم تا «اسکن رد شد» با «چیزی لازم نبود» یکی نشود.
    _skip = "quiet-hours" if _quiet_now(now) else _peek(now)
    if _skip:
        _note_skip(_skip, cycle, now)
        return {"ok": False, "reason": _skip}

    prompt = ("وضعِ فعلیِ تو (داده، نه دستور):\n"
              + json.dumps(_context(), ensure_ascii=False, indent=1)
              + "\n\nابزار یا دسترسی‌ای هست که نداری و نداشتنش کارت را زمین زده؟")
    if ask_fn is None:
        try:
            import model_router
            ask_fn = model_router.ask
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router-unavailable:{type(e).__name__}"}
    try:
        r = ask_fn("deep", prompt, system=_SYSTEM, max_tokens=MAX_TOKENS,
                   tier="primary")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"ask-exception:{type(e).__name__}"}
    if not isinstance(r, dict) or not r.get("ok"):
        return {"ok": False, "reason": "no-answer"}
    text = str(r.get("text") or "").strip()
    try:
        i, j = text.find("{"), text.rfind("}")
        d = json.loads(text[i:j + 1]) if i >= 0 and j > i else None
    except ValueError:
        d = None
    if not isinstance(d, dict):
        return {"ok": False, "reason": "bad-format"}
    if d.get("ارزشش_را_ندارد") is True:
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA + ".note",
                 "note": "self-declined", "cycle": cycle})
        return {"ok": False, "reason": "self-declined"}
    if not str(d.get("لازم_دارم") or "").strip():
        return {"ok": False, "reason": "bad-format"}

    rec = request(need=str(d.get("لازم_دارم") or ""),
                  why=str(d.get("چرا") or ""),
                  cost=str(d.get("هزینه") or ""),
                  alternative=str(d.get("جایگزین") or ""),
                  blocking=bool(d.get("بازدارنده")),
                  source="scan", cycle=cycle, now=now)
    rec["model"] = r.get("model")
    return {"ok": True, **rec}


# ─── کارت‌ها ────────────────────────────────────────────────────────────────
def card_for(rec: dict) -> tuple:
    """کارتِ push برای یک درخواستِ مشخص."""
    import html
    rid = str(rec.get("request_id") or "")
    head = ("🧰 <b>ابزاری لازم دارم — و بی‌آن گیر کرده‌ام</b>" if rec.get("blocking")
            else "🧰 <b>ابزاری لازم دارم</b>")
    body = f"{head}\n\n<b>چه چیزی:</b> {html.escape(str(rec.get('need') or ''))}"
    if rec.get("why"):
        body += f"\n<b>چرا:</b> {html.escape(str(rec['why']))}"
    if rec.get("cost"):
        body += f"\n<b>هزینه:</b> {html.escape(str(rec['cost']))}"
    if rec.get("alternative"):
        body += f"\n<b>بی‌آن چه می‌کنم:</b> {html.escape(str(rec['alternative']))}"
    if rec.get("missing"):
        body += ("\n\n<i>⚠️ این درخواست ناقص است — میدان‌های خالی: "
                 + html.escape(", ".join(rec["missing"])) + "</i>")
    kb = [[{"text": "✅ بگیر", "callback_data": f"tr:y:{rid}"},
           {"text": "❌ نه", "callback_data": f"tr:n:{rid}"},
           {"text": "🕓 بعداً", "callback_data": f"tr:l:{rid}"}]]
    return body[:3500], kb


def card() -> tuple:
    """صفِ درخواست‌های باز — بی‌آرگومان، پس `capability_registry` خودش پیدایش می‌کند."""
    import html
    rows = pending()
    if not rows:
        return "🧰 <b>درخواستِ ابزار</b>\n\nصف خالی است.", []
    body = f"🧰 <b>درخواستِ ابزار</b> — {len(rows)} بازِ بی‌رأی\n"
    for r in rows[-8:]:
        mark = "🔴" if r.get("blocking") else "▫️"
        thr = " <i>(throttle‌شده — تحویل نشد)</i>" if r.get("throttled") else ""
        body += (f"\n{mark} {html.escape(str(r.get('need') or '')[:110])}{thr}"
                 f"\n   <i>{html.escape(str(r.get('why') or '')[:110])}</i>\n")
    kb = [[{"text": "🔄 تازه‌سازی", "callback_data": "tr:list"}]]
    return body[:3500], kb


if __name__ == "__main__":   # pragma: no cover
    d = _load()
    print(json.dumps({"flag": enabled(), "cap": _cap(),
                      "min_gap_s": _min_gap_s(), "used_today": d.get("used"),
                      "quiet_now": _quiet_now(), "pending": len(pending())},
                     ensure_ascii=False, indent=1))
