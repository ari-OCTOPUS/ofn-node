---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: idea
tags: [painting, lead, trust-engine, phase-b, verification, adversarial]
created: 2026-07-21
updated: 2026-07-21
---

# 00 — راستی‌آزماییِ متخاصمِ فاز B + فهرستِ اصلاحات (سندِ حاکمِ بسته)

> این پوشه (`PHASE-B-CONTRACTS/`) خروجیِ **فاز B** مأموریتِ Trust Engine است: قراردادها، ماشین‌های حالت،
> مدلِ تهدید، مرزِ API، و طرحِ مهاجرت. هر artifact توسط یک ایجنتِ طراح ساخته و سپس توسط یک ایجنتِ
> **متخاصمِ مستقل** (که مأمور به رد کردنش بود) در برابرِ اسپکِ بسته و کدِ واقعیِ کانونی بازبینی شد.
> این سند نتیجهٔ آن بازبینی است. **همه‌چیز propose-only است — صفر تغییرِ کد/فلگ/برنچ در ارگانیسم تا رأیِ مالک.**

## روش

۹ واحدِ کار: ۳ بازبینیِ ماژولِ staged + ۶ طراحیِ قرارداد. هر کدام از یک ایجنتِ طراح/بازبین + یک ایجنتِ
verifyِ متخاصم عبور کرد (pipeline، هر دو read-only در worktree). سه قراردادِ JSON چون verifyِ متخاصمشان
به‌خاطرِ اتمامِ credit ناتمام ماند، **مستقیماً با پروبِ تابعیِ اسکیما (jsonschema draft-07) توسطِ خودم**
راستی‌آزمایی شد (نتایج پایین). ماژول‌ها روی محورهای: flag-off no-op · kill-switch-first · stdlib/$0 ·
secret-scan · نوشتنِ فقط استریمِ خودش · resolve شدنِ importها در کانونی · hermetic بودنِ تست.

## نتیجهٔ کلان

| # | artifact/ماژول | verdict | blocking یافت شد؟ | وضعیت اکنون |
|---|---|---|---|---|
| 02 | `CANONICAL_LEAD_CONTRACT.json` | **PASS** (پروبِ من) | نه | استفاده به‌همان‌شکل |
| 03 | `EVENT_CONTRACT.json` | **PASS** (well-formed draft-07) | نه | استفاده به‌همان‌شکل |
| 04 | `PROPOSAL_CONTRACT.json` | **PASS** (well-formed draft-07) | نه | استفاده به‌همان‌شکل |
| 05 | `CONSENT_STATE_MACHINE.md` | ok=true | نه (۹ اصلاحِ غیرمسدود) | استفاده + اصلاحاتِ فاز C پایین |
| 06 | `FUNNEL_STATE_MACHINE.md` | **ok=FALSE** | **آری (۱)** | **اصلاح‌شدهٔ inline** ✅ |
| 07 | `SECURITY_THREAT_MODEL.md` | ok=true | نه (۵ اصلاحِ غیرمسدود) | استفاده + اصلاحاتِ فاز C پایین |
| 07a | `API_BOUNDARY_DESIGN.md` | **ok=FALSE** | **آری (۲)** | **اصلاح‌شدهٔ inline** ✅ |
| 09a | `MIGRATION_AND_OWNERSHIP.md` | ok=true | نه (۶ اصلاحِ غیرمسدود) | استفاده + اصلاحاتِ فاز C پایین |
| M-1 | ماژولِ `llm_intent.py` | **integrate** | نه | آمادهٔ ادغامِ flag-off |
| M-2 | ماژولِ `fuel_meter.py` | **HOLD** | آری (وابستگیِ غایب) | ادغام نشد — پایین |
| M-3 | ماژولِ `cognition_effect.py` | **HOLD** | آری (وابستگیِ غایب) | ادغام نشد — پایین |

## پروبِ تابعیِ قراردادِ لید (جایگزینِ verifyِ credit-failed — همه پاس)

اسکیما draft-07 معتبر است و firewallِ رضایت **ساختاراً در لایهٔ اسکیما** قفل است (نه توصیه‌ای):

