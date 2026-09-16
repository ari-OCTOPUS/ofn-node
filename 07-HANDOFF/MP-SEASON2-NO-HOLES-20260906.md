---
id: MP-SEASON2-NO-HOLES
title: سیزن ۲ — سیزنِ بدون سوراخ: هر توقفِ سیزن ۱ یک ردیف گیت‌دار می‌شود
order: MP-SEASON2-NO-HOLES
version: v1.0
issued_at: 2026-09-06 AEST
gov_version: V8
ladder: L2
effective_cap: L1
mode: GATED_WIRING_VALUE_ALTERNATING
max_diff_lines_per_row: 150
max_open_rows: 1
value_row_quota: پس از هر دو ردیف زیرساخت، یک ردیف ارزش اجباری
state: READY
verify_status: UNVALIDATED
evidence_basis:
  - receipts/mega-debug-20260906T0830Z.jsonl (51 رکورد)
  - receipts/p0-wedge-20260906T2325Z.jsonl (77+ رکورد)
  - ops/organism-anatomy/EXECUTIVE-VERDICT.json
  - ops/WIRING.yaml (14 ردیف، تصمیم کامل)
  - ops/foundry/CONCEPT-DEBT.json (ratio = 1.0، زشت و صادق)
  - ops/STATE.json (binding_gate = GATE-3)
---

# فرمان مالک — سیزن ۲ · «سوراخی نمانَد، ارزشی بنشیند»

**از:** آری · **به:** ایجنت ارشد مقیم
**اصل مادر سیزن ۱ که سیزن ۲ هم مادر است:**

```text
UPTIME ≠ HEALTH · PROCESS_ALIVE ≠ CAPABILITY_READY · RECEIPT_WRITTEN ≠ SUCCESS
UNKNOWN ≠ GREEN · WIRE > BUILD · RETIRE = SUCCESS · SILENCE_IS_APPROVAL = false
REAL_BOTTLENECK = VERIFIED_CASH = 0   ← تا این چهار رقم نشود، هر ردیف زیرساخت
                                        فقط مجاز است وقتی یک ردیف ارزش را باز کند
```

---

## ۰ — مبنای این سند: رسید، نه خاطره

سیزن ۱ این‌ها را با هش ثابت کرد؛ سیزن ۲ اجازه ندارد هیچ‌کدام را دوباره «کشف» کند:

```text
wedged single-slot llama      : last-good 174507Z · first-bad 180008Z · 18 wake · T_WEDGE≈6h (n=1)
GO_DIED_AT                    = NO_READER  (GO بدون خواننده = توقف با نام زیبا)
OWNER_GATE                    = NAME_MATCH → STRUCTURAL_NOT_AUTHENTICATED (S13، RED رسمی)
deadlines                     = client 60s < server 120s (H03، RED رسمی)
freshness                     = صفر ورودی تصمیم freshness دارد (INV-W14، RED رسمی)
census                        = 14 artifact · 5 بی‌مصرف · 0 UNKNOWN
CONCEPT_DEBT_RATIO            = 1.0  (16 استخراج · 1 کد · 0 مصرف‌کننده · 0 نتیجه)
```

هر عدد بالا مسیر رسید دارد. سیزن ۲ از همین نقطه شروع می‌کند و فقط رو به جلو می‌رود.

---

## ۱ — سیزن ۱ چه سوراخ‌هایی گذاشت؛ سیزن ۲ هر سوراخ را می‌بندد

هر سوراخ = یک کلاس توقف + یک invariant کشنده + یک ردیف گیت‌دار با RED اول. ترتیب ثابت است، CAP-1 (یک ردیف باز) و CAP-3 (هر دو زیرساخت → یک ارزش) مطلق‌اند.

