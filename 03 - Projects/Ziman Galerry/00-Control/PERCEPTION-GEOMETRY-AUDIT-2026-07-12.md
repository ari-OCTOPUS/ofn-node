---
type: report
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[00 - Control/CONFLICT-REGISTER]]"
  - "[[00 - Control/TRUTH-REGISTER]]"
  - "[[00 - Control/STATUS]]"
  - "[[11 - Reports/Handoffs/FOUNDATION-PHASE2-HANDOFF]]"
tags: [ziman, audit, calibration, phase2, os-foundation]
aliases: ["Ziman Calibration Audit", "Perception-Geometry Audit"]
---

# CALIBRATION AUDIT — Ziman Phase-2 (2026-07-12)

> ممیزیِ راستی‌آزمایی‌شدهٔ Foundation Phase-2. استعارهٔ «حس/موج/منیفولد» به مهندسیِ واقعی ترجمه شده: ۵ حس = ۵ زیرسیستم (policy/event/memory/execution/eval)؛ منیفولد = تاکسونومیِ محصول (Product Card). **Read + verify + report + propose. هیچ کد اجرا-تغییر، هیچ فایل جابه‌جا، هیچ اکشن بیرونی.** روش: ۲ ورک‌فلوِ موازی + اجرای واقعیِ تست‌ها (۴۰/۴۰ سبز).

## Α. درک حسی — این چه سیستمی است
Ziman یک **پای (leg) اختاپوس** برای بیزنس هدیهٔ محلیِ سیدنی است، فاز validation، **propose-only، ZERO outward execution، capacity-first (D4)**. Phase-2 **از قبل ساخته شده** — ساختار OLP-1 (00–11)، سه schema، leg در `_ops`، ۴۰ تست. نقشِ من: **کالیبراسیون و کشفِ تداخل**، نه بازساخت.

## Β. فایل‌های لمس‌شده (نمونه‌های تماس)
- **Offering/schema:** `03-Offering/{PRODUCT-CARD,INVENTORY-SNAPSHOT,PHOTO-PRODUCT-MAP}-SCHEMA.yaml`, `CATALOG.md`
- **Execution:** `_ops/legs/ziman_leg.py`, `_ops/legs/ziman_phase2.py`, `_ops/wiring.py`, `_ops/organism.py`, `_ops/smoke_ziman_wire.py`
- **Policy:** `contracts/adapter.yaml`, `09-Agents/CONSTITUTION.md`, `10-Interfaces/{OCTOPUS-ADAPTER,TELEGRAM-CONTRACT}.md`, `RUNBOOK/REGISTRY`
- **Memory:** `08-Memory/{MEMORY-POLICY.md, Event-Ledger/SCHEMA.md, Candidates/}`
- **Eval:** `_ops/tests/test_ziman_{leg,phase2,wiring}.py`، `09-Agents/{Qualifications,Role-Cards}`, `05-Growth/Experiments/EXP-001-003`
- **Legacy runtime:** `control-brain/`, `ziman-agent/{worker.py,ziman.yaml}` (+ mirror trees، بخش Ε)

## Γ. نقشهٔ وضعیت فعلی (Wave-State)
```
policy (چشم)    : adapter read-only + CONSTITUTION L0-L3 + HARD_GATED frozenset  → سالم، propose-only واقعی
event (گوش)     : Event-Ledger/SCHEMA فقط؛ هیچ ledger واقعی، Candidates/ خالی    → paper، unwired
memory (بینی)   : MEMORY-POLICY + 6-step gate تعریف‌شده؛ هیچ curator/persist       → paper؛ بدون retention/decay
exec (پوست)     : ziman_leg propose-only + D4؛ leg در organism seam، flag paper-full → structurally سالم؛ اما D4 fail-open (Ε)
eval (زبان)     : ۴۰/۴۰ تست سبز؛ suite QC-01..15؛ اما validatorها unwired و اعداد unverified در suite
brain (تلفیق)   : ziman_beat هر tick → ORGANISM-STATE.ziman؛ در live فعلاً dormant (flag off) → تصمیم فعلاً تک‌حسی، نه fused
```

