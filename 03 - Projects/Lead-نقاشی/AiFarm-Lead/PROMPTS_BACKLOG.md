# Brushline — Backlog پرامپت‌ها (copy-paste ready)

> هر بلوک را مستقیم به یک session بعدی paste کن. ترتیب پیشنهادی ROI پایین آمده.
> منبع کامل: `ARCHITECTURE_MASTER.md`.

## قید مشترک (در همه‌ی پرامپت‌ها فرض شده — اگر session تازه است، این بلوک را اول paste کن)

```
زمینه: پروژه‌ی Brushline، codebase در
  .../Ai farm- sister Painting/brushline/60_code/
قیدهای غیرقابل‌حذف:
- INV-1: هیچ publish/send/sync بدون human approve. مسیر: draft -> Queue -> approve.
- INV-2: PII مشتری هرگز در audit/memory/LANGAR خام نشود — فقط hash-ref.
- INV-3: check_and_enforce(cost_aud, agent_id) اولین خط هر متد بیرونی.
قواعد کد:
- فایل‌های Python را با bash heredoc بنویس (Write tool یونی‌کد را truncate می‌کند).
- داخل کد ASCII-only: -- به‌جای em-dash، -> به‌جای arrow.
- بعد از هر نوشتن: python3 -c "import ast; ast.parse(open('f').read())".
- تست offline سبز قبل از done؛ الگو: tests/test_phase2_leadpath.py.
- config از src/config.py؛ هیچ hard-coding.
```

---

## بخش A — تکمیل فازها

### P1 — Worker C: review-response slice  ✅ DONE (2026-07-01، test_phase2_reviewslice.py 27/27)
```
ContentAgent.draft_review_response(review, sentiment_result) واقعی با Haiku + template
fallback سازگار را پیاده کن. orchestrator.kickoff_review_response را از sentiment_complete
به draft+Gate+Queue کامل کن (الان stub/TODO). draft_type=review_response outbound است؛ در Gate
این تمایز را لحاظ کن: پاسخ عمومیِ پلتفرم opt-out لازم ندارد ولی ABN/ACL آره.
Acceptance: تست review slice مثل test_phase2_leadpath؛ sentiment منفی -> SLA 2h؛
superlative در پاسخ -> SOFT_FLAG.
```

### P2 — Worker C + Gate: suburb-page slice و semantic ACL با Sonnet  ✅ DONE (2026-07-01، test_phase2_suburbslice)
```
1) draft_suburb_page واقعی از bundle تحقیق Worker A+B.
2) لایه‌ی semantic ACL با Sonnet (MODEL_KEY) به Gate اضافه کن که فراتر از superlative scan،
   ادعای ظریفِ اثبات‌نشده را بگیرد (~AUD $0.016/draft).
قید: فقط روی draftهای پرریسک (suburb/marketing) صدا زده شود نه هر draft؛ check_and_enforce قبل
از فراخوان Sonnet؛ خروجی به flags اضافه شود نه جایگزین deterministic.
Acceptance: claim ظریف مثل "trusted by thousands" که از superlative رد می‌شود توسط Sonnet
گرفته شود؛ هزینه‌ی per-draft در cost_events لاگ شود.
```

### P3 — Phase 3: Human Approval Queue واقعی با inline keyboard تلگرام  ✅ DONE (2026-07-01، 47/47)
```
ApprovalQueue.submit/approve/edit/reject واقعی + کارت تلگرام با inline keyboard
(Approve/Edit/Reject). INV-1: هیچ auto-approve حتی روی انقضای SLA (فقط priority+notify).
EDIT با تغییر مادی -> REGATE. هر تصمیم -> audit.append("APPROVAL_DECISION").
allow-list ALLOWED_OPERATOR_CHAT_IDS روی callbackها هم enforce شود نه فقط messageها.
Acceptance: تست چرخه drafted->queued->approved/edited(regate)/rejected؛
تست رد callback از chat_id غیرمجاز.
```

### P4 — Phase 4: Worker E (Channel) — publish فقط DRAFT (GBP + social) ✅ DONE (2026-07-02، test_phase4_channel 17/17)
```
ChannelAgent که برای Google Business Profile و social فقط DRAFT می‌سازد (هرگز auto-post، INV-1).
integration GBP به‌صورت draft/preview. قید: هیچ مسیر کدی بدون عبور از Queue منتشر نکند.
Acceptance: draft GBP از Gate رد و در Queue بنشیند؛ تلاش publish بدون approval -> استثنا؛
تستی که اثبات کند هیچ متد publish بدون approval صدا زده نمی‌شود.
```