| ردیف | سوراخ سیزن ۱ | invariant کشنده | تحویل گیت‌دار | RED موجود؟ |
|---|---|---|---|---|
| **W-A1** | GO/owner-packet بی‌خواننده (`GO_DIED_AT=NO_READER`) | `INV-W1` | خوانندهٔ `state/owner-go/` در scheduler — **ساخته شد (83e2c0443/d5d2f726)** — فعال و تا دو wake متوالی `ok:true` مشاهده شود | ✅ seq 69→71 |
| **W-A2** | alert بی‌مصرف + دکتر بی‌خواننده (`report.json` I3) | `INV-W1` | `doctor report → OWNER-CARD` (الگوی W-03) | ساختِ RED در ردیف |
| **W-A3** | `outcome→score→update` غایب (SA-7، دکتر تکاملی صفر) | `INV-W9/S9` | `outcomes.jsonl` + scorer + `N_DECISIONS_SCORED` با مخرج صریح؛ **ممنوع**: credibility/evolution engine | RED در ردیف |
| **W-A4** | وارونگی deadline (60<120 → wedge) | `INV-W3` | `client timeout ≥ server timeout` در adapter | ✅ seq 64 |
| **W-A5** | ورودی تصمیم بی‌تازگی (SOT Aug-28، sqlite Aug-24) | `INV-W14` | `freshness_s + input_as_of` در هر receipt + آستانه → `STALE_INPUT` | ✅ seq 64 |
| **W-A6** | طوفان incident (۳۸k بی‌مصرف، inode) | `INV-W1/W10` | episode compaction + rotation + مصرف‌کنندهٔ card | پس از W-A1 |
| **W-A7** | `RUNTIME_MODE` دروغ‌گوی سبز (Aug-27) | `INV-W2` | RETIRE یا وصل به حسگر واقعی؛ تا آن موقع مقدار = UNKNOWN نه GREEN | ✅ (STATE) |
| **W-A8** | احراز packet با تطبیق نام (S13) | `INV-W13` | registry-hash append-only + RED جعلیِ خوش‌نام | ✅ seq 50/56 |
| **W-A9** | دو checkout، حادثه در دیده‌نشده | `INV-W5` | اعلام canonical checkout هر نود + تطبیق WorkingDirectory سرویس‌ها | ساخت در ردیف |
| **W-A10** | سقف‌های نامرئی (MemoryHigh 97% · disk 95% · inode) | `INV-W10` | `tools/headroom.py` سه سقف → گیت BLOCKED، خروجی به OWNER-CARD | ساخت در ردیف |
| **W-A11** | خودگواهی (REDِ خودم، GREENِ خودم) | `INV-W12` | هر WIRED با شاهد مستقل یا برچسب `INDEPENDENT_FIXTURE_PASS(caveat)` | پروسهٔ witness |
| **W-A12** | آلودگی تست به state زنده (FIXED_ISO ×۸) | `INV-W13-تست` | هیچ تستی بیرون tmpdir نمی‌نویسد | ✅ درس ثبت‌شده |

**قاعدهٔ مقدار (CAP-3 سیزن ۲):** بعد از W-A1 و W-A2 → **SHELF-1** (یک محصول کامل، لود بی‌خطای مرورگر بیرونی). بعد از W-A4 و W-A5 → **CHECKOUT-1** (order_id + payout_id). بدون این دو، W-A6 به بعد شروع نمی‌شود.

---

## ۲ — ترتیب اجرا (صف گیت‌دار؛ یک ردیف باز، بیشترین مجاز)

```text
فاز ۰  بستن فریز: wedge-2 شاهد گرفته می‌شود (H_TIME=SUPPORTED) یا 12:00Z رد می‌شود (REFUTED)
فاز ۱  W-A1 فعال‌سازی نهایی: دو wake متوالی ok:true → ROW-1=WIRED → OMLL نیمه‌بسته بسته می‌شود
فاز ۲  W-A2 رندر دکتر → کارت؛ W-A3 outcomes.jsonl + scorer (N_DECISIONS_SCORED: 0 → ≥1)
⛔ SHELF-1 (تصمیم محتوایی مالک + آپلود + لود بی‌خطا)
فاز ۳  W-A4 patch deadline (RED→GREEN→رأی deploy) · W-A5 freshness fields
⛔ CHECKOUT-1 (کارت مالک → order_id/payout_id)
فاز ۴  W-A6/W-A7/W-A8/W-A9/W-A10/W-A11/W-A12 به ترتیب leverage
فاز ۵  گیت‌ها: GATE-3 (import contract کامل) → GATE-4 → مسیر حافظه — فقط با رسید
```

