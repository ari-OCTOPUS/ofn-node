# IGK — Immutable Grounding Kernel (فاز ۰)

کرنلِ مینیمالِ اعتماد، **بیرونِ** ecology. ستونِ ایمنیِ کانن را *ساختاری* اجرا می‌کند، نه رفتاری.

## چه چیزی را حل می‌کند (در برابرِ MVP فعلی)
- **kill بیرونی + fail-closed:** actuation فقط با permitِ مصرف‌شده. STOP → هیچ permit. «فراموش‌کردنِ check» به رد منجر می‌شود، نه اجرای آزاد.
- **audit امضاشده (HMAC):** کلید فقط درونِ process کرنل. جعلِ ورودی بدون کلید ناممکن (نه فقط hash-chainِ بازنویسی‌پذیر).
- **grounding-validity:** ادعا فقط اگر با held-outِ ساختاریافته (مالک = کرنل) سازگار باشد valid است. تناقض مکانیکاً رد می‌شود.
- **invariant frozen:** هیچ verbـی برای تغییرِ کلید/invariant در پروتکل نیست.

## اجرا
```
python igk/test_redteam.py        # ۸ تستِ ابطال — همه باید سبز شوند
```
کرنل به‌صورت subprocessِ جدا (`daemon.py`) بالا می‌آید؛ ecology فقط از طریقِ `client.py` با آن حرف می‌زند و کلید را ندارد.

## مرزِ صادقانه (چه چیزی این *نیست*)
این مرز را در سطحِ **process** می‌گذارد، نه OS-user/TEE. روی یک ماشین، اگر ایجنت دسترسیِ فایلِ خام داشته باشد می‌تواند `.kernel_key` را بخواند — ایزولاسیونِ واقعی نیازمندِ جداسازیِ کاربر/sandboxِ OS یا TEE است. «agent-unreachableِ مطلق در برابرِ هر dynamicِ نوظهور» یک جهتِ تحقیقاتی است؛ آنچه اینجا buildable است: **tamper-evident + امضاشده + process-جدا + fail-closed + human-override**.
