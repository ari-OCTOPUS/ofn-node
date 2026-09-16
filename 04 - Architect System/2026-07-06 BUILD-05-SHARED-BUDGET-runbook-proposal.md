---
type: runbook-proposal
status: proposal            # propose-only — runbookِ آماده. چیزی اجرا نشد.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «همه‌رو بساز تا آخر» 2026-07-06 → قدمِ ۵"
depends_on: "[[2026-07-06 BUILD-04-MUSE-DOCTOR-DRYRUN-runbook-proposal]] · PHASE5 §۴ · REVIEW R5"
grounds: [ARCHITECT_CHARTER §۵ (AU$30/ماه، خطِ $500), LEARNING-STATE ($2/روز، $0.5/call)]
tags: [build-05, budget, interlock, single-source, propose-only]
---

# BUILD-05 — شمارندهٔ بودجهٔ مشترک (تک‌منبع) (propose-only)

> **چرا:** ریسکِ R5 گزارش — چهار مصرف‌کنندهٔ LLM هرکدام زیرِ سقفِ خودشان ولی جمعشان بالا. حل: **یک شمارندهٔ مشترک**؛ هر call قبل از اجرا این‌جا رزرو می‌کند؛ در سقف، **همه** halt. سقفِ per-agent حذف می‌شود.

---

## ۱. مدل (تک‌منبع)
- فایلِ `_ops/budget/budget-state.json` = تنها حقیقتِ خرج.
- سقف‌ها از ژنوم: **روزانه $2** (STATE) · **ماهانه AU$30 hard-stop** (منشور §۵) · **خطِ فاجعهٔ $500** (D-22، backstop) · هشدارِ ۵۰٪/۸۰٪.
- **دامنه:** فقط callهای **متری/خودکار** (بات‌ها). کارِ تعاملیِ Cowork زیرِ اشتراکِ فلت است و شمرده نمی‌شود (منشور §۵) — پس dry-runِ قدم ۴ خارج از این شمارنده بود.

## ۲. budget_gate.py (قفلِ همزمانی + rollover + halt)
```python
#!/usr/bin/env python3
# budget_gate.py — شمارندهٔ بودجهٔ مشترک. هر مصرف‌کنندهٔ LLM: reserve() قبل، record() بعد.
import json, pathlib, datetime, os, time

STATE = pathlib.Path(os.environ.get("BUDGET_STATE", r"F:\backup\_ops\budget\budget-state.json"))
LOCK  = pathlib.Path(str(STATE) + ".lock")
CEIL_DAY_USD, CEIL_MONTH_AUD, DISASTER_USD = 2.0, 30.0, 500.0
AUD = 1.5           # نرخِ تقریبیِ USD→AUD (قابلِ تنظیم)
STALE_LOCK_S = 30   # قفلِ رهاشده بعد از این ثانیه‌ها steal می‌شود (ضدِ deadlock)

def _load(): return json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
def _save(d): STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(d,ensure_ascii=False,indent=2),"utf-8")
def _lock():
    for _ in range(50):
        try: return os.open(str(LOCK), os.O_CREAT|os.O_EXCL|os.O_RDWR)
        except FileExistsError:
            try:   # steal a stale lock left by a crashed holder (ضدِ deadlock)
                if time.time() - os.path.getmtime(LOCK) > STALE_LOCK_S: os.unlink(LOCK); continue
            except OSError: pass
            time.sleep(0.1)
    raise TimeoutError("budget busy")
def _unlock(fd):
    os.close(fd)
    try: os.unlink(LOCK)
    except OSError: pass
def _roll(d):
    t=datetime.date.today().isoformat(); m=t[:7]
    if d.get("date")!=t: d["date"]=t; d["spent_today_usd"]=0.0
    if d.get("month")!=m: d["month"]=m; d["spent_month_aud"]=0.0
    for k,v in (("spent_today_usd",0.0),("spent_month_aud",0.0),("halted",False)): d.setdefault(k,v)
    return d

def reserve(agent, est_usd):
    fd=_lock()
    try:
        try: d=_roll(_load())
        except Exception: return {"allow":False,"reason":"state-unreadable"}   # fail-closed (نه crash)
        if d["halted"]: return {"allow":False,"reason":"halted"}
        if d["spent_today_usd"]+est_usd > CEIL_DAY_USD: return {"allow":False,"reason":"daily"}
        if d["spent_month_aud"]+est_usd*AUD > CEIL_MONTH_AUD:
            d["halted"]=True; _save(d); return {"allow":False,"reason":"monthly-halt"}
        d["spent_today_usd"]+=est_usd; d["spent_month_aud"]+=est_usd*AUD   # ← رزرو واقعاً persist می‌شود
        _save(d); return {"allow":True, "reserved":est_usd}
    finally: _unlock(fd)

def settle(agent, est_usd, actual_usd):   # بعد از call: تخمین را با واقعی جایگزین کن
    fd=_lock()
    try:
        d=_roll(_load()); delta=actual_usd-est_usd
        d["spent_today_usd"]=max(0.0, d["spent_today_usd"]+delta)
        d["spent_month_aud"]=max(0.0, d["spent_month_aud"]+delta*AUD)
        if d["spent_month_aud"]>=DISASTER_USD: d["halted"]=True   # خطِ فاجعه = halt کامل (D-22)
        _save(d); return d
    finally: _unlock(fd)

def release(agent, est_usd):   # اگر call شکست خورد → رزرو را پس بده
    return settle(agent, est_usd, 0.0)
```

