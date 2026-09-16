---
type: log
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, decisions, adr, governance, cockpit]
created: 2026-08-02
updated: 2026-08-02
created_by: agent
sources:
  - "[[06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH]]"
  - "[[06 - Architecture Maps/OCTOPUS-INTEGRATION-STATUS]]"
---

# OCTOPUS — Decision Log

<!-- BEGIN GENERATED: vault-docs lane, 2026-08-02. ویرایشِ انسانی زیرِ «Owner notes». -->

> **قاعده:** هر تصمیم یک **provenance** دارد و آن ستون دروغ نمی‌گوید:
> **CODE** = در خودِ درخت پیاده و سنجیده شد · **COMMIT** = از پیامِ کامیت ·
> **CHARTER** = از `_PROJECT_INSTRUCTIONS.md` · **OWNER-RELAYED** = حکمِ مالک که از طریقِ
> بریفِ همین جلسه رسید و **من متنِ اصلیِ مالک را ندیدم** · **UNKNOWN** = نسنجیدم.
>
> این سند **بازسازیِ** تصمیم‌هاست از روی شواهدِ امروز، نه رونوشتِ یک دفترِ تاریخی.
> ردیف‌های قبل از ۲۰۲۶-۰۸-۰۲ تاریخِ **کشف** دارند، نه لزوماً تاریخِ تصمیم.

## تصمیم‌های ساختاری

### D-1 · یک درِ واحد برای مدل — و فقط یکی
- **تصمیم:** هر تماسِ LLM از `_ops/cortex/model_router.py::ask()` (خطِ ۴۲۶) رد می‌شود.
  هیچ providerِ دومی ساخته نمی‌شود، هیچ ماژولی مستقیم کلید نمی‌خواند.
- **provenance:** CODE — `_ops/budget/governor.py` صریح می‌گوید «تنها مسیرِ مدل در این
  ارگانیسم `model_router.ask()` (خطِ ۴۲۶) است» و خودش هم فقط همان را صدا می‌زند.
- **پیامد:** metering، گیتِ پولی، سهمیهٔ fugu و ثبتِ سوخت همه یک نقطهٔ اجرا دارند.
- **نقضِ رایج:** طرح‌هایی که `wlos/packages/fugu-provider` را دروازه می‌نامند. غلط است — D-2.