- `market_signal` + `outreach_allowed=true` → **REJECTED** ✅ (`allOf[0]`)
- `market_signal`ِ معتبر → **ACCEPTED** ✅
- `synthetic_test` با phone/email ناتهی → **REJECTED** ✅ (`allOf[5]` — چیزی برای ارسال ندارد)
- `outreach_allowed=true` بدونِ `candidate_type ∈ {consented_inbound, public_b2b}` → **REJECTED** ✅ (قفلِ معکوسِ `allOf[2]`)
- `consented_inbound` + basis=explicit + فیلدهای کاملِ consent → **ACCEPTED** ✅

## دو یافتهٔ BLOCKING (هر دو اکنون inline اصلاح شده)

### B1 — ادعای غلط روی لبهٔ outbound (سند 06 funnel)
سند ادعا می‌کرد `sweep_stale_effects:416` حالتِ `send_pending` را با backstopِ ۷۲ساعته می‌گیرد.
**در برابرِ کد رد شد:** `chrono.py:424` فقط `WHERE status='pending'` را جارو می‌کند؛ ولی `send_pending`
به `releasable` نگاشت می‌شود (`release_gated_effects:385` وضعیت را pending→releasable می‌کند) که هیچ
مکانیزمِ موجودی منقضی‌اش نمی‌کند. اثر اگر همان‌طور ساخته می‌شد: یک effectِ تأییدشده که release شد ولی
هرگز settle نشد، تا ابد releasable می‌ماند و می‌تواند هفته‌ها بعد ارسال شود (first-touchِ کهنه) بدونِ هیچ
گاردِ fail-closed. **اصلاح (خطوط ۹۴/۲۱۴/۳۱۵ + بنرِ بالای سند):** گاردِ staleness در لایهٔ **worker/bridgeِ
فاز C** (نه chrono): پیش از `settle`، اگر `now − release_ts > O-1 window` → settle نکن، `communication.failed(stale_refused)` + alert.

### B2 — سوراخِ consent-firewall در handoff + تناقضِ receiptِ HALT (سند 07a boundary)
1. **سوراخِ handoff (§5):** مرز برای **هر** لیدِ پذیرفته فایلِ `lead_sense` می‌نوشت، از جمله `market_signal` →
   ورود به قوسِ draftِ consent-نابینا (RUNTIME-TRUTH §0) → ساختِ quote/کارت برای یک سیگنال؛ نقضِ
   `LEAD_INBOX_SPEC §2` و بلوپرینت §4. `outreach_allowed=false` جلوی ارسال را می‌گیرد ولی جلوی ساختِ
   draft را نه. **اصلاح:** handoff حالا بر `candidate_type` گیت شده — فقط `consented_inbound`/`public_b2b`
   فایلِ lead-inbox می‌سازند؛ `market_signal` در `boundary.db` می‌ماند و سطحِ جداگانهٔ digest را تغذیه می‌کند + تستِ ساختاریِ فاز C.
2. **تناقضِ HALT (§6.5):** «صفر نوشتن حتی nonce» با §1.3/§2/spec §0 («receipt برای هر submission») و آلارمِ
   خودِ همان بخش در تناقض بود. **اصلاح:** در halt = صفر جهشِ state، ولی receiptِ append-only + alert نوشته می‌شود (ردِ حسابرسیِ اجباری).

## اصلاحاتِ غیرمسدود که باید در فاز C تا شوند (به تفکیکِ سند)

**05 CONSENT:** افزودنِ دو CHECKِ SQL (consented_inbound+non-explicit+outreach، و explicit-بدونِ-evidence)؛
افزودنِ `ESCALATION_PROPOSED`/`QUARANTINED` به from-setِ گذارِ suppression (T9)؛ برچسبِ «absorbing except
retention tombstone»؛ افزودنِ کارتِ alert به گذارِ T2 (quarantine)؛ مستندسازیِ کوپلینگِ فعال‌سازی (روشن‌شدنِ
WIRE_LEAD_DRAFT پس از این به CONSENT_FW هم نیاز دارد)؛ حفظِ risk-flagِ heritage؛ upsertِ suppression بعد از lift.

**07 THREAT:** افزودنِ ردیفِ تهدیدِ attachment/URL (P0 هرگز media/source_url را auto-fetch نمی‌کند → بی‌SSRF)؛
fail-closed کردنِ خودِ firewall روی استثنا (هر exception ⇒ outreach_allowed=false)؛ حملِ نشانگرِ
`synthetic_test` در ردیفِ gated_effect تا بلوکِ سرِ settle ساختاری شود؛ الزامِ بسته‌بودنِ شاخهٔ
no-secretِ human_append_guard؛ تصحیحِ چند citation.

