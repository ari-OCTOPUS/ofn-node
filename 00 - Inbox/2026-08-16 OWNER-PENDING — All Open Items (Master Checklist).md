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
- [x] ~~انتخاب مگاپرامپت ایجنت بعدی~~ **نسل بستن صف (فرمان ~16:5x):** `agent-prompts/MEGAPROMPT-OWNER-CLOSE-2026-08-16.md` — هشت دروازه. آزاد **C-034**.
- [x] **مگاپرامپت Claude Cowork نوشته شد (~17:1x):** `agent-prompts/MEGAPROMPT-CLAUDE-COWORK-2026-08-16.md` — پیست موازی را SoT نگیر. نوت [[../07 - Knowledge/شناخت-اختاپوس/54-GROK-SESSION-SOT-2026-08-16|۵۴]].
- [ ] **EQUIP ترتیبی — شروع موج A (اختیاری، بعد از صف HARDTEST اگر خواستی):** پیست SHARED + `MEGAPROMPT-EQUIP-01-G2-MEMORY` به **یک** ایجنت. هم‌زمان ۱۰ گروه نده. لانچر: [[2026-08-16 MEGAPROMPT — Equip Octopus Sequential]]. نوت [[../07 - Knowledge/شناخت-اختاپوس/55-EQUIP-SEQUENTIAL-MEGAPROMPTS-2026-08-16|۵۵]]. G8 روی شاخهٔ خودش CONDITIONAL PASS است — از نو نکن.
- [x] **مگاپرامپت ایجنت بعد (مهاجرت/M0) نوشته شد (~21:0x):** `agent-prompts/MEGAPROMPT-MIGRATE-CLOSE-GAPS-2026-08-16.md` — PERPETUAL/SEAM/COWORK برای شروع این کار باطل. نوت [[../07 - Knowledge/شناخت-اختاپوس/59-MIGRATE-CLOSE-GAPS-2026-08-16|۵۹]].
- [x] **نگاشت سه برد + تصحیح FPGA (~21:2x):** نوت [[../07 - Knowledge/شناخت-اختاپوس/60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16|۶۰]]. کل ارگانیسم امشب مهاجرت نشد. PolarFire≠Artix-7.
- [x] **ابسیدین شب قفل شد (~21:3x):** نوت [[../07 - Knowledge/شناخت-اختاپوس/61-OBSIDIAN-NIGHT-LOCK-2026-08-16|۶۱]] نقطهٔ ورود کل روز. عصر هنوز ۵۴.
- [x] ~~MEGAPROMPT-INTERVIEW-OCTOPUS-ORGANISM~~ اجرا شد 2026-08-16 ~15:1x با تفویض «run it and fix it». شواهد: [[../06-EVIDENCE/INTERVIEW-ORGANISM-2026-08-16|INTERVIEW-ORGANISM]].
- [x] **ری‌استارت رسمی سه عضو env-قدیمی** — 2026-08-16 ~16:37 `RESTART-PROCESS.ps1` live/center/gateway exit=0. OLLAMA: 9836/11500/20572 `qwen2.5:latest` → **7852/11724/4504 `qwen2.5:1.5b`**. :8773/api/live=200.

## 🟡 رأی‌های شکار خطا (کارت‌های ۱/۳/۴/۵ + بازمانده) — جزئیات: [[../02-DECISIONS/ERRORHUNT-CARDS-2026-08-16|ERRORHUNT-CARDS]]

- [x] **۱ — پروب orchestr/Fugu:** اجرا 2026-08-16 ~16:36 OWNER-EASE دروازه ۵. یک تماس sakana/fugu · **HTTP 429** · quota 60→61 · مدار خاموش نشد. آخرین موفقیت دیسک همچنان 08-12.
- [x] **۳ — سقف سوکت reason:** OWNER-CLOSE دروازه ۳. `_ASK_BUDGET_BY_ROLE["REASON"]=215` (هم‌تراز ORCHESTR) · cap سوکت ۱۲۹s ≥ need ۱۲۷.۵s برای ۲۰۰۰توکن. cortex تا ری‌استارت بعدی کد کهنه دارد.
- [x] **۴ — HF_TOKEN:** OWNER-CLOSE دروازه ۵ = قفل expected-absent. هیچ `HF_TOKEN` در 4d/_ops نیست؛ توکن ساخته نشد.
- [x] **۵ — هش کرنل body_bridge:** OWNER-CLOSE دروازه ۴ = تازه. `validate_integrity` valid=True برای هر چهار فایل (SENSITIVITY-LADDER + GEOMETRY عوض شدند؛ rsc.py و CLAIMS_LEDGER از قبل جور بودند).
- [x] **بازمانده — OctopusLiveDataRefresh:** سبز. 2026-08-16 15:58 LastTaskResult=0 · `live-data.js` همان دقیقه · SEAM-LOOP از قبل تسک را بسته بود.

