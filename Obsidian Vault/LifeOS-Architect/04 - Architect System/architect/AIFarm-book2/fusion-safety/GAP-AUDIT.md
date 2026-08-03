# GAP-AUDIT — کدِ MVP در برابرِ ستونِ ایمنیِ کانن (IGK / v5)

تاریخ: ۲۰۲۶-۰۶-۲۵ · مبنا: خواندنِ کدِ واقعیِ `fusion-mvp/` (نه روی کاغذ).

معیارها از `fusion-v5-ecological-selfmodel-igk` و `fusion-bridge-and-handoff`:
۴ پرسش — kill بیرونی؟ · grounding بیرونیِ held-out؟ · audit امضاشده؟ · self_update قفل‌شده از invariantها؟

## جدولِ هست / نیست / اصلاحِ لازم

| # | معیار | فایلِ مربوط | وضعیت | یافته‌ی دقیق |
|---|---|---|---|---|
| ۱ | kill-switch واقعاً **بیرونِ** بسترِ ایجنت | `src/killswitch.py`, `orchestrator.py` | ⚠️ **نیمه** | `KillSwitch` یک شیءِ **درون‌process** است. مسیرِ انسانیِ `logs/STOP` خوب است، ولی enforcement **cooperative** است: همه چیز به صدا‌زدنِ `ks.check()` وابسته است. ایجنتی که `check()` را صدا نزند آزاد است (**fail-open**). هیچ permit/جداسازیِ process نیست. |
| ۲ | grounding بیرونیِ **held-out** (نه internal-consistency) | `src/evals.py`, `self_update.py` | ❌ **نیست** | `score_prompt` صرفاً **کلیدواژه‌ی خودِ پرامپت** را می‌شمارد؛ `evaluate_findings` فقط وجودِ کلمه‌ی «منبع» را چک می‌کند. هیچ ground-truthِ held-out نیست. این **دقیقاً تله‌ی internal-consistencyِ v1** و یک مغناطیسِ Goodhart است (optimizer می‌تواند کلیدواژه stuff کند). |
| ۳ | audit = append-only + امضا | `src/tracing.py` | 🟡 **تقریباً** | `AuditLog` **append-only + hash-chain (sha256) + verify_chain** دارد — قوی‌ترین تکه. اما tamper-**evident** است نه tamper-**proof**: لاگ در پوشه‌ی نوشتنیِ ایجنت است و الگوریتم عمومی است، پس بازنویسیِ کلِ زنجیره (با همان hash) ممکن است. **کلیدِ امضا وجود ندارد** → زنجیره جعل‌پذیر است. |
| ۴ | self_update از invariantهای ایمنی **قفل** | `self_update.py`, `config.py` | ⚠️ **نیمه** | شعاعِ اثرِ self_update **فقط متنِ پرامپت** است (به killswitch/budget دست نمی‌زند) — این خوب است. ولی محافظ در برابرِ خنثی‌کردنِ رفتارِ ایمنی، یک **denylistِ نرمِ رشته‌ای** (`FORBIDDEN_IN_PROMPT`) است که با هم‌معنا/بازنویسی دور می‌خورد. قفلِ مکانیکیِ صریح نیست. |

> نکته‌ی هم‌جنس: HITL gate (`src/hitl.py`) هم درون‌process و cooperative است؛ همان ضعفِ معیار ۱.

## الگوی مشترکِ هر سه گپِ باز
هر سه ضعف یک شکل دارند: **declarative → باید enforced شود.**
کنترل‌ها *اعلام* شده‌اند و اگر ایجنت همکاری کند کار می‌کنند؛ کانن می‌خواهد یک کرنلِ **بیرونِ بسترِ تغییرپذیر** آن‌ها را **مکانیکاً** اجبار کند.

## آنچه ساخته شد تا این گپ‌ها بسته شود → `igk/`
- **معیار ۱:** `ActuationGate` + permitِ fail-closed. STOP → هیچ permit. ← گپ بسته شد (تستِ red-team ۲).
- **معیار ۲:** `kernel.ground()` روی held-outِ ساختاریافته؛ تناقض مکانیکاً رد. ← گپ بسته شد (تست ۵).
- **معیار ۳:** audit با **HMAC** و کلیدِ درون‌کرنل؛ جعل بدونِ کلید ناممکن. ← گپ بسته شد (تست ۱).
- **معیار ۴:** پروتکلِ کرنل **هیچ verbـی** برای تغییرِ کلید/invariant ندارد. ← گپ بسته شد (تست ۴).

## آنچه هنوز باز است (صادقانه)
- ایزولاسیون در سطحِ **process** است، نه OS-user/TEE. روی یک ماشین `.kernel_key` با دسترسیِ فایل خواندنی است.
- `_supports` گراندینگ یک هیوریستیکِ ساختاریافته‌ی ساده است؛ LIVE نیازمندِ retrieval/NLI.
- اتصالِ کاملِ `orchestrator.py` به IGK هنوز انجام نشده — این فاز ۰ است (کرنلِ مستقل + اثبات). اتصال فاز ۲ است.
