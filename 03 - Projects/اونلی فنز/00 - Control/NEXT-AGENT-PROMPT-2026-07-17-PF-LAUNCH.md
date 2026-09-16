# NEXT-AGENT PROMPT — Project-F Launch (مسیر الف)
**تاریخ ساخت:** 2026-07-17
**نویسنده:** ایجنت نشست الف (Saba UI debug + VaultBank wiring)
**اسکوپ این پرامپت:** فقط مسیر **الف / Launch infra**. مسیر ب (اختاپوس) و ج (accounting/PocketSmith) جداگانه‌اند — پایین اشاره شده.

---

## 0) قانون طلایی (fail-closed)
- **هیچ اکشن بیرونی نزن:** ساخت اکانت، لاگین، پست عمومی، DM، publish، ارسال PPV، فعال‌سازی BotFather روی chat واقعی — همه human-gated و ممنوع بدون تأیید صریح مالک.
- **هیچ flag با ریسک HIGH را خودت در `.env` روشن نکن.** فقط in-process/propose.
- **commit فقط با pathspec صریح** — هرگز `git add -A`. dirtyهای `_ops/` را لمس نکن.
- **هیچ مبلغ/PII به LLM ابری نرود.**
- اگر آنتی‌ویروس `.git/objects` را lock کرد → retry بعد از چند ثانیه.

---

## 1) اولین کار (بلاک‌کننده): تست‌ها را واقعاً اجرا کن
نشست قبلی shell نداشت؛ کد ویرایش و با خواندن sanity-check شد ولی **تست واقعی اجرا نشد**. اول این را ببند:

```bash
cd "F:/backup/03 - Projects/اونلی فنز/studio"
python -m unittest test_saba_studio -v

cd "F:/backup/03 - Projects/اونلی فنز/langar"
python -m pytest test_pf_admin.py -q
```

یا از root پروژه:
```bash
cd "F:/backup/03 - Projects/اونلی فنز"
python -m pytest studio/test_saba_studio.py langar/test_pf_admin.py -q
```

**انتظار:** Saba ~۱۶ تست سبز، pf_admin سبز (شامل تست vault status).
اگر هر failure واقعی بود → قبل از هر کار جدید، رفعش کن. گزارش نتیجه را در Control ثبت کن.

---

## 2) وضعیت فعلی (بعد از نشست الف)
### فایل‌های تغییرکرده در نشست قبل
- `studio/saba_studio.py`
- `studio/test_saba_studio.py`
- `studio/config.json`
- `studio/README-SABA-RUNBOOK.md`
- `studio/SABA-STUDIO-SPEC.md`
- `langar/pf_admin.py`
- `brain/acquisition_pipeline.py`
- `langar/test_pf_admin.py`

### چه چیزی درست شد
- **Shadow-mode سبا واقعاً کار می‌کند** (`chat=0` مجاز شد؛ قبلاً به‌خاطر `saba_chat_id=0` route نمی‌شد).
- **Text aliases** برای تست بدون تلگرام: `/new /drafts /today /cal /more /trend /ppv /stats /inbox /rules /brief /cap /scope /cancel`.
- **Self-cert aliases:** `/faceless /feet /no_explicit /18 /done`.
- **HALT fail-closed:** فقط `/resume` یا `s:resume` باز می‌ماند.
- **navigation cancel-safe:** رفتن وسط ثبت درفت دیگر متن بعدی را ناخواسته title نمی‌کند.
- **ارقام فارسی/عربی ظرفیت** پشتیبانی شد (`۳٫۵`→`3.5`).
- **OpSec copy:** نام انسانی در خروجی → «اپراتور/Creator».
- **config.json:** taskهای calendar از actionهای بیرونی به Creator-facing/human-gated تبدیل شد.
- **VaultBank به `pf_admin._default_pipe()` inject شد** (LearningBridge از قبل وصل بود، برخلاف deep-scan قدیمی).
- **`/pf_status` وضعیت vault را شفاف می‌گوید:** `vault: N asset — منبع draft` یا `vault: 0 asset — fallback`.

