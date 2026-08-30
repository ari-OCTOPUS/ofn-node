#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""question_producers — تولیدکننده‌های سؤالِ اختاپوس (رأی ۲۴ منشور).

    «هفته‌ای تا ۳۰ سؤال از مالک — انتخابِ سؤال‌ها تصمیمِ خودش؛ چارچوب:
     اهدافِ مشترک (اهدافِ خودمون)، نه فقط اجرای دستور.»

⚠️ چرا این فایل ساخته شد: `question_budget` از ۰۷-۳۱ کاملاً سالم بود — سقف،
صف، تحویل، مصرفِ بودجه، ثبتِ جواب — ولی **هیچ‌کس هیچ‌وقت چیزی submit نمی‌کرد**.
صفر تولیدکننده یعنی صفِ همیشه‌خالی، یعنی قابلیتِ «اعلام‌شده ولی مرده». این
ماژول همان شکاف است: اختاپوس **واقعاً** می‌پرسد.

پنج تولیدکننده — هر کدام فقط **بازرسیِ artifact ِ واقعیِ روی دیسک**:
  ۱) کارِ پا که >۲۴ ساعت BLOCKED مانده   ← `state/telegram/legs/<leg>-tasks.json`
  ۲) لیدِ گیرکرده روی اطلاعاتِ ناقص >۱۲س ← `state/legs/lead-pipeline.json` (stuck)
  ۳) قابلیتِ ساخته‌شده ولی خلعِ‌سلاح       ← `state/flags-loaded-*.json` + جدولِ منشور
  ۴) ماهِ بی‌درآمدِ خرج‌دار                ← `state/fitness-latest.json` + `state/telemetry-latest.json`
  ۵) هدفِ بی‌حرکتِ ۷ روزه                 ← `_ops/GOALS-OCTOPUS.md` + `state/cortex/outcomes.jsonl`

ناوردا‌ها (هیچ‌کدام قابلِ‌مذاکره نیست):
  · **هیچ حقیقتی اختراع نمی‌شود.** هر سؤال در `context=` عینِ متنِ artifact ِ
    انگیزاننده را نقل می‌کند؛ اگر artifact نبود، سؤالی هم نیست (سکوتِ صادق).
  · هر تولیدکننده در هر run حداکثر **یک** سؤال.
  · dedup با کلیدِ پایدار در پنجرهٔ همان هفتهٔ ISO. رزرو **قبل از** submit
    نوشته می‌شود (fail-closed: ذخیره نشد ⇒ submit هم نمی‌شود — سؤالِ تکراری
    از سؤالِ دیرآمده بدتر است).
  · سقفِ تولیدِ هفته = همان `WEEK_CAP` ِ بودجه؛ وگرنه صفِ نپرسیده تلنبار
    می‌شد و هفتهٔ بعد جای سؤالِ تازه را می‌گرفت.
  · صفر ارسال، صفر شبکه؛ تنها نوشتنِ این ماژول store ِ dedup ِ خودش است
    (و submit ِ خودِ question_budget).
  · 🔐 از `flags-loaded-*.json` فقط **نامِ** فلگ و مقایسه با `"1"` خوانده
    می‌شود. هیچ *مقدارِ* فلگی — هرگز — واردِ متنِ سؤال نمی‌شود.
  · دکترینِ صداقت: شکستِ زیرساخت **بلند** برمی‌گردد — آیتمِ
    `{"status": "error", …}` در خروجیِ scan، نه سکوت.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# پنجره‌ها — عددِ منشور، نه سلیقه.
BLOCKED_AFTER_S = 24 * 3600.0      # (۱) پای مسدود بیش از یک روز
LEAD_STUCK_AFTER_S = 12 * 3600.0   # (۲) لیدِ منتظرِ اطلاعات بیش از نیم‌روز
GOAL_STALE_S = 7 * 86400.0         # (۵) هدفِ بی‌حرکتِ یک هفته
# (۴) کفِ محافظه‌کارانهٔ «خرج داشتیم»: زیرِ یک دلار سؤال‌کردن نویز است، نه
# مدیریت. عددِ قضاوتی است و عمداً صریح نوشته شده تا قابلِ بحث بماند.
MONEY_MIN_COST_AUD = 1.0

