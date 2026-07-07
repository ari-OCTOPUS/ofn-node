---
type: report
status: draft
tags: [architecture, genome, agents, second-brain, dashboard]
created: 2026-07-06
updated: 2026-07-06
language: persian
---

# 🧬 اسپک معماری ژنوم — ژنوم اصلی + ژنوم شخصی هر بخش

> خواستهٔ آری (جلسه ۱۹): «بازطراحی هر بخش + استقلال + ژنوم شخصی خودشان کنار ژنوم اصلی» + محدوده = **داشبورد نو روی هستهٔ قدیم** + دامنه = **همهٔ بیزنس‌های کاری**. این اسپک روی کد واقعی `_launchpad/second-brain-live/` گراند شده، نه از صفر. status: draft — منتظر verdict آری.

## ۱. کشف کلیدی: ژنوم از قبل وجود دارد

مفهوم «ژنوم» دقیقاً روی دو چیزِ موجود می‌نشیند — فقط باید رسمی و کامل شود:

| مفهوم آری | چیست | کجای کد |
|---|---|---|
| **ژنوم اصلی** (مشترک، به‌ارث می‌رسد) | DNA مشترک همهٔ ایجنت‌ها | `core/*` + `core/contracts.py` + `evolution/` |
| **ژنوم شخصی** (منحصر هر بخش) | هویت/استراتژی هر بیزنس | `adapters/business/*.py` (الان `BusinessConfig`) |

یعنی «استقلال هر بخش» = هر آداپتر یک فایل مستقل است و Core دست نمی‌خورد (همان اصل پلاگینی `base.py`). این را نگه می‌داریم و قوی‌ترش می‌کنیم.

## ۲. ژنوم اصلی (Main Genome) — DNA مشترک، تغییرناپذیر بدون verdict

هر ایجنت این‌ها را از هسته به ارث می‌برد و **نمی‌تواند override کند**:

- **قرارداد دو رکن** (`contracts.py`): رکن A تحقیق→Brief · رکن B پیام approve-first.
- **Gateway** (`gateway.py`): DeepSeek موتور اصلی · Fugu فقط escalation پشت budget-gate · کش · سقف روزانه.
- **حافظه** (`memory.py` / `core.db`): brief/feedback/knowledge/outbox مشترک با فیلد `business`.
- **صف approve-first** (`approval.py`): هیچ پیام بیرونی بدون تأیید ادمین.
- **ایمنی** (`safety.py`): halt/resume سه‌سطحی + kill.
- **مغز تکاملی** (`evolution/brain.py`): propose-only، هرگز کد اصلی را مستقیم نمی‌زند.
- **گاردهای قفل‌شده:** privacy (دیتای Project-F هرگز به Fugu نرود) · GATE 0 · Inbox-first · secret فقط در `.env`/KeePass.

## ۳. ژنوم شخصی (Personal Genome) — schema پیشنهادی

توسعهٔ `BusinessConfig` فعلی. فیلدهای **موجود** + فیلدهای **نو** (برای استقلال واقعی):

```python
@dataclass
class PersonalGenome:
    # — هویت (موجود) —
    id: str; name: str; owner_ref: str; owner_name: str
    market: str
    # — شخصیت (نو: فراتر از tone) —
    persona: str            # «همکار ارشد مارکتینگ»، نه خودشیفته — سیستم‌پرامپت هویت
    voice: str              # لحن پیام رکن B (= tone فعلی)
    values: list[str]       # خط‌قرمزها/سبک برند (مثلاً ToS-safe, بدون اغراق)
    # — استراتژی (موجود + نو) —
    topics: list[str]       # زوایای تحقیق چرخشی وزن‌دار (موجود)
    goals: list[str]        # اهداف درآمدی/رشد این بخش (نو)
    channels: list[str]     # ["telegram"] فعلاً؛ آماده برای whatsapp/instagram (نو)
    context_note: str       # قیود ثابت (موجود)
    # — استقلال و حکومت (نو) —
    autonomy: str           # "propose_only" | "bounded_auto" | "status_only"
    budget_share: float     # سهم سقف روزانه (جمع همه ≤ ۱.۰)
    privacy_class: str      # "normal" | "sensitive"(→ هرگز Fugu، مثل Project-F)
    evolution_optin: bool   # مغز تکاملی حق پیشنهاد جهش روی این ژنوم دارد؟
    kpis: list[str]         # چه چیزی «برازندگی» این بخش را می‌سنجد
```

