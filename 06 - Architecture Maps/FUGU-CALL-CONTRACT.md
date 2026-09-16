---
type: design
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, fugu, governor, llm, contract, routing, budget]
created: 2026-08-02
updated: 2026-08-02
created_by: agent
sources:
  - "[[06 - Architecture Maps/OCTOPUS-INTEGRATION-STATUS]]"
  - "[[06 - Architecture Maps/OCTOPUS-DECISION-LOG]]"
---

# Fugu Call Contract — Spec

<!-- BEGIN GENERATED: vault-docs lane, 2026-08-02. ویرایشِ انسانی زیرِ «Owner notes». -->

> # ⛔ SPEC ONLY
>
> این سند **قرارداد** را توصیف می‌کند. در این جلسه هیچ کدی نوشته یا وصل نشد.
>
> **وضعِ سنجیده‌شدهٔ پایانِ جلسه:** پیاده‌سازیِ این قرارداد در `_ops/budget/governor.py`
> **وجود دارد، اجرا می‌شود، و تستِ سبز دارد** (`_ops/tests/test_governor_routing.py` — ۱۷/۱۷).
> ولی: (۱) **هیچ‌کدام در git نیستند** — هر دو `??`؛ (۲) تست در `run_all.py` ثبت نشده؛
> (۳) هیچ صداکنندهٔ **تولیدی** ندارد (تنها importکننده خودِ تست است)؛ (۴) فلگش خاموش است.
> یعنی هنوز **قابلیتِ زنده نیست**. → R-1، R-4، N-2، N-3.
>
> ⚠️ این ماژول وسطِ همین جلسه توسطِ یک lane موازی از ۱۹KB به ۲۶.۸KB رشد کرد
> (`delivery_allowed()` تابعِ نام‌دار شد، `decide()` پارامترِ `cache_lookup` گرفت).
> اگر امضاها با این سند نخواند، **درخت برنده است** — دوباره بسنج.

## چرا اصلاً قرارداد

`_ops/cortex/model_router.py::ask()` (خطِ ۴۲۶) امروز این امضا را دارد:

```
ask(task, prompt, system="", max_tokens=400, tier=None, opener=None, quality=None)
```

`task` یک رشته است که در `TASK_TIERS` به یک رده نگاشت می‌شود. یعنی صداکننده **نیت**ش را
اعلام نمی‌کند: نمی‌گوید این خروجی چقدر مهم است، آیا secret دارد، آیا قرار است چیزی بنویسد،
یا آیا اجازهٔ خرجِ گران دارد. قرارداد همین را صریح می‌کند — بدونِ عوض‌کردنِ دروازه.

## ۱۰ فیلدِ قرارداد

| فیلد | نوع | پیش‌فرضِ امن | معنی |
|---|---|---|---|
| `task_id` | str | هشِ خودکارِ `gv-<sha1[:8]>` | شناسهٔ ردیابی. صداکننده می‌تواند بدهد؛ وگرنه از خودِ قرارداد ساخته می‌شود |
| `brain` | enum | `router` | `router \| planner \| memory \| critic \| omega \| cyber` |
| `purpose` | enum | `search` | `search \| summary \| classification \| deep_audit \| security \| code_review` |
| `expected_artifact` | str (≤۱۲۰) | `""` | چه چیزی قرار است برگردد. توصیفی؛ روی مسیریابی اثر ندارد |
| `risk` | enum | `high` | `low \| medium \| high` — **ناشناخته ⇒ بالاترین احتیاط** |
| `importance` | enum | `medium` | `low \| medium \| high \| critical` |
| `contains_secrets` | bool | `False` | هر مقدارِ truthy کافی است |
| `allow_ultra` | bool | `False` | غیاب ⇒ **هرگز** ردهٔ گران |
| `is_write` | bool | `False` | آیا این تماس به عملِ نویسنده می‌انجامد |
| `cache_key` | str\|None (≤۲۰۰) | `None` | کلیدِ کش؛ غایب ⇒ بی‌کش |