### D-2 · `wlos` دروازهٔ مدل نیست
- **تصمیم:** `03 - Projects/WLOS - Weight Loss OS/wlos/` یک پروژهٔ **جدا** (TypeScript/Node،
  DB جدا) است. تنها پلش `_ops/cortex/wlos_bridge.py` است: فقط‌خواندنی، whitelistِ فیلد،
  پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_WLOS`، و OCTOPUS هرگز در DBِ سلامت نمی‌نویسد.
- **provenance:** CODE — docstring ِ `wlos_bridge.py` + وجودِ ۱۰ package در آن مسیر +
  نبودِ `./wlos` در ریشه.
- **تصحیح:** «`wlos/` وجود ندارد» **غلط** است و با یک grep نقض می‌شود. جملهٔ درست:
  «در ریشه نیست؛ در `03 - Projects` هست؛ دروازهٔ مدل نیست.»
- **مرزِ حریمِ خصوصی:** دادهٔ دستهٔ ویژهٔ سلامت هرگز وارد چت/نوت/HANDOFF/لاگ نمی‌شود.

### D-3 · ردهٔ `cyber` و ردهٔ `ultra` وجود ندارند
- **تصمیم:** `_TIER_ROLE` فقط `secondary→glm` و `primary→orchestr` را می‌شناسد. نقشِ
  `premium` (fugu-ultra) از `ask()` **دست‌نیافتنی** است. پس در قراردادِ حاکم،
  «ultra» = گران‌ترینِ *قابلِ‌دسترس* یعنی `primary`؛ و «security → cyber با redaction»
  به سخت‌گیرانه‌ترین شکلِ موجود پیاده شد: `local` + `redact=True` (صفر egress).
- **provenance:** CODE — `model_router._TIER_ROLE` + docstring ِ `governor.py` که خودش
  این را «صداقتِ دربارهٔ همین repo» می‌نامد.
- **چرا مهم است:** هر سندی که «tier ِ cyber» را فرض کند، به چیزی وصل می‌کند که نیست.

### D-4 · لایهٔ حقیقت داخلِ vault باشد، نه `docs/`
- **تصمیم:** سندهای حقیقت در `06 - Architecture Maps/` می‌نشینند تا Obsidian و هر دو
  validator ببینندشان.
- **provenance:** OWNER-RELAYED (بریفِ ۲۰۲۶-۰۸-۰۲).
- **⚠️ وضعِ واقعی:** کد هنوز این را نمی‌داند. `miniapp_state.py::_TRUTH` و شاخهٔ `/truth`
  در `agi2027_control/runtime.py` هر دو `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` در **ریشهٔ
  repo** را hardcode کرده‌اند. → اکشنِ N-1.
- **تصمیمِ باز:** فایلِ ریشه بماند (dual-source) یا طبقِ CHARTER به `_Archive` منتقل شود؟
  **منتظرِ حکمِ مالک.** حذف در هیچ حالتی گزینه نیست.

## تصمیم‌های ایمنی و گیت

### D-5 · Blocked Forever — مرزِ ثابت
- **تصمیم:** اتوماسیونِ لاگینِ OnlyFans/Fansly، scraping، APIهای مهندسی‌معکوس‌شده،
  auto-DM، mass messaging، cookie import — **هرگز**. نه پشتِ فلگ، نه پشتِ گیت، نه «برای تست».
- **provenance:** OWNER-RELAYED + CODE — `ops_actions.BLOCKED_PREFIXES` این را ماشینی
  اجرا می‌کند و **قبل از** allowlist چک می‌شود.
- **چرا ترتیبِ چک مهم است:** اگر روزی کسی اشتباهی یکی از این‌ها را allowlist کند، باز هم
  رد می‌شود. گارد به ترتیبش وابسته است، نه فقط به وجودش.

### D-6 · «ثبت همیشه، گیت فقط روی تحویل»
- **تصمیم:** هر تصمیم/اقدام ثبت می‌شود — چه عبور کند چه رد. فقط **تحویل** گیت دارد.
- **provenance:** CODE — `governor.record()` صریحاً همین جمله را در docstring دارد و هر
  تصمیم را می‌نویسد؛ `OpsActionEngine.execute` هم در پایان همیشه `audit.append` می‌کند.
- **چرا:** بدونِ این، «رد شد» و «اصلاً اتفاق نیفتاد» یک شکل دارند.

### D-7 · گیت وصل می‌شود، برداشته نمی‌شود
- **تصمیم:** پول، secret، حذف، outbound، اجرای کد و PII owner-gated می‌مانند. وصل‌کردنِ
  یک مسیر **به** گیت مجاز است؛ حذفِ گیت هرگز.
- **provenance:** CHARTER §۱۰ + OWNER-RELAYED + CODE (`execute` اولین شرطش `is_owner` است؛
  `POST /api/actions` بدونِ initDataِ معتبر `403`).

### D-8 · حاکم هرگز مجوزِ نوشتن صادر نمی‌کند
- **تصمیم:** `is_write=True` ⇒ `route="approval_gate"`, `granted=False`. حاکم فقط به گیتِ
  موجود (`capability_gate.require`) **ارجاع** می‌دهد.
- **provenance:** CODE — `governor.decide()` قاعدهٔ ۱، قبل از هر قاعدهٔ دیگر.

### D-9 · secret هرگز به ردهٔ راه‌دور نمی‌رود — دو لایه
- **تصمیم:** `contains_secrets` ⇒ `local` + `redact`. و **مستقلاً** در `governor.ask()`
  یک گاردِ دومِ تحویل: اگر به هر دلیلی tier راه‌دور شد، تماس رد می‌شود.
- **provenance:** CODE — `decide()` قاعدهٔ ۲ + شرطِ `d["contains_secrets"] and d["tier"] in REMOTE_TIERS`.
- **چرا دو لایه:** لایهٔ دوم فرض می‌کند لایهٔ اول خراب شده. گاردِ تک‌لایه با یک رگرسیونِ
  بالادست بی‌صدا باز می‌شود.

## تصمیم‌های عملیاتی

### D-10 · فلگِ نو خاموش و **بیرونِ** `PAPER_FULL_FLAGS`
- **تصمیم:** هر قابلیتِ نو پیش‌فرض خاموش، و اسمش داخلِ `wiring.PAPER_FULL_FLAGS` نمی‌رود
  (چون profileِ paper-full اعضای آن tuple را ۱ می‌کند — غیاب یعنی خاموش، حضور یعنی روشن).
- **provenance:** CODE + CHARTER — `wiring.py` سه‌جا این را صریح توضیح می‌دهد؛
  `governor.py` هم می‌گوید «عمداً بیرونِ `PAPER_FULL_FLAGS`». tuple الان ۱۳ عضو دارد.

### D-11 · بدونِ URL، دکمه‌ای وجود ندارد (ضدِ fake-live)
- **تصمیم:** ردیفِ «📊 داشبورد» فقط با `OCTOPUS_TG_MINIAPP=1` **و** فایلِ URL ِ تازهٔ https
  ظاهر می‌شود. `/ui` بدونِ URL صادقانه `CONFIG_NEEDED` می‌دهد، نه یک لینکِ مرده.
- **provenance:** CODE — `center.py::_home_keyboard` + شاخهٔ `/ui` در `runtime.py`.

### D-12 · صفحهٔ خانه حداکثر سه نقطهٔ تصمیم
- **تصمیم:** کیبوردِ خانه بیش از سه تصمیم ندارد؛ دکمهٔ چهارم به سطحِ دوم می‌رود.
  استثنا: ردیفِ web_app چون **نمایشی** است نه تصمیم.
- **provenance:** CODE — docstring ِ `_home_keyboard` می‌گوید این قاعدهٔ خودِ مالک است و
  گاردش (`t_the_home_keyboard_never_exceeds_three_decision_points`) دکمهٔ چهارم را گرفت،
  و **گارد بازنویسی نشد** — طراحی عوض شد.
- **درسِ عمومی:** وقتی گارد جلویت را گرفت، گارد را سبز نکن؛ طرح را عوض کن.

### D-13 · تست‌ها main-style اند
- **تصمیم:** `harness.setup()` اول، توابعِ `t_*`، `harness.run(checks)`، `sys.exit`.
  pytest-style ممنوع.
- **provenance:** OWNER-RELAYED + سابقهٔ ثبت‌شده — فایلِ pytest-styleی که مستقیم اجرا شود
  صفر assert می‌دواند و بی‌صدا سبز شمرده می‌شود؛ همین باگ یک تستِ شکسته را هفته‌ها پنهان کرد.
- **الگو:** `_ops/tests/test_tg_poll_health.py`.

### D-14 · ثبتِ تست مرکزی است — lane موازی `run_all.py` را نمی‌زند
- **تصمیم:** هر lane نامِ فایلِ تستش را **گزارش** می‌کند؛ خودش `_ops/tests/run_all.py` را
  ویرایش نمی‌کند.
- **provenance:** COMMIT — سه کامیتِ جداگانه‌ی «union … registrations» روی همین فایل
  (`8af1924`, `b61d75c`, `5ff1119`) به‌علاوهٔ `6099de4` روی `wiring.py`، `b3fb9a5` روی
  `orphan_scan.py`، `f51a3dc` روی `center.py`.
- **پیامد:** بخشِ WORKLOCK در `01 - Dashboard/HANDOFF.md`.

### D-15 · `*.md merge=union`
- **تصمیم/واقعیت:** `.gitattributes` برای همهٔ markdownها strategy ِ union دارد.
- **provenance:** CODE — `cat .gitattributes` → `*.md merge=union`.
- **پیامد (مهم):** سندهای مشترک مثلِ `HANDOFF.md` و `PROJECT.md` هنگامِ merge **بلوکِ
  تکراری** می‌گیرند نه conflict. یعنی خطای دو-lane این‌جا ساکت است. بعد از هر merge
  چشمی چک کن.

## تصمیم‌هایی که **گرفته نشده‌اند**

صادقانه: این‌ها در درخت جواب ندارند. حدس نزن.

| # | سؤالِ باز | چرا باز است |
|---|---|---|
| O-1 | فایلِ `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` در ریشه بماند یا منتقل شود؟ | دو خواننده به آن وابسته‌اند؛ انتقالِ بی‌فیکس یعنی شکستنِ `/truth` |
| O-2 | `OCTOPUS_WIRE_GOVERNOR` کِی روشن شود؟ | قبل از track شدن و تست، اصلاً نه |
| O-3 | MiniApp کجا host شود (تونل/دامنه)؟ | تصمیمِ مالک، نه ایجنت |
| O-4 | Wave-2 CRM ساخته شود؟ | طرح آماده است؛ حکمِ صریح نیامده |
| O-5 | `type: session-note` وارد Property Schema شود یا نوتِ Inbox اصلاح شود؟ | §۶: کلیدِ نو فقط با تأییدِ مالک |

<!-- END GENERATED -->

## Owner notes

<!-- دستِ مالک. حکم‌های واقعی این‌جا ثبت شوند — بالای مرز فقط بازسازیِ ماشینی است. -->
