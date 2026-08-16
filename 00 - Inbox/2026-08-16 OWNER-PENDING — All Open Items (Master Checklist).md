---
type: knowledge
kind: master-pending
status: active
updated: 2026-08-16
created: 2026-08-16
created_by: agent
tags: [owner, pending, votes, checklist, follow-up]
---

# 📋 OWNER-PENDING — همهٔ کارهای باز مالک (یک‌جا)

> **طرز استفاده:** هر ردیف = یک تصمیم یک‌کلمه‌ای یا یک فرمان. به هر ایجنتی که می‌دهی، فقط این فایل + STATE را نشان بده. بسته که شد، تیک بزن + تاریخ + عین کلمهٔ رأی.

## 🔴 فوری (عملیاتی)

- [x] **«پوش»** — دروازهٔ OWNER-EASE = آری («پوش — برو») 2026-08-16 ~16:3x. شمارش زندهٔ `germline/master..HEAD` را همان لحظه بگیر؛ هش‌های کهنهٔ `0670297`/`5922d39` را تکرار نکن. این نشست پس از کامیت شواهد push می‌کند.
- [x] ~~انتخاب مگاپرامپت ایجنت بعدی~~ **نسل راحتی EXECUTED ~16:3x:** `agent-prompts/MEGAPROMPT-OWNER-EASE-2026-08-16.md` — شواهد [[../06-EVIDENCE/OWNER-EASE-2026-08-16|OWNER-EASE]] · نوت [[../07 - Knowledge/شناخت-اختاپوس/52-OWNER-EASE-2026-08-16|۵۲]]. آزاد **C-034**.
- [x] ~~MEGAPROMPT-INTERVIEW-OCTOPUS-ORGANISM~~ اجرا شد 2026-08-16 ~15:1x با تفویض «run it and fix it». شواهد: [[../06-EVIDENCE/INTERVIEW-ORGANISM-2026-08-16|INTERVIEW-ORGANISM]].
- [x] **ری‌استارت رسمی سه عضو env-قدیمی** — 2026-08-16 ~16:37 `RESTART-PROCESS.ps1` live/center/gateway exit=0. OLLAMA: 9836/11500/20572 `qwen2.5:latest` → **7852/11724/4504 `qwen2.5:1.5b`**. :8773/api/live=200.

## 🟡 رأی‌های شکار خطا (کارت‌های ۱/۳/۴/۵ + بازمانده) — جزئیات: [[../02-DECISIONS/ERRORHUNT-CARDS-2026-08-16|ERRORHUNT-CARDS]]

- [x] **۱ — پروب orchestr/Fugu:** اجرا 2026-08-16 ~16:36 OWNER-EASE دروازه ۵. یک تماس sakana/fugu · **HTTP 429** · quota 60→61 · مدار خاموش نشد. آخرین موفقیت دیسک همچنان 08-12.
- [ ] **۳ — سقف سوکت reason:** هم‌ترازی `PAID_ASK_BUDGET_S_*` با max_tokens فعلی (۳۶ هشدار؛ بدون رأی تماس‌ها ممکن است بریده شوند)
- [ ] **۴ — HF_TOKEN:** توکن اختیاری هاب برای دیمون (فقط نام کلید) — آری = ساکت شدن هشدار هر بوت؛ نه = نویز INFO
- [ ] **۵ — هش کرنل body_bridge:** تازه‌سازی manifest برای SENSITIVITY-LADDER/GEOMETRY یا پذیرش دائمی `integrity_ok=false` (دو فایل دیگر سالم‌اند)
- [x] **بازمانده — OctopusLiveDataRefresh:** سبز. 2026-08-16 15:58 LastTaskResult=0 · `live-data.js` همان دقیقه · SEAM-LOOP از قبل تسک را بسته بود.

## 🟠 رأی‌های تست-سخت (پنج کارت) — جزئیات: [[2026-08-16 DISCOVERY — Capability Hard-Test Scorecard|HARD-TEST Scorecard]]

- [ ] **VOTE 1 — منشای ردیف‌های حافظه:** ستون provenance + احراز، پیش از هر مسیر ورودِ بیرونی (سم ۱۰/۱۰ منحرف می‌کند)
- [ ] **VOTE 2 — ماندگاری ابطال PEP + ضدتکرار امضایی:** پیش‌نیاز هر enforce تلگرام (ابطال با ری‌استارت فراموش می‌شود؛ seen-file جعل‌پذیر)
- [x] ~~بازمانده — http.server :8765~~ **مرده.** 2026-08-16 ~15:1x: هیچ LISTEN روی 8765؛ هیچ پروسهٔ `http.server 8765`. REST-NIGHT کشت؛ این نشست تأیید کرد.
- [ ] **VOTE 3 — گارد هویت/استقلال belief:** مسیر additive `apply_once_per_family` نصب شد (C-031 contained). هنوز رأی می‌خواهد: اجباری روی همهٔ آپدیت‌ها قبل از سیم تولیدی epistemics.
- [ ] **VOTE 4 — پیش‌بینی‌گر پایداری (سایه):** ماژول `_ops/predictor/persistence.py` سایه است؛ **p_base عوض نشد**. ارتقا به مدل ثبت‌شده فقط با معیار روزهای گذار.
- [x] **C-026 — فیکس approve/reject:** owner-ratified 2026-08-16 OWNER-EASE دروازه ۲. گیت روی دیسک · digest+امضا valid · تست مثبت.

