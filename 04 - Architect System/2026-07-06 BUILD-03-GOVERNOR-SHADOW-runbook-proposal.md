---
type: runbook-proposal
status: proposal            # propose-only — runbookِ آماده. من چیزی نصب/اجرا نکردم.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «برو» 2026-07-06 → قدمِ ۳ نقشه"
depends_on: "[[2026-07-06 BUILD-02-GENOME-READONLY-GUARD-runbook-proposal]] · [[2026-07-06 PHASE2-GOVERNOR-SPEC-proposal]] · REPORT §۴ قدم۳"
grounds: [ARCHITECT_CHARTER §۱/§۷ (propose-only، تلگرام=رابطِ مالک), LAPTOP-RUNTIME §۴/§۵, DOCTOR-BLUEPRINT]
tags: [build-03, governor, shadow, supervisor, propose-only]
---

# BUILD-03 — GOVERNOR در حالتِ shadow (propose-only)

> **shadow یعنی:** GOVERNOR فقط **می‌خواند، چک می‌کند، گزارش می‌دهد** — صفر اعمال، صفر call خارجی، صفر جهش، و در این مرحله **صفر LLM** (کاملاً قطعی، پس $0). این «سایه‌اولِ» گزارش (R4) است پیش از هر live.

---

## ۱. GOVERNOR در shadow چه می‌کند (هر تیک)
1. **kill-check:** اگر `STOP`/halted → فقط heartbeat، خروج (fail-closed، D-06).
2. **heartbeat:** فقط سطرِ خودش در `_memory/HEARTBEAT.md`.
3. **health:** `dashboard_doctor.py` را اجرا/می‌خواند؛ `effective_score < 70` → alert.
4. **genome:** `genome_guard.py` (BUILD-02) را اجرا؛ هر `genome-unapproved-change` → alert.
5. **backup:** `FAILED.flag` یا کهنه‌بودنِ `LAST-OK.flag` (BUILD-01) → alert.
6. **escalate:** alertها را در **outboxِ محلی** می‌نویسد؛ (اختیاری) پینگِ تلگرام به **خودِ مالک**.

> **صفر LLM در shadow:** همهٔ چک‌ها قطعی‌اند. routingِ Haiku/Sonnet فقط وقتی GOVERNOR به **live** ارتقا یابد روشن می‌شود (قدمِ ۶، با verdict). پس shadow هم امن‌ترین است هم رایگان.

## ۲. نکتهٔ حاکمیتی — تلگرامِ مالک ≠ «پیام خارجی»
لیستِ سیاهِ منشور «پیامِ خارجی» را منع می‌کند (ایمیل/SMS/پستِ عمومی به شخصِ ثالث). ولی تلگرام **رابطِ خودِ مالک** است و منشور §۱ صراحتاً «ارسالِ پیشنهاد به تلگرام» را مجاز می‌داند. برای احتیاطِ shadow: **اولویت با outboxِ محلی**؛ تلگرام اختیاری و فقط به مالک.

## ۳. governor_shadow.py (قطعی · zero-LLM · فقط خواندن + heartbeat + alert)
```python
#!/usr/bin/env python3
# governor_shadow.py — سرپرستِ shadow. می‌خواند/چک می‌کند/گزارش می‌دهد. صفر اعمال، صفر LLM.
import json, subprocess, sys, pathlib, datetime

VAULT  = pathlib.Path(r"F:\backup\04 - Architect System")
SCRIPTS= VAULT / "scripts"
OPS    = pathlib.Path(r"F:\backup\_ops")
STOP   = VAULT / "STOP"
HEART  = VAULT / "_memory" / "HEARTBEAT.md"
ALERTS = OPS / "governor" / "governor-alerts.md"

def run_json(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "").strip()
        if not out: return {"_error": f"no output (exit={r.returncode}) {r.stderr[:150]}"}
        return json.loads(out)                 # خروجیِ خالی/نامعتبر = خطا، نه «سالم» (رفعِ حفرهٔ integration-test)
    except Exception as e:
        return {"_error": str(e)}

def beat(line):
    HEART.parent.mkdir(parents=True, exist_ok=True)
    with HEART.open("a", encoding="utf-8") as f:
        f.write(line + "\n")            # فقط سطرِ خودش (append)

def alert(now, items):
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS.open("a", encoding="utf-8") as f:
        f.write(f"## {now}\n" + "\n".join(f"- ⚠️ {i}" for i in items) + "\n\n")
    # (اختیاری) اینجا فقط به تلگرامِ مالک از طریقِ langar — هرگز شخصِ ثالث.

def main():
    now = datetime.datetime.now().isoformat(timespec="seconds")
    if STOP.exists():
        beat(f"- {now} · governor=HALTED (STOP) · beat-only"); return
    a = []
    doc = run_json([sys.executable, str(SCRIPTS/"dashboard_doctor.py")])
    if not isinstance(doc, dict) or doc.get("_error"):        # خطای خاموش = شدیدترین باگ (منشور §۴)
        a.append("doctor FAILED to run")
    elif doc.get("effective_score", 100) < 70:
        a.append(f"health effective_score={doc.get('effective_score')}")
    gen = run_json([sys.executable, str(SCRIPTS/"genome_guard.py")])
    if not isinstance(gen, dict) or gen.get("_error") or gen.get("error"):
        a.append("genome_guard FAILED to run")               # عدمِ اجرای گارد ≠ سالم
    elif gen.get("genome_ok") is False:
        a.append("GENOME unapproved change: " + str([f.get('file') for f in gen.get('findings',[])]))
    if (OPS/"backup"/"FAILED.flag").exists():
        a.append("backup FAILED flag present")
    if a: alert(now, a)
    beat(f"- {now} · governor=shadow · {'ALERT×'+str(len(a)) if a else 'ok'}")

if __name__ == "__main__":
    main()
```

