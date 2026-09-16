# 06 — LEAD FUNNEL STATE MACHINE (P0 OutcomeAttributionLeg contract)
**Version:** 1.0 · **Date:** 2026-07-21 · **Phase:** B (architecture & contracts — طراحی، نه پیاده‌سازی)
**Governing docs:** `00_MASTER_BLUEPRINT.md` §5/§10 · `lead_inbox/LEAD_INBOX_SPEC.md` §1–§3 (قرارداد canonical v1.1 + event contract) · `OPUS_MISSION_PROMPT.md` (invariants + P0-4) · `RUNTIME-TRUTH-RECONCILE-2026-07-21.md` (نقشهٔ file:line آنچه واقعاً هست)
**Companion:** `05_CONSENT_STATE_MACHINE.md` (چه کسی اصلاً حق ورود به funnel را دارد — این سند فرض می‌کند firewall قبلاً رأی داده)

> ⚠️ **تصحیحِ راستی‌آزماییِ متخاصم (2026-07-21) — یک ادعای غلط در برابرِ کد اصلاح شد.** ادعای اولیهٔ این سند
> که «`sweep_stale_effects:416` حالتِ `send_pending` را backstop می‌کند» **غلط بود و در برابرِ کد رد شد**:
> `chrono.py:424` فقط `WHERE status='pending'` را جارو می‌کند، ولی `send_pending`ِ funnel به وضعیتِ
> `releasable` نگاشت می‌شود (چون `release_gated_effects:385` وضعیت را pending→releasable می‌کند) — که هیچ
> مکانیزمِ موجودی هرگز منقضی‌اش نمی‌کند (تنها خروجی‌ها: `settle`→settled یا refuse سرِ settle). **پس گاردِ
> staleness برای این لبه در کدِ فعلی وجود ندارد و باید در لایهٔ bridge/workerِ فاز C ساخته شود** (نه در chrono).
> جزئیاتِ کامل + همهٔ اصلاحاتِ غیرمسدودکننده: `00_VERIFICATION_AND_FIXES.md`. سطرهای متأثر پایین با «تصحیح» علامت خورده‌اند.

---

## 0. اصل حاکم — دو سیگنال که هرگز قاطی نمی‌شوند

این state machine دو نیمهٔ به‌عمد جدا دارد و جدایی‌اش **از قبل در کد enforce شده است** — طراحی P0 آن را تغذیه می‌کند، نه بازاختراع:

1. **نیمهٔ داخلی (internal quality signal):** `received → qualified → delivered_to_owner → owner_approved|edited|rejected`. رأی مالک فقط measurement است. کد موجود این را ساختاراً قفل کرده: `_ops/outcomes/verdict_recorder.py:26` فقط `{accepted-measurement, rejected, deferred}` را می‌پذیرد و `:33` صراحتاً `{delivered, settled, failed, verified}` را از رأی ممنوع کرده — رأی مالک هرگز به «ارسال/تحویل/درآمد» تعبیر نمی‌شود.
2. **نیمهٔ بازار (market outcome signal):** `sent → delivered → replied → inspection_booked → quote_sent → won|lost → paid → gross_profit → repeat|referral`. پول فقط از مسیر reconcile تأیید می‌شود: `_ops/budget/attribution.py:9-10` — «CONFIRMED/ATTRIBUTED را فقط reconcile-job می‌نویسد؛ خودگزارشیِ ایجنت هرگز CONFIRMED نمی‌شود».

**قاعدهٔ سخت:** هیچ رویداد بازاری هرگز از مسیر `verdict_recorder` نوشته نمی‌شود و هیچ رأی مالکی هرگز state بازاری نمی‌سازد. Governor (`goal_directed.measure`) هر دو را جدا می‌خواند.

---

## 1. سه ماشین، نه یکی (مالکیت state)

| ماشین | کلید | مالک state | محل زندگی |
|---|---|---|---|
| **LeadFunnel** (این سند) | `lead_id` | **derived** — هرگز ذخیرهٔ mutable؛ همیشه fold از ژورنال append-only | ژورنال جدید `state/outcomes/funnel.db` (§8) |
| **Proposal** | `proposal_id` (چند نمونه per lead: first_touch، quote، follow-up) | live_loop (in-memory) + رأی durable در `outcomes.db` | `_ops/live_loop.py:327/429` + `_ops/outcomes/outcome_store.py` |
| **Effect** | `effect_id` | **EffectorGate — دست نمی‌زنیم** | `_ops/chrono.py:344` — `pending → releasable → settled | refused` |

