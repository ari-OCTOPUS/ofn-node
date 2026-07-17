# ZIMAN DISCOVERY REPORT

- **زمان اسکن:** 2026-07-17 11:07 (+1000 Sydney) · **روش:** static read-only analysis فقط
- **دامنه:** `F:\backup` (هیچ فایلی خارج از این ریشه خوانده/ساخته نشد)
- **محدودیت‌ها:** هیچ فایل اجرایی/اسکریپت ناشناخته‌ای در این فاز اجرا نشد. هیچ `.env`، کلید، توکن، cookie یا PII خوانده/کپی/نمایش داده نشد — فایل‌های حساس فقط با نام و مسیر ثبت شده‌اند.
- **شفافیت:** نتایج تست‌هایی که در این گزارش آمده («verified by execution») صبح همین روز (2026-07-17 ~10:55) و **پیش از فعال‌شدن قانون static-only این نقش**، تحت دستور مستقیم هندآف مالک (بخش «دستورات پیشنهادی برای verify») اجرا شده‌اند. در فاز فعلی هیچ اجرای جدیدی انجام نشد.

---

## 1) Executive summary

پروژه «Ziman» با اطمینان بالا پیدا شد: **`F:\backup\03 - Projects\Ziman Galerry`** — کسب‌وکار هدیهٔ دست‌ساز محلی سیدنی (گل‌آرایی مصنوعی، شادوباکس، سبد هدیه، همپر؛ بنیان‌گذار: آری + مادرش). این **نه یک پروژهٔ خریدوفروش Gift/NFT دیجیتال، بلکه یک بیزنس محصول فیزیکی** در مرحلهٔ validation (صفر فروش ثبت‌شده) است که روی آن یک زیرساخت حاکمیتی کامل و تست‌شده (propose-only، shadow gate، دفتر حسابرسی hash-chain، RBAC، capacity guard، بودجهٔ fail-closed) ساخته شده است.

دو کپی دیگر وجود دارد: mirror قدیمی‌تر در `_code` و یک درخت واگرا/پرخطر در `_launchpad/second-brain-live` که علاوه بر ziman-agent، پروژه‌های دیگر (painting-bot، accounting-bot، projectf-agent) و قابلیت SEND واقعی + فایل `.env` حقیقی دارد — ناقض قاعدهٔ «zero outward execution» و ناقض اصل تفکیک پروژه‌ها.

⚠️ **گَپ اساسی دامنه:** نقشهٔ 2027 درخواستی (خریدوفروش نیمه‌خودکار Gift / Telegram Gifts / NFT) با دامنهٔ واقعیِ پروژهٔ موجود (هدیه فیزیکی دست‌ساز) یکسان نیست. این دو می‌توانند یک پروژهٔ واحدِ در حال تحول باشند یا دو دامنهٔ جدا — **تصمیم با مالک** (به ZIMAN_RISK_REGISTER و بخش ۹ مراجعه شود).

## 2) Candidate projects ranked by confidence