نکته: `autonomy` و `privacy_class` و `budget_share` همان قفل‌های ژنوم اصلی را **در سطح هر بخش** اجرا می‌کنند — استقلال بله، ولی زیر سقف مشترک.

## ۴. ژنوم هر بخش (نگاشت همهٔ پروژه‌ها)

| بخش | persona (خلاصه) | autonomy | privacy | کانال‌ها | KPI اصلی |
|---|---|---|---|---|---|
| **زیمان** (Sydney gifts) | مشاور فروش گرم و خانوادگی مامان | propose_only | normal | telegram (→ instagram) | سفارش/هفته زیر سقف ۳۰ |
| **نقاشی** (Lead-gen) | لیدجن حرفه‌ای نقاشی سیدنی | propose_only | normal | telegram | لید واجد شرایط/هفته |
| **حسابداری** | دستیار دقیق و بی‌اغراق | propose_only | sensitive | telegram | کار به‌موقع/خطای صفر |
| **Project-F** (OnlyFans) | مارکتر ToS-safe، محتاط | **status_only** 🔒 | **sensitive** (هرگز Fugu) | — تا GATE 0 | (منتظر verdict) |
| **دو رکن روزانه** | زیرساخت تحقیق+تعامل | propose_only | normal | telegram | — |

«خودشیفتگی» که گفتی: در `voice`/`persona` هر ژنوم صریح می‌شود «حرفه‌ای، کمک‌کننده، متواضع با اعتمادبه‌نفس» — با یک خط در سیستم‌پرامپت هویت، بدون دست‌زدن به منطق.

## ۵. داشبورد نو (محدودهٔ انتخابی آری) — view روی هستهٔ قدیم

- **اصل:** داشبورد فقط *می‌خواند* از `core.db` و API موجود + دکمه‌های approve؛ **منطق ایجنت‌ها دست‌نخورده** (همان تصمیم «داشبورد نو + هستهٔ قدیم»).
- **معماری داده:** یک endpoint سبک JSON روی `app.py`/dashboard که هر ژنوم + آخرین brief/queue/budget/KPI را می‌دهد؛ فرانت مدرن آن را رندر می‌کند.
- **تصمیم tech (verdict آری، §۷):** گزینهٔ کم‌هزینه = ارتقای همان داشبورد لوکال (تک‌فایل، بدون بیلد) · گزینهٔ شیک = Next.js جدا که فقط همان JSON را مصرف کند (بدون Vercel لازم — لوکال هم اجرا می‌شود). پیشنهاد من: **اول تک‌فایل لوکال با کارت هر ژنوم**، بعد اگر خواستی Next.js.
- **کارت هر ژنوم:** persona · autonomy/budget/privacy · آخرین brief + 👍/👎 · صف approve · KPI. — همان «داشبورد شیک» ولی روی داده‌های واقعی.

## ۶. فازبندی پیشنهادی (افزایشی، هر فاز با تأیید)

۱. **ژنوم اصلی رسمی:** `PersonalGenome` را در `base.py` بساز؛ ۵ آداپتر به آن مهاجرت کنند (backward-compatible). تست‌سوئیت سبز بماند.
۲. **persona/voice:** خط هویت هر بخش (حذف خودشیفتگی) + `privacy_class`/`autonomy` واقعی وصل به gateway.
۳. **API ژنوم:** endpoint JSON روی داشبورد.
۴. **داشبورد نو:** کارت هر ژنوم (اول لوکال).
۵. **حلقهٔ تکامل per-genome:** مغز تکاملی فقط ژنوم‌های `evolution_optin=True` را پیشنهاد جهش دهد.

## ۷. verdictهای باز برای آری

۱. Project-F: `status_only` بماند یا با GATE 0 بازِ فعلی همان محدود؟ (ریسک ToS مارکتینگ خودمختار).
۲. داشبورد: تک‌فایل لوکالِ ارتقایافته (پیشنهاد من) یا Next.js جدا؟
۳. `budget_share` هر بخش چند؟ (جمع ≤ سقف روزانهٔ DeepSeek).
۴. کدام بخش‌ها `evolution_optin=True` باشند؟

## منابع

[[00 - Inbox/2026-07-06 1325 MASTER-COWORK-STRATEGY]] · [[01 - Dashboard/HANDOFF]] · [[04 - Architect System/MYCELIAL-MASTER-SPEC]] · [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]] · کد: `_launchpad/second-brain-live/control-brain/core/contracts.py` · `adapters/business/base.py`
