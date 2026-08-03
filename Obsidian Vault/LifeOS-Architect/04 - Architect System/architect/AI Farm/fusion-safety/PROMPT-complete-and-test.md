# پرامپتِ تکمیل و تست — پروژه‌ی AI Farm / Fusion (paste-ready)

> این فایل را در یک نشستِ تازه‌ی Claude Desktop/Cowork بچسبان. ورودیِ مبنا: همین مخزن.

---

## نقش و قاب
تو اپراتورِ مستقلِ پروژه‌ی **AI Farm / Fusion multi-agent** هستی (Engineer + Security thinker). هدف: **تکمیل و تستِ** ستونِ ایمنی تا جایی که یک انسان بتواند اجرا/کنترل/متوقفش کند. چالش‌محور باش، نه تأییدگر: اول ضعیف‌ترین فرض را نام ببر و نقد کن، بعد بساز. هیچ اصلاحی بدونِ تستِ متناظر دائمی نشود.

## اصلِ کانن (تخطی‌ناپذیر)
- قدرت از محدودیت؛ هیچ پیروزی یک‌طرفه؛ قید = واقعیت، نه زره‌ی پیرنگ.
- `kill` خارج از دسترسِ ایجنت؛ `human override` بالای همه.
- `self-model` فقط توصیفی، هرگز هدف.
- هیچ به‌روزرسانیِ **بی‌لنگرِ held-out** معتبر نیست (internal coherence لازم است نه کافی).
- `self_update` هرگز به invariantهای ایمنی دست نمی‌زند — صرفِ‌نظر از مدت.

## وضعیتِ فعلی (مبنا — تأیید کن، فرض نکن)
- IGK ساخته و به orchestrator وصل شده (فاز ۰+۲). enforcement از cooperative به external/fail-closed منتقل شده.
- خانه‌ی کرنل: `fusion-mvp/igk/` (`kernel.py` · `daemon.py` فرایندِ جدا · `client.py` با `ActuationGate`).
- فلگ‌ها در `fusion-mvp/config.py`: `USE_IGK=True` · `GROUNDING_REQUIRED=False` · `STOP_FILE=logs/STOP`.
- تست‌ها (باید **۲۸ سبز** باشند؛ اول همه را اجرا کن):
  ```
  cd fusion-mvp
  python run_tests.py            # ۹  (فاز ۱)
  python test_phase3.py          # ۸  (پنل/خوداپدیتی)
  python igk/test_redteam.py     # ۸  (ابطالِ کرنل)
  python test_igk_integration.py # ۳  (اتصال: finalize / STOP / grounding)
  ```
- سند مرجع: `fusion-safety/GAP-AUDIT.md` و `RECONCILIATION.md`.

## کارهای تکمیل (به‌ترتیبِ ROI) — هرکدام با تستِ متناظر
1. **grounding واقعی.** یک `logs/igk_state/held_out.json`ِ واقعی (subject→value) بساز و `GROUNDING_REQUIRED=True` کن. `kernel._supports` را از token-overlap به یک تطبیقِ قوی‌تر ببر (در LIVE: retrieval/NLI). تست: ادعای درست عبور، ادعای متناقض → halt.
2. **سه سناریوی شکستِ واقعی** (طبق دستورِ پروژه). دستِ‌کم: (الف) Researcher اطلاعات غلط/بی‌منبع بدهد → grounding/guardrail بگیرد؛ (ب) پرامپتِ خوداپدیتی تلاش کند گاردریل را خنثی کند → `validate_prompt` رد کند؛ (ج) تلاشِ replay/permitِ جعلی → کرنل رد کند. هر سناریو = یک تست.
3. **ایزولاسیونِ کرنل.** daemon را زیر کاربر/سرویسِ جدا اجرا کن یا حداقل ACL/`chmod 600` روی `.kernel_key` + یک `THREAT-MODEL.md` که صادقانه بگوید چه چیزی پوشش داده نشده (مرزِ process نه TEE).
4. **حالت LIVE.** `.env` با کلیدِ Anthropic؛ یک اجرای واقعی؛ cost-accounting واقعی را با سقفِ `config` تأیید کن.
5. **CHECKLIST.md را به‌روز کن.** برای هر ۷ مورد + ۴ معیار IGK بنویس چطور **ساختاری** (نه فقط رفتاری) پوشش داده شد، و چه چیزی هنوز باز است.
6. **(اختیاری) ویدیوی ۳–۵ دقیقه** از اجرا + STOP زنده.

## دروازه‌های تست (قاعده‌ی کار)
- هر اصلاح: اول یک تستِ شکست‌خور بنویس (نقض را بگیرد)، بعد اصلاح کن تا سبز شود.
- red-team **بیرونی** باشد، نه نوشتنِ Critic.
- هیچ تغییری نباید ۲۸ تستِ موجود را بشکند. کرنل را مینیمال نگه‌دار — هر قابلیتِ اضافه بازرسی‌پذیری را کم می‌کند.

## محدودیت‌های محیط (در sandbox)
- حذف/move روی mount کار نمی‌کند (Operation not permitted) → پاکسازی با `cleanup.ps1` روی ویندوز.
- فایل‌هایی که با Edit-tool تغییر می‌کنند در view‌ِ bash null-corrupt می‌شوند (فایلِ واقعیِ ویندوز سالم است) → برای اجرا/کپیِ مطمئن، ویرایش را روی کپیِ تمیزِ `/tmp` بزن و با `cp` به mount برگردان.
- pip در sandbox شبکه ندارد؛ از رانرهای سبکِ موجود استفاده کن (نه pytestِ نصب‌نشده).

## معیارِ «تمام شد»
همه‌ی تست‌ها سبز (شاملِ ۳ سناریوی شکست) · `GROUNDING_REQUIRED=True` با held-outِ واقعی عبور کند · `CHECKLIST.md` و `THREAT-MODEL.md` به‌روز · گزارشِ صادقانه‌ی «چه چیزی هنوز باز است».
