---
type: master-state
audience: external-agents
created: 2026-08-15 (night ~19:00 local)
supersedes: همهٔ اسنپ‌شات‌های قبل از شب 2026-08-15
entry_point: این فایل نقطهٔ شروع هر ایجنت خارجی است
---

# 🐙 STATE — وضعیت جامع سیستم در پایان شب 2026-08-15

> ایجنت خارجی؟ این فایل را بخوان، بعد [[../00-INDEX|00-INDEX]] (نقشهٔ کامل vault) و [[../07-HANDOFF/NEXT-AGENT-HANDOFF|NEXT-AGENT-HANDOFF]] (۶ الحاقیهٔ اجرایی). اعداد این فایل همه با فرمان/فایل منبع‌دار شده‌اند.

## ۰. دو مخزن، دو نقش — اول این را بفهم

| مخزن | نقش | هشدار |
|------|-----|-------|
| `F:\backup` | **درختِ زندهٔ ارگانیسم + vault کانونیکال** — ۵ پروسهٔ python دائم روشن | درختِ در حالِ اجراست؛ تغییر فلگ = ری‌استارت رسمی (`_ops/RESTART-ALL.ps1`)؛ هرگز دستی kill نکن |
| `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` | خطِ توسعهٔ NBB-CP + **رصدخانهٔ اینترنت** (کد/تست/دیتابیس) | شاخهٔ `claude/second-brain-governor-v02-2a6e36` |

## ۱. ارگانیسم — زنده و سالم (سطح A)

- بوت 18:30:42 · **beat 36803+** · **coherence 0.977** (از 0.942 امشب بالا آمد) · halted=False · conflicts=[]
- ۵ عضو: organism · center · gateway · live · cortex — همه با PID تازه (ری‌استارت کنترل‌شدهٔ سوم امشب)
- منبع زنده: `OCTOPUS/CURRENT-TRUTH.md` (runtime می‌نویسد — تو فقط بخوان) · `_ops/state/ORGANISM-STATE.json`
- کلیدهای کشتن (همه سالم): فلگ `halted` در DB · فایل STOP · `_ops/observatory/data/kill.switch`

## ۲. فلگ‌های روشن (مکانیزم: `_ops/OCTOPUS-flags.cmd` — ۱۴۸۲ خط CRLF؛ تغییر = بکاپ + ری‌استارت)

`OCTOPUS_UNIFIED_CHAT=1` · `CORTEX_HYPOTHESIS=1` · `OCTOPUS_WIRE_VAULT_RAG=1` (حافظهٔ RAG والت) · `OCTOPUS_WIRE_DOCTOR_TG=1` (relay دکتر) — همه با تأیید چتی مالک 2026-08-15. بقیهٔ WIREها عمداً خاموش. **`OBSERVATORY` فلگ ندارد چون آداپتور فاز ۳ هنوز ساخته نشده — روشن‌کردنش بی‌معناست.**

## ۳. دکتر — تک‌صدا و رأی‌گیر (معماری نهایی امشب)

- دکتر در حالت **outbox**: کارت‌ها فقط در `OCTOPUS-DOCTOR/90-_meta/state/tg-outbox.jsonl` صف می‌شوند
- **صدای واحد** = ربات center از طریق `_ops/telegram_center/doctor_link.py` (relay) — دیگر هیچ ارسال مستقیم/دوتایی نیست (توکن مستقیم از `.env` حذف شد)
- **پل رأی** (کامیت `3156316`): هوک سه‌بخشی `ok|no:<gate>:<mission_id>` در `center._handle_callback` قبل از جدول verb → `_doctor_ingest` → صندوق `tg-inbox.jsonl` (گیت مالک + ضدتکرار در کد). تست: `_ops/tests/test_doctor_vote_bridge.py` (۵/۵)
- اثبات زنده: **۷ رأی واقعی مالک** همین شب ثبت شد (رأی‌دهنده با چت مالک bool-verified)
- سابقه: باگ «نادیده» = C-009 (بسته شد) — هم‌خانوادهٔ باگ ۲۹-دکمه‌ای 2026-07-28

## ۴. رصدخانهٔ اینترنت — چشمِ ساعتی

