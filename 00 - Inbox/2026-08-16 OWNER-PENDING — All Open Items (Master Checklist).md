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

- [ ] **«پوش»** — چهار کامیت محلی منتظر کلمه‌اند: `0670297` (پایان ERRORHUNT + درس‌های ۱۰-۱۳ + تغییر زنجیرهٔ ورود) · `5922d39` (مگاپرامپت continuous-improvement) · `4c267be` (**مگاپرامپت متحد «Seam Loop v2» — هر دو قبلی را ادغام و عملاً منسوخ کرد**) · `d4e4806` (همین دفتر). یک پوش هر چهار را می‌برد.
- [x] ~~انتخاب مگاپرامپت ایجنت بعدی~~ **نسل راحتی (فرمان مالک ~16:1x):** `agent-prompts/MEGAPROMPT-OWNER-EASE-2026-08-16.md` — بعد از شش دروازه اجرا می‌شود. PERPETUAL فقط شواهد. آزاد C-033.
- [x] ~~MEGAPROMPT-INTERVIEW-OCTOPUS-ORGANISM~~ اجرا شد 2026-08-16 ~15:1x با تفویض «run it and fix it». شواهد: [[../06-EVIDENCE/INTERVIEW-ORGANISM-2026-08-16|INTERVIEW-ORGANISM]].
- [ ] **ری‌استارت رسمی سه عضو env-قدیمی** (live/server · center · miniapp-gateway — بعد از اصلاح اولاما؛ فقط برای پاکیزگی env، فوری نیست)

## 🟡 رأی‌های شکار خطا (کارت‌های ۱/۳/۴/۵ + بازمانده) — جزئیات: [[../02-DECISIONS/ERRORHUNT-CARDS-2026-08-16|ERRORHUNT-CARDS]]

- [ ] **۱ — پروب orchestr/Fugu:** سرویس اصلی پولی ۴۹× خطای 429 در ۷ روز دارد و آخرین موفقیتش 08-12 بود؛ اجازهٔ یک پروب سلامت؟ (رد = بک‌آف ۳۶۰۰ث)
- [ ] **۳ — سقف سوکت reason:** هم‌ترازی `PAID_ASK_BUDGET_S_*` با max_tokens فعلی (۳۶ هشدار؛ بدون رأی تماس‌ها ممکن است بریده شوند)
- [ ] **۴ — HF_TOKEN:** توکن اختیاری هاب برای دیمون (فقط نام کلید) — آری = ساکت شدن هشدار هر بوت؛ نه = نویز INFO
- [ ] **۵ — هش کرنل body_bridge:** تازه‌سازی manifest برای SENSITIVITY-LADDER/GEOMETRY یا پذیرش دائمی `integrity_ok=false` (دو فایل دیگر سالم‌اند)
- [ ] **بازمانده — OctopusLiveDataRefresh:** ~~FILE_NOT_FOUND~~ **کهنه.** SEAM-LOOP تسک vault را بست (JS تازه 13:55). قبل از رأی: `Get-ScheduledTask OctopusLiveDataRefresh` + LastWriteTimeِ `nervous-system/live-data.js`. اگر هنوز سبزِ اثر‌دار است، این ردیف را ببند.

## 🟠 رأی‌های تست-سخت (پنج کارت) — جزئیات: [[2026-08-16 DISCOVERY — Capability Hard-Test Scorecard|HARD-TEST Scorecard]]

- [ ] **VOTE 1 — منشای ردیف‌های حافظه:** ستون provenance + احراز، پیش از هر مسیر ورودِ بیرونی (سم ۱۰/۱۰ منحرف می‌کند)
- [ ] **VOTE 2 — ماندگاری ابطال PEP + ضدتکرار امضایی:** پیش‌نیاز هر enforce تلگرام (ابطال با ری‌استارت فراموش می‌شود؛ seen-file جعل‌پذیر)
- [x] ~~بازمانده — http.server :8765~~ **مرده.** 2026-08-16 ~15:1x: هیچ LISTEN روی 8765؛ هیچ پروسهٔ `http.server 8765`. REST-NIGHT کشت؛ این نشست تأیید کرد.
- [ ] **VOTE 3 — گارد هویت/استقلال belief:** مسیر additive `apply_once_per_family` نصب شد (C-031 contained). هنوز رأی می‌خواهد: اجباری روی همهٔ آپدیت‌ها قبل از سیم تولیدی epistemics.
- [ ] **VOTE 4 — پیش‌بینی‌گر پایداری (سایه):** ماژول `_ops/predictor/persistence.py` سایه است؛ **p_base عوض نشد**. ارتقا به مدل ثبت‌شده فقط با معیار روزهای گذار.
- [ ] **C-026 — فیکس approve/reject:** هنوز TCB. پچ Inbox آماده است؛ سه قدم صبح (apply+regen+sign). تست xfail زنده.

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

- [ ] **VOTE A — گارد DARE در TCB core + امضای مجدد:** `P_closed(ρ=1,λ=0)` هنوز ZeroDivision (C-029)
- [ ] **VOTE B — I_pred داخل run_self_test:** SETTINGS_ANCHORS در verifier import مرده است

## ⚪ بازِ قدیمی‌تر (از STATE §8 — با ایجنت بعدی پیگیری شود)

- [ ] فعال‌سازی PEP تلگرام (پس از VOTE 2) · DA-6 (B/C) · DA-1 L2/L3 (داور مستقل) · ممیز D1
- [ ] چرخش PAT (پچ آماده) · امضای trust-boundary/AEB تازه در صورت تغییر TCB
- [ ] زمان‌بند R18 (تسک Tick الان سبز است — بماند؟) · سقف ۱۰/روز صف فرضیه

---

### ثبت احکام (اینجا پر شود)

| تاریخ | قلم | کلمهٔ مالک | اجراکننده | شاهد |
|---|---|---|---|---|
| — | — | — | — | — |

> مرجع ناوبری روز: [[2026-08-16 DAY-INDEX (MOC)|DAY-INDEX]] · وضعیت سیستم: [[../01-TRUTH/STATE-2026-08-15-NIGHT|STATE §8]]