## ۴. زمان‌بندی (Task Scheduler — سبک برای shadow)
```powershell
schtasks /Create /TN "GovernorShadow" /TR "powershell -NoProfile -Command python C:\ops\governor_shadow.py" `
         /SC MINUTE /MO 15 /RU SYSTEM /RL HIGHEST /F
```
> هر ۱۵ دقیقه کافی است (قطعی و ارزان). **NSSM** برای فازِ live/always-onِ واقعی می‌ماند (قدم ۶). برای shadow، Task Scheduler ساده‌تر است و با الگویِ زمان‌بندِ موجودت یکی است.

## ۵. تضمین‌های shadow (چه چیزی *نمی‌کند*)
- ❌ هیچ اعمال/جهش/تغییرِ کد/قاعده. ❌ هیچ call خارجی. ❌ هیچ LLM.
- ✅ فقط خواندن + سطرِ heartbeatِ خودش + فایلِ alert. مسیرِ نوشتنِ Anchor Ledger ندارد (منشور §۴).
- ✅ STOP/halted را محترم می‌شمارد (fail-closed).

## ۶. متریک‌های پایلوت (۳۰ روز، برای تصمیمِ live)
- uptime٪ (تعدادِ heartbeatهای به‌موقع).
- تعداد و **دقتِ** alertها (false-positiveِ پایین لازم است).
- صفر CRITICALِ ژنومِ رسیدگی‌نشده.
- backup: `LAST-OK` همیشه تازه، `FAILED` هرگز طولانی.

## ۷. معیارِ ارتقا shadow → live (قدم ۶)
فقط با: (الف) ۳۰ روز shadowِ تمیز · (ب) drillِ restore موفق · (پ) دقتِ alert قابل‌قبول · (ت) **verdictِ صریحِ آری**. آن‌موقع GOVERNOR می‌تواند routingِ LLM + اقداماتِ از-پیش-تأییدشده را بگیرد — نه زودتر.

## ۸. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی از سمتِ من.** کد فقط برای مرور. با یک «برو» فایل‌های `scripts/governor_shadow.py` (+ BUILD-01/02) را propose می‌کنم؛ نصبِ Task Scheduler دستِ توست.

## ۹. QA checklist
- [ ] با `STOP` حاضر، فقط beat می‌زند (تستِ fail-closed).
- [ ] دکتر/گارد را درست می‌خواند و alert را در outbox می‌نویسد.
- [ ] هیچ مسیرِ نوشتنی جز HEARTBEAT(سطرِ خودش) + governor-alerts.md ندارد.
- [ ] صفر فراخوانِ LLM/خارجی (ممیزیِ کد).

## ۱۰. باز مانده و گامِ بعد
- بازِ verdict نیست.
- **قدمِ ۴ نقشه:** MUSE + دکترِ تکاملی در **dry-run** (قرنطینه پر می‌شود، هیچ‌چی forward نمی‌شود تا کالیبره شود).

## ۱۱. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۳ | governor_shadow.py (قطعی) + زمان‌بندی + outboxِ alert | آماده‌ی اجرای مالک |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد و چیزی نصب/اجرا نشد.*