- تسک ویندوزی **«OCTOPUS Observatory Hourly»** — هر ساعت یک fetch واقعی USGS + پیش‌بینی pre-registered (نبض امشب: ۴→۵→۶ ردیف)
- بودجه با `EvidenceStore.begin_epoch()` هر روز UTC ریست (کامیت `e3e9d36`؛ سقف USGS = 100/روز)
- زنجیره‌های hash **مستقل تأییدشده**: `scripts/verify_live_store.py` → **PASS 27/27** (فرمول‌های src در فایل)
- allowlist **v2** = ۷ دامنه با شاهد robots (USGS: robots 404→allow طبق RFC 9309 §2.3.1.3 · hacker-news: صریح `Allow: /*.json$`) — `_ops/observatory/architecture/observatory-allowlist.yaml` + کپی `F:\backup\architecture\`
- ADR-041 نوشته شد (پرش ۰۴۰→۰۴۲ بسته) · ناسازگاری‌های باز: استراتژی = persistence (0.80=0.80؛ ریشه: `run_observatory.py:120-135`)
- **قضاوت n≥60**: رصد روزانه ۱۹:۰۰×۵روز (خودکار؛ گزارش در `00 - Inbox/OBSERVATORY-WATCH-*`)

## ۵. حاکمیت — شبِ رأی و امضا

- **امضای Ed25519 مالک**: `MANIFEST.sig` + `SIG-RECEIPT.md` در `_ops/D1-AUDIT-PACKAGE-2026-08-15/` — «Signature Verified Successfully» · کلید عمومی: `_ops/owner-signing/` · خصوصی: `~/.octopus-signing/` (بیرون از repo — هرگز واردش نکن)
- **رأی ORANGE 4d**: ثبت در addendum خودِ ADR-008 — سیم‌کشی shadow→live مجاز، کارِ نشستِ بعد
- D1 ممیزی مستقل: بسته آماده، **NOT_STARTED** تا ممیز بیرونی اجرا کند · D7/production: قفل تا قضاوت n≥60
- دفتر تناقض‌ها: **C-001…C-009** در [[CONTRADICTIONS]] — همه ثبت، اکثراً بسته با شواهد

## ۶. تست‌ها (همه سطح A)

NBB-CP vault: **171** · رصدخانه: **93** · hypothesis: **23** (پس از stash رأی NEW-4) · سوئیت working: **320** · پل رأی: **5** · کل `_ops` از ریشه: INTERNALERROR (رانر رسمی=`_ops/tests/run_all.py`، ~۱۷min — باز)

## ۷. قواعد خانه برای ایجنت خارجی — نقض = توقف

1. **شواهد نه ادعا** — هر عدد با فرمان/فایل منبع‌دار شود؛ سطح‌بندی A (اجرا دیدم) / B (ایجنت دیگر) / C (فقط سند)
2. **propose-only** · حذف ممنوع · improve-don't-rewrite · fail-closed · نقض invariant = halt نه retry
3. **رازها**: `.env` فقط نام کلید، هرگز مقدار؛ کلید خصوصی امضا دست‌نخوردنی
4. فلگ‌ها فقط از `OCTOPUS-flags.cmd` + ری‌استارت رسمی + گیت پذیرش (پنجرهٔ پیشنهادی: ۳۰۰s)
5. WORKLOCK را در [[../01 - Dashboard/HANDOFF|HANDOFF]] بخوان قبل از هر کار موازی؛ تستِ نو = فایل نام‌یکتا در `_ops/tests/`
6. ماینینگ: تحلیل آزاد، **اجراهای مالی هرگز** (D-10) · brain_core: promote ممنوع تا شاهد بخلاف (missing_old=3473)

## ۸. کارِ باز (به ترتیب درسِ معلم)

۱. قضاوت n≥60 (~۲.۵ روز؛ خودکار) ۲. جداسازی استراتژی از persistence ۳. آداپتور observation.v1 (فاز ۳) ۴. سیم‌کشی 4d shadow→live ۵. NBB-CP به پاها (فاز ۴-۵؛ V2/V3/V4) ۶. فرمان‌دهی برد پس از بازبینی امنیتی ۷. ممیز مستقل D1 ۸. ریزکارها: shortfall=4 فلگ · پنجرهٔ گیت ۳۰۰s · run_all کامل · خاستگاه رکورد evidence#۴ (17:36) · سرنوشت brain_core

## ۹. جای همه‌چیز

نقشهٔ کامل: [[../00-INDEX|00-INDEX]] · حقیقت زنده: [[CURRENT-TRUTH]] · تست‌ها: [[TEST-COUNT]] · سرویس‌ها: [[SERVICE-STATUS]] · تناقض‌ها: [[CONTRADICTIONS]] · تصمیم‌ها/بازها: [[../02-DECISIONS/OPEN-VERDICTS|OPEN-VERDICTS]] · سیستم‌ها: [[../04-SYSTEMS/OCTOPUS|04-SYSTEMS/*]] · لاگ شب: [[../00 - Inbox/2026-08-15 NIGHT — Activation & Test Session (all gates)|SESSION NIGHT]] · پک رصدخانه: `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/` (تا 17:09 دقیق است؛ پس از آن این فایل مقدم است)
