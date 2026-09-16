---
type: evidence
session: ERRORHUNT
created: 2026-08-16 ~11:5x local
window: 2026-08-09 .. 2026-08-16
agent: errorhunt-debug
mode: شواهد نه ادعا · فکت‌چک پیش‌فرض (C-015/C-018)
contradiction_next_free_id: C-027
updated: 2026-08-16
---

# ERRORHUNT — خوشه‌ها و ریشه‌ها (2026-08-16)

پنجره: ۷ روز. برداشت خام: [[ERRORHUNT-RAW-2026-08-16]]. اعدادِ خوشه از pass-2 (sqlite mode=ro + لاگ‌ها) است نه از regex اول که دو مثبتِ کاذب داشت (`REVIVE` روی «no revive» · `یافت نشد` روی خط‌های غیر-readback).

**فکت‌چک پیش‌فرض مگاپرامپت (اجباری):**
- «C-019 آزاد» در لحظهٔ شروع درست بود؛ هنگام نوشتنِ دفتر، ایجنت‌های موازی C-019/C-020/C-021 را گرفته بودند. این نشست C-022 را گرفت. آزادِ زندهٔ پایان روز = **C-027**.
- «cortex گیرکرده ۲ بار در ۲۴ساعت»: در ۲۴ساعتِ گذشته **۰ REVIVE**؛ ۸× `STOP-CORTEX honored` هنگام ری‌استارت رسمی. آخرین REVIVE واقعی: 2026-08-14T11:44.
- «۱۱ خطای readback پس از فیکس باید صفر باشد»: **پس از 05:00: 67/67 ok، fail=0**. پیش از فیکس: 11 fail از 12.

## خوشه‌ها