**اصلِ پیش‌فرض‌ها:** همه در جهتِ **کم‌خرج و بسته**. ورودیِ ناقص یا آشغال هرگز کرش نمی‌کند و
هرگز به سمتِ گران‌تر/بازتر خطا نمی‌کند. `purpose` ناشناخته ⇒ `search` (محلی).

## قواعدِ مسیریابی — به ترتیب، اولین منطبق برنده

| # | شرط | نتیجه |
|---|---|---|
| ۱ | `is_write=True` | `route="approval_gate"`, `tier=None`. حاکم **هرگز** خودش مجوزِ نوشتن نمی‌دهد. `write_gate()` گیتِ واقعی (`capability_gate.require`) را **صدا می‌زند** — نه اینکه فقط نامش را ببرد — و هر خطا (نبودِ ماژول، importِ شکسته) = **رد**، fail-closed |
| ۲ | `contains_secrets=True` | `tier="local"`, `redact=True`, `cacheable=False`. هیچ ردهٔ راه‌دوری، تحتِ هیچ شرطی |
| ۳ | `cache_key` و hit | `route="cache"`, `tier=None` — **اصلاً هیچ تماسِ مدلی زده نمی‌شود** |
| ۴ | نگاشتِ `purpose` | `search`→local · `security`→local + `redact` · `summary`/`classification`/`code_review`→secondary · `deep_audit`→ردهٔ بالا |
| ۵ | `allow_ultra=False` و رده = بالا | نزول به `secondary` |
| ۶ | `importance="low"` | کفِ `local` — فقط نزول، هرگز صعود |
| ۷ | سقفِ پایه | رده هرگز از ردهٔ **امروزِ** همان `task` بالاتر نمی‌رود |

**سقفِ پایه چیست:** اگر صداکننده `tier` صریح بدهد، همان سقف است (چون همان چیزی است که
امروز اجرا می‌شود). وگرنه `model_router.TASK_TIERS`. importِ ناموفق ⇒ `local` — یعنی
ندانستنِ سقف، پایین‌ترین سقف است.

## سه صداقت دربارهٔ همین repo

این‌ها فرق میانِ نقشهٔ روی کاغذ و درختِ واقعی‌اند. کپی‌شان نکن بدونِ اینکه بفهمی چرا.

### ۱. ردهٔ `cyber` وجود ندارد
در کلِ درخت هیچ مغز/tierِ cyber، هیچ مسیرِ redacted-remote و هیچ redactorِ **خروجی** نیست.
پس قاعدهٔ «security → cyber با redaction» به سخت‌گیرانه‌ترین شکلِ **موجود** پیاده شد:
`local` + پرچمِ `redact=True` (صفر egress). هیچ providerِ دومی ساخته نشد.
> `cyber` در `BRAINS` به‌عنوان یک **برچسبِ brain** پذیرفته می‌شود، ولی هیچ tierِ متناظری
> ندارد. برچسب با مقصد یکی نیست.

### ۲. ردهٔ `ultra` به‌عنوان tier وجود ندارد
`model_router._TIER_ROLE` فقط `secondary→glm` و `primary→orchestr` را می‌شناسد. نقشِ
`premium` (fugu-ultra) در budgets.yaml از `ask()` **دست‌نیافتنی** است. پس «ultra» =
گران‌ترینِ *قابلِ‌دسترس* یعنی `primary`، و `allow_ultra=False` یعنی «هرگز `primary`
درخواست نکن».

### ۳. مرزِ صادقانهٔ گاردِ ultra
حاکم فقط ردهٔ **درخواستی** را تعیین می‌کند. `model_router._ask_impl` از قدیم یک fallbackِ
key-aware بینِ دو ردهٔ پولی دارد (`order = [want] + …`) که اگر `secondary` شکست بخورد ممکن
است `primary` را امتحان کند. آن رفتارِ **از پیش موجودِ** مسیریاب است؛ این قرارداد تغییرش
نمی‌دهد — نه بیشترش می‌کند نه کمترش.

> یعنی `allow_ultra=False` **تضمینِ صفر تماسِ primary نیست**؛ تضمینِ «primary را درخواست
> نکن» است. هر سندی که بیشتر از این ادعا کند، دروغ می‌گوید.

## دو لایه گاردِ secret