همهٔ سه ماشین با IDهای مشترک به هم لینک‌اند (تست الزامی #14 در OPUS_MISSION_PROMPT): هر رویداد ژورنال `correlation_id=lead_id` + `causation_id=event_id قبلی` + در صورت وجود `proposal_id`/`effect_id`/`attribution_id` را حمل می‌کند (envelope دقیقاً SPEC §3).

---

## 2. کاتالوگ stateها

شناسه‌ها ASCII و ثابت‌اند. کلاس: `INT` = داخلی، `MKT` = بازاری، `DEAD` = پایانه (هرگز outbound از آن نمی‌روید).

| # | state | کلاس | رویداد ورود (SPEC §3) | معنی دقیق |
|---|---|---|---|---|
| 1 | `received` | INT | `lead.candidate.received` | مرز امضاشده payload را پذیرفت؛ receipt append شد |
| 2 | `quarantined` | DEAD | `lead.candidate.rejected` | payload نامعتبر/بی‌امضا → قرنطینه + کارت هشدار؛ هرگز drop بی‌صدا |
| 3 | `duplicate` | DEAD* | `lead.duplicate.detected` | replay با همان Idempotency-Key → merge به لید اصلی (pseudo-terminal: خودش funnel ندارد، به `lead_id` اصلی اشاره می‌کند) |
| 4 | `normalized` | INT | `lead.normalized` | نگاشت به قرارداد canonical v1.1 کامل شد (state گذرا؛ در fold با received ادغام‌پذیر ولی رویدادش الزامی است) |
| 5 | `qualified` | INT | `lead.qualified` | scorer قطعی رأی داد (score/category/action) + پرسش‌های غایب + risk flags |
| 6 | `compliance_blocked` | DEAD† | `lead.compliance_blocked` | firewall رضایت یا suppression مسیر را بست (fail-closed). † خروج فقط با شواهد رضایت جدید = زنجیرهٔ رویداد جدید (سند 05) |
| 7 | `delivered_to_owner` | INT | `proposal.routed` | کارت پیشنهاد (first_touch یا quote) به سطح مالک تحویل شد |
| 8 | `owner_approved` | INT | `proposal.owner_approved` | رأی «آره» — فقط measurement؛ هنوز هیچ اثری در جهان نیست |
| 9 | `owner_edited` | INT | `proposal.owner_edited` | متن ویرایش‌شدهٔ مالک جایگزین draft شد؛ diff برای learning ذخیره می‌شود؛ از نظر funnel معادل approved با پرچم edited |
| 10 | `owner_rejected` | DEAD | `proposal.owner_rejected` | «نه» یا «Junk» — payload.reason ∈ {junk, not_now, out_of_scope, other}؛ junk به کیفیت source امتیاز منفی می‌دهد |
| 11 | `expired` | DEAD‡ | `outcome.recorded` (payload.kind=`proposal_expired`) | کارت بی‌اقدام: nudge در T+15min، سپس expiry (§6). ‡ لید نمی‌میرد — proposal می‌میرد؛ re-propose با proposal_id جدید مجاز |
| 12 | `send_pending` | MKT-edge | `effect.released` | LANGAR append انجام شد و EffectorGate اثر را releasable کرد؛ هنوز settle نشده |
| 13 | `sent` | MKT | `communication.sent` | اولین پیام خارجی واقعاً رفت (settle موفق یا attestation دستی مالک — §7) → `leads.first_response_at` ست می‌شود |
| 14 | `send_failed` | MKT (re-entrant) | `communication.failed` | provider خطا داد یا gate refuse کرد → alert + retry-safe؛ برگشت به `send_pending` یا `owner_approved` |
| 15 | `replied` | MKT | `customer.replied` | مشتری پاسخ داد (تکرارپذیر — رتبه regress نمی‌کند) |
| 16 | `inspection_booked` | MKT | `inspection.booked` | بازدید قطعی شد (دستور `/meeting`) |
| 17 | `quote_sent` | MKT | `quote.sent` | کوت به مشتری رفت — همزمان `attribution.claim` → state پولی CLAIMED |
| 18 | `won` | MKT | `quote.won` | مشتری بله گفت (claim بازاری، هنوز نه پول) |
| 19 | `lost` | DEAD | `quote.lost` | باخت + `lost_reason` اجباری ∈ {price, timing, competitor, no_response, out_of_area, scope_mismatch, licence_gate, expired, other} |
| 20 | `dead` | DEAD | `outcome.recorded` (payload.kind=`lead_dead`) | دستور `/dead` — لیدی که هرگز جواب نداد/منتفی شد؛ جدا از lost (کوتی در کار نبود) |
| 21 | `paid` | MKT | `invoice.paid` | **فقط** reconcile-job پس از تطبیق با feed مستقل (attribution CONFIRMED/ATTRIBUTED) |
| 22 | `gross_profit_recorded` | MKT | `outcome.recorded` (payload.kind=`gross_profit`) | paid − هزینهٔ owner-entered؛ P0-اختیاری (تصمیم باز O-3) |
| 23 | `repeat_or_referral` | MKT-loop | `outcome.recorded` (payload.kind=`repeat`&#124;`referral`) | لید جدیدی با `parent_lead_id` به همین لید رسید → حلقه به `lead.candidate.received` جدید بازمی‌گردد |
| 24 | `synthetic_done` | DEAD | `outcome.recorded` (payload.kind=`synthetic_complete`) | پایانهٔ اجباری لیدهای `source.channel=synthetic_test` — هرگز وارد نیمهٔ بازاری نمی‌شوند (§9) |

نکتهٔ نام‌گذاری (تلهٔ شناسایی‌شده در RUNTIME-TRUTH §4-7): `event_type="delivered"` در `outcomes.db` موجود یعنی «رسید تصمیم در sandbox / کارت به مالک تحویل شد» — **نه** «پیام به مشتری تحویل شد». در funnel، تحویل به مالک = `delivered_to_owner` (رویداد `proposal.routed`) و تحویل provider = رویداد الحاقی `communication.delivered` (EXT، §5). این دو هرگز یک ستون/نام مشترک نمی‌گیرند.

---

## 3. جدول گذارها (transition table)

قالب: `از → به` · تریگر · گارد (همه fail-closed) · رویداد emit‌شده · ثبت‌کنندهٔ موجود.

### 3.1 نیمهٔ داخلی

| از → به | تریگر | گاردها | رویداد | ثبت‌کنندهٔ امروز (file:line) |
|---|---|---|---|---|
| ∅ → `received` | POST امضاشده به `/api/v1/lead-candidates` یا `/lead` مالک | HMAC+ts+nonce+allowlist+schema (سند 07)؛ suppression check | `lead.candidate.received` | مرز = جدید؛ الگوی persist از `lead_leg_inbox.register_lead` (`_ops/legs/lead_leg_inbox.py:86`، atomic tmp+replace) reuse می‌شود |
| ∅ → `quarantined` | payload نامعتبر/امضای بد | هرگز drop بی‌صدا؛ کارت هشدار الزامی | `lead.candidate.rejected` | الگوی quarantine موجود: `lead_sense._move_with_sidecar → rejected/` + سایدکار دلیل (`_ops/legs/lead_sense.py:104`) |
| ∅ → `duplicate` | Idempotency-Key تکراری | پاسخ 200 با lead_id اصلی (idempotent، نه خطا) | `lead.duplicate.detected` | منطق dup موجود ولی روی text-hash: `lead_leg_inbox.py:110-126` (24h) و `lead_sense.seen_before:72`؛ **re-key به `source:external_id`** (تغییر، نه ساخت) |
| `received` → `normalized` | نگاشت به قرارداد v1.1 | فیلدهای الزامی پر؛ خطا → quarantine | `lead.normalized` | امروز فقط lowercase/hash (`lead_leg_inbox.py:42`) — normalizer canonical **جدید** |
| `normalized` → `qualified` | scorer | firewall رضایت قبلاً رأی داده (سند 05)؛ suppression دوباره چک | `lead.qualified` | **موجود:** `lead_scorer.score_lead` (`_ops/legs/lead_scorer.py:236,280`) که همین حالا از `wiring.py:1826-1866` (lead_discovery_beat، پشت فلگ) صدا می‌شود؛ فقط emit رویداد funnel جدید است |
| `normalized` → `compliance_blocked` | firewall/suppression | — | `lead.compliance_blocked` | **جدید** (firewall صفر occurrence در کد — RUNTIME-TRUTH §0) |
| `qualified` → (artifact) | draft آماده شد | propose-only؛ صفر ارسال | `response.draft.prepared` / `quote.draft.prepared` | first-response = **جدید** (تنها نیمهٔ غایب P0-3 — RUNTIME-TRUTH §2-8)؛ quote = **موجود:** `lead_quote.create_quote` + `lead_to_intake:77` (پشت `OCTOPUS_WIRE_LEAD_DRAFT`، صدا در `wiring.py:1873-1879`) و `lead_leg.draft_quote:89` |
| `qualified` → `delivered_to_owner` | router کارت را تحویل داد | یک first_touch proposal باز per lead (idempotency از LEG P0-1) | `proposal.routed` | **موجود (SHADOW):** `live_loop.route_leg_proposals` (`_ops/live_loop.py:327`؛ رویداد advisory «delivered» در `:396-400`؛ دکمه‌ها پشت `OCTOPUS_WIRE_PROPOSAL_BUTTONS` در `:366`) + رسید durable: `lead_outcome_recorder.record_lead_decision` (`_ops/outcomes/lead_outcome_recorder.py:38`، event_type=`delivered` یعنی رسید sandbox) |
| `delivered_to_owner` → `owner_approved` | تپ «آره» | single-use: اولین تصمیم برنده (`meta["decided"]`) | `proposal.owner_approved` | **موجود:** `record_proposal_outcome_by_token` (`live_loop.py:429`) → `_record_durable_verdict:454` → `verdict_recorder.record_verdict_durably:99` → ردیف `accepted-measurement` در `outcomes.db` (idempotent با کلید `corr|proposal|event_type`) |
| `delivered_to_owner` → `owner_edited` | مالک متن را ویرایش و تأیید کرد | متن ویرایش‌شده = متن ارسالی؛ diff ذخیره | `proposal.owner_edited` | **جدید:** verb map فعلی فقط ok/no/later دارد (`_PROPOSAL_VERBS`) — دکمه/فلوی Edit + ثبت diff ساخته می‌شود؛ ثبت durable از همان `verdict_recorder` با `payload.edited=true` (vocabulary موجود کافی است: accepted-measurement) |
| `delivered_to_owner` → `owner_rejected` | تپ «نه»/Junk | reason اجباری | `proposal.owner_rejected` | **موجود:** همان قوس، `rejected` |
| `delivered_to_owner` → `expired` | تایمر §6 | nudge یک‌بار در T+15min قبلش | `outcome.recorded` (kind=`proposal_expired`) | sweep **جدید** (الگوی lazy-sweep موجود: `chrono.sweep_stale_effects:416` و `_epoch_fire` در `wiring.py:1824`) |

### 3.2 پل داخلی→بازار (زنجیرهٔ اثر — دست‌نخورده reuse)

| از → به | تریگر | گاردها | رویداد | ثبت‌کنندهٔ امروز |
|---|---|---|---|---|
| `owner_approved|edited` → `send_pending` | LANGAR append → release | **G-SYN:** `source.channel==synthetic_test` → این گذار ساختاراً ممنوع (§9)؛ STOP/FREEZE/halted → refuse (`chrono.force_closed:358`)؛ `outreach_allowed==true` الزامی (سند 05)؛ suppression آخرین‌بار چک | `effect.released` | **موجود ولی DISCONNECTED از لید:** `EffectorGate.request:369` (pending) + `release_gated_effects:380` (پس از human-append). سیم‌کشی مسیر لید به آن = کار Phase C؛ خود gate تغییر نمی‌کند |
| `send_pending` → `sent` | settle + ارسال worker | `settle:397` تنها نقطهٔ عبور؛ kill مقدم؛ بدون LANGAR ref → refuse (TINV-7) | `communication.sent` | **worker = جدید** (MISSING، RUNTIME-TRUTH §1-15)؛ settle موجود. تا worker نیامده: attestation دستی مالک (§7) |
| `send_pending` → `send_failed` | provider error / refuse | alert الزامی (invariant #11)؛ retry-safe | `communication.failed` | **جدید** (ingestion نتیجهٔ provider صفر است — RUNTIME-TRUTH §1-16)؛ شاخهٔ refuse موجود: `chrono.py:401-410` |
| `send_pending` → `expired`(effect) | release-age > O-1 window | **تصحیح — گاردِ نو لازم است** | `communication.failed` (kind=`stale_refused`) | **NEW (Phase C):** `sweep_stale_effects:424` فقط `status='pending'` را می‌گیرد؛ `send_pending`=`releasable` را نمی‌گیرد. گارد در worker: پیش از `settle`، اگر now−release_ts > پنجره → settle نکن، `communication.failed(stale_refused)` + alert. chrono دست‌نخورده |

### 3.3 نیمهٔ بازار

| از → به | تریگر | گاردها | رویداد | ثبت‌کنندهٔ امروز |
|---|---|---|---|---|
| `sent` → `replied` | پاسخ مشتری (دستور `/replied <lead>` در P0؛ webhook در P1) | تکرارپذیر با discriminator (§7) | `customer.replied` | **جدید** (سطح دستور)؛ sink سنجش موجود: `live_loop.record_proposal_outcome:411` |
| `sent|replied` → `inspection_booked` | `/meeting <lead>` | — | `inspection.booked` | **جدید** (دستور)؛ blueprint §10 این دستورها را جزو محصول اعلام کرده |
| `replied|inspection_booked|sent` → `quote_sent` | کوت رفت (settle کوت یا گزارش مالک) | مبلغ+ref اجباری | `quote.sent` | **موجود:** `lead_leg.claim:115` → `attribution.claim` (`_ops/budget/attribution.py:97`) → state پولی CLAIMED؛ فقط emit رویداد funnel افزوده می‌شود |
| `quote_sent` → `won` | `/won <qt|lead> [amount]` | claim بازاری، نه پول | `quote.won` | sink موجود (`record_proposal_outcome` با verdict∈{won,paid} — `live_loop.py:477` positive set)؛ **سطح دستور جدید** |
| `quote_sent|won-path` → `lost` | `/lost <qt|lead> <reason>` | reason اجباری (enum §2-19) | `quote.lost` | همان — سطح دستور جدید |
| `won` → `paid` | reconcile-job تطبیق داد | **فقط** `actor=reconcile-job`؛ ایجنت/مالک نمی‌توانند مستقیم بنویسند؛ پنجرهٔ انتساب ۷ روز (`ATTR_WINDOW_DAYS`، `attribution.py:22`) | `invoice.paid` | **موجود:** `attribution.confirm:105` (CONFIRMED+ATTRIBUTED) → `confirmed_revenue:157` تنها سطحی که fitness می‌خواند |
| `paid` → `gross_profit_recorded` | مالک هزینه ثبت کرد | paid قبلاً CONFIRMED | `outcome.recorded` (kind=`gross_profit`) | **جدید، P0-اختیاری** (O-3) |
| `paid|won` → `repeat_or_referral` | لید جدید با همان contact-hash یا `src:referral` | تشخیص در inbox؛ `parent_lead_id` روی لید جدید | `outcome.recorded` (kind=`repeat|referral`) | **جدید** (تشخیص)؛ الگوی content_hash موجود: `lead_sense.content_hash:48` |
| هر state≥`sent` → `dead` | `/dead <lead>` | — | `outcome.recorded` (kind=`lead_dead`) | سطح دستور جدید |

---

## 4. دیاگرام ASCII

```
                          [quarantined]* <── invalid/unsigned
                               ▲
  POST /api/v1/lead-candidates │            (replay: Idempotency-Key)
  یا /lead مالک ──────────► [received] ──► [duplicate]* ──merge──► lead اصلی
                               │ lead.normalized
                               ▼
                          [normalized] ──firewall/suppression──► [compliance_blocked]*†
                               │ lead.qualified  (lead_scorer — موجود)
                               ▼
                          [qualified] ─── response.draft.prepared / quote.draft.prepared
                               │ proposal.routed  (route_leg_proposals — موجود)
                               ▼
                      [delivered_to_owner] ──T+15m nudge──► [expired]*‡
                        │         │        │
              owner_approved  owner_edited  owner_rejected*
                        │         │              (reason)
                        ▼         ▼
              ┌──────── [owner_approved / owner_edited] ────────┐   ← مرز دو سیگنال
   synthetic_test │  G-SYN: ممنوع                                │  LANGAR append +
        ▼         │                                              ▼  effect.released
  [synthetic_done]*                                       [send_pending] ──72h──► refuse
  (outcome.recorded،                                        │         │
   kind=synthetic_complete)                     communication.sent  communication.failed
                                                            │         │ (alert، retry-safe)
                                                            ▼         ▼
                                                         [sent] ◄─[send_failed]
                                                            │
                                              customer.replied (0..n)
                                                            ▼
                                                        [replied] ──► [inspection_booked]
                                                            │               │
                                                            └──────┬────────┘
                                                                   ▼ quote.sent (= attribution.claim)
                                                             [quote_sent]
                                                              │        │
                                                        quote.won   quote.lost* (reason)
                                                              ▼
                                                           [won] ──reconcile-job فقط──► [paid]
                                                                                          │
                                                                       outcome.recorded  ▼
                                                                    [gross_profit_recorded]
                                                                                          │
                                                                                          ▼
                                                             [repeat_or_referral] ──► lead.candidate.received جدید
                                                                                       (parent_lead_id)
   * = dead state (هرگز outbound)   † = خروج فقط با شواهد رضایت جدید (سند 05)   ‡ = proposal می‌میرد نه lead
   هر state≥sent می‌تواند با /dead به [dead]* برود.
```

---

## 5. نگاشت کامل رویداد ↔ ثبت‌کنندهٔ موجود (هستهٔ این سند)

واژگان = دقیقاً SPEC §3. ستون آخر صادقانه می‌گوید چه چیزی واقعاً ساخته می‌شود.

| رویداد SPEC §3 | تابع موجودی که همین امروز نزدیک‌ترین حقیقت را ثبت می‌کند | وضعیت | چه چیزی genuinely جدید است |
|---|---|---|---|
| `lead.candidate.received` | `lead_leg_inbox.register_lead` (`legs/lead_leg_inbox.py:86` — dead-code، صفر caller) | DEAD_CODE → احیا | مرز HTTP امضاشده + emit رویداد؛ persist اتمیک reuse |
| `lead.candidate.rejected` | `lead_sense._move_with_sidecar → rejected/` (`legs/lead_sense.py:104`) | موجود (الگو) | فقط اتصال به مرز + کارت هشدار |
| `lead.normalized` | `_normalize` (`lead_leg_inbox.py:42`) — کمینه | SHADOW | normalizer به قرارداد canonical v1.1 |
| `lead.duplicate.detected` | `register_lead` شاخهٔ dup (`lead_leg_inbox.py:110`)؛ `lead_sense.seen_before:72` | موجود (کلید غلط) | re-key به `Idempotency-Key: source:external_id` |
| `lead.qualified` | `lead_scorer.score_lead` (`legs/lead_scorer.py:280`) via `wiring.py:1826` | BLOCKED_BY_FLAG | هیچ — فقط emit + الحاق intent/urgency/missing-questions به schema (سند 02) |
| `lead.compliance_blocked` | — (صفر occurrence) | MISSING | کل firewall (سند 05) — بالاترین ریسک |
| `response.draft.prepared` | — | MISSING | نیمهٔ first-response لِگ P0-3 (تنها نیمهٔ غایب قوس داخلی) |
| `quote.draft.prepared` | `lead_quote.create_quote` + `lead_to_intake:77` via `wiring.py:1873`؛ `lead_leg.draft_quote:89` | BLOCKED_BY_FLAG | هیچ — فقط emit |
| `proposal.routed` | `live_loop.route_leg_proposals:327` (advisory `delivered` در `:396`) + رسید durable `lead_outcome_recorder.record_lead_decision:38` | SHADOW + فلگ | هیچ — فقط emit funnel؛ **هشدار نام:** `delivered` این‌جا = رسید کارت به مالک، نه تحویل پیام |
| `proposal.owner_approved` | `record_proposal_outcome_by_token:429` → `verdict_recorder.record_owner_verdict:44` (`accepted-measurement`) | موجود (پشت `OCTOPUS_WIRE_PROPOSAL_BUTTONS` + `OCTOPUS_WIRE_VERDICT_OUTCOME`) | هیچ |
| `proposal.owner_edited` | — (verbs فقط ok/no/later) | MISSING | دکمه/فلوی Edit + ذخیرهٔ diff؛ ثبت durable از همان verdict_recorder با `payload.edited=true` |
| `proposal.owner_rejected` | همان قوس، `rejected` | موجود | هیچ (فقط reason اجباری) |
| `effect.released` | `EffectorGate.release_gated_effects` (`chrono.py:380`) پس از LANGAR append | موجود، DISCONNECTED از لید | سیم‌کشی مسیر لید به gate (Phase C)؛ خود gate صفر تغییر |
| `communication.sent` | `EffectorGate.settle:397` (تنها نقطهٔ عبور) | settle موجود؛ worker MISSING | outbound worker متعلق به Octopus + emit؛ تا آن روز: attestation مالک (§7) |
| `communication.failed` | شاخهٔ refuse (`chrono.py:401-410`) + `sweep_stale_effects:416` | جزئی | ingestion نتیجهٔ provider + alert |
| `customer.replied` | — | MISSING | دستور `/replied` (P0) + webhook (P1) |
| `inspection.booked` | — | MISSING | دستور `/meeting` |
| `quote.sent` | `lead_leg.claim:115` → `attribution.claim` (`budget/attribution.py:97` → CLAIMED) | **موجود** | فقط emit funnel هم‌زمان با claim |
| `quote.won` / `quote.lost` | sink سنجش: `live_loop.record_proposal_outcome:411` (positive set `:477` شامل won/paid) | sink موجود | دستورهای `/won` `/lost` + emit |
| `invoice.paid` | `attribution.confirm:105` — فقط `actor=reconcile-job`؛ `confirmed_revenue:157` → fitness | **موجود** | فقط emit funnel از خود reconcile-job (هرگز از دستور مالک) |
| `outcome.recorded` | `outcome_store.record` (`outcomes/outcome_store.py:87`، idempotent UNIQUE) + قوس بسته به `goal_directed._baseline_metrics:196` / `measure:229` | **موجود — قوس واقعاً بسته** | هیچ در قوس؛ کینِ‌های payload جدید (§2) |

**رویدادهای الحاقی پیشنهادی (EXT — نیازمند تأیید مالک، v1.2 additive به SPEC §3):** `communication.delivered` (رسید provider)، `proposal.expired`. تا تأیید، هر دو با `outcome.recorded` + `payload.kind` پوشش داده می‌شوند تا قرارداد v1.1 دست نخورد.

### قاعدهٔ دوگانه‌نویسی (dual-write) و مرجعیت
ژورنال funnel جدید **جایگزین هیچ store موجودی نیست** — کنارشان می‌نشیند (append-only, fail-soft):
- مرجع رأی مالک: `outcomes.db` (verdict_recorder) — funnel فقط آینه.
- مرجع پول: ledger ژنوم (`MONEY_ATTRIBUTION`, `attribution.fold:133`) — funnel فقط آینه.
- مرجع پیشروی بازاری (sent/replied/inspection/…): ژورنال funnel (این‌ها امروز هیچ خانه‌ای ندارند — شکاف #3/#4 در RUNTIME-TRUTH §2).
واگرایی بین آینه‌ها → کارت هشدار، هرگز اصلاح بی‌صدا (invariant #11).

---

## 6. تایمرها و SLAها

همهٔ تایمرها lazy-sweep روی beat موجودند (الگوی `_epoch_fire` در `wiring.py:1824` و `sweep_stale_effects` — scheduler جدیدی ساخته نمی‌شود).

| نام | تعریف اندازه‌گیری | هدف | نوع سیگنال | اقدام در تخطی |
|---|---|---|---|---|
| `t_receive_to_card` | `proposal.routed` − `lead.candidate.received` | p50 ≤ 10s (کارت stage-1)، draft append ≤ 30s | سیستم | alert card |
| `t_card_nudge` | کارت بی‌اقدام | T+15min یک‌بار re-ping، سپس `proposal_expired` (زمان expiry: تصمیم O-1) | انسانی | nudge → expire |
| **`time_to_first_response`** | اولین `communication.sent` (kind=first_touch) − `received`؛ **ساعت‌کاری-آگاه:** ساعت بیرون 07:30–20:30 AEST شمرده نمی‌شود (گارد quiet-hours لِگ P0-1: draft الان، ارسال scheduled در بازشدن پنجره) | **p50 ≤ 5min · p95 ≤ 30min** (MASTER §10) | ترکیبی — ولی گزارش همیشه دو-تکه: `t_system` (received→routed) و `t_human` (routed→sent) جدا؛ هرگز conflate (KPI split لِگ P0-1) | کارت هفتگی Governor |
| `t_effect_stale` (pending) | effect در `pending` (=قبل از release) | > 72h → auto-refuse | سیستم | **موجود:** `sweep_stale_effects:424` (فقط `status='pending'`) — دست نمی‌زنیم |
| `t_effect_stale` (releasable) | effect در `releasable` (=`send_pending`) | > O-1 window → stale_refused | worker (Phase C) | **تصحیح — NEW:** کدِ فعلی این حالت را جارو نمی‌کند؛ گارد در worker پیش از settle (بالا) |
| `t_quote_validity` | از `quote.sent` | 14 روز (`validity_days`) | بازار | کارت follow-up (P1) یا `/lost reason=expired` |
| `t_reply_wait` | از `sent` بدون `customer.replied` | 48h ساعت‌کاری | بازار | کارت پیشنهاد follow-up (P1)؛ state عوض نمی‌شود |
| `t_attr_window` | `quote.won` → `invoice.paid` | 7 روز (`ATTR_WINDOW_DAYS`, `attribution.py:22`) | پولی | **موجود** — اعتبار به cell تاریخ تصمیم |
| `t_signal_retention` | لیدهای `market_signal` | 30 روز → purge (aggregate می‌ماند) | حاکمیتی | سند 05 |

مقصد متریک‌ها: producer صادقانه به `ORGANISM-STATE.json` می‌نویسد (کلید جدید `funnel_metrics` کنار `proposal_metrics` که `goal_directed._baseline_metrics:196` می‌خواند). قاعدهٔ صداقت موجود حفظ می‌شود: کلید نبوده هرگز جعل نمی‌شود (`goal_directed.py:207-210` و `_movement_keys:214`) — Governor فقط وقتی funnel واقعاً دیتا داد، آن را می‌سنجد.

---

## 7. قواعد عملیاتی نیمهٔ بازار در دورهٔ گذار (تا ساخت outbound worker)

RUNTIME-TRUTH §1-15: worker وجود ندارد؛ امروز ارسال دستی است. Funnel از روز اول باید حقیقت را ثبت کند:
- هر رویداد بازاری فیلد `payload.channel_mode ∈ {gated_worker, owner_manual}` دارد.
- `owner_manual`: مالک از تلفن خودش فرستاد و با دستور (`/sent`, `/replied`, `/meeting`, `/won`, `/lost`) attest کرد — فعل انسانی بیرون سیستم است (مثل الگوی Path C «owner posts himself»)، پس ناوردی «اثر بیرونی فقط با gate» نقض نمی‌شود؛ سیستم فقط صادقانه ثبت می‌کند.
- `gated_worker`: مسیر کامل verdict → LANGAR → EffectorGate.settle → worker. **تنها مسیر ارسالِ سیستمی.**
- گزارش Governor دو mode را جدا برچسب می‌زند؛ گیت «۲۰ نتیجهٔ واقعی» با هر دو mode قابل‌عبور است (MASTER §5 milestone 3).
- رویدادهای تکرارپذیر (`customer.replied`, `communication.failed`): discriminator در کلید idempotency (§8).

---

## 8. ذخیره‌سازی و replay-safety

### 8.1 ژورنال funnel (جزء جدید — دنبال‌روی مو-به-موی الگوی موجود)
`_ops/outcomes/funnel_store.py` — قرینهٔ `outcome_store.py`: stdlib-only، SQLite WAL، `INSERT OR IGNORE` روی `idempotency_key UNIQUE`، قفل single-writer، schema-versioned، UTC-aware، `metrics()` همیشه از rows بازساخته (replay). مسیر: `STATE_DIR/outcomes/funnel.db` (همان دایرکتوری `outcomes.db`).

```sql
CREATE TABLE IF NOT EXISTS funnel_events(
  event_id        TEXT PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,
  lead_id         TEXT NOT NULL,
  proposal_id     TEXT, effect_id TEXT, attribution_id TEXT,
  event_type      TEXT NOT NULL,   -- فقط واژگان SPEC §3 (+kind در payload)؛ ناشناخته → ValueError (الگوی outcome_store.record:92)
  correlation_id  TEXT NOT NULL,   -- = lead_id (envelope SPEC §3)
  causation_id    TEXT,            -- event_id قبلی
  source_component TEXT NOT NULL,  -- LeadInboxLeg | LeadQualificationLeg | ResponseQuoteLeg | ProposalRouter | EffectorGateBridge | OutboundWorker | OwnerCommand | ReconcileJob
  channel_mode    TEXT,            -- gated_worker | owner_manual | NULL(داخلی)
  occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,
  schema_version INTEGER NOT NULL, payload_json TEXT);
```

### 8.2 دستور پخت کلیدهای idempotency
| دسته | رویدادها | کلید |
|---|---|---|
| تک‌وقوعی per lead | received, normalized, qualified, compliance_blocked | `lead_id|event_type` |
| تک‌وقوعی per proposal | routed, owner_*, draft.prepared, effect.released | `lead_id|proposal_id|event_type` (قرینهٔ `verdict_recorder`: `corr|proposal|event_type`) |
| تک‌وقوعی per effect | communication.sent | `lead_id|effect_id|communication.sent` |
| تکرارپذیر | customer.replied, communication.failed | `lead_id|event_type|<discriminator>` — discriminator = provider message-id یا `ts` دستور مالک (دقت دقیقه) |
| پولی | quote.sent, quote.won, quote.lost, invoice.paid | `lead_id|attribution_id|event_type` |

### 8.3 اشتقاق state — fold خالص
state هرگز ذخیرهٔ mutable نمی‌شود؛ همیشه `fold(lead_id)` روی رویدادها با ترتیب قطعی `ORDER BY occurred_at, event_id` (قرینهٔ `outcome_store.events:121` و `attribution.fold:133`):
- رتبهٔ monotonic: received=0 … repeat_or_referral=13؛ رویداد با رتبهٔ پایین‌تر از state فعلی **regress نمی‌دهد** (ثبت می‌شود، state ثابت می‌ماند) — بی‌نظمیِ رسیدنِ رویدادها بی‌خطر است.
- گذار غیرمجاز (مثلاً `quote.won` بدون هیچ `quote.sent`): رویداد append می‌شود (هرگز drop)، state تغییر نمی‌کند، کارت هشدار `funnel_anomaly` صادر می‌شود — no-silent-failure.
- stateهای DEAD چسبنده‌اند (قرینهٔ CONFLICT چسبنده در `attribution.fold:145-146`)؛ خروج فقط از مسیرهای صریح † و ‡ در §2.
- replay کامل دیتابیس = همان stateها، بایت‌به‌بایت (تست الزامی).

### 8.4 پاسخ به تست‌های الزامی OPUS_MISSION_PROMPT
| تست | مکانیزم این طراحی |
|---|---|
| #5 duplicate idempotency-key → لید دوم نه | UNIQUE در inbox + `lead.duplicate.detected` merge |
| #11 approval idempotent | single-use `meta["decided"]` (`live_loop.py:437`) + کلید idempotent verdict (`verdict_recorder.py:14`) — موجود |
| #12 callback تکراری → double-send نه | effect یکتا per proposal + `settle` فقط از releasable می‌گذرد (`chrono.py:397-414`)؛ settle دوم → False |
| #13 خطای provider → alert + retry-safe | `communication.failed` + state re-entrant `send_failed` |
| #14 همبستگی Proposal↔Lead↔Effect | ستون‌های lead_id/proposal_id/effect_id/attribution_id روی هر ردیف |
| #15 رویدادها به لایهٔ سنجش می‌رسند | `funnel_metrics` در ORGANISM-STATE.json → `goal_directed._baseline_metrics:196` (قوس موجود) |

---

## 9. لاین synthetic (milestone 1 — بدون هیچ ارسال)

- `source.channel=synthetic_test` کل نیمهٔ داخلی را کامل طی می‌کند: received → … → verdict → `outcome.recorded(kind=synthetic_complete)` → state پایانهٔ `synthetic_done`.
- **بلوک ساختاری، نه قراردادی:** گذار `owner_approved → send_pending` برای این channel در کد گذار ممنوع است (G-SYN) **و** لایهٔ دفاع دوم در پل EffectorGate: درخواست effect برای لید synthetic اصلاً `request` نمی‌شود؛ اگر به هر مسیری رسید، `settle` با `payload_ref` نشان‌دار synthetic → refuse + alert. دو لایه، هر دو fail-closed.
- خروجی milestone: «owner verdict recorded + outcome event observed» (SPEC §7 گام 1) — دقیقاً همین زنجیره.

---

## 10. فلگ‌ها (همه default-off؛ روشن‌کردن = فقط مالک)

| فلگ | پوشش | وضعیت |
|---|---|---|
| `OCTOPUS_WIRE_LEAD_FUNNEL` | ژورنال funnel + emit رویدادها (measurement-only) | **جدید** |
| `OCTOPUS_WIRE_LEAD_FUNNEL_CMDS` | دستورهای مالک `/sent /replied /meeting /won /lost /dead` | **جدید** |
| `OCTOPUS_WIRE_LEAD_INBOX` · `OCTOPUS_WIRE_LEAD_DISCOVERY` · `OCTOPUS_WIRE_LEAD_DRAFT` · `OCTOPUS_WIRE_PROPOSAL_BUTTONS` · `OCTOPUS_WIRE_VERDICT_OUTCOME` · `OCTOPUS_WIRE_LEAD_OUTCOME` | قوس داخلی موجود | موجود — reuse، تغییر معنا ممنوع |

`invoice.paid` فلگ ندارد — چون فقط reconcile-job (مسیر موجود) می‌نویسد؛ funnel صرفاً آینه است.

---

## 11. خلاصهٔ ساخت: reuse در برابر جدید

**Reuse بدون تغییر (دست نزن):** `outcome_store.py` (واژگان ۵تایی پین‌شده)، `verdict_recorder.py`، `attribution.py` + reconcile، `EffectorGate` کامل (`chrono.py:344-434`)، `route_leg_proposals` + دکمه‌ها، `lead_scorer.py`، `lead_quote.py`، `goal_directed.measure`.

**Reuse با تغییر کوچک:** dedup re-key به Idempotency-Key (`lead_leg_inbox.py`)، انتخاب/همگرایی دو inbox متناقض (RUNTIME-TRUTH §4-3 — پیشنهاد: schema `lead_sense` مبنا، `lead_leg_inbox` منجمد شود؛ ارجاع سند 11).

**Genuinely جدید (به‌ترتیب وابستگی):** ① firewall رضایت + emit `lead.compliance_blocked` (سند 05)؛ ② مرز امضاشده + normalizer + quarantine wiring (سند 07)؛ ③ `funnel_store.py` + fold + متریک‌ها؛ ④ فلوی Edit + diff؛ ⑤ دستورهای مالک؛ ⑥ سیم لید→LANGAR→EffectorGate؛ ⑦ outbound worker + ingestion نتیجهٔ provider؛ ⑧ تشخیص repeat/referral؛ ⑨ nudge/expiry sweep.

---

## 12. تصمیم‌های باز مالک (به 10_OWNER_DECISIONS_REQUIRED.md منتقل می‌شود)

- **O-1:** زمان expiry کارت بی‌اقدام پس از nudge پانزده‌دقیقه‌ای (پیشنهاد: پایان همان روز کاری). **تصحیح:** «backstop سیستمی 72h» فقط برای effectهای `pending` است؛ برای `releasable`/`send_pending` گاردِ stale نو در worker لازم است (بالا) — O-1 window همان پنجرهٔ این گارد را هم تعیین می‌کند.
- **O-2:** تأیید دو رویداد الحاقی EXT (`communication.delivered`، `proposal.expired`) به‌عنوان v1.2 قرارداد رویداد، یا ماندن روی `outcome.recorded+kind`.
- **O-3:** فعال‌سازی `gross_profit` در P0 (نیازمند ورود هزینه توسط مالک per job) یا موکول به P1.
- **O-4:** در دورهٔ گذار owner_manual، آیا `/sent` بدون کارت approved قبلی مجاز باشد (لید تلفنی که مالک فی‌البداهه جواب داد)؟ پیشنهاد: مجاز با برچسب `unproposed_manual` — حقیقت را ثبت کن، قضاوت را به Governor بده.