| رتبه | مسیر | اطمینان «ریشهٔ درست زیمان» | شواهد |
|---|---|---|---|
| 1 | `F:\backup\03 - Projects\Ziman Galerry` | **0.97 — canonical** | تازه‌ترین (modified تا 2026-07-15/17) · اسناد حاکمیت کامل (00-Control، FOUNDATIONS، VERDICT_QUEUE) · کد + تست (ziman-agent 57/57، control-brain 76/76 — verified by execution 2026-07-17) · `_ops/legs/ziman_leg.py` در resolve order اول همین مسیر را انتخاب می‌کند · MANIFEST.yaml + PROJECT.md |
| 2 | `F:\backup\_code\Ziman Galerry` | 0.90 «مرتبط با زیمان» / 0.05 «canonical» | فقط `control-brain\` + `ziman-agent\`؛ قدیمی‌تر؛ طبق PROJECT.md کد در 2026-07-06 به `_code/` منتقل و سپس به Projects بازگردانده شده — **mirror/legacy** |
| 3 | `F:\backup\_launchpad\second-brain-live` (شامل `ziman-agent`) | 0.85 «مرتبط» / 0.02 «canonical» | superset واگرا: `accounting-bot`، `control-brain` (دارای `.env` واقعی ⚠️)، `painting-bot`، `panels`، `projectf-agent`، `setup_wizard.py`، `ziman-agent`، `START-HERE.bat`/`KILL-ALL-BRAIN.bat` · طبق CONFLICT-REGISTER (CF-08): SEND واقعی تلگرام/WhatsApp + PII + کلید با برچسب اشتباه — **لمس نشد** |

نکته: find عمق‌۴ روی کل `F:\backup` دقیقاً همین ۳ ریشه را برای ziman/zeiman/zeman یافت. کپی‌های داخل `.claude\worktrees` پروژه‌های دیگر (Mining، اونلی فنز) snapshot/worktree هستند، نه canonical.

## 3) Selected project and evidence

**انتخاب: `F:\backup\03 - Projects\Ziman Galerry`** — چون: (الف) اسناد خودِ پروژه (CF-03) آن را canonical اعلام کرده؛ (ب) کد زندهٔ `_ops` همین را resolve می‌کند؛ (ج) کامل‌ترین و تازه‌ترین است؛ (د) تست‌هایش سبزند.

شواهد ردگیری (sha256[:16] · حجم · mtime — محاسبه‌شده 2026-07-17):

| هش | حجم | زمان | فایل |
|---|---|---|---|
| 61e55f86b0f927f8 | 6,223 | 2026-07-12 | PROJECT.md |
| efab875c9ed3ea2e | 6,391 | 2026-07-12 | MANIFEST.yaml |
| 40af2f797a29d30e | 999 | 2026-07-15 | DecisionLog.md |
| aa1042d1ae8da61f | 2,801 | 2026-07-12 | ziman-agent/ziman.yaml |
| e2d713ffd004541b | 11,319 | 2026-07-17 | ziman-agent/ziman/content.py |
| 2d99353aa5d33ec2 | 4,692 | 2026-07-17 | ziman-agent/tests/test_content.py |
| 047310eab701bbbf | 68,788 | 2026-07-12 | 03-Offering/ziman-catalog.json |
| 247d526833b4c50e | 7,929 | 2026-07-12 | control-brain/app.py |

**Git:** پروژه داخل یک repo سطح‌کلِ vault است (نه repo مستقل). آخرین commit: `2026-07-16 22:55 +1000 — 3f12c0e docs(prompt): next-agent security prompt`. تغییرات uncommitted فعلی شامل خروجی کارِ صبح امروز (content.py، AGENT-HANDOFF.md، test_content.py جدید) است — طبق قانون ۱، هیچ commit/push انجام نشد.

## 4) Architecture map

```text
F:\backup (vault + git repo سطح‌کل)
├── _ops\                              ← ارگانیسم اختاپوس (زنده، خارج از پروژه)
│   ├── wiring.py                      ← make_ziman_leg() · ziman_beat()  [biology=None hardcode]
│   └── legs\
│       ├── ziman_leg.py               ← پای زیمان: propose-only، D4 با capacity_fail_closed (≤6/هفته)
│       └── ziman_biology.py           ← قلب/اعصاب/دکتر — فقط advisory
│
└── 03 - Projects\Ziman Galerry\       ← CANONICAL
    ├── 00-Control\                    ← حاکمیت: HANDOFF/STATUS/ROADMAP/TRUTH/CONFLICT + FOUNDATIONS + command-registry.yaml
    ├── 03-Offering\                   ← CATALOG.md + ziman-catalog.json (35 محصول) + Photos\ (41 JPG) + ۳ schema
    ├── 10-Interfaces\                 ← قراردادها: TELEGRAM (dry-run)، OCTOPUS-ADAPTER، BIOLOGY
    ├── control-brain\                 ← core{governance(RED ladder), store(evt.v1 hash-chain), shadow, authz(RBAC),
    │                                    command_registry, manager} + adapters{telegram_bot, dashboard, octopus_bridge} + app.py
    ├── ziman-agent\                   ← ziman\{catalog_loader, content, budget($15 fail-closed), product(cards/ATP/anti-misread),
    │                                    capacity(D4), self_model, steering, llm_router(Ollama→API→offline), telegram_adapter}
    │                                  + worker.py + phase2_cli.py + ziman.yaml + ziman-self.yaml
    ├── content\                       ← higgsfield-video-kit-2026-07-07.md · first-sale-pack.md · Ziman-FirstSale-Tracker.xlsx
    └── 11-Reports\Handoffs\           ← گزارش‌های هندآف (از جمله CONTENT-CAPACITY-LEAK-FIX-2026-07-17.md)