# پاهای گروه — هم‌ترازِ power.PAUSABLE_LEGS ِ بیزنسی (system/mirror پا نیستند).
LEGS = ("lead", "ziman", "mining", "crypto", "accounting")

# ضربانِ مرکز چند-ثانیه‌ای است و هر scan تا ۲۵۶KB از دنبالهٔ outcomes.jsonl را
# می‌خواند. cadence داخلِ خودِ ماژول است (نه در سیمِ مرکز) تا قراردادِ wiring
# یک خط بماند: «هر beat صدا بزن» — throttle خودش را نگه می‌دارد.
MIN_SCAN_INTERVAL_S = 900.0

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(n) -> str:
    return str(n).translate(_FA)


# ── مسیرها (env-اول، همان الگوی weekly_review — harness ایزوله‌شان می‌کند) ──
def _state_dir() -> Path:
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if base:
        return Path(base)
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import opslib
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state"


def _ops_dir() -> Path:
    """ریشهٔ `_ops` — محلِ GOALS-OCTOPUS.md. همان `opslib.OPS` ِ خوانندهٔ
    اصلیِ این فایل (`cortex/goal_directed`) تا هر دو یک چیز ببینند."""
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import opslib
        return Path(opslib.OPS)
    except Exception:  # noqa: BLE001
        return _HERE.parent


def _ledger_path() -> Path:
    return _state_dir() / "telegram" / "question-producers.json"


def _week_key(now: float) -> str:
    y, w, _ = datetime.fromtimestamp(float(now)).isocalendar()
    return f"{y}-W{int(w):02d}"