## Δ. ثبت حقیقت (Truth Register — delta این جلسه)
- **T16 [VERIFIED_FACT، conf 0.95]:** تست‌های Ziman **واقعاً اجرا و سبز** شدند این جلسه: `test_ziman_leg.py` 17/17، `test_ziman_phase2.py`+`test_ziman_wiring.py` 23/23 = **۴۰/۴۰**. → **T11 (REPORTED_NOT_RERUN) ارتقا یافت به VERIFIED.** (⚠ توجه: pytest روی کلِ `_ops/tests/` به‌خاطر `sys.exit()` در import یک تستِ اسکریپت‌سبک crash می‌کند؛ فایل‌های Ziman باید جدا اجرا شوند.)
- بقیهٔ T1–T15 با خواندنِ کد این جلسه تأیید شدند (به‌جز موارد conflict که در Ε تشدید شدند).

## Ε. تداخل‌های تخریبی (Interferences — یافته‌های ممیزی، رتبه‌بندی‌شده)

**🔴 I-1 (CF-01/CF-06) — D4 fail-open: گاردِ ۶/هفته unwired است.**
`capacity_fail_closed()` (سقف مؤثر=۶ تا revalidation مالک) در **دو جا** وجود دارد — `_ops/legs/ziman_phase2.py:101-107` و `ziman-agent/ziman/product.py:222-229` — ولی **در هیچ‌کدام به گیتِ D4 وصل نیست**:
- `_ops`: `campaign_check` سقف خام yaml=۳۰ را می‌خواند (`ziman_leg.py:143`)؛ ماژول `ziman_phase2` فقط توسط تستِ خودش import می‌شود.
- standalone: `worker.py:106` سقف خام ۳۰ را به `capacity.check_campaign` می‌دهد؛ `capacity_fail_closed` فقط در `phase2_cli.py:102` (snapshot reporting) استفاده می‌شود.
→ کمپینِ ۶..۳۰/هفته **approve می‌شود**، برخلافِ CONFLICT-REGISTER + QC-03 + qualification-floorِ CONSTITUTION («۳۰/هفته را verified نگیر»). گاردْ prose + dead-code است، گیتِ زنده fail-open روی ۳۰. **این باگِ اصلی است** (هم‌ریختِ «learning.py سیم‌نشدهٔ Project-F»).

**🔴 I-2 (CF-08) — کپیِ `_launchpad/second-brain-live/` یک superset با قابلیتِ SEND واقعی است.**
Ziman در واقع **چهار** درختِ کد دارد نه سه (CF-03 فقط ۳ را می‌شمرد). درختِ launchpad («مغز دوم v2») کانالِ **Telegram + WhatsApp با `send()` واقعی**، approval-queue، gateway، memory، evolution-brain، ۴ پروژهٔ اضافه، **`.env` زندهٔ لودشده**، و **chat-idِ مالک به‌صورت hardcode (PII، مقدار عمداً اینجا ثبت نمی‌شود) در `projects.yaml`+`users.yaml`** دارد. این **ناقضِ invariantِ «ZERO outward execution»** است. سؤال مالک: آیا این باتِ زندهٔ واقعی است؟ اگر بله، بیرونِ containmentِ propose-only است و حکمرانیِ جداگانه + انتقالِ PII به `.env` لازم دارد.

**🟠 I-3 (CF-07) — ATP fail-open روی timestampِ کهنه/آینده/naive.**
`compute_atp` (`ziman_phase2.py:28-39`) فقط `not measured_at` را چک می‌کند؛ هر رشتهٔ truthy (حتی `"banana"` یا `"2099-01-01"`) ATPِ واقعی می‌دهد. docstring/error-string/نامِ تست ادعای «fresh/stale detection» دارند که در کد **نیست** (هیچ `datetime` parse، هیچ پنجرهٔ freshness، هیچ ردِ آینده). تستِ `test_atp_stale_rejected` فقط `measured_at=None` را می‌آزماید (misnamed).

**🟠 I-4 (CF-09) — provider mislabel: هویت مدل ناوردا نیست (پاسخِ RQ-05).**
در launchpad، کلیدِ برچسبِ `anthropic-key`/`ANTHROPIC_API_KEY` عملاً **کلید DeepSeek** است (via `ANTHROPIC_BASE_URL`)، برخلافِ `ziman.yaml:33 model: claude-sonnet-5`. یعنی «تعویض مدل» همین حالا هویت را عوض کرده.

