# بستهٔ تصمیم مالک — F-001 (retire-miss) + OW-8 (گرسنگی صف)

**تاریخ تهیه: 2026-09-15 · GOV_VERSION=V8 · LADDER=L2 · نیازمند رأی مالک: APPLY به‌بعد از anchor-check**
**هدف تغییر: یک فایل — `/home/ari/ofn/state/ops-agent/ops_agent.py` (live sha `c2e290fd` هنگام اسکن)**
**کلاس اثر: B8-adjacent executor logic · برگشت‌پذیر با restore فایل (ops-agent oneshot-per-tick است؛ restart لازم نیست)**

---

## ۰ — شواهد جمع‌شده (همه receipt-دار، نه حدس)

| شاهد | محتوا |
|---|---|
| F-001 | G8-021 در 06:54:16Z `OPS_B_EXECUTED verified=True` و 06:59:31Z `OPS_B_CYCLE_CLOSED` گرفت، ولی هرگز از `canary-requests/` خارج نشد؛ حالا هر tick روی base خودش (`02fb704d`) در برابر live (`fc993720`) `OPS_B_STALE_BASE` می‌خورد و پنجرهٔ ۳۰دقیقه‌ای component را می‌سوزاند |
| OW-8 | در کد زنده، بررسی dependency قبل از بودجه است، ولی `return "budget-blocked"` کل حلقهٔ category را می‌بندد؛ اثبات runtime: probe گره G22 پس از ۳۴ دقیقه صفر disposition |
| OW-8b | `budget_allows(category[-2:], …)` روی `"B8_NON_TCB_PATCH_CANARY"` برچسب `"RY"` استخراج می‌کند — breaker عملاً با کلید تصادفی تغذیه می‌شود؛ رفع موقت با signature کلید «RY» انجام شده ولی کد زنده هنوز defect دارد |
| پیشینهٔ مثبت | `executed/` قبلاً کار می‌کرد (008 و 010 در آن نشسته‌اند) — پس retire path وجود دارد؛ miss مخصوص مسیر deferred/exec-then-outcome است |

دو request زنده هم‌اکنون پشت این نقص‌اند: W24-BINDER-006 (base سالم `00dd4ef3`) و TRIO-002 (`70be7440`، staged).

---

## ۱ — تغییر پیشنهادی F-001: retirement دو‌لایه

### لایهٔ ۱ — retire در لحظهٔ cycle-close (اصلاح ریشه)

در هندلری که `OPS_B_CYCLE_CLOSED` emit می‌کند، **قبل** از emit رسید، request فایل را اتمیک منتقل کن:

```python
# anchor: جایی که kind == "OPS_B_CYCLE_CLOSED" ساخته می‌شود
src = canary_dir / f"{request_id}.json"
dst = executed_dir / src.name
if src.exists():
    os.replace(src, dst)          # اتمیک، همان فایل‌سیستم
chain_emit(kind="OPS_B_CYCLE_CLOSED", request_id=request_id)
```

قانون: **رسید بعد از حرکت فایل** — اگر حرکت شکست بخورد، cycle «closed» محسوب نمی‌شود و disposition جدا (`RETIRE_FAULT`) ثبت می‌شود. این ترتیبِ عکسِ حاضر را می‌گیرد (رسید بدون اثر).

### لایهٔ ۲ — fail-safe در ابتدای ارزیابی (self-healing)

قبل از هر budget/dependency check، اگر برای `request_id` رسید `verified=True` در receipts هست:

```python
# anchor: ابتدای حلقهٔ ارزیابی هر request
if last_outcome(request_id).verified is True:
    retire_now(request_id)   # os.replace to executed/، idempotent
    continue                 # ZERO budget spend؛ bookkeeping = اثر نیست
```

اثر: حتی اگر لایهٔ ۱ در آینده miss کند (classe 020/021 دوباره ظاهر شود)، request موفق در tick بعد خودبه‌خود پاک می‌شود.

---

## ۲ — تغییر پیشنهادی OW-8: `continue` به‌جای `return`

```python
# anchor: داخل handle_spool_category، مسیر شکست بودجه
- return "budget-blocked"
+ record_disposition(request_id, "OPS_B_BLOCKED", reason=budget_reason)
+ results.append({"request": request_id, "outcome": "budget-blocked"})
+ continue
```

تمام شاخه‌های early-return دیگر (`OPS_B_STALE_BASE`، `OPS_B_DEPENDENCY_UNMET`، `UNVERIFIABLE_REQUEST`) نیز به همین الگو تبدیل شوند: **disposition ثبت + جهش به request بعدی**. خلاصهٔ نهایی cycle از `results` ساخته شود؛ رفتار cycle-level فقط اگر **همه** requestها block شدند «budget-blocked» گزارش کند.

### OW-8b — canonical category key

