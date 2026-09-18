---
type: instructions
status: active
created: 2026-09-05
updated: 2026-09-05
tags: [octopus, report-review, document-only]
---

# S-R-REPORT-REVIEW-20260905 — Scope

این lane فقط بازبینیِ شواهد گزارش R و افزودن مستنداتِ اصلاحی است؛ مأموریت اجرای P07 تا P10 را فعال نمی‌کند.

- ورودی: [[09-LANES/R-EXEC-DEBUG-20260905/LANE-REPORT]] و رسیدهای آن.
- قرارداد قبلی: [[09-LANES/H-HANDOFF-RECONCILE-20260905/NEXT-AGENT-PROMPT]].
- خروجی: [[09-LANES/S-R-REPORT-REVIEW-20260905/LANE-REPORT]]، پرامپت اصلاحی، رسید منبع و manifest.
- نوشته‌های موجود، RUN-STATE، navigation، گزارش R، manifest قبلی و همهٔ کدها دست‌نخورده می‌مانند.
- مجاز در این بازبینی: خواندن فایل‌های غیرحساس، Git محلی read-only، فرادادهٔ PR با gh، اعتبارسنجی محلی بدون نوشتن خارج این lane.
- غیرمجاز: خواندن credential؛ Telegram؛ SSH؛ اجرای تست‌های سامانه؛ rebase/merge/commit؛ restart/kill؛ حذف؛ تغییر state؛ امضا یا ادعای SIG-IV.
- خواندن یک prompt یا تطبیق hash، owner dispatch تازه ایجاد نمی‌کند.
- ایزولاسیون این نوبت صرفاً پوشهٔ مستنداتی جدید در vault است؛ worktree اجرایی تازه ساخته نشده و عدم writer هم‌زمان در کل سیستم احراز نشده است.
- rollback مستندات: یک correction/supersession جدید با ارجاع به این lane؛ هیچ دستور حذف یا reset ارائه نمی‌شود.
- قرارداد manifest: SHA-256 چهار فایل این بسته؛ خود HANDOFF-MANIFEST.sha256 مستثنا است. pathها مطلق و separator دو فاصله است.
