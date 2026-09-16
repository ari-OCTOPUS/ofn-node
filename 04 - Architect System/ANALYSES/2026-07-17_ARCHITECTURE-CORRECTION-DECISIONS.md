---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, architecture, correction, subtractive-design, proposal-router]
created: 2026-07-17
updated: 2026-07-17
created_by: agent
sources:
  - "[[04 - Architect System/ANALYSES/2026-07-17_DEEP-SCAN-OCTOPUS-ARCHITECTURE]]"
  - "[[04 - Architect System/ANALYSES/2026-07-17_ARCHITECTURE-CRITIQUE-PROMPT]]"
---

# 🐙 Architecture Correction Decisions — آزادسازیِ پتانسیلِ اختاپوس

> هدف: تبدیلِ اختاپوس از «زنده ولی idle» به «حلقهٔ یادگیریِ کوچک و بسته» بدون شکستنِ I1–I10، I7، TINV-7، append-only و propose-only.
>
> تغییرِ کدیِ همین جلسه: بستنِ شکافِ G1 با یک Proposal Router سبک در `_ops/live_loop.py` و اتصالش به beat در `_ops/organism.py`؛ outcome metric حداقلی برای G3 اضافه شد. هیچ مسیرِ پولی/settle/approve/secret/schtasks لمس نشد.

---

## ۱) اعتبارسنجی تشخیص G1–G4 + گپ پنجم

تشخیص G1–G4 درست است، اما یک گپ پنجم عمیق‌تر هم هست:

| گپ | رأی معماری |
|---|---|
| **G1 پاهای بی‌سر** | ریشه‌ای و فوری. پاها proposal می‌سازند ولی تحویل انسانی ندارند؛ این یعنی سیستم حتی چیزی برای کلیک به مالک نمی‌دهد. |
| **G2 مسیر پولی زنده ندارد** | درست، ولی نباید اول با پول شروع شود. اول باید proposalها دیده شوند؛ بعد فقط یک مسیر lead paper-to-human فعال شود. |
| **G3 حلقه یادگیری باز است** | درست. `delta_self` و `velocity` خیلی دور از action هستند؛ اول باید near-action metrics ساخته شود. |
| **G4 intake موازی** | درست ولی P1، نه P0. اگر Router نباشد، canonical کردن intake هم سیگنالی تولید نمی‌کند. |
| **G5 گپ observability/actionability** | سیستم «می‌داند» اما «مالک نمی‌بیند و نمی‌تواند تصمیم بگیرد». نمونه: `_emit_advisory()` subscriberها را واقعاً notify نمی‌کرد؛ `proposals_emitted` داخل پا می‌ماند؛ بعضی stateها فقط سایدکارند. |

**تصمیم:** P0 = قابل‌دیدن کردن proposalها و advisoryها؛ نه اضافه‌کردن مغز یا قلب جدید.

---

## ۲) کجا بیش‌ازحد مهندسی شده؟ حذف/ادغام پیشنهادی

### حذف/تعلیق ۳–۵ مؤلفه تا وقتی flywheel اول نچرخیده

1. **Cardiac allometry / `OCTOPUS_WIRE_BIO` — تعلیق تا revenue یا active mass واقعی**
   - چرا: وقتی mass≈1 و revenue=0، ریتم زیستی فقط استعارهٔ پرهزینه است.
   - ریسک روشن‌کردن زودهنگام: periodهای زیبا ولی بی‌معنا؛ تشدید توهم حیات.

2. **Ignition/GWT/WTA — تعلیق تا queue واقعی proposal/outcome داشته باشیم**
   - چرا: attention بدون ورودی واقعی، attention به نویز است.
   - جایگزین فعلی: ranking سادهٔ Proposal Router.

3. **Evolution/Box-of-Agents — freeze تا n≥20 outcome واقعی**
   - چرا: تکامل بدون fitness معتبر، تولید mutationهای نمایشی است.
   - شرط بازگشت: حداقل ۲۰ proposal delivered و ۵ outcome انسانی.

4. **۵۸ فلگ wiring → سه profile قابل‌فهم**
   - پیشنهاد: `paper`, `mvo-live`, `research`؛ هر فلگ جزئی فقط زیر profile و با دلیل.
   - خطر فعلی: drift و green-lie؛ کسی نمی‌داند چرا فلگ روشن است.

5. **سه قلب → یک قلب عملیاتی + یک shadow diagnostic**
   - Pacemaker/chrono بماند؛ heart-shadow فقط metric؛ cardiac خاموش.
   - کنترل‌لای ۷لایه تا وقتی velocity واقعی نیست، decision-maker نباشد.

---

## ۳) Proposal Router / delivery pipeline — طراحی و اجرای حداقلی

### Data-flow