**🟡 I-5 — اعداد unverified که به همه‌جا نشت می‌کنند (CF-01/CF-02).**
`ziman.yaml` خود را «تنها منبعِ حقیقتِ اعداد» می‌نامد ولی ۳۰/هفته و ۲۰ موجودی را `[Measured]` تگ زده — که TRUTH-REGISTER/STATUS/OpenQuestions/CONSTITUTION همه unverified می‌دانند (ورودی مالک=۵۰ محصول). عددِ مناقشه‌دار ۳۰ به‌صورت verbatim داخلِ متنِ draft نشت می‌کند (`ziman_leg.py:235,242`).

**🟡 I-6 — memory pipeline کاملاً paper.**
`Candidates/` خالی، هیچ ledger واقعی، هیچ curator code، `memory_candidate()` هرگز persist نمی‌کند؛ **هیچ retention/decay/TTL** هیچ‌جا. scrubِ PII ضعیف (`payid\s*:` فقط literal). idempotency_key/content_hash مصرف‌کننده ندارند.

**🟡 I-7 — انسجامِ eval/experiments:**
- Role Card به suiteِ ناموجود اشاره می‌کند: `product_inventory.yaml:45 suite: "ziman_product_shared"` ولی suite واقعی `ZM-QUAL-PRODINV-v1` است → pointerِ dangling.
- Role Card فقط ۳ critical_test غیررسمی دارد؛ suite ۱۲ critical تعریف کرده + گیتِ «all critical pass» را حذف کرده.
- `EXP-002` هیچ success/failure/stop ندارد؛ `EXP-003` بدونِ stop؛ EXP-002/003 بدونِ frontmatter/experiment_id (untracked).
- `worker.py` docstring چهار subcommandِ Phase-2 (`--product-card/--inventory-snapshot/--photo-index/--telegram-dry`) را تبلیغ می‌کند ولی `main()` آن‌ها را dispatch نمی‌کند → silent no-op با exit 0؛ CLIِ واقعیِ Phase-2 (`phase2_cli.py`) جداست و control-brain هرگز صدایش نمی‌زند.

**🟡 I-8 — read-allowlist دور زده می‌شود:** `_load_yaml_capacity/_load_inventory_hint/status_snapshot` مستقیم `Path.read_text/glob` می‌زنند و `packet.can_read()` را دور می‌زنند؛ فعلاً فقط چون candidate-1 وجود دارد امن است. اگر resolution به candidate-2 (`_code`، منطقهٔ ممنوعِ `.agentignore`) یا candidate-3 بیفتد، بیرونِ allowlist می‌خواند.

**🟢 چیزهایی که واقعاً سالم‌اند:** propose-only ساختاری (هیچ متدِ send/publish/pay در leg)؛ D4 روی سقفِ null/≤0 fail-closed (کمپینِ حجمی رد)؛ C4 local-only در کد enforce‌شده (`product.py:108-123`)؛ ۴۰/۴۰ تست سبز؛ Telegram bot در control-brain owner-authenticated؛ dashboard فقط localhost + بدونِ mutation endpoint؛ schemaها fail-closed و evidence-classed؛ `.env` زنده git-ignored (نشت نکرد).

## Ζ. پاسخِ سؤالاتِ تحقیق (RQ) — به زبانِ مهندسی
- **RQ-01 (policy↔event):** policy درست propose-only است؛ اما گیتِ D4 (سیاستِ ظرفیت) fail-open است (I-1) و لایهٔ event/ledger paper است → «شنیدن» عملاً وصل نیست.
- **RQ-02 (memory→eval نفوذ):** memory خالی است پس آلودگیِ فعلی صفر؛ ولی چون **retention/decay نیست** و suite اعدادِ unverified (۵۰/۳۰) را hardcode کرده، لایهٔ eval **همین حالا** با ثابت‌های تأییدنشده آلوده است (I-5/I-7).
- **RQ-03 (exec↔policy):** propose-only ساختاری محکم؛ ولی D4 روی سقفِ اشتباه (۳۰ نه ۶)، read-allowlist دور می‌خورد، و `campaign_check` گاردِ نوعِ ورودی ندارد → لبه‌های fail-open.
- **RQ-04 (تلفیق/synthesis):** تصمیم فعلاً **جمعِ خطیِ تک‌حسی** است نه تداخلِ چندحسی — memory هیچ سهمی ندارد (paper)، seam در live dormant است.
- **RQ-05 (ناوردیِ مدل):** **نقض شده** — کلیدِ Anthropic عملاً DeepSeek است (I-4)؛ هویتِ مدل بین سند و config ناسازگار.

