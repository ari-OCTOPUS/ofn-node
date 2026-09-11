"""initiative — اختاپوس خودش شروع می‌کند، و از مالک سؤال می‌پرسد.

رأیِ مالک ۲۰۲۶-۰۷-۲۷: «آره، و حتی از من سؤال بپرسد.»

تا امروز رابطه یک‌طرفه بود: مالک می‌پرسید، اختاپوس جواب می‌داد. دایجست‌های
دوره‌ای هم گزارش بودند نه گفت‌وگو. یعنی هر چیزی که اختاپوس **نمی‌دانست** و
دانستنش کارش را بهتر می‌کرد، تا ابد نادانسته می‌ماند — مگر اینکه مالک تصادفاً
همان را می‌پرسید.

دو نوع پیامِ آغازگر
──────────────────
  · **خبر** — چیزی که فکر می‌کند مالک باید بداند (با دلیلِ صریح).
  · **سؤال** — چیزی که نمی‌داند و دانستنش تصمیمِ بعدی‌اش را عوض می‌کند.

نوعِ دوم مهم‌تر است و تا امروز اصلاً وجود نداشت.

چرا محتاطانه
────────────
ابتکار سریع به سرریز تبدیل می‌شود و آن‌وقت مالک کلِ کانال را خاموش می‌کند. پس:
حداکثر دو پیام در روز، حداقل چهار ساعت فاصله، ساکت در ساعتِ سکوت، و هر پیام یک
دکمهٔ **«کمتر حرف بزن»** دارد که سقفِ روزانه را همان‌جا نصف می‌کند. سکوت حالتِ
پیش‌فرض است؛ حرف‌زدن باید توجیه داشته باشد.

مرزها: فقط متن. هیچ اجرا. سهمیهٔ مغز از `ask_brain` قرض گرفته می‌شود.
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

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_INITIATIVE"
UNKNOWNS_FLAG = "OCTOPUS_INITIATIVE_UNKNOWNS"   # ۲۰۲۶-۰۷-۲۸ — پیش‌فرض خاموش
SCHEMA = "initiative.v1"
STATE = opslib.STATE_DIR / "telegram" / "initiative-state.json"
LEDGER = opslib.STATE_DIR / "telegram" / "initiative.jsonl"

DAILY_DEFAULT = 2
DAILY_MIN = 1
MIN_GAP_S = 4 * 3600.0
MAX_TOKENS = int(os.environ.get("INITIATIVE_MAX_TOKENS", "1500"))   # 09-11 رأی مالک (گزینهٔ ۱ حداقلی): 700 سوخت می‌داد (لجر)؛ rollback: =700
MIN_CHARS = 60

# ─── WS-5 · بی‌سقف ولی حساب‌پس‌ده (رأیِ مالک ۲۰۲۶-۰۸-۰۱) ────────────────────
# رأی: «هر وقت چیزِ واقعی برای گفتن دارد» — سقفِ ۲/روز برداشته شود. ولی شرطی که
# مالک به رأیش چسباند خودِ نکته است: بی‌سقفِ **بی‌حساب** همان چیزی است که گروه را
# به لولهٔ نویز تبدیل کرد (۶۲٪ از ۱۷۶ ارسالِ دو روز در General افتاد).
#
# پس عدد با **آستانهٔ ارزش** عوض می‌شود، نه با هیچ:
#   ۱. هر ابتکار باید بگوید چرا ارزشِ قطعِ کارِ مالک را داشت، و آن دلیل **ثبت**
#      می‌شود. بی‌دلیل = سکوت (`no-justification`)، نه ارسال.
#   ۲. ساعتِ سکوت دست‌نخورده — رأیِ مالک دربارهٔ سقف بود، نه دربارهٔ نیمه‌شب.
#   ۳. هر ابتکار با **سرنوشتش** جفت می‌شود (جواب داد؟ نادیده گرفت؟) تا نرخِ
#      «به‌دردخور بود» سنجیدنی شود.
#
# ⚠️ فاصلهٔ کمینه **سقفِ حرف نیست، ترمزِ خرج است**: `speak()` هر tick صدا زده
# می‌شود و هر اجازه یک تماسِ مغزِ پولی است. بدونِ هیچ فاصله‌ای، بی‌سقف یعنی
# تماسِ پولی در هر بیت. ۳۰ دقیقه = ۸ برابر سخاوتمندتر از امروز، و همچنان
# غیرِسقف برای کانالی که «چیزِ واقعی» می‌گوید.
UNCAPPED_FLAG = "OCTOPUS_INITIATIVE_UNCAPPED"   # پیش‌فرض خاموش
OUTCOME_SCHEMA = "initiative-outcome.v1"
UNCAPPED_MIN_GAP_S = 30 * 60.0     # ترمزِ خرج، نه سقفِ پیام
QUIET_GAP_MAX_S = 24 * 3600.0      # سقفِ ترمز وقتی مالک مکرر «کمتر حرف بزن» می‌زند
MIN_WHY_CHARS = 25                 # آستانهٔ ارزش: دلیل باید جمله باشد نه تیک
OUTCOME_WINDOW_S = 6 * 3600.0      # پنجرهٔ جفت‌شدنِ ابتکار با سرنوشتش
# سیگنالِ **مثبت** از دفترِ موجودِ `ask_brain` خوانده می‌شود (مالک از اختاپوس
# می‌پرسد). هیچ صداکنندهٔ تازه‌ای لازم نیست: این دفتر همین حالا در مسیرِ زندهٔ
# تولید نوشته می‌شود. اسمش عمداً `engaged` است نه `answered` — این پروکسیِ
# «بعد از قطع‌شدن، با اختاپوس حرف زد» است، نه اثباتِ جوابِ همان ابتکار.
ASK_LEDGER = opslib.STATE_DIR / "telegram" / "ask-brain.jsonl"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def uncapped() -> bool:
    """WS-5 روشن است؟ خاموش = رفتارِ امروز بایت‌به‌بایت."""
    return str(os.environ.get(UNCAPPED_FLAG, "")).strip().lower() in (
        "1", "true", "yes", "on")


# ─── سهمیه ──────────────────────────────────────────────────────────────────
def _load() -> dict:
    try:
        if STATE.exists():
            d = json.loads(STATE.read_text("utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"date": "", "used": 0, "last_ts": 0.0, "cap": DAILY_DEFAULT}


def _save(d: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, STATE)
    except OSError:
        pass


def quieter() -> dict:
    """دکمهٔ «کمتر حرف بزن» — سقفِ روزانه را نصف می‌کند (کفِ ۱).

    WS-5: وقتی سقف برداشته شده، نصف‌کردنِ سقف دیگر اثری ندارد و این دکمه به یک
    **دکمهٔ مرده** تبدیل می‌شود — همان تلهٔ `iv:q` که یک‌بار گرفته شد. پس در
    حالتِ بی‌سقف، تپِ مالک به‌جای سقف **ترمز را دو برابر** می‌کند، و مهم‌تر:
    به‌عنوان سرنوشتِ منفیِ آخرین ابتکارِ باز ثبت می‌شود. تپ = «ارزشش را نداشت»،
    و این تنها سیگنالِ سرنوشتی است که همین امروز در **دو** روترِ تولیدی سیم دارد.
    """
    d = _load()
    cap = max(DAILY_MIN, int(d.get("cap", DAILY_DEFAULT)) // 2)
    d["cap"] = cap
    out = {"ok": True, "cap": cap}
    if uncapped():
        floor = min(QUIET_GAP_MAX_S,
                    float(d.get("gap_floor") or UNCAPPED_MIN_GAP_S) * 2.0)
        d["gap_floor"] = floor
        out["gap_floor_h"] = round(floor / 3600.0, 2)
        iid = _newest_open()
        if iid:
            _ledger({"ts": opslib.now_iso(), "schema": OUTCOME_SCHEMA, "id": iid,
                     "outcome": "quieted", "signal": "owner-tap", "wait_s": None})
            out["outcome_recorded"] = True
    _save(d)
    return out


def _take(now: float) -> "str | None":
    """سهمیه را **قبل از** تماس بردار. None = مجاز."""
    today = opslib.today()
    d = _load()
    if d.get("date") != today:
        _fresh = {"date": today, "used": 0, "last_ts": 0.0,
                  "cap": int(d.get("cap", DAILY_DEFAULT))}
        # ⚠️ `gap_floor` باید از چرخشِ روز جان سالم به در ببرد، وگرنه تپِ «کمتر
        # حرف بزن» هر نیمه‌شب بی‌صدا باطل می‌شود — یعنی مالک دکمه را زده و فردا
        # هیچ اثری نمانده. همان شکلِ «دکمهٔ مرده»، فقط با تأخیرِ ۲۴ ساعته.
        if d.get("gap_floor"):
            _fresh["gap_floor"] = d["gap_floor"]
        d = _fresh
    try:
        gap = now - float(d.get("last_ts", 0.0) or 0.0)
    except (TypeError, ValueError):
        gap = MIN_GAP_S + 1
    if uncapped():
        try:
            floor = float(d.get("gap_floor") or UNCAPPED_MIN_GAP_S)
        except (TypeError, ValueError):
            floor = UNCAPPED_MIN_GAP_S
    else:
        floor = MIN_GAP_S
    if gap < floor:
        return "too-soon"
    if not uncapped() and int(d.get("used", 0)) >= int(d.get("cap", DAILY_DEFAULT)):
        return "daily-cap"
    d["used"] = int(d.get("used", 0)) + 1
    d["last_ts"] = now
    _save(d)
    return None


def _quiet_now(now: "float | None" = None) -> bool:
    """آیا الان ساعتِ سکوتِ مالک است؟

    ⚠️ ۲۰۲۶-۰۷-۲۸ — نسخهٔ اول ساعتِ تزریق‌شده را **نادیده می‌گرفت** و همیشه ساعتِ
    دیوار را می‌خواند، در حالی که `speak(now=…)` ساعت می‌پذیرفت. یعنی تابع
    نیمه‌تزریقی بود: `now` سهمیه را کنترل می‌کرد ولی سکوت را نه.

    دو پیامد داشت، و دومی بدتر است:
      · تست‌ها **هر شب بین ۰ تا ۷ قرمز می‌شدند** و روزها سبز — و همان شب گرفته شد.
      · و در مسیرِ زنده، صداکننده‌ای که `now` صریح می‌داد رفتارِ نیمه‌تزریقی
        می‌گرفت — همان دوپارگی که «در تست کار می‌کند، زنده نه» می‌سازد.

    `approval_channel._quiet_now` از قبل پارامترِ زمان داشت؛ فقط کسی پاسش نمی‌داد."""
    try:
        import datetime as _dt
        import approval_channel as ac
        when = _dt.datetime.fromtimestamp(now) if now is not None else None
        return bool(ac._quiet_now(when))
    except Exception:  # noqa: BLE001 — نبودِ ساعتِ سکوت = صحبت مجاز
        return False


# ─── context ────────────────────────────────────────────────────────────────
def _context() -> dict:
    ctx: dict = {}
    try:
        p = opslib.STATE_DIR / "doctor" / "self-knowledge-latest.json"
        sk = json.loads(p.read_text("utf-8")) if p.exists() else {}
        ctx["فهمِ_من"] = {k: sk.get(k) for k in ("focus", "understanding", "trajectory")}
        if sk.get("owner_verdicts_open"):
            ctx["منتظرِ_رأیِ_تو"] = sk["owner_verdicts_open"]
        if sk.get("owner_corrections"):
            ctx["تصحیح‌های_تو"] = sk["owner_corrections"]
        # ── «چیزی که نمی‌دانم» به‌صورتِ صریح (۲۰۲۶-۰۷-۲۸، پشتِ فلگ) ──────────
        # `open_questions` در کلِ `_ops` **صفر مصرف‌کنندهٔ نام‌برده** داشت. اینجا
        # به‌شکلِ پنهان داخلِ `understanding` سریال می‌شد، ولی در یک بلوبِ بزرگ گم
        # بود و پرامپت هرگز به آن اشاره نمی‌کرد. حالا نام دارد — و مهم‌تر: از
        # ریشه‌های نامعلوم **جدا** شده، چون تقسیمِ کار روشن است:
        #   ریشهٔ نامعلوم → قابلِ کاوش → صفِ C6 (خودش آزمایش می‌کند)
        #   پرسشِ باز    → غیرقابلِ ابطال → فقط مالک می‌تواند جواب بدهد
        # پس ابتکار باید دربارهٔ دومی بپرسد، نه اولی.
        if str(os.environ.get(UNKNOWNS_FLAG, "")).strip().lower() in ("1", "true", "yes", "on"):
            u = sk.get("understanding") if isinstance(sk.get("understanding"), dict) else {}
            qs = [str(q)[:200] for q in (u.get("open_questions") or [])][:5]
            probing = [str((p or {}).get("symptom"))[:120]
                       for p in (u.get("pathology") or [])
                       if isinstance(p, dict) and "نامعلوم" in str(p.get("root_cause") or "")]
            if qs or probing:
                ctx["نمی‌دانم‌ها"] = {
                    "پرسش‌های_باز_که_فقط_تو_جواب_داری": qs,
                    "ریشه‌های_نامعلومی_که_خودم_دارم_می‌کاوم": probing[:5],
                    "راهنما": ("دربارهٔ ردیفِ اول بپرس؛ ردیفِ دوم صفِ آزمایشِ خودم "
                               "است و مزاحمتش لازم نیست."),
                }
    except (OSError, ValueError):
        pass
    try:
        import goal_directed as gd
        ctx["اهدافی_که_داده‌ای"] = gd.load_goals()[:8]
    except Exception:  # noqa: BLE001
        pass
    try:
        import needs_digest as nd
        ctx["نیازهای_فعلی"] = (nd.compute() or {}).get("items") or []
    except Exception:  # noqa: BLE001
        pass
    return ctx


_SYSTEM = (
    "تو اختاپوسی و **خودت** داری این گفت‌وگو را شروع می‌کنی — مالک چیزی نپرسیده.\n"
    "دو نوع پیام مجاز است، و باید یکی را انتخاب کنی:\n"
    "  · «خبر» — چیزی که مالک باید بداند و نمی‌داند.\n"
    "  · «سؤال» — چیزی که **تو** نمی‌دانی و دانستنش تصمیمِ بعدی‌ات را عوض می‌کند.\n"
    "نوعِ دوم را جدی بگیر: اگر جای خالیِ واقعی در فهمت هست، بپرس. یک سؤالِ خوب از "
    "یک گزارشِ خوب ارزشمندتر است.\n"
    "خروجی دقیقاً این JSON، بدونِ متنِ اضافه:\n"
    '{"نوع":"خبر|سوال","متن":"<حداکثر ۴ جمله، فارسی>",'
    '"چرا_حالا":"<یک جمله: چرا این ارزشِ قطعِ کارِ مالک را دارد>",'
    '"ارزشش_را_ندارد":true|false}\n'
    "قواعد: فقط از دادهٔ داده‌شده استدلال کن؛ عدد نساز. اگر چیزی واقعاً ارزشِ "
    "مزاحمت ندارد، `ارزشش_را_ندارد` را true بگذار — **سکوت جوابِ محترمی است** و "
    "بیشترِ وقت‌ها جوابِ درست است. هرگز ادعا نکن کاری کرده‌ای؛ اجرا مسیرِ جدا دارد."
)


def _ledger(rec: dict) -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ─── WS-5 · جفت‌کردنِ هر ابتکار با سرنوشتش ──────────────────────────────────
# دفتر append-only می‌ماند: سرنوشت یک **رکوردِ تازه** است، نه بازنویسیِ رکوردِ
# قبلی. پس هیچ خواننده‌ای (از جمله `output_critic` که همین فایل را نمونه
# می‌گیرد) چیزی از دست نمی‌دهد؛ رکوردِ سرنوشت `text` ندارد پس در نمونهٔ آن
# منتقد نمی‌افتد.
def _read_ledger() -> list:
    rows = []
    try:
        for ln in LEDGER.read_text("utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except ValueError:
                continue
    except OSError:
        pass
    return rows


def _ask_epochs() -> list:
    """زمانِ هر باری که مالک از اختاپوس پرسیده — از دفترِ زندهٔ `ask_brain`.

    ⚠️ `opslib.now_iso()` ساعتِ **محلیِ بدونِ منطقه** می‌نویسد. پس تبدیل هم باید
    محلی باشد (`fromisoformat().timestamp()` دقیقاً همین کار را می‌کند). اگر
    اینجا UTC فرض می‌شد، پنجرهٔ ۶ ساعته به‌اندازهٔ اختلافِ منطقه جابه‌جا می‌شد و
    «جواب داد» بی‌صدا به «نادیده گرفت» تبدیل می‌شد — همان نویسنده/خوانندهٔ
    ناهم‌ساعت که یک‌بار سقفِ پول را ده ساعت در روز کور کرد.
    """
    import datetime as _dt
    out = []
    try:
        lines = ASK_LEDGER.read_text("utf-8").splitlines()
    except OSError:
        return out
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        try:
            out.append(_dt.datetime.fromisoformat(str(r.get("ts") or "")).timestamp())
        except (ValueError, TypeError):
            continue
    return out


def _mkid(now: float, body: str) -> str:
    import hashlib
    return hashlib.sha256(f"{now:.3f}|{body[:80]}".encode("utf-8")).hexdigest()[:12]


def _fold() -> tuple:
    """(delivered: id→ts_epoch, outcomes: id→outcome) از دفتر."""
    delivered, outcomes = {}, {}
    for r in _read_ledger():
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "")
        if not rid:
            continue
        if r.get("schema") == OUTCOME_SCHEMA:
            outcomes[rid] = str(r.get("outcome") or "")
        elif r.get("ok"):
            try:
                delivered[rid] = float(r.get("ts_epoch") or 0.0)
            except (TypeError, ValueError):
                delivered[rid] = 0.0
    return delivered, outcomes


def _newest_open() -> "str | None":
    delivered, outcomes = _fold()
    open_ids = [(t, i) for i, t in delivered.items() if i not in outcomes]
    return max(open_ids)[1] if open_ids else None


def resolve_outcomes(*, now: "float | None" = None) -> dict:
    """ابتکارهای بازِ گذشته را به سرنوشتشان ببند. append-only، بدونِ ارسال.

    صداکنندهٔ زنده: خودِ `speak()` — که `organism.py` هر tick صدا می‌زند. یعنی
    این سنجه **صداکنندهٔ تازه لازم ندارد**؛ روی همان سیمِ موجود سوار است.
    """
    if not uncapped():
        return {"ok": False, "reason": "flag-off"}
    now = float(now if now is not None else time.time())
    delivered, outcomes = _fold()
    asks = None
    n = 0
    for iid, t in sorted(delivered.items(), key=lambda kv: kv[1]):
        if iid in outcomes or not t:
            continue
        if asks is None:
            asks = _ask_epochs()
        hit = [a for a in asks if t < a <= t + OUTCOME_WINDOW_S]
        if hit:
            _ledger({"ts": opslib.now_iso(), "schema": OUTCOME_SCHEMA, "id": iid,
                     "outcome": "engaged", "signal": "ask-brain-window",
                     "wait_s": round(min(hit) - t, 1)})
            n += 1
        elif now - t > OUTCOME_WINDOW_S:
            _ledger({"ts": opslib.now_iso(), "schema": OUTCOME_SCHEMA, "id": iid,
                     "outcome": "ignored", "signal": "window-elapsed",
                     "wait_s": None})
            n += 1
    return {"ok": True, "resolved": n}


def stats() -> dict:
    """نرخِ «به‌دردخور بود» — **سه‌حالتی**، نه صفرِ دروغین.

    اگر هیچ سرنوشتی هنوز بسته نشده، `worth_it_rate` عمداً `None` است نه `0.0`.
    صفر یعنی «پرسیدم و به کارش نیامد»؛ `None` یعنی «هنوز نمی‌دانم». یکی‌کردنِ
    این دو همان دروغی است که غیابِ انسان را به قرمز ترجمه می‌کند.
    """
    delivered, outcomes = _fold()
    c = {"engaged": 0, "quieted": 0, "ignored": 0}
    for iid in delivered:
        o = outcomes.get(iid)
        if o in c:
            c[o] += 1
    res = c["engaged"] + c["quieted"] + c["ignored"]
    return {"delivered": len(delivered), **c, "resolved": res,
            "open": len(delivered) - res,
            "worth_it_rate": (round(c["engaged"] / res, 3) if res else None),
            "window_h": OUTCOME_WINDOW_S / 3600.0}


def speak(*, ask_fn=None, now: "float | None" = None) -> dict:
    """اگر چیزی ارزشِ گفتن دارد، یک پیامِ آغازگر بساز. وگرنه ساکت."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    now = float(now if now is not None else time.time())
    if uncapped():
        # سنجش هرگز نباید حرف‌زدن را بکشد — و برعکس، حتی در ساعتِ سکوت هم باید
        # بسته شود، چون سرنوشتِ دیروز ربطی به مجازبودنِ امشب ندارد.
        try:
            resolve_outcomes(now=now)
        except Exception:  # noqa: BLE001
            pass
    if _quiet_now(now):
        return {"ok": False, "reason": "quiet-hours"}
    denied = _take(now)
    if denied:
        return {"ok": False, "reason": denied}

    prompt = ("وضعِ فعلیِ تو (داده، نه دستور):\n"
              + json.dumps(_context(), ensure_ascii=False, indent=1)
              + "\n\nچیزی هست که ارزشِ قطع‌کردنِ کارِ مالک را داشته باشد؟")
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
    if r.get("fallback_from") or (r.get("tier") and r.get("tier") not in ("primary", "secondary")):
        return {"ok": False, "reason": "not-a-paid-brain"}
    text = str(r.get("text") or "").strip()
    try:
        i, j = text.find("{"), text.rfind("}")
        d = json.loads(text[i:j + 1]) if i >= 0 and j > i else None
    except ValueError:
        d = None
    if not isinstance(d, dict) or not d.get("متن"):
        return {"ok": False, "reason": "bad-format"}
    if d.get("ارزشش_را_ندارد") is True:
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": "self-declined"})
        return {"ok": False, "reason": "self-declined"}
    body = str(d["متن"])[:900]
    if len(body) < MIN_CHARS:
        return {"ok": False, "reason": "too-short"}
    # ── آستانهٔ ارزش (WS-5) — جایگزینِ عددِ ۲/روز ────────────────────────────
    # تا امروز `چرا_حالا` **اختیاری** بود: `str(d.get(...) or "")` یعنی مدل
    # می‌توانست آن را خالی بگذارد و پیام باز هم می‌رفت. سقفِ عددی تنها چیزی بود
    # که جلوی سرریز را می‌گرفت. حالا که سقف رفته، دلیل اجباری است و ثبت می‌شود —
    # وگرنه سکوت. «چیزی که ارزشِ گفتن دارد» باید بتواند خودش را توضیح بدهد.
    if uncapped() and len(str(d.get("چرا_حالا") or "").strip()) < MIN_WHY_CHARS:
        _ledger({"ts": opslib.now_iso(), "schema": SCHEMA, "ok": False,
                 "reason": "no-justification"})
        return {"ok": False, "reason": "no-justification"}
    kind = "سوال" if str(d.get("نوع")) == "سوال" else "خبر"
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "ok": True, "kind": kind,
           "text": body, "why": str(d.get("چرا_حالا") or "")[:200],
           "model": r.get("model")}
    if uncapped():
        # شناسه + مهرِ **تزریق‌شده**. `ts` بالا از ساعتِ دیوار می‌آید در حالی که
        # `now` تزریق‌شدنی است؛ جفت‌کردن روی همان ساعتِ نیمه‌تزریقی یعنی سنجه‌ای
        # که فقط در تولید کار می‌کند و در تست بی‌صدا دروغ می‌گوید.
        rec["id"] = _mkid(now, body)
        rec["ts_epoch"] = now
        rec["outcome"] = "open"
        # عکسِ حسابِ من **در لحظهٔ تصمیم به قطع‌کردن**: دفتر باید بتواند نشان
        # بدهد «باز هم حرفش را قطع کردم در حالی که ۰ از ۵ بارِ قبل به کارش آمد».
        rec["worth_it"] = {k: stats()[k] for k in
                           ("delivered", "engaged", "quieted", "ignored",
                            "worth_it_rate")}
    _ledger(rec)
    return {"ok": True, **rec}