**قفل‌های مطلق (دست نمی‌خورند):** `may_authorize=false` · A2/A3 · TCB · allowlist · Event Spine (پشت GATE-6) · سه قفل GOV-V8 · push/merge بدون رأی.

---

## ۳ — invariantهای سیزن ۲ (هر کدام یک تست، هر تست رسید)

```text
INV-W1  هیچ artifactی بدون مصرف‌کنندهٔ ثبت‌شده یا RETIRE با تاریخ   (سبز: W-02)
INV-W2  هر گزارش سلامت liveness و capability را جدا دارد          (RED: RUNTIME_MODE دروغ)
INV-W3  deadline بیرونی ≥ درونی در هر زنجیره                       (RED: 60<120)
INV-W5  هر نود دقیقاً یک canonical checkout اعلام‌شده
INV-W9  ادعای T2+ نیازمند رسید خواندنِ مصرف‌کنندهٔ واقعی
INV-W10 سه سقف منبع (RSS/disk/inode) گیت‌اند نه هشدار
INV-W12 بدون شاهد مستقل، برچسب SELF_AUTHORED می‌ماند
INV-W13 اصالت packet = registry-hash، نه تطبیق نام                 (RED: seq 56)
INV-W14 هر ورودی تصمیم freshness_s + آستانه دارد                   (RED: seq 64)
INV-W15 هیچ تستی بیرون tmpdir نمی‌نویسد
```

---

## ۴ — قرارداد گزارش سیزن ۲ (هفتگی، ماشین‌تولید از STATE+WIRING+LEDGER)

```text
ORDER=MP-SEASON2-NO-HOLES · HOLES_CLOSED= · HOLES_OPEN= · CAP3_VALUE_ROWS=
CONCEPT_DEBT_RATIO= (باید از 1.0 پایین بیاید) · N_DECISIONS_SCORED= · WIRING_UNKNOWN=0
LIVE_CAUSAL_RATIO= (هدف: از 6/23 بالا برود چون RETIRE هم حساب می‌شود)
VERIFIED_CASH= · SHELF1_STATE= · CHECKOUT1_STATE= · MTBF_EPISODES=
NO_NEW_SUBSYSTEMS=0 · MAX_DIFF≤150 · PUSHED=no · HISTORY_REWRITTEN=no
```

---

## ۵ — پنج تلهٔ سیزن ۲ (هر کدام سیزن ۱ را دیدیم)

1. **«مدل برگشت، حل شد»** — restart probe بازیابی است؛ ROOT_CAUSE تا `n≥2` PARTIAL می‌ماند.
2. **«تست سبز = اثبات»** — بدون شاهد مستقل، SELF_AUTHORED است. سیزن ۱ خودش را باخودش گواهی گرفت.
3. **«سیم بکشیم بعداً مصرف‌کننده می‌سازیم»** — نه. مصرف‌کنندهٔ نام‌دار پیش‌شرط سیم است (G-A).
4. **«سه جبههٔ موازی»** — CAP-1. استنتاج علّی با موازی‌کاری مرد.
5. **«زیرساخت پاک است، ارزش بعدی»** — CAP-3. دو زیرساخت بدون یک ارزش = شکست دور، حتی با ۱۲ سبز.

---

## ۶ — و تعریف موفقیت سیزن ۲

```text
سیزن ۲ موفق است اگر و فقط اگر:
  (الف) همهٔ ۱۲ سوراخ، حالت گیت‌دار داشته باشند (بسته یا RETIRE با دلیل — UNKNOWN ممنوع)
  (ب) حداقل یک حلقهٔ مشاهده→تصمیم→نتیجه با یک trace_id کامل بسته شده باشد
  (ج) N_DECISIONS_SCORED ≥ 1 با مخرج صریح
  (د) VERIFIED_CASH مسیرش باز باشد: یک تراکنش REPORTED_NOT_VERIFIED ثبت شده
  (هـ) هیچ زیرسیستم تازه‌ای ساخته نشده باشد
و اگر فقط یکی ممکن بود: (د) — چون REAL_BOTTLENECK پول است، نه دید.
```