## Η. منیفولدِ محصول (M_product) — ارزیابی، نه بازساخت
`PRODUCT-CARD-SCHEMA.v1` **همان منیفولدِ ۶بعدیِ درخواستی است و از قبل ساخته شده** (Option A): `family · classification/variation · inventory · commercial · fulfilment · assets` + evidence + governance. انضباطِ fail-closed عالی است: `quantity_on_hand: null` («هرگز ۰ یا ۵۰ فرض نکن»)، ATP فقط measured+fresh، C4→perishable+local_only، price-gate، photo sha256. **ولی کاملاً null است** (هیچ اندازه‌گیری). `INVENTORY-SNAPSHOT.v1` (append-only، «units ≠ SKU ≠ capacity») و `PHOTO-PRODUCT-MAP.v1` (read-only، originals هرگز move/rename، privacy_flag) نیز آماده‌اند.
→ **تصمیمِ باز دیگر «چند بعد» نیست (۶بعد ساخته شده)؛ تصمیمِ باز «استراتژیِ پرکردن» است** (Π).

## Θ. تغییرات امنِ پیشنهادی (همه propose-only — کد اجرا-تغییر گیت‌دار)
1. **[fix I-1] وصل‌کردنِ `capacity_fail_closed` به D4:** در `campaign_check`/`check_campaign` سقفِ مؤثر = `capacity_fail_closed(yaml_ceiling, owner_revalidated=False)` تا بستنِ CF-01. + تستِ رگرسیون «کمپینِ ۷/هفته رد شود تا revalidation». (تغییرِ گیتِ ایمنی → verdict لازم.)
2. **[fix I-3] freshness واقعی در `compute_atp`:** parse ISO8601، ردِ future، پنجرهٔ کهنگی (مثلاً >۳۰ روز → None). + تستِ stale/future/naive واقعی.
3. **[fix I-5] برچسب‌گذاری اعداد:** leg به‌جای عددِ خامِ yaml، `evidence_class` را در digest/draft بیاورد و تا revalidation «~۶/هفته (unverified)» بگوید؛ draftها عددِ ۳۰ را verbatim نگذارند.
4. **[fix I-7] pointer/experiments:** Role Card → `ZM-QUAL-PRODINV-v1` + گیتِ all-critical؛ EXP-002 stop/thresholds، EXP-003 stop، frontmatter برای هر EXP.
5. **[doc] worker.py docstring** با CLIِ واقعی هم‌تراز یا subcommandها به `phase2_cli` مسیر داده شوند.

## Ι. شواهدِ تست
```
python -m pytest _ops/tests/test_ziman_leg.py -q      → 17 passed (0.23s)
python -m pytest _ops/tests/test_ziman_phase2.py \
                 _ops/tests/test_ziman_wiring.py -q    → 23 passed (0.26s)
python _ops/smoke_ziman_wire.py                        → OK (D4 رد ۱۰۰>۳۰، propose-only، zero external exec)
```
جمع: **۴۰/۴۰**. (اخطار: کلِ dir با pytest به‌خاطر یک تستِ اسکریپت‌سبک crash می‌کند — جدا اجرا شود.)

## Κ. قراردادِ Telegram
`10-Interfaces/TELEGRAM-CONTRACT.md` از قبل هست (dry-run، owner-allowlist، هیچ publish/send/spend، STOP-TG-CENTER برنده). ⚠ digestِ آن `ظرفیت {ceil}/هفته · موجودی≈{inv}` را خام نشان می‌دهد → I-5 به تلگرام هم نشت می‌کند؛ باید evidence-class اضافه شود.

