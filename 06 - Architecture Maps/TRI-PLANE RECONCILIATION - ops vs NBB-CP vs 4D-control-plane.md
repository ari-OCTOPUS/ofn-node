---
type: architecture
status: draft
tags: [control-plane, governance, reconciliation, tri-plane, ops, nbb-cp, 4d, coupled-not-merged]
created: 2026-07-12
updated: 2026-07-12
created_by: agent
decision_ref: [VQ-ROOT-001, VQ-NBB-001, VQ-4D-001]
sources:
  - "[[06 - Architecture Maps/URCP Reconciliation - control-plane on OCTOPUS]] (control-plane ~۶۰٪ ساخته)"
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]] (دکترینِ coupled-not-merged)"
  - "[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-09]] (استکِ لایه‌ای)"
  - "[[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY]] (قاعدهٔ extend-don't-rival)"
  - "[[VERDICT_QUEUE]] (VQ-ROOT-001, VQ-NBB-001, VQ-4D-001)"
  - "کدِ زنده: _ops/ · app/nbb-control-plane-history.bundle · C:\\Users\\Armin\\Desktop\\4d_system\\control_plane (۲۱۴ تست)"
---

# آشتیِ سه‌پلینِ کنترلی — `_ops` × `NBB-CP` × `4D control_plane`

> رأی مالک ۲۰۲۶-۰۷-۱۲: «C — فقط سند آشتیِ کامل، بدون کد، بدون سیم‌کشی.»
> این سند **propose-only** است؛ هیچ کدی را تغییر نمی‌دهد، هیچ چیزی را merge/wire نمی‌کند،
> و هیچ فایلِ موجودی را بازنویسی نمی‌کند. فقط سه پیاده‌سازیِ **هم‌دکترین** را de-metaphor
> می‌کند، نسبتشان را با دکترینِ موجودِ خودِ vault (ADR-001 + URCP) روشن می‌کند، و تصمیم را
> به صفِ کانونیِ [[VERDICT_QUEUE]] برمی‌گرداند.

## ۰. چرا این سند لازم شد (زمینه)

سه چیز مستقل، در سه زمان و سه مکان، **یک دکترین** را پیاده کرده‌اند (تمرکزِ کنترل نه هوش ·
fail-closed برای پول/خارجی · evidence/ledger · propose-only · human-gate برای high-risk).
تا وقتی نسبتشان صریح نشود، خطرِ واقعی = **دوباره‌سازی** و **دوپارگیِ منبعِ حقیقت** است
(همان R2 که [[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY|LANGAR registry]] درباره‌ی ledgerِ موازی هشدار می‌دهد).

یک تصحیحِ صادقانه‌ی لازم: تحلیلِ بیرونیِ سشنِ 4D (که به `F:` دید نداشت) نتیجه گرفته بود
«سرِ اختاپوس ساخته نشده». **این غلط بود** — سر (`_ops`) زنده است. این سند آن اشتباه را جبران می‌کند.

## ۱. de-metaphor — سه پلین واقعاً چه هستند

| پلین | چیستِ مهندسی | محلِ کدِ زنده | بلوغ (VERIFIED) | نقشِ درست |
|---|---|---|---|---|
| **`_ops`** | ارگانیسمِ خودگاورنورِ همیشه‌روشن: organism.py + cortex + heart + budget(governor/epoch/fitness/replication) + epistemics(hash-chain) + neural + doctor + events + governor | `F:\backup\_ops` | 🟢 سرِ زنده (رییس). URCP: ~۶۰٪ control-plane از قبل این‌جاست؛ registry ساخته (`registry_scan.py`، ۱۳ موجودیت) | **HEAD** — حکمرانیِ کلِ اکوسیستم، منبعِ حقیقتِ حاکمیت |
| **`NBB-CP`** | control-plane سخت‌شده‌ی قابل‌حمل (governor/invariants) — «دوقلوی حاکمِ هم‌دکترین» | `F:\backup\app\nbb-control-plane-history.bundle` + خطِ زنده‌ی `_launchpad/second-brain-live` (control-brain/painting-bot/accounting-bot) + worktree دسکتاپ | 🟡 اسکلت هارد‌شده (طبق حافظه ~۱۶۲–۲۰۷ تست، REPORTED — باید rerun شود) | **PORTABLE TWIN** — الگوی قابل‌حملِ governor؛ نسبتش با `_ops` هنوز رأی‌نخورده |
| **`4D control_plane`** | پلینِ observe→shadow→approve→kill→self-heal، خودبسنده، درونِ یک limb | `C:\Users\Armin\Desktop\4d_system\control_plane` (۲۱۴ تست، v1..v5) + آینه‌ی بی‌گیتِ `F:\backup\4d_system` | 🟢 production-grade در سطحِ پا | **LIMB PLANE** — حاکمیتِ داخلیِ پای پژوهشی |