```text
Leg.emit_proposal()
   ↓  local leg.proposals  [propose-only; no send/pay/publish]
LiveLoop.route_leg_proposals([lead,ziman,cartographer])
   ↓ normalize Proposal.to_dict()
   ↓ dedupe by hash/proposal_id
   ↓ rank: quote/revenue-like first, then reports/content
   ↓ create Telegram advisory card
   ├─ if channel exists: channel.send_text(card)  [visibility only]
   └─ LiveLoop._emit_advisory("PROPOSAL", …)       [no ledger write]
   ↓
ORGANISM-STATE.proposal_router
   ↓
owner can later judge via existing human-gated paths
```

### تغییر اعمال‌شده

- `_ops/live_loop.py`
  - `_notify_advisory_subscribers()` اضافه شد: advisory subscriberها واقعاً notify می‌شوند بدون `bus.publish` و بدون ledger write.
  - `route_leg_proposals()` اضافه شد: gather/rank/dedupe/deliver proposalهای پا.
  - `record_proposal_outcome()` و `proposal_metrics()` اضافه شد: نزدیک‌ترین حلقهٔ یادگیری برای G3.
- `_ops/organism.py`
  - هر beat، Router روی `_leg`, `_ziman_leg`, `_cartographer_leg` صدا زده می‌شود با `limit=5` و در state با کلید `proposal_router` دیده می‌شود.
- `_ops/tests/test_live_loop.py`
  - تست برای notify واقعی advisory، dedupe delivery، و outcome metrics اضافه شد.

### ناوردی‌ها

- هیچ `approve` خودکار.
- هیچ `settle`.
- هیچ مسیر spend یا publish بیرونی.
- هیچ حذف از leg.proposals.
- dedupe in-memory برای جلوگیری از spam در همان run.

---

## ۴) بستن حلقه یادگیری G3 — outcome attribution

متریک‌های درست باید نزدیک به action باشند، نه فقط `velocity/delta_self`.

### متریک‌های P0

| Metric | چرا |
|---|---|
| `proposals_delivered` | آیا سیستم چیزی قابل‌تصمیم به مالک رسانده؟ |
| `proposal_outcomes` | آیا مالک/دنیا پاسخ داده؟ |
| `proposal_accept_rate` | quality signal ساده و واقعی. |
| `proposal_value_aud` | ارزش نزدیک به درآمد، حتی قبل از reconcile. |
| `lead_to_quote`, `quote_to_sent`, `sent_to_paid` | funnel واقعی Lead. |

### Data-flow outcome

```text
Proposal delivered
   ↓
Owner response / sent / rejected / paid / ignored
   ↓
LiveLoop.record_proposal_outcome(proposal_id, verdict, value_aud)
   ↓
proposal_metrics()
   ↓
Cortex.measure() should ingest these before velocity/delta_self
   ↓
rerank future proposals
```

**تصمیم بعدی:** `goal_directed.measure()` باید این metrics را از state/live_loop بخواند. فعلاً foundation در LiveLoop ساخته شد؛ اتصال Cortex گام بعدی است.

---

## ۵) نردبان خودمختاری L0→L4 بدون شکستن I7

I7 یعنی «پذیرفته» فقط انسان. اما خودمختاری می‌تواند در انتخاب/ترتیب/پیش‌پردازش رشد کند.

| سطح | اختیار سیستم | شرط ارتقا | انسان چه می‌کند؟ |
|---|---|---|---|
| L0 Observe | فقط telemetry و گزارش | همیشه | می‌بیند |
| L1 Propose | proposal بسازد و تحویل دهد | invariants سبز | رد/تأیید انسانی |
| L2 Prioritize | rank/dedupe/throttle کند | ≥20 delivered، no PII leak، accept_rate معلوم | فقط موارد مهم را می‌بیند |
| L3 Prepare | draft کامل quote/email/invoice بسازد | ≥10 outcome مثبت، صفر incident | ارسال/settle همچنان انسان |
| L4 Bounded auto-internal | knobهای داخلی $0 را تنظیم کند | proof-of-reliability + rollback | فقط audit/verdict دوره‌ای |

### Proof-of-reliability

- ۳۰ روز log بدون PII/secret leak.
- proposal_accept_rate بالاتر از baseline دستی.
- صفر double-send / double-post.
- هر action replayable و bounded.
- fail-closed تحت STOP/FREEZE.

---

## ۶) اندازه درست قلب

حداقل قلب عملیاتی:

```text
Pacemaker/HLC + STOP awareness + heartbeat row
   + lightweight state freshness
   + advisory velocity only when outcome stream exists
```

تا وقتی outcome stream نداریم:

- `velocity=0.083` mostly liveness است؛ نباید به‌عنوان productivity تعبیر شود.
- `delta_self=0` نشان شکست cognition نیست؛ نشان نبود سیگنال است.
- control-law ۷لایه باید diagnostic بماند، نه governor اصلی.

**تصمیم:** قلب را ساده کن: pacemaker authoritative؛ shadow diagnostic؛ cardiac off تا `proposal_outcomes >= 20` یا `confirmed_revenue > 0`.

---

## ۷) کوچک‌ترین flywheel درآمد→یادگیری / MVO

### MVO پیشنهادی