## Λ. کوپلینگِ قلب/مغز (χ)
seam واقعی است: `organism.py:201 make_ziman_leg → :419-425 ziman_beat → :476 state["ziman"]`. کوپلینگ **یک‌طرفه و امن**: Ziman فقط status می‌نویسد، هرگز heart-rate/policy/permission را ست نمی‌کند (T14). در liveِ فعلی **dormant** (flag `OCTOPUS_WIRE_ZIMAN` پیش‌فرض در profileِ paper-full روشن است ولی beatِ اخیر ziman را ننوشته — پروفایل/پروتکتیو). χ عملی ≈ 0 تا فعال‌سازیِ عمدی. **درست برای فاز validation.**

## Μ. مرزهای تصمیم (کجا |Ψ|²=۰ / سیستم باید بایستد)
source-of-truth مبهم (CF-01/02/05 باز)، هر outward action، اجرای کدِ گیت‌دار بدونِ verdict، فعال‌سازیِ launchpad-send، پرکردنِ canonical memory بدونِ curator. تا این‌ها → read/propose بماند.

## Ν. فایل‌های ساخته‌شده این جلسه (additive)
- همین AUDIT · `11-Reports/Handoffs/PERCEPTION-PHASE2-HANDOFF.md` · append: CONFLICT-REGISTER (CF-06..CF-10) + TRUTH-REGISTER (T16) · بروزرسانیِ PROJECT Active Context. **هیچ schema/suite/contract بازساخته نشد (از قبل بودند) — فقط نگاشت شد.**

## Ξ. نگاشتِ artifactهای درخواستیِ پرامپت → واقعیت
| درخواستِ پرامپت | وضعیت |
|---|---|
| PERCEPTION-GEOMETRY-AUDIT | ✅ همین فایل |
| MANIFOLD-MAP / PRODUCT-MANIFOLD.yaml | ✅ از قبل: `03-Offering/PRODUCT-CARD-SCHEMA.yaml` (۶بعد) |
| INVENTORY-SURFACE.yaml | ✅ از قبل: `INVENTORY-SNAPSHOT-SCHEMA.yaml` |
| PHOTO-HOLOGRAM.yaml | ✅ از قبل: `PHOTO-PRODUCT-MAP-SCHEMA.yaml` |
| invariance/resonance suites | ✅ از قبل: `product-inventory-suite.yaml` + ۴۰ تست (اجرا شد) |
| TELEGRAM-WAVE-CONTRACT | ✅ از قبل: `TELEGRAM-CONTRACT.md` |
| RESONANCE-REGISTER / WAVE-ANALYSIS | ↦ درونِ بخشِ Ε/Ζ همین AUDIT (فایلِ جدا ساخته نشد — ضدِ تکثیر) |
| PHASE2 HANDOFF | ✅ `PERCEPTION-PHASE2-HANDOFF.md` |

## Ο. خلاصهٔ Telegram (≤۸ خط)
```
🖼 Ziman calibration — ۴۰/۴۰ تست سبز، Phase-2 از قبل ساخته
🔴 D4 fail-open: گاردِ ۶/هفته unwired؛ گیت روی ۳۰ approve می‌کند
🔴 launchpad copy می‌تواند SEND کند + PII + کلیدِ DeepSeek با برچسبِ Anthropic
🟠 ATP روی timestampِ کهنه/آینده fail-open · memory کاملاً paper
🟢 propose-only، C4 local-only، schemaها fail-closed — سالم
منیفولدِ ۶بعدیِ محصول آماده ولی null (هیچ اندازه‌گیری)
۵ فیکسِ propose-only + ۵ CF جدید ثبت شد
تصمیمِ باز: استراتژیِ پرکردنِ منیفولد A/B/C
```

## Π. یک تصمیمِ انسانی
> **استراتژیِ پرکردنِ منیفولدِ محصول (چون schema ۶بعدی از قبل هست، سؤال «چطور پر شود» است):**
> **A.** هر ۵۰ محصول جداگانه Product Card
> **B.** اول گروه‌بندی C1–C4، بعد SKU/Product Card ← **توصیه**
> **C.** فقط پایلوتِ ۱۰محصوله (family+inventory) → بعد بسط
>
> توصیه: **B** — مگر عکس‌ها/زمانِ مالک پایلوتِ ۱۰محصوله (C) را امن‌تر کند. (هم‌راستا با OpenQuestions #6 و STATUS next-gate #1.)