# ── دفترِ dedup ِ هفته ─────────────────────────────────────────────────────
def _load_ledger(now: float) -> dict:
    d = {"week": _week_key(now), "keys": {}}
    try:
        raw = json.loads(_ledger_path().read_text("utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("keys"), dict):
            d = raw
    except (OSError, ValueError):
        pass
    wk = _week_key(now)
    if d.get("week") != wk:            # هفتهٔ نو ⇒ همان سؤال دوباره مجاز است
        d = {"week": wk, "keys": {}}
    d.setdefault("keys", {})
    return d


def _save_ledger(d: dict) -> bool:
    try:
        p = _ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


def asked_keys(now: "float | None" = None) -> dict:
    """کلیدهای همین هفته (برای بازرسی/تست) — {key: {"ts", "qid"}}."""
    return dict(_load_ledger(float(now if now is not None
                                   else time.time())).get("keys", {}))


# ── کمکی‌های خواندنِ artifact (همه fail-soft: خطا/غیاب ⇒ None/[]) ──────────
def _read_json(p: Path):
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def _tail_lines(p: Path, max_bytes: int = 262144) -> list:
    """آخرِ فایلِ jsonl بدونِ خواندنِ کلِ آن (outcomes.jsonl صدها کیلوبایت است).
    نیم‌خطِ بریدهٔ ابتدای پنجره دور ریخته می‌شود."""
    try:
        size = p.stat().st_size
        with p.open("rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()
            data = f.read()
    except OSError:
        return []
    return data.decode("utf-8", errors="ignore").splitlines()


def _iso_ts(s) -> "float | None":
    try:
        dt = datetime.fromisoformat(str(s or ""))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.timestamp()


def _hours(delta_s: float) -> str:
    return _fa(max(0, int(float(delta_s) / 3600)))


def _cut(s, n: int) -> str:
    """نقلِ کوتاه‌شده باید **بگوید** که کوتاه شده — نقلِ بریده‌ای که خودش را
    کامل جا بزند، همان اختراعِ حقیقت است در لباسِ نقل‌قول."""
    t = str(s or "").strip()
    return t if len(t) <= n else t[:n].rstrip() + "…"


# ── (۱) پای مسدودِ بیش از ۲۴ ساعت ─────────────────────────────────────────
def _p_blocked_leg(ctx: dict) -> "dict | None":
    lt = ctx.get("lt")
    if lt is None:
        return None
    now = ctx["now"]
    best = None                                  # قدیمی‌ترین مانع، نه اولی
    for leg in LEGS:
        try:
            rows = lt.queue(leg)
        except Exception:  # noqa: BLE001
            continue
        for t in rows:
            if t.get("state") != getattr(lt, "BLOCKED", "BLOCKED"):
                continue
            try:
                upd = float(t.get("updated") or 0)
            except (TypeError, ValueError):
                continue
            if upd <= 0 or (now - upd) < BLOCKED_AFTER_S:
                continue
            if best is None or upd < best[2]:
                best = (leg, t, upd)
    if best is None:
        return None
    leg, t, upd = best
    tid = str(t.get("id") or "؟")
    need = str(t.get("question") or "").strip()
    text = str(t.get("text") or "").strip()
    return {
        "key": f"blocked:{leg}:{tid}",
        "q": (f"کارِ {tid} در پای «{leg}» {_hours(now - upd)} ساعت است پشتِ "
              f"مانع مانده. چه چیزی بازش می‌کند؟"),
        "context": (f"state/telegram/legs/{leg}-tasks.json · {tid} "
                    f"«{_cut(text, 70)}» · مانع: «{_cut(need, 90) or '—'}»"),
        "goal": ("هدفِ مشترک: هیچ کارِ پا بیش از یک روز پشتِ مانع نماند — "
                 "کارِ گیرکرده نه پول می‌سازد نه چیزی یاد می‌دهد."),
    }


# ── (۲) لیدِ گیرکرده روی اطلاعاتِ ناقص بیش از ۱۲ ساعت ──────────────────────
def _p_lead_missing_info(ctx: dict) -> "dict | None":
    """منبع: `lead_pipeline._make_stuck` که دقیقاً این شکل را می‌نویسد —
    `{"stuck": {lead_id: {"task_id","lead","question","since"}}}`. خواننده و
    نویسنده به یک قرارداد pin شده‌اند."""
    d = _read_json(ctx["state"] / "legs" / "lead-pipeline.json")
    if not isinstance(d, dict) or not isinstance(d.get("stuck"), dict):
        return None
    now = ctx["now"]
    best = None
    for lead_id, entry in d["stuck"].items():
        if not isinstance(entry, dict):
            continue
        try:
            since = float(entry.get("since") or 0)
        except (TypeError, ValueError):
            continue
        need = str(entry.get("question") or "").strip()
        if since <= 0 or not need or (now - since) < LEAD_STUCK_AFTER_S:
            continue                    # سؤالِ بی‌متن سؤالِ مالک نمی‌شود
        if best is None or since < best[2]:
            best = (str(lead_id), entry, since)
    if best is None:
        return None
    lead_id, entry, since = best
    need = str(entry.get("question") or "").strip()
    desc = str((entry.get("lead") or {}).get("description") or "")
    return {
        "key": f"lead-stuck:{lead_id}",
        "q": (f"لیدِ {lead_id[:12]} {_hours(now - since)} ساعت است منتظرِ یک "
              f"قلم اطلاعات مانده: {_cut(need, 150)}"),
        "context": (f"state/legs/lead-pipeline.json · stuck[{lead_id[:12]}] "
                    f"«{_cut(desc, 60)}» · سؤالِ باز: «{_cut(need, 110)}»"),
        "goal": ("هدفِ مشترک (GOALS-OCTOPUS): اولین پولِ مطالبه‌شده — "
                 "لیدِ نیمه‌کاره هرگز به فاکتور نمی‌رسد."),
    }


# ── (۳) قابلیتِ ساخته‌شده ولی خلعِ‌سلاح ────────────────────────────────────
# جدولِ منشور: (فلگ، فایلِ ماژول، نامِ فارسی، پیامدِ یک‌خطیِ روشن‌کردن).
# ترتیب = اولویتِ منشور (ریتم و یادآوری اول، نمایش آخر).
CHARTER_CAPABILITIES = (
    ("OCTOPUS_TG_REMINDERS", "reminders.py", "یادآوریِ زبانِ طبیعی",
     "روشن شود، موعدهایی که به من می‌گویی خودشان سرِ وقت در DM زنگ می‌زنند."),
    ("OCTOPUS_TG_BRIEF", "brief.py", "بریفِ صبح و جمع‌بندیِ شب",
     "روشن شود، هر صبح ۳ کارِ مهمِ روز و هر شب یک جمع‌بندی می‌آید."),
    ("OCTOPUS_TG_QBUDGET", "question_budget.py", "بودجهٔ ۳۰ سؤال",
     "خاموش بماند، سؤال‌ها فقط در صف جمع می‌شوند و هیچ‌کدام به تو نمی‌رسد."),
    ("OCTOPUS_TG_WEEKLY_REVIEW", "weekly_review.py", "مرورِ هفتگیِ شنبه",
     "روشن شود، شنبه صبح گزارشِ هر بیزنس + پول + سنجه‌ها می‌آید."),
    ("OCTOPUS_TG_ASK_VAULT", "ask_vault.py", "سؤال از vault با ذکرِ منبع",
     "روشن شود، جوابِ سؤال‌هایت از نوت‌های خودت با لینکِ منبع می‌آید."),
    ("OCTOPUS_TG_MINIAPP", "miniapp_gateway.py", "داشبوردِ Mini App",
     "روشن شود، صفحهٔ وضعیتِ پول/لید/سلامت داخلِ تلگرام باز می‌شود."),
)


def _loaded_flags(state: Path) -> "tuple[dict, list]":
    """اتحادِ فلگ‌های واقعاً بارشدهٔ پروسه‌های زنده + نامِ فایل‌های خوانده‌شده.

    🔐 خروجی فقط برای مقایسهٔ `== "1"` مصرف می‌شود؛ هیچ مقداری از این dict
    هرگز واردِ متنِ سؤال نمی‌شود (فایلِ زنده کلیدهای secret هم دارد)."""
    armed: dict = {}
    seen: list = []
    try:
        files = sorted(state.glob("flags-loaded-*.json"))
    except OSError:
        return armed, seen
    for p in files:
        d = _read_json(p)
        fl = (d or {}).get("flags") if isinstance(d, dict) else None
        if not isinstance(fl, dict):
            continue
        seen.append(p.name)
        for k, v in fl.items():
            if str(v) == "1":
                armed[str(k)] = True
    return armed, seen


def _p_disarmed_capability(ctx: dict) -> "dict | None":
    state = ctx["state"]
    armed, seen = _loaded_flags(state)
    # هیچ پروسه‌ای فلگ‌هایش را ننوشته ⇒ ادعای «خلعِ‌سلاح است» شاهد ندارد.
    # سکوتِ صادق، نه حدس.
    if not seen:
        return None
    for flag, mod, name, consequence in CHARTER_CAPABILITIES:
        if not (_HERE / mod).is_file():
            continue                    # «ساخته‌شده» یعنی ماژولش واقعاً هست
        if armed.get(flag) or os.environ.get(flag) == "1":
            continue
        return {
            "key": f"disarm:{flag}",
            "q": (f"قابلیتِ «{name}» ساخته شده ولی خاموش است. روشنش کنم؟ "
                  f"({consequence})"),
            "context": (f"{', '.join(seen[:3])} · فلگِ {flag} در هیچ‌کدام "
                        f"«۱» نیست · ماژول: telegram_center/{mod}"),
            "goal": ("هدفِ مشترک: ۹۵٪ کارها را خودم انجام بدهم — قابلیتی که "
                     "خاموش است، ساخته‌شده حساب نمی‌شود."),
        }
    return None


# ── (۴) ماهِ بی‌درآمدِ خرج‌دار ─────────────────────────────────────────────
def _p_money_zero_revenue(ctx: dict) -> "dict | None":
    """دو artifact با هم: `fitness-latest.json` (درآمدِ منتسب) و
    `telemetry-latest.json` (خرجِ ماه). یکی نبود ⇒ سکوت؛ ادعای «صفر درآمد»
    بدونِ فایلِ درآمد، عددسازی است."""
    fit = _read_json(ctx["state"] / "fitness-latest.json")
    tel = _read_json(ctx["state"] / "telemetry-latest.json")
    if not isinstance(fit, dict) or not isinstance(tel, dict):
        return None
    attr = fit.get("attribution")
    if not isinstance(attr, dict):
        return None
    try:
        claimed = float(attr.get("claimed") or 0)
        confirmed = float(attr.get("confirmed") or 0)
    except (TypeError, ValueError):
        return None
    cells = attr.get("revenue_by_cell")
    if claimed or confirmed or (isinstance(cells, dict) and cells):
        return None                      # درآمدی هست ⇒ این سؤال بی‌موضوع است
    month = tel.get("month") if isinstance(tel.get("month"), dict) else {}
    try:
        aud = float(month.get("aud") or 0)
    except (TypeError, ValueError):
        return None
    if aud < MONEY_MIN_COST_AUD:
        return None
    mkey = str(month.get("key") or datetime.fromtimestamp(
        ctx["now"]).strftime("%Y-%m"))
    return {
        "key": f"money-zero:{mkey}",
        "q": ("این ماه هیچ درآمدِ منتسبی ثبت نشده ولی خرج داشتیم. هفتهٔ "
              "بعد روی کدام بیزنس خودکارسازی کنم — نقاشی، زیمان، یا "
              "حسابداری؟"),
        "context": (f"state/fitness-latest.json (ts {fit.get('ts')}): "
                    f"attribution.claimed=۰ · revenue_by_cell خالی — "
                    f"state/telemetry-latest.json (ts {tel.get('ts')}): "
                    f"خرجِ ماهِ {mkey} = AU${_fa(round(aud, 2))}"),
        "goal": ("هدفِ مشترک (GOALS-OCTOPUS): اولین پولِ مطالبه‌شده — "
                 "`attribution.claimed` باید از صفر دربیاید."),
    }


# ── (۵) هدفِ بی‌حرکتِ ۷ روزه ──────────────────────────────────────────────
def _goal_lines(ops: Path) -> list:
    """همان قرارداد `cortex/goal_directed.load_goals` — فقط bulletهای مالک."""
    try:
        text = (ops / "GOALS-OCTOPUS.md").read_text("utf-8")
    except OSError:
        return []
    return [ln[2:].strip() for ln in text.splitlines()
            if ln.startswith("- ") and ln[2:].strip()]


def _p_stale_goal(ctx: dict) -> "dict | None":
    """«حرکت» تعریفِ دقیق و قابلِ‌بازرسی دارد: رکوردِ نیتی در
    `state/cortex/outcomes.jsonl` که `serves_goal` ِ آن **عینِ همین خط** باشد.
    فایلِ outcomes نبود ⇒ اصلاً سکوت — «حرکتی ندیدم» با «جایی برای دیدن
    نبود» یکی نیست."""
    goals = _goal_lines(ctx["ops"])
    if not goals:
        return None
    ledger = ctx["state"] / "cortex" / "outcomes.jsonl"
    if not ledger.is_file():
        return None
    now = ctx["now"]
    since = now - GOAL_STALE_S
    moved = set()
    for ln in _tail_lines(ledger):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(r, dict):
            continue
        g = str(r.get("serves_goal") or "").strip()
        if not g or g == "—":
            continue
        ts = _iso_ts(r.get("ts"))
        if ts is not None and since <= ts <= now:
            moved.add(g)
    for g in goals:
        if g in moved:
            continue
        h = hashlib.sha1(g.encode("utf-8")).hexdigest()[:10]
        return {
            "key": f"goal-stale:{h}",
            "q": (f"این جهت هفت روز است هیچ کاری آن را پیش نبرده: "
                  f"«{_cut(g, 120)}» — هنوز هدف است یا حذفش کنم؟"),
            "context": (f"_ops/GOALS-OCTOPUS.md خطِ «{_cut(g, 90)}» · "
                        f"state/cortex/outcomes.jsonl: هیچ نیتی در ۷ روزِ "
                        f"گذشته این جهت را نام نبرده"),
            "goal": ("هدفِ مشترک: فهرستِ اهداف باید راست بگوید — هدفی که "
                     "هیچ‌کس دنبالش نیست، جهت نیست، نویز است."),
        }
    return None


PRODUCERS = (
    ("blocked-leg", _p_blocked_leg),
    ("lead-missing-info", _p_lead_missing_info),
    ("disarmed-capability", _p_disarmed_capability),
    ("money-zero-revenue", _p_money_zero_revenue),
    ("stale-goal", _p_stale_goal),
)


# ── API ────────────────────────────────────────────────────────────────────
def _leg_tasks():
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import leg_tasks as lt
        return lt
    except Exception:  # noqa: BLE001
        return None


def _budget():
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    import question_budget as qb        # عمداً بی‌try: نبودِ بودجه = خطای بلند
    return qb


def scan(now: "float | None" = None, deps: "dict | None" = None) -> list:
    """یک دورِ بازرسی: هر تولیدکننده حداکثر یک سؤال، dedup ِ هفتگی، submit.

    خروجی: فهرستِ آیتم‌های ثبت‌شده — هر عنصر خروجیِ `question_budget.submit`
    به‌علاوهٔ `producer` و `key`. عنصرِ `{"status": "error", …}` یعنی چیزی
    واقعاً خراب است (دکترینِ صداقت: بلند، نه بی‌صدا).

    این تابع **هیچ‌چیز نمی‌فرستد** — تحویل کارِ ضربانِ مرکز است (`pending` →
    ارسال → `mark_asked`)، پشتِ فلگِ `OCTOPUS_TG_QBUDGET`."""
    now = float(now if now is not None else time.time())
    deps = deps or {}
    out: list = []
    try:
        qb = deps.get("qb") or _budget()
    except Exception as e:  # noqa: BLE001
        return [{"status": "error", "producer": "-",
                 "error": f"question_budget در دسترس نیست: {e}"}]

    ledger = _load_ledger(now)
    try:
        last = float(ledger.get("last_scan") or 0)
    except (TypeError, ValueError):
        last = 0.0
    if not deps.get("force") and 0 < last <= now < last + MIN_SCAN_INTERVAL_S:
        return []                       # هنوز زودِ — بازرسیِ بی‌ثمرِ هر ثانیه نه
    ledger["last_scan"] = now
    _save_ledger(ledger)                # شکستش کشنده نیست؛ خطای بلند سرِ رزرو

    keys = ledger["keys"]
    cap = int(getattr(qb, "WEEK_CAP", 30))
    ctx = {"now": now,
           "state": Path(deps.get("state_dir") or _state_dir()),
           "ops": Path(deps.get("ops_dir") or _ops_dir()),
           "lt": deps.get("leg_tasks", _leg_tasks())}

    for name, fn in PRODUCERS:
        if len(keys) >= cap:
            break                       # سقفِ تولیدِ هفته = سقفِ بودجه
        try:
            cand = fn(ctx)
        except Exception as e:  # noqa: BLE001 — یک تولیدکننده بقیه را نمی‌کشد
            out.append({"status": "error", "producer": name, "error": str(e)})
            continue
        if not cand:
            continue
        key = str(cand.get("key") or "")
        if not key or key in keys:
            continue                    # همین هفته پرسیده شده ⇒ دوباره نه
        # رزروِ قبل از submit: اگر دیسک نگرفت، هیچ سؤالی هم ثبت نمی‌شود.
        keys[key] = {"ts": now, "producer": name, "qid": None}
        if not _save_ledger(ledger):
            keys.pop(key, None)
            out.append({"status": "error", "producer": name,
                        "error": "دفترِ dedup ذخیره نشد — سؤال ثبت نشد "
                                 "(fail-closed تا تکرار رخ ندهد)"})
            continue
        res = qb.submit(cand["q"], context=cand.get("context", ""),
                        goal=cand.get("goal", ""), now=now)
        if not res:
            keys.pop(key, None)         # ثبت نشد ⇒ رزرو هم آزاد
            _save_ledger(ledger)
            out.append({"status": "error", "producer": name,
                        "error": "question_budget.submit چیزی ثبت نکرد"})
            continue
        keys[key]["qid"] = res["item"]["id"]
        _save_ledger(ledger)
        res = dict(res)
        res["producer"] = name
        res["key"] = key
        out.append(res)
    return out


if __name__ == "__main__":            # بازرسیِ دستی — فقط چاپ، صفر ارسال
    print(json.dumps(scan(), ensure_ascii=False, indent=2, default=str))
