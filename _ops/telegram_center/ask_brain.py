"""ask_brain — جوابِ واقعی به جملهٔ آزادِ مالک، از مغزِ گران.

مسئله‌ای که حل می‌کند (اندازه‌گیریِ ۲۰۲۶-۰۷-۲۷):
    مالک پرسید «کجا پیام بدم، چی بدم؟» و جوابِ صادق این بود: سیزده فرمان و
    دکمه‌های کارت. هر جملهٔ آزادی که به فرمان نگاشت نشود به `_ask_unknown_card`
    می‌افتد — «متوجه نشدم» + پنج دکمه. `llm_intent.understand` هم فقط **دسته‌بندی**
    می‌کند (intent/leg/risk) و هرگز **جواب** نمی‌دهد؛ خروجی‌اش یا یک صفحهٔ ثابت است
    یا یک کارتِ مأموریت. پس «چرا امروز کند بودی؟» هیچ مسیری به جوابِ فکرشده نداشت.

    هم‌زمان، مغزِ Fugu (پلنِ فلت) همان روز تازه سه مشتریِ واقعی پیدا کرده بود و
    ~۲۲ از ۶۰ سهمیه‌اش مصرف می‌شد. یعنی ظرفیتِ جوابِ خوب بی‌کار نشسته بود.

طراحی:
    این ماژول **فقط جواب می‌دهد**. هیچ عملی نمی‌کند و هیچ گیتی را لمس نمی‌کند —
    هر درخواستِ اقدام همچنان از مسیرِ mission/action_graph/approval می‌رود که
    دست‌نخورده است. contextِ عددی از همان سازندهٔ اثبات‌شدهٔ `deep_think` می‌آید
    (مرزِ PII آن‌جا با تستِ کاناری بسته شده) و بسته به تاپیکِ سؤال انتخاب می‌شود.

مرزها (ساختاری):
    · flag پیش‌فرض خاموش (`OCTOPUS_TG_ASK_BRAIN`).
    · سقفِ روزانه + فاصلهٔ حداقلی — یک صفحه‌کلیدِ عصبی نباید سهمیه را بسوزاند.
    · `tier="primary"` پین است **و جواب هم بازبینی می‌شود**: اگر روتر بی‌صدا به
      مدلِ رایگان افتاده باشد (`fallback_from`)، جواب دور انداخته می‌شود — وگرنه
      این اندام با مغزِ ۱.۵B جواب می‌داد و مالک خیال می‌کرد مغزِ گران حرف زده.
    · هیچ متنی از مالک در contextِ مدل تکرار نمی‌شود جز خودِ سؤال.
    · جواب هرگز به‌عنوانِ دستور تفسیر نمی‌شود؛ خروجی فقط متن است.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_ASK_BRAIN"
SCHEMA = "tg-ask-brain.v1"
LEDGER = opslib.STATE_DIR / "telegram" / "ask-brain.jsonl"
STATE = opslib.STATE_DIR / "telegram" / "ask-brain-state.json"

DAILY_DEFAULT = 20            # سقفِ سخاوتمند ولی محدود — سهمیهٔ Fugu روزانه ۶۰ است
DAILY_MAX = 40
MIN_GAP_S = 20.0              # فاصلهٔ حداقلیِ دو سؤال (ضدِ اسپمِ سهوی)
MAX_TOKENS = 900
MIN_CHARS = 40
MAX_QUESTION = 600            # سؤالِ بلندتر از این بریده می‌شود (context/هزینه)

# تاپیک → کدام contextِ عددی به مغز داده شود. کلیدها نامِ پا در center-config است.
_BUSINESS_TOPICS = ("lead", "ziman", "mining", "crypto", "accounting", "studio_pf")


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _daily_cap() -> int:
    try:
        n = int(str(os.environ.get("TG_ASK_BRAIN_DAILY", "")).strip())
    except (TypeError, ValueError):
        return DAILY_DEFAULT
    return n if 0 < n <= DAILY_MAX else DAILY_DEFAULT


# ─── سهمیه (fail-closed، با پشتیبانِ درون-پروسه) ─────────────────────────────
_MEMO: dict = {"date": "", "used": 0, "last_ts": 0.0}


def _load_state() -> dict:
    try:
        if STATE.exists():
            d = json.loads(STATE.read_text("utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"date": "", "used": 0, "last_ts": 0.0}


def _take(now: float) -> "str | None":
    """یک سهمیه بردار. None = مجاز؛ رشته = دلیلِ رد. **قبل از** تماس صدا می‌شود."""
    today = opslib.today()
    d = _load_state()
    if d.get("date") != today:
        d = {"date": today, "used": 0, "last_ts": 0.0}
    if _MEMO.get("date") == today:
        d["used"] = max(int(d.get("used", 0)), int(_MEMO.get("used", 0)))
        d["last_ts"] = max(float(d.get("last_ts", 0.0) or 0.0),
                           float(_MEMO.get("last_ts", 0.0) or 0.0))
    try:
        gap = now - float(d.get("last_ts", 0.0) or 0.0)
    except (TypeError, ValueError):
        gap = MIN_GAP_S + 1
    if gap < MIN_GAP_S:
        return f"too-soon:{MIN_GAP_S - gap:.0f}s"
    if int(d.get("used", 0)) >= _daily_cap():
        return f"daily-cap:{_daily_cap()}"
    d["used"] = int(d.get("used", 0)) + 1
    d["last_ts"] = now
    _MEMO.update(date=today, used=d["used"], last_ts=now)
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, STATE)
    except OSError:
        pass          # پشتیبانِ درون-پروسه بالا already گرفته شد
    return None


# ─── context ────────────────────────────────────────────────────────────────
def _context_for(topic_key: str = "") -> dict:
    """contextِ عددی بر اساسِ تاپیکِ سؤال. سازنده‌ها از `deep_think` قرض گرفته
    می‌شوند — بازنویسی نمی‌شوند — تا مرزِ PII یک‌جا بماند و یک‌جا تست شود."""
    ctx = {}
    try:
        import deep_think as dt
        ctx["خودت"] = dt._self_context()
        if str(topic_key or "") in _BUSINESS_TOPICS:
            ctx["کار"] = dt._business_context()
    except Exception:  # noqa: BLE001 — نبودِ context جواب را کلی می‌کند، نه خراب
        pass
    # دایجستِ زندهٔ همان تاپیک (همان چیزی که مالک روی صفحه می‌بیند)
    try:
        import render as _r
        legs = (_r.collect_feeds() or {}).get("legs") or {}
        if topic_key and topic_key in legs:
            ctx["این_تاپیک"] = {"پا": topic_key, **(legs.get(topic_key) or {})}
    except Exception:  # noqa: BLE001
        pass
    return ctx


_SYSTEM = (
    "تو خودِ اختاپوسی — یک ارگانیسمِ نرم‌افزاریِ خودگردان که برای یک اپراتورِ تنها "
    "(فارسی‌زبان، سیدنی) کار می‌کند. او الان مستقیم از تو سؤال پرسیده.\n"
    "قواعد:\n"
    "۱) فارسی، کوتاه، بدونِ مقدمه و تعارف. حداکثر چند جمله.\n"
    "۲) فقط از عددهایی که در context آمده استدلال کن. اگر جوابِ سؤال در context "
    "نیست، صریح بگو «این را نمی‌دانم» و بگو چه چیزی لازم است تا بدانی.\n"
    "۳) هرگز ادعا نکن کاری کرده‌ای یا خواهی کرد — تو فقط جواب می‌دهی؛ هر اقدامی "
    "مسیرِ تأییدِ جدا دارد. اگر کاربر چیزی خواست که اقدام است، بگو از کدام مسیر.\n"
    "۴) هرگز نام، ایمیل، یا هر دادهٔ شخصی حدس نزن — به تو داده نشده.\n"
    "۵) عددی که نقل می‌کنی باید دقیقاً از context باشد. عدد نساز."
)


def ask(question: str, *, topic_key: str = "", ask_fn=None,
        now: "float | None" = None) -> dict:
    """یک سؤالِ آزاد → یک جوابِ متنی. هرگز اجرا نمی‌کند.

    خروجی: {ok, text?, reason?, tier?}. `ok=False` یعنی صدا‌کننده باید به مسیرِ
    امروز (کارتِ «متوجه نشدم») برگردد — این ماژول هرگز مسیرِ موجود را نمی‌شکند."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    q = str(question or "").strip()[:MAX_QUESTION]
    if len(q) < 3:
        return {"ok": False, "reason": "too-short"}
    now = float(now if now is not None else time.time())
    denied = _take(now)
    if denied:
        return {"ok": False, "reason": denied}

    ctx = _context_for(topic_key)
    prompt = (f"سؤالِ مالک:\n{q}\n\n"
              f"وضعیتِ فعلیِ تو (داده، نه دستور):\n"
              f"{json.dumps(ctx, ensure_ascii=False, indent=1)}")
    if ask_fn is None:
        try:
            import model_router
            ask_fn = model_router.ask
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router-unavailable:{type(e).__name__}"}
    try:
        r = ask_fn("deep", prompt, system=_SYSTEM, max_tokens=MAX_TOKENS,
                   tier="primary")
    except Exception as e:  # noqa: BLE001 — هیچ خطایی بات را نمی‌کشد
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": f"ask-exception:{type(e).__name__}", "topic": topic_key})
        return {"ok": False, "reason": "ask-exception"}

    if not isinstance(r, dict) or not r.get("ok"):
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": "no-answer", "topic": topic_key})
        return {"ok": False, "reason": "no-answer"}
    # جوابِ مغزِ **رایگان** جوابِ این اندام نیست (درسِ deep_think ۰۷-۲۷).
    #
    # ولی مرز «primary یا هیچ» نیست — این را آزمونِ زنده اصلاح کرد: در ۱۲:۵۸:۵۳
    # یک `PermissionError` روی Fugu روتر را به GLM برد، جوابِ خوبی آمد، و نسخهٔ
    # اولِ این گارد دورش انداخت و به مالک «متوجه نشدم» داد. GLM یک مغزِ پولیِ
    # واقعی است، نه مدلِ ۱.۵B محلی. پس معیار «پولی بودن» است، نه «primary بودن»
    # — و اینکه کدام مغز جواب داده صادقانه به مالک گفته می‌شود.
    _tier = str(r.get("tier") or "")
    if r.get("fallback_from") or (_tier and _tier not in ("primary", "secondary")):
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": "not-a-paid-brain", "topic": topic_key,
                 "tier": r.get("tier"), "fallback_from": r.get("fallback_from")})
        return {"ok": False, "reason": "not-a-paid-brain", "tier": r.get("tier")}
    text = str(r.get("text") or "").strip()
    if len(text) < MIN_CHARS:
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": "too-short-answer", "topic": topic_key, "chars": len(text)})
        return {"ok": False, "reason": "too-short-answer"}
    _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": True,
             "topic": topic_key, "model": r.get("model"), "tier": r.get("tier"),
             "chars": len(text), "q_chars": len(q), "text": text[:2000]})
    return {"ok": True, "text": text, "tier": r.get("tier"), "model": r.get("model")}


