---
type: system-note
system: internet-observatory
created: 2026-08-15
updated: 2026-08-15 (چرخش کامل: hypothesis → verified-in-working-repo)
status: verified — کد در مخزن کاری Desktop مستقر است؛ ADR آن هنوز در این vault نیست
---

# INTERNET-OBSERVATORY — رصدخانهٔ اینترنت فقط-خواندنی

> ⚠️ **تاریخچهٔ صادقانه:** یادداشت قبلی (صبح 2026-08-15) این سیستم را `hypothesis` می‌گرفت چون در `F:\backup` هیچ ردی نبود. عصر همان روز معلوم شد کد کامل در **مخزن کاری Desktop** مستقر است — غیبتش در vault شکاف انتقال بود، نه نبود سیستم.

## کجا زندگی می‌کند (خارج از F:\backup)

| قلم | مسیر |
|-----|------|
| مخزن کاری | `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` · شاخهٔ `claude/second-brain-governor-v02-2a6e36` · HEAD `d964f5f` |
| کد (نسخهٔ src) | `src/nbb_cp/adapters/observatory/{gateway,robots,audit,evidence_store,prediction_registry,redteam,verifier}.py` |
| کد (نسخهٔ _ops) | `_ops/observatory/impl/` (۴ فایل) + tests |
| دیتابیس زنده | `_ops/observatory/data/{evidence.db, predictions.db}` — gitignored (کامیت `d964f5f`) |
| کلید کشتن | `_ops/observatory/data/kill.switch` (محتوا: `KILL`) — الان absent = normal |

## شواهد زنده (سطح A — خروجی اجرا دیده شد)

- تست‌ها: **93 passed** (۴ مجموعه: gateway ۳۰ · structural ۷ · evidence_store ۲۵ · red-team ۳۱) + تست جهش‌یافتگی ۷/۷ و ۶/۶ — منبع: SYNC-REPORT-20260815-163907.md (خوانده‌شده مستقیم)
- اولین اجرای واقعی: USGS all_day.geojson — ۲۰۲٬۸۹۳ بایت · ۲۸۴ زمین‌لرزه · body_hash `1049b925…c911112`
- انبار زنده هنگام بازرسی این جلسه: evidence_chain=۲ ردیف · budget: `earthquake.usgs.gov 2/100`, `hacker-news.firebaseio.com 0/50` · predictions: ۲ رویداد registered
- **بازتولید مستقل hash (خودِ این ایجنت، 2026-08-15): هر ۴ ردیف ۴/۴ منطبق ✅** — فرمول‌ها در [[../07-HANDOFF/NEXT-AGENT-HANDOFF.md|HANDOFF]]

## allowlist امضاشده (v1 — پنج دامنه)

`www.rba.gov.au` · `www.abs.gov.au` · `blockchain.info` · `api.frankfurter.dev` · `data.api.abs.gov.au`
رد شده با شاهد robots: `www.bom.gov.au` · `api.coingecko.com` · `nemweb.com.au` · `www.aemo.com.au`
**USGS: پذیرش موقت** (`needs_formal_allowlist: true` — رأی مالک، PHASE-1-DECISIONS.md)

## ناسازگاری‌ها — وضعیت پس از نشست اجرایی 2026-08-15 عصر

| مورد | وضعیت |
|------|-------|
| آستانه: کد `n ≥ 60` ↔ سند ۲۰ | **✅ بسته شد** — رأی: حفظ ۶۰ (محافظه‌کارانه) + اصلاحیهٔ تاریخ‌دار در PHASE-1-DECISIONS.md؛ چون هنوز ۰ پیش‌بینی resolve شده، pre-registration سالم ماند |
| پنجره: ۱۴ ↔ ۳۰ روز | **✅ بسته شد** — ۳۰ روز ثبت شد (همان‌جا) |
| `store_meta` خالی | **✅ بسته شد** — EvidenceStore هنگام باز شدن schema_version مهر می‌زند (ON CONFLICT DO NOTHING، کامیت e3e9d36)؛ روی دیتابیس زنده مهر خورد |
| USGS خارج از allowlist امضاشده | **✅ بسته شد** — allowlist **v2**: ردیف F (USGS؛ robots 404 → RFC 9309 §2.3.1.3 allow-all) + ردیف G (hacker-news؛ robots صریح `Allow: /*.json$`) — yaml در مخزن کاری + کپی در `F:\backup\architecture\` |
| راستی‌آزما: CRITICAL×3 | **✅ بسته شد** — VERDICT: **PASS 27/27**، هر دو زنجیره مستقل بازتولید شدند |
| جمع‌آوری داده | **✅ تسک «OCTOPUS Observatory Hourly»** — سیکل ساعتی؛ بودجه با `begin_epoch` روزانه ریست می‌شود (سقف 100/روز USGS = حفاظ طراحی‌شده؛ کادنس دقیقه‌ای عمداً رد شد) |
| تساوی OCTOPUS=persistence=0.80 | **باز** — ریشه مستند شد: `run_observatory.py:120-135` مدل سادهٔ فعلی همان سیگنال persistence را می‌گیرد؛ کار مدل‌سازی آتی |

## ADR-041

در پروژهٔ Perplexity موجود است؛ موتور octopus_sync در `--apply` آن را در پوشهٔ ADR این vault می‌گذارد → [[../06-EVIDENCE/ADR-041.md|ADR-041]] · [[../01-TRUTH/CONTRADICTIONS.md|C-005]]