```

## 5) Run/development instructions inferred from files

- تست‌ها (از AGENT-HANDOFF.md §۴): `cd control-brain && python -m pytest -q` · `cd ziman-agent && python -m pytest -q` · تست‌های `_ops` برای leg/wiring/biology. نکته: pytest در Python کاربر 3.13 نصب است، نه مفسر managed؛ پروژه venv ندارد.
- ورودی‌های اجرا: `ziman-agent/worker.py [--once|--dm|--posts|--selftest|--status|--campaign]` · `ziman-agent/phase2_cli.py` (Phase 2: product-card / inventory-snapshot / photo-index / telegram-dry) · `control-brain/app.py` (start/stop/halt) · `_ops/wiring.ziman_beat()` (tick ارگانیسم؛ نیازمند restart برای load).
- `ziman-agent/START-ZIMAN.bat` و `_ops/RUN-ZIMAN-OCTOPUS-TESTS.bat` موجودند (اسکریپت‌های شناخته‌شده؛ در این فاز اجرا نشدند).
- پرچم‌های فلگ (همه خاموش پیش‌فرض مگر paper-full): `OCTOPUS_WIRE_ZIMAN`، `_RICH`، `ZIMAN_UNDER_OCTOPUS`، `_MATRIX` (گام ۲، هنوز ساخته نشده).

## 6) Integrations and external dependencies

| اتصال | وضعیت | شواهد |
|---|---|---|
| `_ops` اختاپوس (organism، budgets، telegram_center، innervation SLA 120min) | سیم‌کشی‌شده در کد؛ فلگدار | MANIFEST.yaml §ecosystem · `_ops/legs/ziman_leg.py` |
| Telegram | **طراحی dry-run فقط**؛ توکن تنظیم‌نشده؛ live نیازمند verdict | 10-Interfaces/TELEGRAM-CONTRACT.md |
| Anthropic API | بودجهٔ سخت AU$15/ماه fail-closed | ziman.yaml §budget · budget.py |
| Ollama محلی (llama3.1:8b) | مسیر رایگانِ اول؛ [Unverified نصب] | ziman.yaml §routing |
| **Higgsfield** (ویدیو/ریل محصول) | کیت ۱۰ متد آماده (2026-07-07)؛ اعتبار ~$70 AUD ≈ 835 credits [To measure]؛ حساب مالک | MANIFEST §video_engine · content/higgsfield-video-kit-2026-07-07.md |
| PayID (پرداخت) | فقط در متن برند؛ هیچ یکپارچگی فنی | ziman.yaml §business |
| Accounting / project_f / lead | «هیچ اتصالی — دامنه‌های جدا» طبق MANIFEST | MANIFEST §ecosystem |

## 7) Data model and storage locations

| داده | محل | نوع |
|---|---|---|
| کاتالوگ ۳۵ محصول (F1:18، F2:2، F3:4، F4:11) + ۱ عکس blank | `03-Offering/ziman-catalog.json` | JSON |
| عکس‌ها (41 JPG، 12.76 MB) | `03-Offering/Photos\` | فایل |
| دفتر رویداد evt.v1 (hash-chain + ULID + ZIM-DEC) | `control-brain/core/store` | ledger |
| draftهای محتوا | `ziman-agent/drafts/` | Markdown |
| وضعیت بودجه | `ziman-agent/.budget_state.json` | JSON |
| وضعیت ارگانیسم | `_ops/state/ORGANISM-STATE.ziman` (atomic write) | JSON |
| schemaهای v1: product_card / inventory_snapshot / photo_product_map | `03-Offering/*.yaml` | YAML schema |
| کانفیگ اعداد/قواعد | `ziman-agent/ziman.yaml` + `ziman-self.yaml` | YAML |
| KPI فروش اول | `content/Ziman-FirstSale-Tracker.xlsx` | XLSX (خالی) |

## 8) Security observations

1. ✅ **درخت canonical تمیز است:** هیچ `.env` یا فایل محرمانه‌ای در آن یافت نشد (find نام‌محور، maxdepth 3).
2. 🔴 **`_launchpad/second-brain-live/control-brain/.env` واقعی وجود دارد** — خوانده/کپی نشد. طبق CF-08/CF-09: درخت دارای SEND واقعی، PII (chat-id مالک در projects/users.yaml) و کلید DeepSeek با برچسب Anthropic است. **اقدام: verdict مالک (حاکمیت جدا یا archive) + چرخش/تصحیح برچسب کلید.**
3. ⚠️ **اختلاط پروژه‌ها در همان درخت:** `painting-bot` کنار `ziman-agent` — ناقض اصل تفکیک ZIMAN/Painting (نگاه به بخش مرز در Blueprint).
4. ⚠️ فایل‌های حساسِ قالبی (امن): `_code/.../control-brain/.env.example`، `core/secrets.py`، `SECRETS.md` — فقط نام‌برده شدند.
5. ✅ اصلاح امنیتی صبح امروز: نشت عدد ظرفیت تأییدنشده (۳۰/هفته) از متن عمومی و پرامپت‌های LLM حذف و تست رگرسیون اضافه شد (`tests/test_content.py`، ۷ تست).
6. ⚠️ CF-06 باقی‌مانده: گیت D4 در `ziman-agent/worker.py:106` هنوز سقف خام ۳۰ را مصرف می‌کند (در `_ops/legs/ziman_leg.py` رفع شده) — تغییر گیت ایمنی = verdict لازم.
7. قاعدهٔ رعایت‌شده: هیچ secret در این گزارش/پرامپت/خروجی قرار نگرفت و قرار نخواهد گرفت.

## 9) Gaps and unanswered questions

1. **دامنهٔ 2027:** آیا «خریدوفروش نیمه‌خودکار Gift» توسعهٔ همین زیمانِ فیزیکی است یا دامنهٔ جدید (دیجیتال/NFT)؟ → اثر بر معماری/قانون.
2. verdictهای باز مالک: ZIM-V1 ظرفیت · V2 hero · V3 عکس · V4 نام برند · V5 قیمت/COGS · V6 تحویل · V7 کانال · V8/V9 سیاست الکل/تحویل F4.
3. موجودی: ۲۰ (yaml) در برابر ۵۰ (شفاهی) — نیازمند جلسهٔ شمارش (CF-02).
4. وضعیت قانونی/پلتفرمی مسیر Telegram Gifts/NFT/TON — نامشخص → **BLOCKED** (قانون ۵).
5. نام/دامنهٔ رسمی سرویس «Higgsfield» و وجود API/OAuth مستند — نیازمند تأیید مالک (فاز ۴).
6. `panels/` در second-brain-live — ماهیت/زبان بررسی‌نشده (لمس نشد).

## 10) Recommended next actions

1. مالک دامنهٔ 2027 را تصمیم بگیرد (فیزیکی ↔ دیجیتال/NFT ↔ ترکیب گیت‌شده).
2. بستن verdictهای ZIM-V1..V9 قبل از هر قیمت/کمپین عمومی.
3. CF-06 (گیت worker) و CF-08/CF-09 (درخت launchpad + کلیدها) با verdict مالک حل شود.
4. گام ۲ roadmap: `ziman_matrix.py` پشت فلگ خاموش (ادامهٔ کار کدنویسی موجود).
5. فاز ۴ Higgsfield: تأیید نام/دامنه → بررسی مستندات رسمی → Integration Plan → لاگین توسط خود مالک.

## 11) Explicit statement

**No secrets were copied or exposed.** هیچ فایل `.env`، کلید API، توکن، رمز، cookie، session یا PII در هیچ مرحله خوانده، کپی، نمایش یا در گزارش درج نشد؛ فایل‌های حساس فقط با نام و مسیر ثبت شدند.