| کلید | شمار | روند | تاکسونومی | حکم |
|---|---:|---|---|---|
| governor ⚠️ (۷روز) | 457 | ثابت/پر | مخلوط | زیرخوشه شود؛ خاموش‌کردن دفتر ممنوع |
| — circuit OPEN orchestr 429 | 49 | ↓ پس از 08-15 13:25 | WEDGE | مسیر Fugu/orchestr مرده؛ اسنپ‌شات دروغ می‌گفت closed — [[#R1]] + C-022 |
| — discovery_nudge TypeError | 11 | تکرار تا 11:31 امروز | NEW→fixed | `mark_nudged()` بی‌آرگومان — فیکس همین نشست |
| — سایر (email OAuth، سقف توکن، debate timeout، …) | ~397 | ثابت | NOISE-KNOWN / NEW | کارت/پیشنهاد؛ نه کورکردن آلارم |
| task.blocked خودتحول (تازگی 0.0<0.0) | 126 | ثابت هر بوت | NOISE-KNOWN | معیار اکیداً بیشتر؛ مرز دانش اشباع؛ فایل TCB — دست نخورده |
| memory.readback error | 11 | **صفر پس از 05:00** | NOISE-KNOWN (رفع‌شده) | رگرسیون نیست |
| STOP-CORTEX honored | 17 | خوشه‌های ری‌استارت | NOISE-KNOWN | درمان `-Force` برای wedge؛ این‌ها stop عمدی‌اند |
| cortex REVIVE (۲ miss) | 5 | آخرین 08-14 | WEDGE | واچداگ self-heal کرد؛ ۲۴ساعت اخیر صفر |
| HALT-ALL 08-12 (live+center+cortex) | 51+50+50 | تک‌رویداد ۴ساعته | NOISE-KNOWN | پنیک عمدی؛ revive نشد (درست) |
| paid-timeout (reason 36 / glm 10) | 46 | reason تا 06:01 امروز | NEW | سقف سوکت < نیاز مشتق — فلگ، کارت |
| organ-denied | 16 | ۱۳× halted:STOP + ۲× unreadable | NOISE-KNOWN | گیت درست هنگام STOP |
| miniapp tunnel restart | 12 | پراکنده، آخر 06:58 امروز | WEDGE | واچداگ تونل؛ cloudflare |
| centre HUNG | 2 | 08-13 411s · 08-15 514s | WEDGE | self-heal کشت+ریلانچ |
| REFERENCE_DIR هر بوت دیمون | 3 | ۱/نسل | NOISE-KNOWN | تشخیص C-013؛ خاموش نشود |
| HF unauth + 404های مدل | ۳ بوت | ثابت | NOISE-KNOWN | کلید `HF_TOKEN` غایب؛ 404 فایل‌های اختیاری مدل |
| RAG score < 0 | چند هشدار/بوست | ثابت | NEW | langchain؛ بدون فیکس این نشست (اولویت پایین‌تر) |
| kernel.integrity_ok=false | پیوسته در daemon_state | ثابت از 2026-07-14 | NEW | SENSITIVITY-LADDER.md + GEOMETRY.md هش نمی‌خوانند؛ rsc.py و CLAIMS_LEDGER.csv سالم |
| PEP سایه deny | 2 | امروز 05:32/05:43 | NOISE-KNOWN | طراحی سایه؛ ترافیک واقعی |
| _flaky mtime در پنجره | 68/127 فایل | — | NOISE-KNOWN | mtime ≠ flake زنده |
| Poisoning Watch LastResult | 0x80070002 → **۰ در 13:04** | تعمیر شد | NEW→fixed | لانچر `python.exe` مطلق — [[#R3]] |
| OctopusLiveDataRefresh | 2147942402 | زنده ۱۳:1x | NEW | همان کلاس FILE_NOT_FOUND؛ Execute مسیر Desktop درهم — bat در `nervous-system/refresh-live-data.bat` |

صف فرضیه زنده: pending=397 · dedup=759. beat زنده (CURRENT-TRUTH auto): 37781 · coherence 0.972 · halted=False.

## سه ریشهٔ برتر (شمار × اثر)

### R1 — اسنپ‌شات circuit «closed» بدون ریکاوریِ اثبات‌شده (C-022)

**زنجیره:** Fugu/orchestr از 08-09 با HTTP 429 trip می‌شود (۴۹ OPEN در پنجره) → بک‌آف تا 3600s → یک RECOVERED فقط در 08-10 → فایل زنده هنوز `state=closed` + `opened_at_ts` پر + `last_ok_ts=2026-08-12` + ۲۰/۲۰ false. `record_success` واقعی `opened_at` را خالی می‌کند؛ این شکل = ریست جزئی. `_target_entry` از قبل به half_open تنزل می‌داد **فقط در حافظه**؛ `status()` و JSON روی دیسک دروغِ سالم می‌گفتند. مغزِ زنده روی `reason`/DeepSeek است (`last_ok` امروز 11:20) — orchestr دیگر مسیر اصلی نیست، ولی اسنپ‌شات هنوز دروغ است.

**self-heal:** مدار بک‌آف دارد؛ ریکاوریِ اثبات‌شده ندارد تا دو `record_success`.  
**فیکس (کم‌ریسک):** persist تنزل روی دیسک + `status()` از `_target_entry` می‌گذرد. تست ۴/۴ + رگرسیون قبلی ۴/۴. **بستن پایانی 13:1x:** `status('orchestr')` روی دیسک نوشت `half_open` (opened_at هنوز پر — ریکاوری فقط با دو موفقیت).  
**باقیِ رأی:** خاموش‌کردن پروب orchestr / سهمیه Fugu — کارت ۱.

### R2 — discovery_nudge TypeError (تولیدی، ۱۱ بار)

**زنجیره:** `discoveries.mark_nudged(high_water)` اجباری شد؛ `wiring.discovery_nudge_beat` هنوز `mark_nudged()` می‌خواند؛ استثنای beat آن را می‌بلعد و در governor-alerts انبار می‌کند. فلگ دلتا در تولید روشن است وگرنه این مسیر شلیک نمی‌شد.

**self-heal:** ندارد — هر ارسال موفقِ دلتا دوباره TypeError.  
**فیکس:** `mark_nudged(time.time())` در HEAD (`f6aedd1`). تست ۲/۲. آخرین TypeError در دفتر: 11:31 — بعد از آن تکرار نشده.

### R3 — خودِ مانیتور Poisoning Watch در آخرین اجرا مرد

**زنجیره:** تسک `OCTOPUS 4d Poisoning Watch` در 10:08 با LastResult=-2147024894 (ERROR_FILE_NOT_FOUND) مرد — `py` per-user در PATH زمان‌بند نیست. نشست پایانی شب فرمان را به `C:\Program Files\Python313\python.exe` مطلق برد.

**self-heal:** ندارد.  
**فیکس Watch:** انجام شد — Ready · LastResult=0 · LastRun 13:04. خاموش‌کردن تسک ممنوع بود و نشد.  
**بازماندهٔ همان کلاس:** `OctopusLiveDataRefresh` هنوز 2147942402؛ Execute مسیر Desktop درهم است. bat زنده: `F:\backup\nervous-system\refresh-live-data.bat`.

## فیکس‌ها / غیر فیکس‌ها

| کار | چرا |
|---|---|
| persist تنزل circuit | صداقت انبار؛ allow/deny همان half_open قبلی |
| mark_nudged(high_water) | باگ تولیدی واضح؛ قرارداد از قبل در تست discoveries بود |
| readback | از قبل فیکس r16-view؛ شمار پس از فیکس صفر — دست نخورده |
| novelty 0.0 | TCB (`self_evolve.py`) + رفتار عمدی اکیداً بیشتر |
| REFERENCE_DIR | تشخیص C-013 — خاموش نشود |
| فایل زنده circuit-state.json | نوشته شد در بستن پایانی: orchestr=`half_open` (کامیت نشود) |

تست‌های نو — **ثبت در `run_all.py` در بستن پایانی** (lane آزاد شد پس از ثبت recall):
- `_ops/tests/test_circuit_demote_persist_errorhunt.py` (۴)
- `_ops/tests/test_discovery_nudge_high_water_errorhunt.py` (۲)
- `_ops/tests/test_circuit_reset_not_recovery.py` (۴)

بستن پایانی + درس‌های ۱۰–۱۳: [[../07 - Knowledge/شناخت-اختاپوس/49-NIGHT-CLOSE-ERRORHUNT-PERSIST-2026-08-16|نوت ۴۹]].