```python
# anchor: خط ~587، فراخوان budget_allows
- budget_allows(category[-2:], component)
+ budget_allows(CANONICAL_CATEGORY[category], component)
```

با نگاشت صریح `{"B8_NON_TCB_PATCH_CANARY": "B8", ...}` و مهاجرت خواندن signature: lookup ابتدا canonical، سپس fallback به legacy key قدیمی (تا signatureهای «RY» Append-only معتبر بمانند وbreaker فعلی ناگهان باز نشود). کلید legacy **فقط خواندنی**؛ هر signature تازه با کلید canonical ثبت می‌شود.

---

## ۳ — تست‌های پذیرش (اجباری، قبل از رأی مثبت به apply)

در harness ایزوله (الگوی systemd-run با fixture root اثبات‌شدهٔ این فصل):

| # | سناریو | قبولی |
|---|---|---|
| T1 | دو request هم‌category: اول budget-blocked، دوم ready | هر دو disposition مستقل؛ دومی execute می‌شود |
| T2 | execution موفق + verify → cycle-close | request از `canary-requests/` غایب، در `executed/` حاضر؛ رسید **بعد** از move |
| T3 | retire دوباره روی همان request | `OPS_B_REQUEST_ALREADY_EXECUTED`، بدون اثر تکراری، بدون خطا |
| T4 | request با verified قدیمی و base کهنه (شبیه‌سازی G8-021) | auto-retire در tick بعد با **صفر** مصرف بودجه |
| T5 | failure جدید در همان category + signature کلید canonical | breaker با کلید «B8» (نه «RY») باز و بسته شود؛ signatureهای legacy «RY» همچنان خوانده شوند |
| T6 | request وابسته (dependency unmet) + request مستقل آماده | مستقل اجرا شود؛ وابسته disposition حفظ شود و پاک نشود |

---

## ۴ — rollback

1. pre-image: `cp ops_agent.py ops_agent.py.pre-f001-ow8-<timestamp>` قبل از apply (در همان فایل‌سیستم state).
2. restore: `cp` برعکس + `sha256sum` read-back = pre-apply sha. ops-agent oneshot-per-tick است؛ هیچ daemon-reload یا restart لازم نیست — tick بعدی نسخهٔ قدیم را می‌خواند.
3. اگر TRIO-002 (که روی همان بلوک retire جراحی شده) هنوز deploy نشده: این تغییر base او را می‌شکند → TRIO-002 باید پس از land شدن این بسته **rebaseٔ سوم** بگیرد یا قبل‌تر از این بسته land شود. **ترتیب را مالک تعیین می‌کند** (پیشنهاد: اول این بسته؛ TRIO-002 rebase ارزان‌تر است چون ابزارش ساخته شده).

---

## ۵ — anchor-check پیش از apply (چون این بسته بدون خواندن فایل زنده نوشته شده)

این بسته از روی رسیدها و گزارش‌های runtime نوشته شده، نه از روی خواندن مستقیم خطوط فعلی `ops_agent.py`. بنابراین پیش از هر apply، سه anchor باید روی فایل زنده (`sha256sum` = مقدارِ read-شده در همان لحظه) تأیید شود:

1. `grep -n "OPS_B_CYCLE_CLOSED" ops_agent.py` → محل emit رسید، برای وصلهٔ لایهٔ ۱.
2. `grep -n "budget-blocked\|def handle_spool_category" ops_agent.py` → محل return، برای وصلهٔ OW-8.
3. `grep -n "budget_allows(.*\[-2:\]" ops_agent.py` → تأیید defect کلید «RY»، برای وصلهٔ OW-8b.

اگر هر anchor جابه‌جا شده: بسته را با نسخهٔ تازهٔ فایل re-derive کن؛ حدسِ line-number ممنوع (همان درس demُ sha اشتباه در rebase اول TRIO).

---

## ۶ — رأی درخواستی از مالک

سؤال دقیق: **آیا اعمال این بسته روی `/home/ari/ofn/state/ops-agent/ops_agent.py` پس از anchor-check + شش تست سبز در harness ایزوله مجاز است؟**

- دامنه: فقط executor logic؛ هیچ تماس با money gate، budget numbers، quota، یا transport بیرونی.
- اثر بیرونی: صفر. پیام مالک یا مشتری ارسال نمی‌شود.
- ریسک ناشناختهٔ باقی‌مانده: رقابت با TRIO-002 روی بلوک retire — در §۴ با ترتیب land مدیریت شد.
- اگر «بلی»: execution با همان کانال اثبات‌شده (فایل اسکریپت محلی → pipe به ssh، pre-image، probe رفتاری post-apply، sha read-back).
- اگر «خیر/تغییر ترتیب»: TRIO-002 اول land شود و این بسته با rebase بعد از آن.