def card(rec: dict) -> tuple:
    import html
    kind = rec.get("kind")
    head = "❓ <b>یک سؤال از تو دارم</b>" if kind == "سوال" else "💡 <b>یک چیزی</b>"
    body = f"{head}\n\n{html.escape(str(rec.get('text') or ''))}"
    if rec.get("why"):
        body += f"\n\n<i>چرا حالا: {html.escape(str(rec['why']))}</i>"
    # ── حسابِ خودم، رویِ خودِ کارت (WS-5) ───────────────────────────────────
    # بی‌سقف فقط وقتی قابل‌دفاع است که مالک بتواند هزینه‌اش را **ببیند**. عدد از
    # خودِ رکورد می‌آید (I/O ندارد) و فقط وقتی چاپ می‌شود که سنجیدنی باشد:
    # `worth_it_rate is None` یعنی «هنوز نمی‌دانم» و درباره‌اش ساکت می‌ماند.
    w = rec.get("worth_it") if isinstance(rec.get("worth_it"), dict) else None
    if uncapped() and w and w.get("worth_it_rate") is not None:
        _fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        body += ("\n\n<i>حسابِ من: {d} بار حرفت را قطع کرده‌ام، {e} بار به کارت "
                 "آمد.</i>").format(
            d=str(int(w.get("delivered") or 0)).translate(_fa),
            e=str(int(w.get("engaged") or 0)).translate(_fa))
    kb = [[{"text": "🔇 کمتر حرف بزن", "callback_data": "iv:q"},
           {"text": "🪞 آینه", "callback_data": "mr:know"}]]
    return body[:3500], kb


if __name__ == "__main__":   # pragma: no cover
    d = _load()
    out = {"flag": enabled(), "cap": d.get("cap", DAILY_DEFAULT),
           "used_today": d.get("used"), "quiet_now": _quiet_now(),
           "uncapped": uncapped()}
    if uncapped():
        out["gap_floor_h"] = round(
            float(d.get("gap_floor") or UNCAPPED_MIN_GAP_S) / 3600.0, 2)
        out["worth_it"] = stats()
    print(json.dumps(out, ensure_ascii=False, indent=1))