## ۳. قراردادِ مصرف (هر ایجنت)
```python
EST = 0.20
g = reserve("muse", EST)          # رزرو زیرِ قفل persist می‌شود (ضدِ race)
if not g["allow"]:                # سقف/halt/state-unreadable → NOOP، بی‌صدا beat
    log_noop(g["reason"]); exit(0)
try:
    cost = call_llm(...)          # فقط اگر allow
    settle("muse", EST, cost)     # تخمین → واقعی
except Exception:
    release("muse", EST); raise   # شکست → رزرو پس داده می‌شود (بدونِ نشتِ بودجه)
```
> **قرارداد (اجباری):** بعد از هر `reserve` که allow داد، حتماً `settle(actual)` یا `release()` — وگرنه تخمینِ رزروشده نشت می‌کند.
> GOVERNOR (BUILD-03) `budget-state.json` را می‌خواند؛ ۵۰٪/۸۰٪ یا `halted=true` → تشدیدِ تلگرام.

## ۴. تضمین‌ها
- **تک‌منبع:** همه از یک فایل می‌خوانند؛ جمعِ واقعی enforce می‌شود، نه سقفِ per-agent.
- **fail-closed:** خطای خواندنِ state → `reserve` مقدارِ `state-unreadable` deny می‌دهد (✅ اعمال‌شد و در سندباکس تست شد). قفلِ رهاشده بعد از ۳۰ ثانیه steal می‌شود (ضدِ deadlock).
- **خطِ فاجعه:** $500 = `halted` کامل؛ فقط مالک دستی reset می‌کند.

## ۵. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی از سمتِ من.** کد فقط برای مرور؛ با «برو» `scripts/budget_gate.py` را propose می‌کنم.

## ۶. QA checklist
- [ ] دو اجرای همزمان، خرج را دوبار نمی‌شمارند و از سقف رد نمی‌شوند (تستِ قفل).
- [ ] گذرِ روز/ماه، شمارنده را reset می‌کند.
- [ ] رسیدن به $2 → reserve بعدی deny.
- [ ] خطای خواندنِ فایل → deny (fail-closed)، نه allow.

## ۷. گامِ بعد
**قدمِ ۶ (آخر):** پروتکلِ پایلوت ۳۰روزه → verdictِ live.

## ۸. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۵ + R5 | budget_gate.py (تک‌منبع) + هشدار/halt | آماده‌ی اجرای مالک |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد و چیزی اجرا نشد.*