```text
Lead discovery/manual lead
   ↓
LeadLeg.intake → attribution_id
   ↓
LeadLeg.draft_quote / lead_quote.create_quote
   ↓
Proposal Router → Telegram advisory card
   ↓
Owner: send / reject / edit
   ↓
record_proposal_outcome
   ↓
If sent/paid: claim/reconcile later
   ↓
Cortex learns ranking and copy/scope quality
```

### ۸۰٪ سیستم که فعلاً نادیده گرفته شود

- Evolution/Box/Chamber-T.
- Cardiac allometry.
- Ignition/GWT.
- Multi-leg autonomy beyond Lead + Ziman status.
- Paid LLM lanes.
- Code autonomy.

### ۲۰٪ که باید بچرخد

- LeadLeg.
- Proposal Router.
- Telegram visibility.
- Outcome metric.
- Manual owner action.
- Reconcile later.

---

## ۸) ریسک‌های پنهان طراحی

1. **Single human append = bottleneck** — امن است اما اگر UI چیزی نشان ندهد، سیستم می‌میرد. Router درمان P0 است.
2. **Flag drift** — ۵۸ فلگ بدون profile discipline تبدیل به معماری غیرقابل‌حکمرانی می‌شود.
3. **Propose-only everywhere = no owner of decision** — باید owner of proposal quality داشته باشیم: Proposal Router + metrics.
4. **Metric theater** — coherence و heartbeat بالا می‌توانند failure را پنهان کنند.
5. **State sidecars بدون consumer** — نوشتن state کافی نیست؛ باید مسیر مشاهده/تصمیم هم باشد.
6. **Parallel intakes** — اگر canonical نشوند، attribution گم می‌شود.
7. **No persistence for router dedupe** — فعلاً in-memory است برای کم‌ریسک بودن؛ اگر spam بعد از restart دیدیم، state-backed dedupe با TTL اضافه شود.
8. **Outcome metric misuse** — `record_proposal_outcome(approved)` نباید با I7 approval اشتباه گرفته شود؛ فقط measurement است.

---

## ۱۰ تصمیم اولویت‌بندی‌شده

1. **[P0] Proposal Router فعال شد** — چرا: بدون delivery، هیچ حلقه‌ای نمی‌چرخد — ریسک: spam کنترل‌شده با dedupe/limit — اگر نکنیم: پاها تاریک می‌مانند.
2. **[P0] Advisory subscriber no-op بسته شد** — چرا: نخاع باید واقعاً notify کند — ریسک: subscriber خراب؛ fail-soft است — اگر نکنیم: سیستم می‌داند ولی مصرف‌کننده نمی‌شنود.
3. **[P0] Outcome metrics حداقلی ساخته شد** — چرا: G3 با near-action signal بسته می‌شود — ریسک: اشتباه گرفتن با approval؛ docstring/test محافظ دارد — اگر نکنیم: `delta_self=0` می‌ماند.
4. **[P0] Cortex.measure را در گام بعد به `proposal_metrics` وصل کن** — چرا: مغز باید از acceptance/rejection یاد بگیرد — ریسک: metric gaming — اگر نکنیم: یادگیری فقط روی درآمد صفر می‌ماند.
5. **[P1] Lead intake را canonical کن** — چرا: G4 — ریسک: شکستن مسیر قدیمی `/lead` — اگر نکنیم: attribution گم می‌شود.
6. **[P1] فقط Lead MVO را زنده کن** — چرا: کوچک‌ترین حلقه درآمدی — ریسک: وابستگی به مالک برای ارسال — اگر نکنیم: revenue=0 ادامه دارد.
7. **[P1] فلگ‌ها را به سه profile کاهش بده** — چرا: کاهش بار شناختی — ریسک: migration bug — اگر نکنیم: drift ادامه دارد.
8. **[P1] Cardiac/BIO را تا outcome کافی خاموش نگه دار** — چرا: جلوگیری از science theater — ریسک: از دست دادن allometry زودهنگام — اگر نکنیم: heartbeat زیبا ولی بی‌اثر.
9. **[P2] Evolution/Box را پشت شرط outcome باز کن** — چرا: fitness واقعی لازم دارد — ریسک: دیر فعال شدن — اگر نکنیم: mutation روی نویز.
10. **[P2] Router dedupe را اگر لازم شد state-backed کن** — چرا: restart spam — ریسک: state complexity — اگر نکنیم: after-restart duplicate cards.

---

## وضعیت اجرای همین جلسه

- کد additive و propose-only است.
- مسیرهای ممنوع، secret، `.git`، `_code`، پول، schtasks، حذف/آرشیو لمس نشد.
- تست‌ها به فایل موجود اضافه شدند، اما در این محیط ابزار اجرای Python/Shell در دسترس نبود؛ اجرای مالک/ایجنت بعدی:

```powershell
python -X utf8 "F:\backup\_ops\tests\test_live_loop.py"
python -X utf8 "F:\backup\_ops\tests\run_all.py"
```

اگر تست سبز بود، next step = اتصال `proposal_metrics()` به `goal_directed.measure()` و سپس canonical کردن Lead intake.