---

## 3) تست دستی shadow-mode (بعد از سبز شدن unit tests)
```bash
cd "F:/backup/03 - Projects/اونلی فنز/studio"
python saba_studio.py
```
stdin:
```
/start
/new
ست ابریشم — قرمز انار
/faceless
/feet
/no_explicit
/18
/done
/drafts
/cap
۳٫۵
/halt
/drafts
/resume
```
**انتظار:** درفت ثبت، self-cert کامل، cap=3.5، در HALT هیچ صفحهٔ عادی باز نشود، بعد از resume منو برگردد.

---

## 4) قدم‌های بعدی مسیر الف (به‌ترتیب، همه propose-only)
1. **پر کردن VaultBank** با ۱۰–۲۰ asset امن از طریق `/vault_add` (یا `vault_admin.py`).
2. تست flow کامل اکتساب:
   ```
   /vault_list
   /pf_status        ← باید vault: N asset نشان دهد
   /pf_plan 3
   /pf_queue
   /pf_ok <id>
   /pf_ready <id>
   ```
3. تأیید اینکه drafts واقعاً از vault می‌آیند (نه fallback `_SAFE_HOOKS`).
4. **DM HITL** و **KPI recording** — همچنان بدون اجرای بیرونی (فقط ثبت/propose).
5. بعد از سبز شدن همه، «۶ تعارض باز» را برای مالک reconcile کن (نام برند، نردبان قیمت ۳ نسخه، Fansly، Persian/Sydney در copy، body expansion). این‌ها **تصمیم مالک‌اند**، خودت انتخاب نکن — کارت پیشنهاد بده.

---

## 5) ضدالگوها (تکرار نکن)
- روشن‌کردن token/chat واقعی سبا بدون تأیید مالک.
- فعال‌کردن هر publish/send/DM path.
- `git add -A` یا commit روی `_ops/`.
- تغییر «۶ تعارض باز» بدون رأی مالک.
- overwrite کردن گزارش‌های Control موجود.

---

## 6) مسیرهای موازی (خارج از اسکوپ این پرامپت — دست نزن مگر مالک بگوید)
- **ج) Accounting/PocketSmith:** deep-scan جدا انجام شده. رجوع کن به:
  - `DEEP-SCAN-2026-07-17-POCKETSMITH-STATUS.md`
  - `EXEC-PROMPT-2026-07-17-POCKETSMITH-RESYNC.md`
  خلاصه: داده ~۳ ماه stale (آخرین txn 2026-04-20)، فلگ‌های `OCTOPUS_WIRE_POCKETSMITH` و `_PS_WRITEBACK` خاموش، ۸۳٪ تراکنش‌ها `unknown/needs_review`، double-entry ledger هرگز اجرا نشده. کد آماده است؛ فقط resync امن + فعال‌سازی. **باگ dedup واقعی:** `_hash` (full desc) vs `_content_hash` (desc[:20]) ناهماهنگ → ریسک double-count؛ قبل از resync ببند.
- **ب) اختاپوس/security/activation:** رجوع به deep-scan اصلی و ACTIVATION-REPORT. اول S1 auth-gate، S2 `_write_env` non-destructive، S3 watchdog split-brain؛ بعد ~۷۰ قابلیت خفته.

---

## 7) ترتیب لود پیشنهادی برای شروع
1. این فایل.
2. `DEEP-SCAN-2026-07-17-FOR-NEXT-AGENT.md` (§۷ نقش، §۹ ترتیب لود).
3. `studio/README-SABA-RUNBOOK.md` + `studio/SABA-STUDIO-SPEC.md`.
4. `langar/pf_admin.py` + `brain/acquisition_pipeline.py`.
5. سپس بخش ۱ (اجرای تست) را انجام بده.