**09a MIGRATION:** قاعدهٔ صریح که مرحلهٔ qualification/draft باید `candidate_type` را بخواند و `market_signal`
را ساختاراً از draft کنار بگذارد (هم‌راستا با اصلاحِ B2)؛ پین‌کردنِ محلِ `_idem.json` زیرِ `processed/`؛
مشورتِ `_seen.json` پیش از نوشتن در M3؛ قراردادِ resolve شدنِ `payload_ref→source.channel` برای بلوکِ
synthetic در EffectorGate؛ یک‌جمله معادل‌سازیِ `budget_gate`≡`money_gate.py`.

**M-1 llm_intent (پیش از ادغام):** رشتهٔ متنِ خامِ مالک را هم به بازبینیِ کلیدواژه‌ایِ گیت بده
(`_is_important(f"{action} {summary} {text}")`) تا مدل نتواند درخواستِ خطرناک را در کلماتِ بی‌خطر پنهان کند
(فقط گیت را بالا می‌برد، هرگز پایین نمی‌آورد)؛ ثبت در `run_all.py TESTS` (نه PYTEST_TESTS)؛ حذفِ
`setdefault('...','1')` از بلوکِ `__main__`.

## تصمیمِ ماژول‌های staged (یکپارچه‌سازی)

- **`llm_intent.py` (`OCTOPUS_TG_LLM_ASK`) → INTEGRATE:** روی همهٔ محورها تمیز (flag-off no-op مطلق،
  kill-switch-first، stdlib/$0، بی‌secret، importها در کانونی resolve، تستِ hermetic). propose-only ذاتی:
  هر شکستِ parse/LLM ⇒ ok=False fallback؛ autonomy_matrix پیشنهادِ مدل را دوباره چک می‌کند پس مدل هرگز گیت
  را پایین نمی‌آورد. با اصلاحِ دفاعیِ بالا ادغام می‌شود.
- **`fuel_meter.py` + `cognition_effect.py` → HOLD:** خودِ ماژول‌ها تمیزند، اما **تستشان به یک patchِ
  `producers.py` وابسته است که در هیچ درختی (نه کانونی نه زنده) وجود ندارد** — به `_count_fuel`/`_count_cognition`
  و کلیدهای velocity_meter (`fuel_velocity_per_hr`, `honest_pulse`, …) که هیچ‌کجا نیستند. ادغامِ اکنون =
  تستِ قرمز + dead-flag (صفر consumer). این patchِ سوم (احتمالاً از تبارِ برنچِ hybrid-heart `d0bfa7b`) باید
  پیدا یا بازپیاده و **اتمیک با این دو ماژول** کامیت شود. تا آن‌وقت روی دیسکِ زنده به‌عنوان staged می‌مانند.

## سوالاتِ بازِ مالک (تجمیع از همهٔ اسناد)

1. تأییدِ انتخابِ آداپترِ canonical = خانوادهٔ `lead_sense` + نامِ ماژولِ نو `lead_candidate_inbox.py` (09a §1.2).
2. تأییدِ freezeِ `lead_leg_inbox.py` + منسوخ‌شدنِ فلگِ `OCTOPUS_WIRE_LEAD_INBOX` (09a F1/F2).
3. جای‌گیریِ مرز: listenerِ جدا روی `127.0.0.1:8774` (07a §0) — تأیید؟
4. رفتارِ AusTender: پیش‌فرضِ fail-closed = `market_signal`؛ ارتقا به `public_b2b` تصمیمِ آگاهانهٔ مالک.
5. پنجرهٔ O-1 برای گاردِ stalenessِ نو (پیش‌فرضِ پیشنهادی: پایانِ همان روزِ کاری؛ سقفِ سختِ ۷۲h).
6. `DoS-hardening`: بدنهٔ بی‌امضا quarantine نشود (07a §6.3) — تأیید؟
7. secretهای per-sourceِ ingestion (owner-provisioned، هرگز در repo).
8. پیدا/بازپیاده‌سازیِ patchِ `producers.py` برای آزادسازیِ دو ماژولِ heart.

**دربارهٔ فاز C:** پیاده‌سازی تا تأییدِ این قراردادها آغاز نمی‌شود (قاعدهٔ صریحِ مأموریت). اولین milestone =
یک لیدِ سنتتیک که کلِ لولهٔ داخلی را طی کند، صفر ارسالِ بیرونی.