## 🟠 رأی‌های تست-سخت (پنج کارت) — جزئیات: [[2026-08-16 DISCOVERY — Capability Hard-Test Scorecard|HARD-TEST Scorecard]]

- [ ] **VOTE 1 — منشای ردیف‌های حافظه:** ستون provenance + احراز، پیش از هر مسیر ورودِ بیرونی (سم ۱۰/۱۰ منحرف می‌کند)
- [ ] **VOTE 2 — ماندگاری ابطال PEP + ضدتکرار امضایی:** پیش‌نیاز هر enforce تلگرام (ابطال با ری‌استارت فراموش می‌شود؛ seen-file جعل‌پذیر)
- [x] ~~بازمانده — http.server :8765~~ **مرده.** 2026-08-16 ~15:1x: هیچ LISTEN روی 8765؛ هیچ پروسهٔ `http.server 8765`. REST-NIGHT کشت؛ این نشست تأیید کرد.
- [ ] **VOTE 3 — گارد هویت/استقلال belief:** مسیر additive `apply_once_per_family` نصب شد (C-031 contained). هنوز رأی می‌خواهد: اجباری روی همهٔ آپدیت‌ها قبل از سیم تولیدی epistemics.
- [ ] **VOTE 4 — پیش‌بینی‌گر پایداری (سایه):** ماژول `_ops/predictor/persistence.py` سایه است؛ **p_base عوض نشد**. ارتقا به مدل ثبت‌شده فقط با معیار روزهای گذار.
- [x] **C-026 — فیکس approve/reject:** owner-ratified 2026-08-16 OWNER-EASE دروازه ۲. گیت روی دیسک · digest+امضا valid · تست مثبت.

## 🔵 تصمیم‌های بودجه

- [ ] **P0 overlay v3 سیم به یک PEP** — کد هست (`_ops/octopus_v3/`, WIRED=False, ۱۸/۱۸). تا رأی به organism وصل نشود. نوت ۵۶.
- [ ] **سیم fencing lease به chrono** — SoT `_ops/runtime/beat_lease.py` (۱۷/۱۷). `assert_valid()` قبل از هر beat؛ `on_event` به لجر؛ نوشتن state با token. پیشنهاد: no-lease → `pause`. نوت ۵۷.
- [ ] **اسکریپت بازرسی M0** — hardcode / CRLF / case-fold در `F:\backup` قبل از هر کپی به Arm 1.
- [ ] **IP/OS سه برد** — تا ندهی، rsync/scp نوشته نمی‌شود. نگاشت نقش‌ها: نوت ۶۰.
- [ ] **ممنوع تا رأی جدا:** کپی `killswitch.py` / approvals نوشتنی به برد خالی · dual-beat · فلگ lease روی پروسهٔ زنده.
- [ ] **قبل از M3 cutover:** یک‌بار rollback واقعی (مسیر تست‌نشده وجود ندارد).
- [ ] **deepseek v4 flash:** پروب رد شد ⇒ پیشنهاد نهایی: **بودجه همان بماند** (سقف $20/هفته = بیمه؛ مصرف ۱٫۲٪). فقط اگر مصرف‌کنندهٔ نو با عدد رأی شد، سقف بالاتر. ([[2026-08-16 SESSION — Hard-Test + Ops + DeepSeek Budget|SESSION §3-پروب]])
- [ ] (قدیمی) سقف‌های budgets.yaml / spike / disaster — بازبینی دوره‌ای

## 🟢 رأی‌های درز خودبهبودی (اجرا شد 2026-08-16 ~13:2x) — [[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|DEEP-SEAMS]]

- [x] **VOTE 1 — experiments:** OWNER-CLOSE close-honest. `STATUS.md` retired · صفر caller بیرون بسته · حذف نشد.
- [ ] **VOTE 2 — مسیر رأی improve:** فلگ LEARN=1 است ولی `improve-verdicts.jsonl` غایب؛ کارت digest به live_loop نمی‌رسد
- [x] **VOTE 3 — money-claimed:** OWNER-CLOSE: قفل ابدی نشد · recall-events صدر می‌ماند.
- [x] **VOTE 4 — ledger_ok روزانه = verify ∧ tip:** OWNER-CLOSE: ارتقا نشد · روزانه همان `verify()` · tip additive می‌ماند.
- [x] **پوش نشست Deep-Seams / OWNER-EASE:** germline هم‌تراز شد (`1c8f6b0` و بعد OWNER-CLOSE).