## 🔵 تصمیم‌های بودجه

- [ ] **deepseek v4 flash:** پروب رد شد ⇒ پیشنهاد نهایی: **بودجه همان بماند** (سقف $20/هفته = بیمه؛ مصرف ۱٫۲٪). فقط اگر مصرف‌کنندهٔ نو با عدد رأی شد، سقف بالاتر. ([[2026-08-16 SESSION — Hard-Test + Ops + DeepSeek Budget|SESSION §3-پروب]])
- [ ] (قدیمی) سقف‌های budgets.yaml / spike / disaster — بازبینی دوره‌ای

## 🟢 رأی‌های درز خودبهبودی (اجرا شد 2026-08-16 ~13:2x) — [[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|DEEP-SEAMS]]

- [ ] **VOTE 1 — experiments:** `_ops/hypothesis_engine/experiments/` صفر caller تولیدی — وصل سایه یا STATUS retired
- [ ] **VOTE 2 — مسیر رأی improve:** فلگ LEARN=1 است ولی `improve-verdicts.jsonl` غایب؛ کارت digest به live_loop نمی‌رسد
- [ ] **VOTE 3 — money-claimed:** deadline اجرا شد و صدر رفت به recall-events=90؛ اگر پول باید تا ابد قفل بماند بگو (وگرنه همین بماند)
- [ ] **VOTE 4 — ledger_ok روزانه = verify ∧ tip:** tip-commit additive است؛ ارتقای گیت روزانه جداست
- [ ] **پوش این نشست هم** بعد از کامیت DEEP-SEAMS (C-027/C-028 مصرف شدند — آزاد بعدی الان C-031 پس از IMPROVE-ACF)

## 🟢 رأی‌های خودبهبودی A+C+F (2026-08-16 ~14:2x) — [[../06-EVIDENCE/IMPROVE-ACF-2026-08-16|IMPROVE-ACF]]

- [x] **VOTE A — گارد DARE در TCB core + امضای مجدد:** owner-ratified 2026-08-16 OWNER-EASE دروازه ۳. `P_closed(±1,λ=0)` دیگر ZeroDivision نیست (۲.۵e۹ finite). امضای موجود valid بود. پوشش digestِ `core/model.py` = **C-033** (رأی جدا).
- [ ] **VOTE B — I_pred داخل run_self_test:** SETTINGS_ANCHORS در verifier import مرده است

## ⚪ بازِ قدیمی‌تر (از STATE §8 — با ایجنت بعدی پیگیری شود)

- [ ] فعال‌سازی PEP تلگرام (پس از VOTE 2) · DA-6 (B/C) · DA-1 L2/L3 (داور مستقل) · ممیز D1
- [ ] چرخش PAT (پچ آماده) · امضای trust-boundary/AEB تازه در صورت تغییر TCB
- [ ] زمان‌بند R18 (تسک Tick الان سبز است — بماند؟) · سقف ۱۰/روز صف فرضیه

---

### ثبت احکام (اینجا پر شود)

| تاریخ | قلم | کلمهٔ مالک | اجراکننده | شاهد |
|---|---|---|---|---|
| 2026-08-16 ~16:2x | پوش | پوش — برو | Cursor Grok 4.6 OWNER-EASE | دروازه ۱ · push پس از کامیت شواهد |
| 2026-08-16 ~16:2x | C-026 TCB | بله، انجام بده | همان | C-026 resolved-in-code · امضا valid |
| 2026-08-16 ~16:2x | DARE TCB | بله | همان | C-029 resolved-in-code · C-033 پوشش digest |
| 2026-08-16 ~16:2x | ری‌استارت live/center/gateway | بله، سه عضو | `RESTART-PROCESS.ps1` | pid 7852/11724/4504 · OLLAMA 1.5b |
| 2026-08-16 ~16:2x | پروب Fugu | بله، یک پروب | MultiProviderClient orchestr | HTTP 429 · quota 61 |
| 2026-08-16 ~16:2x | دامنه | B — بهداشت + طبقهٔ A | همان | LIVE-STRIP · تست NEVER-WIRED |

> مرجع ناوبری روز: [[2026-08-16 DAY-INDEX (MOC)|DAY-INDEX]] · وضعیت سیستم: [[../01-TRUTH/STATE-2026-08-15-NIGHT|STATE §8]]