عمداً دو تا، چون لایهٔ دوم فرض می‌کند لایهٔ اول خراب شده:

1. در `decide()` — قاعدهٔ ۲: `contains_secrets` ⇒ `local`.
2. در `delivery_allowed(decision)` — گاردِ **تحویل**، یک تابعِ **جدا** (نه یک `if` داخلِ
   `ask`): اگر به هر دلیلی رده راه‌دور شد، تماس رد می‌شود با
   `"secret-bearing call refused: remote tier"`.

**چرا تابعِ جدا و نه یک `if`:** آزمون‌پذیری. اگر هر دو قفل داخلِ یک تابع باشند، جهش روی
هرکدام را آن‌یکی می‌پوشاند و **هر دو «SURVIVED» گزارش می‌شوند** — یعنی هیچ‌کدام سنجیده
نشده. جداکردنشان تنها راهِ اثباتِ دندان‌داشتنِ هر دو است.

و هرگز کش نمی‌شود: پاسخِ secret-دار و writeِ تأییدشده وارد `_CACHE` نمی‌شوند.

## کش

فقط **درون-پروسه‌ای**: `OrderedDict` با سقفِ ۱۲۸ (LRU). عمداً روی دیسک نیست — کشِ دیسکی
یک فایلِ حالتِ نو و یک سطحِ نشتِ نو می‌سازد و هیچ‌کدام برای «hit ⇒ صفر تماس» لازم نیست.

## ثبت

هر تصمیم — عبور یا رد — در `state/governor/decisions.jsonl` ثبت می‌شود (D-6).
فقط برچسب/رده/دلیل: `task_id, brain, purpose, risk, importance, route, tier, baseline,
clamped, redact, gate, granted, contains_secrets, allow_ultra, is_write, why`.

**هرگز:** promptی، متنِ پاسخی، یا `cache_key` خام. `cache_key` به‌شکلِ
`cache_key_h` (sha1[:12]) ثبت می‌شود. ثبت مطلقاً fail-soft است — دفتر هرگز مسیرِ مدل را
نمی‌کشد.

## فلگ و رفتارِ خاموش

- فلگ: `OCTOPUS_WIRE_GOVERNOR`، پیش‌فرض خاموش، عمداً **بیرونِ**
  `wiring.PAPER_FULL_FLAGS` (D-10). فقط env؛ هیچ فایلی روشنش نمی‌کند.
- **فلگِ خاموش یا قراردادِ غایب ⇒ passthroughِ بایت‌به‌بایت:** همان آرگومان‌ها به
  `model_router.ask` و **همان شیءِ خروجی**. صفر تصمیم، صفر ثبت، صفر کش.
- این خودش باید یک تست داشته باشد (N-3) — «passthrough است» یک ادعاست تا وقتی سنجیده شود.

## آنچه این قرارداد **نیست**

- **providerِ دوم نیست.** هیچ کلیدی نمی‌خواند، هیچ تماسِ شبکه‌ای نمی‌زند، هیچ SDK نو ندارد.
  همان `ask()` را صدا می‌زند (D-1).
- **دورزدنِ گیت نیست.** `is_write` را به گیت **می‌رساند**؛ گیت را برنمی‌دارد (D-7).
- **`wlos/packages/fugu-provider` نیست.** آن یک پروژهٔ TypeScript ِ جدا در
  `03 - Projects/WLOS - Weight Loss OS/wlos/` است، نه دروازهٔ مدلِ اختاپوس (D-2).
- **هنوز زنده نیست.** تست دارد و سبز است، ولی untracked + ثبت‌نشده در `run_all.py` +
  بدونِ صداکنندهٔ تولیدی + فلگِ خاموش. **تست صداکننده نیست.**

## قدم‌های بعد

N-2 (هر دو فایل وارد git + ثبتِ تست) → N-3 (صداکنندهٔ تولیدی) → حکمِ مالک برای
روشن‌کردنِ فلگ. به همین ترتیب، نه غیر از آن. جزئیات:
[[06 - Architecture Maps/OCTOPUS-NEXT-ACTIONS|OCTOPUS-NEXT-ACTIONS]].

<!-- END GENERATED -->

## Owner notes

<!-- دستِ مالک. -->
