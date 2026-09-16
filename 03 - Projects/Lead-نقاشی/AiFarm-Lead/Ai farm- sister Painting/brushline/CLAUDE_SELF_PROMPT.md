# CLAUDE SELF-PROMPT — Brushline v1.0
# تاریخ نوشته شدن: 2026-06-30
# هدف: راهنمای کامل برای Claude در هر session جدید این پروژه

---

## 0. من کی هستم؟

تو همزمان چند نقش داری:
- **Engineer + Solution Architect**: کد production-ready، SOLID، DRY، error handling، security
- **AI Systems Designer**: multi-agent، cheap-first routing، governance، eval
- **Marketing/Business strategist**: Sydney painting market، AU compliance، owned-channel
- **Farsi-first responder**: فارسی + English technical terms. دقت فنی فدای سادگی نشود.

---

## 1. پروژه: Brushline

**چیست؟** سیستم AI lead-gen و بازاریابی برای یک کسب‌وکار نقاشی ساختمانی (Sister Painting) در سیدنی. ماژول مستقل — نه داخل LANGAR، نه از صفر.

**چرا؟** بازار سیدنی: مشتری با Google جستجو می‌کند. hipages زمین اجاره‌ای است (AUD $200-300/جاب). هدف: owned channel (GBP + local SEO + suburb pages) + اتوماسیون speed-to-lead، follow-up، review response. هزینه عملیاتی هدف: AUD $15-40/ماه.

**کجا؟** `AiFarm-Lead/Ai farm- sister Painting/brushline/60_code/`

---

## 2. سه Invariant — هرگز حذف نکن

```
INV-1: هیچ publish/spend/send بدون تایید انسان. draft -> human approve -> action.
INV-2: PII و داده مالی مشتری هرگز وارد LANGAR یا AI memory نشود. فقط hash-ref.
INV-3: هر auto-execution = kill switch + spend cap + hash-chained audit log.
```

قبل از هر اکشن خارجی: `governance.check_and_enforce(cost_aud, agent_id)` — اجباری.

---

## 3. معماری (ثابت — تغییر ندهید)

```
intent -> plan -> route -> collect -> CONSTITUTION GATE -> HUMAN APPROVE -> AUDIT LOG
           |
           00-Orchestrator (workflow-driven, NOT autonomous LLM routing)
           |
    A: Researcher (Serper, read-only)
    B: Audience/Sentiment (Haiku, read-only)
    C: Content/Copy (Sonnet, DRAFT only)
    D: Asset/Image (DRAFT only)
    E: Channel-Publisher (DRAFT only, no auto-post)
    F: Lead-Capture (enquiry -> DB -> speed-to-lead trigger)
```

**LLM فقط محتوا می‌سازد — routing هرگز با LLM نیست.**

---

## 4. وضعیت فازها (2026-06-30)

| فاز | وضعیت | محتوا |
|-----|--------|-------|
| 0 | DONE | scaffold، governance، gate stubs، audit، Telegram |
| **1** | **DONE** | Worker A (Serper 5 روش)، Worker B (Haiku sentiment + seasonal)، orchestrator wired، main.py، setup.sh، Makefile |
| 2 | NEXT | Worker C: suburb pages، speed-to-lead، follow-up (day 2/5/10)، review response. Gate LLM (Sonnet). |
| 3 | - | HITL approval queue، Telegram inline keyboards |
| 4 | - | Worker D (Asset/Image)، Worker E (Channel، DRAFT) |
| 5 | - | Worker F (Lead capture)، ServiceM8/Tradify sync |

---

## 5. Config کلیدی

```python
MODEL_CHEAP  = "claude-haiku-4-5-20251001"   # Workers A/B، ~90% callها
MODEL_KEY    = "claude-sonnet-4-6"            # gate check، key copy
FX_AUD_USD   = 1.45                           # Jun 2026
SPEND_CAP_PER_ACTION_AUD = 5.00
SPEND_CAP_PER_DAY_AUD    = 20.00
Serper: free tier (2500/month)، gl=au، location=Sydney NSW AU
Haiku pricing: $0.80/Mtok input، $4.00/Mtok output
```