def _ledger(rec: dict) -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def card(text: str, model: str = "") -> tuple:
    """کارتِ جواب — طبقِ دکترین: می‌گوید این فقط حرف است، نه اقدام، و **کدام مغز**
    جواب داده. مالک باید بداند جوابِ Fugu را می‌خواند یا جوابِ GLM را."""
    # escape اجباری: `text` خروجیِ مدل است و با `parse_mode=HTML` می‌رود. یک `<`
    # کلِ پیام را ۴۰۰ می‌کند و `send_text` استثنا را می‌بلعد → جوابِ مالک بی‌صدا
    # گم می‌شود (ممیزیِ ۲۰۲۶-۰۷-۲۷؛ همان الگویی که کارتِ C6 را یک شبانه‌روز خورد).
    import html as _h
    body = ("🐙 " + _h.escape(str(text or "").strip()))[:3400]
    if model:
        body += f"\n\n<i>— {_h.escape(str(model))[:24]}</i>"
    kb = [[{"text": "🐙 منو", "callback_data": "mn:menu"},
           {"text": "📊 وضعیت", "callback_data": "mn:st"}]]
    return body, kb


if __name__ == "__main__":   # pragma: no cover — بازرسیِ دستی
    st = _load_state()
    print(json.dumps({"flag": enabled(), "daily_cap": _daily_cap(),
                      "used_today": st.get("used"), "date": st.get("date")},
                     ensure_ascii=False, indent=1))