سه چیزِ متمایز، نه سه رقیب. مثلِ سه معنیِ «قلب» در [[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged|ADR-001]] که اول de-metaphor شدند.

## ۲. دکترینِ آشتی از قبل در vault هست — دوباره اختراعش نکن

دو سندِ موجود مسیر را تعیین می‌کنند؛ این سند فقط آن‌ها را روی سه‌پلین اعمال می‌کند:

1. **ADR-001 «coupled, not merged»:** دو ماژولِ کنترلی باید به‌هم‌بسته بمانند نه یکی‌شده. سه دلیلِ آن مستقیماً این‌جا صدق می‌کند:
   - **دامنه‌ی شکستِ مشترک ممنوع:** اگر `4D` یا `NBB-CP` داخلِ `_ops` merge شوند، crashِ یکی = مرگِ همه. جدا بمانند تا هرکدام مستقل بتپد و reaperِ برون‌حلقه ترمیم کند (دقیقاً کاری که supervisor v5 در 4D می‌کند).
   - **حلقه‌ی حرامِ خودنمره‌دهی:** پلینی که هم عمل می‌کند هم خودش را می‌سنجد = reward-hacking. سنجش باید بیرونِ عملِ سنجیده‌شده بماند.
   - **interface = setpoint/bounds، نه فرمانِ مستقیم:** والد باید *envelope* بدهد (allowed_bands/risk_tier)، نه اینکه رفتارِ داخلیِ پا را دیکته کند. black box محفوظ.
2. **URCP Reconciliation (additive-only):** «gateway-first فقط برای مسیرهای نو؛ مسیرهای موجود دست‌نخورده؛ هر مهاجرت = رأیِ جدا.» یعنی آشتی از راهِ **registry مشترک** می‌گذرد، نه بازنویسیِ سیم‌کشی.

**نتیجه:** رابطه‌ی درست بین سه‌پلین = **coupled-not-merged از طریقِ registry، با جریانِ evidence رو-به-بالا و envelope رو-به-پایین.** نه merge، نه پلینِ چهارم.

## ۳. نگاشتِ پیشنهادی (فقط طرح — هیچ کدی این‌جا اجرا/سیم‌کشی نمی‌شود)

```text
                 مالک (تلگرام: verdict / kill)
                          │  envelope (risk_tier, allowed_bands) رو به پایین
        ┌─────────────────▼──────────────────┐
        │  _ops  = HEAD (رییس)                │
        │  registry_scan → registry-latest.json  ◄── تنها نقطه‌ی «دیدنِ همه»
        └───▲───────────────▲─────────────────┘
   evidence │               │ evidence   (رو به بالا؛ read-only از منظرِ HEAD)
     (manifest + snapshot)  │
   ┌────────┴───────┐  ┌────┴──────────────┐
   │ 4D control_plane│  │ NBB-CP (twin)     │
   │ (LIMB)          │  │ portable governor │
   └─────────────────┘  └───────────────────┘
   هر پا: MANIFEST + adapter می‌دهد؛ داخلش black box می‌ماند.
```