### P5 — Phase 5: Worker F (Lead-capture) + sync با ServiceM8/Tradify ✅ DONE (2026-07-02، test_phase5_leadsync 25/25)
```
LeadCaptureAgent کامل + sync_jobs واقعی به ServiceM8/Tradify. INV-2 بحرانی: فقط sync_* اجازه‌ی
push PII دارند، آن‌هم بعد از ConsentRecord تأییدشده؛ PII هرگز در audit payload (hash-ref).
pricing و vendor lock-in هر دو CRM ذکر شود.
Acceptance: تست بلاک sync بدون ConsentRecord؛ تست که audit حاوی phone/email خام نیست
(verify_chain + اسکن payload).
```

---

## بخش B — بهینه‌سازی طراحی و کد

### P6 — Eval framework (KB-08)  ✅ DONE (2026-07-01، test_phase6_eval)
```
یک eval harness بساز که کیفیت draftهای Worker C و دقت Gate را بسنجد: golden set از
enquiry/review/suburb با خروجی مورد انتظار + متریک (gate precision/recall روی consent/ABN/ACL،
نرخ HARD_BLOCK کاذب، هزینه per-draft). offline و قابل‌اجرا در CI (mock/cassette، بدون API واقعی).
Acceptance: make eval گزارش متریک چاپ کند؛ regression روی gate باعث fail CI شود.
```

### P7 — بهینه‌سازی هزینه: فعال‌سازی واقعی prompt caching و batch ✅ DONE (2026-07-02، test_phase7_costopt 26/26)
```
flagهای CACHE_ENABLED/BATCH_ENABLED وجود دارند ولی به فراخوان Anthropic سیم نشده‌اند.
prompt caching روی بخش ثابت پرامپت‌های Worker C (system/template) + batch API برای
follow-upهای روز 2/5/10 (زمان‌حساس نیستند). قید: check_and_enforce هزینه‌ی واقعی پس از
cache discount را لاگ کند.
Acceptance: مقایسه هزینه per-draft قبل/بعد؛ هدف >=50% کاهش روی توکن system تکراری.
```

### P8 — مقاوم‌سازی I/O خارجی: retry/backoff + rate-limit + idempotency  ✅ DONE (2026-07-01)
```
Serper و Anthropic بدون retry هستند؛ یک شکست شبکه = شکست draft. wrapper مشترک با exponential
backoff + jitter، احترام به Retry-After، و idempotency key علیه draft/charge تکراری روی retry.
قید: backoff سقف per-day را دور نزند (check_and_enforce هر تلاش)؛ هر retry در audit.
Acceptance: تست شبیه‌سازی 429/500 -> backoff و موفقیت نهایی؛ تست که retry هزینه‌ی مضاعف لاگ نکند.
```

### P9 — بهینه‌سازی لایه‌ی داده: connection pooling + معماری DB  ✅ DONE (2026-07-01)
```
الان هر audit.append/gate/governance یک connection باز و بسته می‌کند (هر اکشن چند بار).
یک connection manager/pool سبک بساز + ارزیابی trade-off SQLite vs Postgres برای رشد
(concurrency نوشتن audit). قید: append-only و hash-chain صدمه نبیند؛ verify_chain سبز بماند؛
DB از LANGAR جدا.
Acceptance: benchmark تعداد connection per enquiry قبل/بعد؛ تست concurrency نوشتن audit
بدون شکست زنجیره.
```

### P10 — استقرار end-to-end infra-control + SOPS+age + threat-model hardening
```
اسکلت infra-control را روی VPS end-to-end deploy و تست کن: stackctl up brushline پشت Traefik،
یک چرخه‌ی کامل CI (push->test->gitleaks->build->GHCR->deploy->health->rollback)، جایگزینی
.env دستی Brushline با SOPS+age، و پیاده‌سازی موارد باز THREAT_MODEL.md.
قید: branch protection روی main؛ stackctl kill --all تست شود؛ هیچ secret خام در git.
Acceptance: یک deploy عمداً-خراب -> auto-rollback + alert تلگرام؛ secretها فقط رمزنگاری‌شده
در repo؛ RUNBOOK/DEPLOY.md به‌روز.
```

---

## ترتیب پیشنهادی (ROI + survival filter)
1. ✅ P3  (Approval Queue — DONE 2026-07-01) — قلب INV-1 برقرار
2. ✅ P1 + P2 (review + suburb + semantic ACL) DONE 2026-07-01 — Phase 2 کامل؛ شکاف compliance بسته
3. ✅ P8 + P9  (مقاوم‌سازی I/O و DB) DONE 2026-07-01
4. ✅ P6  (eval — golden set + gate metrics + make eval) DONE 2026-07-01
5. P10 (infra e2e — وقتی اپ production-ready شد)  <- 