## 🟢 رأی‌های خودبهبودی A+C+F (2026-08-16 ~14:2x) — [[../06-EVIDENCE/IMPROVE-ACF-2026-08-16|IMPROVE-ACF]]

- [x] **VOTE A — گارد DARE در TCB core + امضای مجدد:** owner-ratified 2026-08-16 OWNER-EASE دروازه ۳. `P_closed(±1,λ=0)` دیگر ZeroDivision نیست (۲.۵e۹ finite). امضای موجود valid بود. پوشش digestِ `core/model.py` = **C-033** (رأی جدا).
- [ ] **VOTE B — I_pred داخل run_self_test:** SETTINGS_ANCHORS در verifier import مرده است

## ⚪ بازِ قدیمی‌تر (از STATE §8 — با ایجنت بعدی پیگیری شود)

- [ ] فعال‌سازی PEP تلگرام (پس از VOTE 2) · DA-6 (B/C) · DA-1 L2/L3 (داور مستقل) · ممیز D1
- [x] ~~امضای trust-boundary تازه~~ **valid** عصر ۱۶ اوت — ۱۵ فایل شامل `core/model.py` (C-033). امضای مجدد فقط اگر TCB دوباره عوض شود.
- [ ] چرخش PAT **حساب گیت‌هاب** (وب) — فایل توکن به `os.environ` رفته (SELFRUN F1). مقدار را چاپ نکن.
- [ ] زمان‌بند R18 (تسک Tick الان سبز است — بماند؟) · سقف ۱۰/روز صف فرضیه
- [ ] ری‌استارت رسمی **cortex** تا `_ASK_BUDGET_BY_ROLE[REASON]=215` در پروسه لود شود
- [ ] OFN روی برد: پوش به `ofn/board-snapshot` (دستور در [[2026-08-17 MORNING-CARDS|کارت صبح الحاقیه]])

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
| 2026-08-16 ~16:5x | پوش این پنجره | پوش — برو | Cursor Grok 4.6 OWNER-CLOSE | دروازه ۱ |
| 2026-08-16 ~16:5x | C-033 digest | بله، انجام بده | همان | 15 فایل TCB · signature valid |
| 2026-08-16 ~16:5x | سقف سوکت reason | بله | `_ASK_BUDGET_BY_ROLE[REASON]=215` | need 127.5 ≤ cap 129 |
| 2026-08-16 ~16:5x | هش کرنل | digest واقعی را تازه کن | manifest.json integrity | validate_integrity valid |
| 2026-08-16 ~16:5x | HF_TOKEN | قفل expected-absent | همان | صفر ارجاع HF_TOKEN در 4d/_ops |
| 2026-08-16 ~16:5x | Deep-Seams باقی | close-honest | STATUS retired · recall بماند · ledger verify | |
| 2026-08-16 ~16:5x | پروب پولی | نه، دیگر نزن | — | صفر تماس نو |
| 2026-08-16 ~16:5x | دامنه | B | همان + دروازه ۲/۳ مستقل | |
| 2026-08-16 ~17:2x | ابسیدین عصر | براساس تمام چت به‌روز کن | Cursor Grok 4.6 | نوت ۵۴ · DAY-INDEX #۲۱ |
| 2026-08-16 ~21:0x | مگاپرامپت ایجنت بعد | تموم چت را بخوان + مگاپرامپت + ابسیدین | Cursor Grok 4.6 | نوت ۵۹ · MIGRATE-CLOSE-GAPS |
| 2026-08-16 ~21:2x | سه برد + FPGA | مهاجرت کن / کاربرد عجیب FPGA | Cursor Grok 4.6 | نوت ۶۰ · بدون rsync · PolarFire رد |
| 2026-08-16 ~21:3x | ابسیدین | ابسیدین را بروز کن | Cursor Grok 4.6 | نوت ۶۱ · STATE §8 · HANDOFF |

> مرجع ناوبری روز: [[2026-08-16 DAY-INDEX (MOC)|DAY-INDEX]] · وضعیت سیستم: [[../01-TRUTH/STATE-2026-08-15-NIGHT|STATE §8]]
