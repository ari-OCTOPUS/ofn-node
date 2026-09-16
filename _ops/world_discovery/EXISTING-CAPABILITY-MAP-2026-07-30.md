# EXISTING-CAPABILITY-MAP-2026-07-30
# نقشهٔ قابلیت‌های موجود اختاپوس (فقط‌خواندنی) — مبنا برای adapter نه duplicate

> [FACT] هدف: قابلیت موجود را دوباره نسازیم؛ adapter می‌سازیم. این ماتریس از بازخوانی
> فقط‌خواندنی فایل‌های canonical (بند ۵ پرامپت) در 2026-07-30 ساخته شده.

## ماتریس قابلیت

| قابلیت | موجود | زنده | قابل استفاده | شکاف برای world-discovery | فایل canonical |
|---|:---:|:---:|:---:|---|---|
| web retrieval (public, no paid API) | ✅ | ✅ | بله | فقط snippet نه full-page؛ ۳ منبع ثابت (DDG/Wiki/arXiv)؛ بدون tiering | `cortex/web_research.py` (`search`, `research_topics`, `Opener`) |
| source policy / tiering (A/B/C/D) | ❌ | ❌ | — | وجود ندارد؛ باید ساخته شود | — |
| freshness / stale detection | ❌ | ❌ | — | وجود ندارد؛ باید ساخته شود | — |
| evidence با URL + date | نیمه | ✅ | بله | `{title,snippet,url,source}` دارد ولی date/structured confidence نه | `cortex/web_research.py` |
| source independence (same-origin dedup) | ❌ | ❌ | — | وجود ندارد؛ باید ساخته شود | — |
| contradiction search | ❌ | ❌ | — | وجود ندارد؛ باید ساخته شود | — |
| competitor analysis | ❌ | ❌ | — | وجود ندارد؛ باید ساخته شود | — |
| novelty check vs octopus memory | ❌ | ❌ | — | `learning_gate` فقط admission دارد، pre-check نه | — |
| opportunity scoring | نیمه | ✅ | نه | `lead_scorer.py` دامنه-specific (نقاشی) است؛ generic لازم است | `legs/lead_scorer.py` |
| experiment design | ✅ | ✅ | الگو | `research_contract` immutable + falsifiable ولیtools= self-improvement | `outcomes/research_contract.py`, `outcomes/research_loop.py` |
| owner handoff / owner gate | ✅ | ✅ | بله | Telegram ApprovalChannel کامل با buttons؛ `propose_only_apply_guard` | `budget/approval_channel.py`, `outcomes/research_loop.py` |
| outcome feedback | ✅ | ✅ | الگو | calibration loop generic ولی wired به research outcomes | `outcomes/research_loop.py` (`record_calibration`) |
| egress / external action gating (L0–L4) | ✅ | نیمه | بله | `egress_policy.py` deny-by-default + self-tested؛ wiring `[EST]` | `synapse/egress_policy.py` |
| prompt-injection isolation | ❌ | ❌ | — | "caller مسئول sanitize" ولی sanitizer وجود ندارد؛ باید ساخته شود | — |

## نقاط اتصال کلیدی (reuse)

1. **retrieval**: از `cortex/web_research.py` با `Opener` قابل‌تزریق → در `public_web.py` wrapper می‌سازیم که tier/date/independence اضافه می‌کند.
2. **egress gating**: از الگوی `synapse/egress_policy.py` (deny-by-default، `DECLARED_ENDPOINTS`) برای allowlist هاست‌های مجاز تحقیق.
3. **owner gate / Telegram**: `budget/approval_channel.py::TelegramApprovalChannel.send_text` نقطهٔ اتصال نهایی است — ولی چون dirty است، در `action_boundary.py` یک interface مستقل تعریف می‌کنیم و در `INTEGRATION-MANIFEST.md` این نقطه را ثبت می‌کنیم.

## نقاط ساخت جدید (ارزش افزودهٔ اندام)

tiering, freshness, source-independence, contradiction search, novelty receipt, competitor matrix, generic opportunity scorer, prompt-injection isolation — این‌ها غایب‌اند و همین‌ها مزیت اندام جدید هستند.

## تصمیم‌های طراحی `[INFERENCE]`

- **retrieval را duplicate نمی‌کنیم**: `public_web.py` یک retriever interface تعریف می‌کند که پیاده‌سازیِ پیش‌فرضش `cortex.web_research` را به‌عنوان backend صدا می‌زند (با import محافظت‌شده، بدون ویرایش آن فایل). اگر import شکست خورد (مثلاً dirty/unavailable)، یک fallback stdlib-only فعال می‌شود.
- **scorer generic**: الگوی dataclass از `lead_scorer` الهام می‌گیرد ولی کاملاً مستقل و دامنهٔ رقابت AI است.
- **owner gate**: interface مستقل `OwnerGate` با پیاده‌سازی `TelegramOwnerGate` که در manifest به `approval_channel.send_text` وصل می‌شود — اما **داخل کد فعال نیست تا پذیرش ایجنت ارشد**.