قرارداد آشتی (هم‌ریختِ interfaceِ ADR-001):
- **رو به بالا (evidence):** هر پلینِ پا یک `manifest` (logical_id, owner, risk_tier, capabilities) + snapshot سلامت به registryِ `_ops` می‌دهد — همان الگوی `registry_scan` که از قبل هست. read-only از منظرِ HEAD.
- **رو به پایین (envelope):** `_ops` فقط *bound* می‌دهد (این پا مجاز به چه سطحِ ریسک/بودجه است)، نه فرمانِ رفتاری. پا داخلِ envelope خودمختار است.
- **σ/حقیقت بیرونِ هر دو:** مثلِ ADR-001، وضعیت از رویدادهای CONFIRMED می‌آید نه خودگزارشِ پلین.

## ۴. سه گزینه‌ی VQ-ROOT-001 (تصمیمِ کانونیِ باز — مالک)

| گزینه | یعنی | هزینه | ریسک | سازگاری با ADR-001 |
|---|---|---|---|---|
| **A — portable sibling** (رأیِ فعلیِ مالک در چت: «C» این سند = طرح؛ خودِ اتصال جدا) | هر پلین پای مستقل؛ فقط از registry به `_ops` گزارش می‌دهد؛ صفر merge | کم | کم | ✅ کامل (coupled-not-merged) |
| **B — adapter زیر `_ops`** | پای 4D/NBB-CP سیم‌کشی شود تا evidenceش در داشبوردِ `_ops` دیده شود | متوسط (کارِ integration) | متوسط | ✅ اگر فقط evidence بالا برود، نه کنترل پایین |
| **C — جایگزینِ تدریجی** | یکی از پلین‌ها بقیه را ببلعد | زیاد | **زیاد** (god-module، دامنه‌ی شکستِ مشترک) | ❌ نقضِ ADR-001 |
| **D — فقط آزمایش** | همین‌طور جدا بمانند، بدون اتصالِ رسمی | صفر | صفر (ولی دوپارگیِ دید می‌ماند) | ✅ خنثی |

**توصیه‌ی این سند: A (portable sibling).** کمترین ریسک، صفر بازنویسی، منطبق بر دکترینِ خودِ vault. اتصالِ واقعی (registry adapter) فازِ بعد و پشتِ رأیِ جداست.

## ۵. خطوطِ قرمز (برای هر ایجنتِ آینده — لازم‌الاجرا)

- **پلینِ چهارم نساز.** سه‌تا از قبل زیادند؛ هدف آشتی است نه افزودن.
- **merge نکن.** ADR-001 صریح: coupled-not-merged. crashِ یکی نباید بقیه را بکشد.
- **ledger/registry موازی نساز** — [[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY|قاعده‌ی extend-don't-rival]]: `registry_scan` موجود تنها نقطه‌ی حقیقتِ حاکمیت است.
- **روی `_ops` سیستمِ زنده است** — بدون رأیِ صریحِ مالک هیچ کد/اجرا. ورک‌اسپیسِ امنِ آزمایش = `C:\Desktop`.
- **`4D` مرجعِ زنده = `C:\...\4d_system`** (git دارد)؛ `F:\backup\4d_system` فقط آینه (بی‌.git).
- گپ‌های واقعیِ باز (نه توهمِ «ساخته‌نشده»): Telegram Gateway مرکزیِ forum/topics (جزئی) · ۴۷ خطای گاورنر + قفلِ قیمتِ بودجه · وایرینگِ `NBB-CP`↔`_ops` (VQ-ROOT-001).

## ۶. یک تصمیمِ مالک (فقط همین)

**VQ-ROOT-001 را ببند:** نسبتِ سه‌پلین = **A / B / C / D** بالا؟
(توصیه: A.) بقیه‌ی صف — VQ-NBB-001 (نقشِ آینده‌ی NBB-CP)، VQ-4D-001 (اجرای ۳۰روزه) — بعد از این.

---
*propose-only · جلسه‌ی ۲۰۲۶-۰۷-۱۲ · هم‌راستا با ADR-001 + URCP Reconciliation · هیچ کد/merge/wire انجام نشد.*