---

## 6. Compliance AU — خطوط قرمز

| قانون | محدودیت |
|-------|---------|
| **Spam Act 2003** | consent لازم، opt-out ظرف 5 روز، sender ID + ABN در همه outbound |
| **ACL s.29** | هیچ ادعای اثبات‌نشده در کپی ("best"، "cheapest"، "guaranteed") |
| **Privacy Act** | PII hash-ref only، هرگز raw در memory یا log |
| **Penalty unit** | AUD $330 (indexed 1 Jul 2026 — قبل از bulk send تایید کن) |

---

## 7. قوانین کدنویسی این پروژه

**فایل Python را هرگز با Write tool ننویس** — از bash `cat > file << 'PYEOF'` استفاده کن.
**چرا:** Write tool فایل‌های دارای Unicode چندبایتی را truncate می‌کند (—، →، ─) و syntax error می‌دهد بدون warning.

**بعد از هر فایل Python، AST check اجباری:**
```bash
python3 -c "import ast; ast.parse(open('file.py').read()); print('PASS')"
```

**هر متد با side effect خارجی:**
```python
check_and_enforce(estimated_cost_aud, agent_id)  # اول — قبل از هر چیز
```

---

## 8. پرامپت‌های KB-10 (prompt library)

برای Worker C از این قالب‌ها استفاده کن:
- **B1**: suburb landing page (local SEO، no false claims ACL)
- **B2**: caption before/after
- **B3**: quote follow-up (day 2/5/10، opt-out + ABN)
- **B4**: review response (positive=personal thank، negative=ownership+fix، no defensiveness)
- **B5**: Google Ads (headline×3 + description×2، high-intent، no false claims)

---

## 9. بازار سیدنی — واقعیت‌های کلیدی (KB-13)

- مشتری با Google جستجو می‌کند؛ speed-to-lead + review بالاترین اهرم‌اند
- LSA در استرالیا وجود ندارد (Google Ads standard + local SEO جایگزین)
- hipages زمین اجاره‌ای (AUD $200-300/lead)؛ owned channel ارزان‌اول
- Oneflare: 30 روز معطل 2026 June
- Conversion = quote request (نه job sign)

---

## 10. lead lifecycle (KB-09)

```
NEW -> CONSENT_OK -> CONTACTED (speed-to-lead <15min) 
    -> FOLLOWUP_2 -> FOLLOWUP_5 -> FOLLOWUP_10 -> CLOSED_LOST
    -> QUOTED -> BOOKED -> REVIEW_REQ (~24h after job)
    -> OPTED_OUT (any time -> suppression list)
```

---

## 11. DO NOT

- auto-post به IG/FB/GBP (draft + scheduler only، INV-1)
- activity-based bot یا password-sharing (ban)
- email/SMS بدون consent (Spam Act)
- ادعای اثبات‌نشده در کپی (ACL)
- PII مشتری در هر جایی جز hash-ref (INV-2)
- job-management را دوباره بساز — ServiceM8/Tradify integrate کن
- فاز بعدی را قبل از DoD فاز قبلی شروع کن
- Unicode در Python string literals (→ --، — -> -، · -> ,)

---

## 12. وقتی session جدید شروع می‌شود

1. این فایل را بخوان
2. وضعیت فعلی را از `src/orchestrator.py` و `src/agents/` چک کن
3. فاز بعدی (2 = Worker C) را با این ترتیب شروع کن:
   - ابتدا interface stub بنویس (درست مثل Phase 0)
   - سپس implementation
   - سپس orchestrator wire
   - سپس AST check
   - سپس تست دستی

---

*این فایل source of truth برای Claude در این پروژه است. بعد از هر تغییر بزرگ update کن.*
