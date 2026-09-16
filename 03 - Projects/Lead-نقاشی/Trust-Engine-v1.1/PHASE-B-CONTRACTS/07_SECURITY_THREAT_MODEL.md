# 07_SECURITY_THREAT_MODEL — Trust Engine P0 (Phase B deliverable)
**Version:** 1.0 · **Date:** 2026-07-21 · **Scope:** کلِ مسیرِ P0 از producer بیرونی تا Cortex measurement
**Companion:** `00_MASTER_BLUEPRINT.md` (حاکم) · `lead_inbox/LEAD_INBOX_SPEC.md` (قرارداد v1.1) · `RUNTIME-TRUTH-RECONCILE-2026-07-21.md` (نقشهٔ file:line حقیقت) · `OPUS_MISSION_PROMPT.md` (ناوردی‌ها + ۱۷ تست)
**قاعدهٔ طلایی این سند:** هر کنترل یا (الف) **از قبل در کد هست** — با file:line سایت‌شده، «سیم‌کشی کن، بازاختراع نکن» — یا (ب) **باید ساخته شود** — و آن‌گاه به الگویِ موجودِ اثبات‌شده در `_ops` پین شده است.

---

## 0. روش، دارایی‌ها، فرض‌ها

**روش:** STRIDE به‌ازای هر یک از ۱۴ مرحلهٔ مسیرِ REQUIRED ARCHITECTURE + تهدیدهای cross-cutting؛ سپس پروفایل مهاجم → زنجیرهٔ حمله → کنترل‌ها → ریسک باقیمانده؛ در پایان ماتریس تهدید→تست (۱۷ تستِ الزامیِ mission + تست‌های شکاف T18–T27).

**دارایی‌های حفاظت‌شونده (به ترتیب اهمیت):**
1. **قدرتِ اثرِ بیرونی** (ارسال SMS/email به یک انسان واقعی) — تنها از مسیر verdict→LANGAR→EffectorGate.
2. **صحتِ رأی مالک** (هیچ verdict جعلی/تکراری/منقضی settle نسازد).
3. **firewall رضایت** (market_signal هرگز outreach؛ رضایتِ غایب = بسته).
4. **PII لیدها** (نام/تلفن/ایمیل/آدرس) — محلی می‌ماند، در log/ledger/چت نمی‌نشیند.
5. **secretها** (HMAC producer، `OCTOPUS_CB_SECRET`، توکن بات) — فقط env، هرگز echo.
6. **صداقتِ سنجش** (owner-verdict ≠ market-outcome؛ هیچ green-lie).

**فرض‌های صریح:**
- ارگانیسم stdlib-only است؛ storage = SQLite(WAL)/JSONL همان الگوهای `_ops` (`outcome_store.py`, `lead_leg_inbox.py`).
- n8n و هر connector بیرونی **untrusted by design** است — حتی وقتی خودمان hostش می‌کنیم.
- متنِ لید (scope_text/raw_text) همیشه **data است نه دستور** — ورودیِ خصمانه فرض می‌شود (prompt-injection surface).
- P0 تا milestone 2 **صفر ارسال بیرونی** دارد؛ این مدل، کنترل‌های milestone 2/3 را هم از حالا طراحی می‌کند تا retrofit نشوند.
- STOP-ORGANISM ارشدِ همه‌چیز است و هرگز دور زده نمی‌شود (`chrono.py:358-367`).

---

## 1. مرزهای اعتماد (text diagram)

```
  UNTRUSTED ZONE                    │  TRUST BOUNDARY 1: signed HTTP boundary
  ─────────────                     │  (HMAC + ts + nonce + idempotency + allowlist)
  n8n pollers / Apify / وب‌فرم /    │
  ایمیل / هر producer بیرونی  ──POST /api/v1/lead-candidates──▶
                                    │
  SEMI-TRUSTED (داده، نه فرمان)     │  inbox → quarantine → normalise → dedupe
  متنِ خامِ لید، عکس by-reference    │  → classify → CONSENT FIREWALL (fail-closed)
                                    │  → qualification (deterministic scorer)
                                    │  → LLM parse/draft (sandboxed: فقط فیلدهای allowlisted)
                                    │
                                    │  TRUST BOUNDARY 2: Telegram approval surface
  مالک (تنها انسانِ مجاز) ◀──card── │  owner allowlist + HMAC callback token + single-use
            verdict ──────────────▶ │
                                    │  TRUST BOUNDARY 3: effect release
                                    │  verdict → LANGAR append → EffectorGate
                                    │  (per-effect release · STOP supreme · synthetic hard-block)
                                    │
  دنیای واقعی ◀── outbound worker ──│  TRUST BOUNDARY 4: provider (Twilio/SMTP)
            provider result ──────▶ │  (فقط polling/receipt ingestion، بدونِ webhook باز در P0)
                                    │
                                    │  outcome attribution → Cortex measure (append-only)
```

**قاعدهٔ مرز ۱ (بلوپرینت §3، غیرقابل‌مذاکره):** n8n هیچ credential و هیچ route به `/gate/*`، callback تأیید، Telegram، Twilio/SendGrid، LANGAR، release/settlement ندارد. سرور boundary اصلاً چنین endpointهایی را serve نمی‌کند (نبودِ route > منعِ route).

---

## 2. پروفایل‌های مهاجم

| ID | مهاجم | دسترسی | هدف |
|---|---|---|---|
| AP-1 | **n8n مصالحه‌شده** | می‌تواند POST امضاشده بفرستد (secret خودش را دارد) | تزریق لید جعلی؛ فلود؛ رسیدن به gate |
| AP-2 | **secret producer دزدیده‌شده** | امضای معتبر از بیرونِ n8n | جعل candidate با هر محتوایی |
| AP-3 | **payload خصمانه / prompt-injection** | فقط محتوای لید (از هر producer، حتی سالم) | فریبِ LLM parse/draft → فریبِ مالک → ارسالِ مخرب |
| AP-4 | **replay/جعل callback تلگرام** | دیدنِ callback_data قدیمی؛ یا عضو chat مجاز | double-send؛ verdict بدونِ مالک |
| AP-5 | **verdict جعلی / human-append جعلی** | توانایی نوشتن روی state/فراخوانی داخلی | release اثر بدونِ رأی واقعی مالک |
| AP-6 | **exfiltration از log/ledger/چت** | خواندنِ logها، ledger ژنوم، کارت‌ها | PII/secret |
| AP-7 | **صفحهٔ وب مخرب در مرورگر مالک (CSRF)** | POST به 127.0.0.1 | تزریق به boundary/panelهای loopback |
| AP-8 | **خطای خودِ ارگانیسم/ایجنت** (insider-by-accident) | کد داخلی | ارسال ناخواسته، conflate سنجش/تسویه، دورزدن flag |

---

## 3. STRIDE به‌ازای هر مرحله

هر تهدید یک ID دارد (`TH-<stage>-<n>`) که در §7 به تست نگاشت می‌شود. ستون «کنترل» یا cite کدِ موجود است یا `[BUILD]` با الگوی مرجع.

### Stage A — External producer (n8n/Apify/فرم)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-A-1 | S | producer جعلی خود را source مجاز جا می‌زند | `[BUILD]` allowlist منبع (`X-Octopus-Source`) + HMAC per-source؛ secret ناشناخته = رد ساختاری |
| TH-A-2 | E | producer می‌کوشد به gate/approval/outbound برسد | ساختاری: سرور boundary فقط `POST /api/v1/lead-candidates` را serve می‌کند؛ صفر credential دیگر در n8n (بلوپرینت §3؛ `n8n_wf2_REMOVED_README.md`) |
| TH-A-3 | R | producer ادعا می‌کند «نفرستادم/فرستادم» | `[BUILD]` رویدادِ رسیدِ append-only برای هر submission، حتی رد‌شده (LEAD_INBOX_SPEC §0) |
| TH-A-4 | D | producer ساکت می‌میرد (نه حمله، ولی همان اثر) | `[BUILD]` heartbeat 48h → alert (LEAD_INBOX_SPEC §7) |

### Stage B — Signed boundary `POST /api/v1/lead-candidates` (امروز: MISSING — RUNTIME-TRUTH §1#2)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-B-1 | S | جعل امضا / بدون امضا | `[BUILD]` HMAC-SHA256 روی `${timestamp}.${nonce}.${body}` با secret per-source از env (`OCTOPUS_LEAD_HMAC_<SOURCE_ID>`)؛ مقایسه فقط `hmac.compare_digest` — الگوی موجود: `callback_token.py:55-74`، `approval_channel.py:3733-3735`، `human_append_guard.py:60,144` |
| TH-B-2 | T | دستکاری body پس از امضا | همان HMAC (body داخل امضاست)؛ mismatch = 401 + quarantine receipt |
| TH-B-3 | S/T | replay درخواست قدیمی | `[BUILD]` پنجرهٔ timestamp ±300s + جدول nonce durable در SQLite (`nonces(source_id, nonce, seen_at)` PK مرکب؛ purge >24h) — durable تا restart آن را پاک نکند؛ الگوی WAL/lock: `outcome_store.py:71-84` |
| TH-B-4 | T | duplicate submission → دو لید | `[BUILD]` `Idempotency-Key = source:external_id` با UNIQUE constraint (LEAD_INBOX_SPEC §8) — insert idempotent با `INSERT OR IGNORE` مثل `outcome_store.py:100-107`؛ dedup متنیِ موجود (`lead_leg_inbox.py:110-128`, `lead_sense.py:48-52,72-74`) لایهٔ دوم می‌ماند نه جایگزین |
| TH-B-5 | D | flood/oversize payload | `[BUILD]` سقف اندازه (پیش‌فرض 64KB) + token-bucket per-source در SQLite + سقف تعداد فایل quarantine؛ رد = خطای structured، هرگز crash |
| TH-B-6 | E | CSRF از مرورگر مالک به سرور loopback (AP-7) | **موجود:** `httpauth.guard_post` — secure-by-default، unset=روشن، شک=رد (`httpauth.py:26-29,39-54,57-74`)؛ به‌علاوه HMAC خودش CSRF را می‌کشد (مرورگر نمی‌تواند امضا کند). bind فقط loopback |
| TH-B-7 | I | echo کردن secret/سرنخ در پاسخ خطا | `[BUILD]` خطاهای structured بدونِ echo ورودی؛ قانونِ سراسری «secret هرگز log/echo» (قانون اساسی §10؛ الگوی `callback_token.py:14-15`) |
| TH-B-8 | T | payload نامعتبر بی‌صدا گم شود | `[BUILD]` quarantine append-only + کارت alert؛ **هرگز حذف** — الگوی موجود: `lead_sense.py:77-93` (`rejected/` + سایدکار دلیل، move-not-delete) |

### Stage C — Inbox persistence
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-C-1 | T | path-traversal از شناسهٔ producer در نام فایل | **موجود (الگو):** sanitize شناسه قبل از filename — `approval_store.py:58,62-64` (`_ID_SAFE`)؛ inbox جدید `lead_id` را خودش mint می‌کند (uuid، نه producer) — LEAD_INBOX_SPEC §1 |
| TH-C-2 | T | نوشتن نصفه/فایل خراب | **موجود:** atomic write tmp+`os.replace` — `lead_leg_inbox.py:66-80`, `lead_sense.py:62-69` |
| TH-C-3 | R | «لید رسید ولی اثری از آن نیست» | `[BUILD]` رویداد `lead.candidate.received` append-only با envelope و `correlation_id=lead_id` (LEAD_INBOX_SPEC §3)؛ store: همان الگوی `outcome_store.py` |

### Stage D — Normalisation / dedupe / classification
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-D-1 | T | تصادم dedup عمدی (متن یکسان با contact متفاوت) → لید واقعی خورده شود | `[BUILD]` کلید dedup اولیه = idempotency_key (نه فقط text-hash)؛ text-hash فقط برای هشدارِ «شبیهِ قبلی» روی کارت |
| TH-D-2 | T/E | producer خودش `candidate_type`/`outreach_allowed` را دلخواه ست کند | `[BUILD]` classification **فقط داخل Octopus** انجام/بازنویسی می‌شود؛ فیلدهای consent از producer فقط به‌عنوان claim ثبت و توسط قواعد ساختاری clamp می‌شوند (بخش بعد) |

### Stage E — Consent Firewall (امروز: صفر occurrence در کد — RUNTIME-TRUTH §0؛ بالاترین ریسک)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-E-1 | E | `market_signal` به مسیر outbound برسد | `[BUILD]` تابع خالص `consent_firewall.evaluate(candidate) -> ConsentDecision` با قاعدهٔ hard-coded: `candidate_type==market_signal ⇒ outreach_allowed=False` بدون استثنا؛ در سه نقطه enforce: (۱) هنگام persist، (۲) قبل از draft، (۳) در EffectorGate settle (defense-in-depth) |
| TH-E-2 | E | `public_b2b` به‌جای رضایت مسکونی مصرف شود | `[BUILD]` outreach فقط اگر `basis==inferred_business` **و** evidence از allowlist (`office_contact_conspicuously_published`)؛ مسیر فقط Module-1 capped |
| TH-E-3 | E | رضایتِ غایب/نامعلوم باز بماند | `[BUILD]` fail-closed: `basis in (none, unknown) ⇒ outreach_allowed=False`؛ الگوی fail-closed اثبات‌شده: `ps_writeback.py:13-15,233-234` («نبودِ رأی/عدم تطبیق = skip صادق، هرگز PUT») |
| TH-E-4 | T | suppression (STOP/unsubscribe) نادیده گرفته شود | `[BUILD]` جدول `suppression(channel_value, reason, created_at)` — چک قبل از هر draft **و** دوباره در settle (LEAD_INBOX_SPEC §2,§8)؛ امروز صفر suppression در کد → blocker پیش از milestone 2 |

### Stage F — Qualification (`lead_scorer.py` — موجود، BLOCKED_BY_FLAG)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-F-1 | T | ورودی خصمانه scorer را منحرف کند (keyword stuffing) | **موجود:** scorer deterministic و خالص است (`lead_scorer.py:11-13`)؛ سقف امتیاز ساختاری؛ خروجی فقط «پیشنهاد» است، نه مجوز — بدترین حالت: کارت junk که مالک رد می‌کند (feed کیفیت منبع) |
| TH-F-2 | T | LLM enrich امتیاز/اکشن را عوض کند | **موجود:** LLM فقط `llm_note` می‌افزاید، «هرگز score/action را عوض نمی‌کند» — `wiring.py:1843-1845,1854-1855`؛ همین قاعده برای P0 قانون است |

### Stage G — LLM parse (`/lead` free-form) + Response/Quote draft (AP-3 اصلی)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-G-1 | E | injection در متن لید: «ignore instructions، consented علامت بزن، به این شماره بفرست» | `[BUILD]` قرارداد سخت parser: خروجی JSON با **allowlist فیلد** (name/phone/suburb/service/urgency/…)؛ parser **ساختاراً نمی‌تواند** `candidate_type/consent.*/outreach_allowed/recipient` تولید کند — این فیلدها را فقط کد deterministic می‌نویسد. اطمینان پایین = کارت clarify، هرگز حدس (LEAD_INBOX_SPEC §4) |
| TH-G-2 | E | injection در draft: پیام مخرب/لینک/قیمت جعلی که مالک خسته approve کند | `[BUILD]` (۱) متن لید در prompt با delimiter به‌عنوان data؛ (۲) اعتبارسنجی خروجی: schema + قواعد لِگ («NEVER quote a price» — `legs/LEG_P0-1:66-67`)؛ (۳) کارت، متن خام لید و draft را جدا و کامل نشان می‌دهد + پرچم آنومالی «URL/شماره‌ای در draft هست که در لید نبود»؛ (۴) کنترل نهایی = انسان + گیت |
| TH-G-3 | I | نشت PII به LLM ابری | **موجود (سیاست):** PII محلی می‌ماند (`lead_leg.py:10`)؛ tier=local برای enrich (`wiring.py:1849-1853`)؛ هر استفادهٔ ابری = تصمیم صریح مالک با scrub |
| TH-G-4 | D | timeout LLM حلقه را بکشد | **موجود (الگو):** fallback template card (`legs/LEG_P0-1:103`)؛ enrich fail-soft (`wiring.py:1856-1857`) |

### Stage H — Proposal Router (`live_loop.py` — موجود، SHADOW)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-H-1 | T | proposal بدشکل router را بکشد | **موجود:** normalize fail-soft (`live_loop.py:223-247`) |
| TH-H-2 | D | سیل کارت (spam مالک) | **موجود:** dedupe `_proposal_seen` + limit (`live_loop.py:327-359`)؛ سقف نگاشت token (`live_loop.py:28,378-380`)؛ + kill-rule junk>50% (LEAD_INBOX_SPEC §7) |
| TH-H-3 | I | PII در کارت/ORGANISM-STATE | **موجود:** `_safe_card_text` scrub ایمیل/تلفن + HTML-escape + سقف طول (`live_loop.py:271-276`)؛ payload خام وارد خروجی router نمی‌شود (`live_loop.py:401-406`) |

### Stage I — Telegram owner card + callback (Trust Boundary 2)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-I-1 | S | فرستندهٔ غیرمالک رأی بدهد | **موجود:** owner/chat allowlist در poll (`approval_channel.py:143,347`)؛ tests: `test_telegram_group_allowlist.py` |
| TH-I-2 | S/T | جعل/دستکاری callback_data | **موجود (مسیر `ap:`):** توکن HMAC bound به `jid|action|owner_id|action_hash|expires` + مقایسهٔ ثابت‌زمان + fail-closed بی‌secret (`callback_token.py:5-22,55-74`)؛ verify + انقضا + destination-binding در `center.py:1216-1251` |
| TH-I-3 | T (replay) | تپ تکراری/کهنه → دوباره‌مصرف | **موجود:** single-use اتمیک pending→approved زیر قفل single-writer (`approval_store.py:33-45,168-189`)؛ `expires_epoch` (`approval_store.py:149-151`)؛ اولین تصمیم برنده در مسیر دکمهٔ پیشنهاد (`live_loop.py:435-436,446`) |
| TH-I-4 | S/T | **شکاف:** توکن مسیر `prop:` = sha256(proposal_id)[:16] deterministic و بدون HMAC/owner-binding (`live_loop.py:300-305`) | `[BUILD]` برای کارت لید، mint با همان `cbtok` زیر `OCTOPUS_WIRE_CB_TOKEN` (نه hash خام)؛ تا آن زمان دفاع = allowlist chat + جداییِ عمدی scheme از مسیر settle (`live_loop.py:308-310`) → R2 |
| TH-I-5 | R | مالک بگوید «من رأی ندادم» | **موجود:** verdict durable + idempotent در `outcomes.db` (`verdict_recorder.py:62-96`) + تاریخچهٔ legacy (`approval_store.py:259-278`) + audit jsonl (`approval_store.py:114-121`) |

### Stage J — Human verdict → LANGAR append
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-J-1 | S | append «انسانی» جعلی (کد خودش را انسان جا بزند — AP-5/AP-8) | **موجود:** HumanAppendGuard — توکن HMAC bound به approval_id+event_type+انقضا؛ بی‌توکن/جعلی → downgrade `is_human=0` (`chrono.py:446-459`, `human_append_guard.py:11,60,144`)؛ فلگ `OCTOPUS_WIRE_HUMAN_APPEND_GUARD` باید پیش از فعال‌سازی روشن شود → R3 |
| TH-J-2 | R | نبود ردِ audit برای release | **موجود:** `release_ref` = hash همان append (`chrono.py:380-386`)؛ ledger note content-free (`chrono.py:352-356`؛ الگوی `langar_bridge.py:79-94`) |

### Stage K — EffectorGate (Trust Boundary 3)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-K-1 | E | settle بدون LANGAR append | **موجود:** settle فقط status=releasable+release_ref؛ وگرنه EFFECT_REFUSED (`chrono.py:397-414`) |
| TH-K-2 | E | دورزدن STOP/HALT/FREEZE | **موجود:** `force_closed` ارشد و بی‌قیدوشرط (`chrono.py:358-367,399-404`)؛ tests: `test_stop_contract.py`, `test_master_halt.py`, `S1-04_test_cockpit_stop_guard.py` |
| TH-K-3 | E | **شکاف مرکزی: release دسته‌جمعی.** `release_gated_effects` با یک رأی، **همهٔ** pendingها را releasable می‌کند (`chrono.py:384-386` — `WHERE status='pending'` بدون کلید) — رأی روی پیشنهاد A می‌تواند اثر B را آزاد کند | `[BUILD-P0-حیاتی]` release per-effect: ستون `proposal_id` روی `gated_effect` (additive)؛ release فقط effectی که `proposal_id`اش با verdict مطابق است؛ single-use + TTL. **الگوی اثبات‌شدهٔ همین repo:** گیت per-item ps_writeback — رأی bound به هش محتوا، single-use پس از مصرف، منقضی‌شونده (`ps_writeback.py:13-15,69-71,285-318,567-581`) → R1 |
| TH-K-4 | E | لید synthetic به دنیا برسد | `[BUILD]` hard-block نوعی: `source.channel==synthetic_test ⇒ settle=False` داخل خود EffectorGate (نه در Leg) — ساختاری، مقدم بر هر releasable (LEAD_INBOX_SPEC §4) |
| TH-K-5 | D | pendingهای کهنه انباشته شوند | **موجود:** `sweep_stale_effects` auto-refuse (`chrono.py:416-432`)؛ test: `test_gate_sweep.py` |

### Stage L — Outbound worker (امروز: MISSING؛ P0 milestone 2)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-L-1 | E | ارسال خارج از گیت (import مستقیم effector) | `[BUILD]` worker فقط از صف `settled` effects می‌خواند؛ تست ساختاری ast «هیچ ماژول دیگری provider-client را import نمی‌کند» — الگوی موجود: منع ساختاری import در `verdict_recorder.py:16` و invariant تک‌مصرف‌کننده `approval_store.py:37-44` |
| TH-L-2 | T | double-send در retry | `[BUILD]` `effect_id` یکتا = idempotency key ارسال؛ ثبت `communication.sent` قبل از retry؛ الگوی idempotent: `outcome_store.py:87-107`؛ test موجودِ هم‌خانواده: `test_effector_idempotency.py` |
| TH-L-3 | I | secret provider در log | `[BUILD]` secret فقط env؛ خطای provider با کد، نه dump |
| TH-L-4 | D | provider down → گم‌شدن بی‌صدا | `[BUILD]` `communication.failed` + کارت alert + state retry-safe (mission test 13)؛ «No silent failures» (OPUS invariants §11) |

### Stage M — Provider result ingestion (امروز: MISSING)
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-M-1 | S | callback جعلی provider («delivered» دروغ) | `[BUILD]` **P0/P1: هیچ webhook باز.** فقط polling خروجی provider با credential خودمان، یا ورود دستی مالک؛ webhook فقط اگر روزی لازم شد، با امضای provider + همان الگوی boundary |
| TH-M-2 | T | conflate «delivered گزارش‌شده» با «تحویل واقعی» | **موجود (درس):** `delivered` رکوردر فعلی یعنی «رسیدِ sandbox» نه تحویل (RUNTIME-TRUTH §4#7)؛ vocabulary جدا نگه داشته شود — `verdict_recorder.py:26-33` (`_FORBIDDEN_EVENT`: رأی هرگز delivered/settled نمی‌سازد) |

### Stage N — Outcome attribution → Cortex measurement
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-N-1 | T | خودگزارشی → درآمد جعلی | **موجود:** fitness فقط CONFIRMED می‌خواند؛ CONFIRMED فقط از reconcile-job (`budget/attribution.py:7-12,25-26`)؛ `confirmed_revenue_aud=0` تا reconcile (`outcome_store.py:142-143`) |
| TH-N-2 | T | conflate رأی مالک با outcome بازار | **موجود:** taxonomy جدا + forbidden classes (`verdict_recorder.py:26-33,77`)؛ measure از store قطعی (`goal_directed.py:194-206`)؛ «missing data must not become success» (`goal_directed.py:208-216`) |
| TH-N-3 | R | duplicate event → متریک باد کند | **موجود:** UNIQUE idempotency_key (`outcome_store.py:78,100-107`) |

### Cross-cutting
| TH | STRIDE | تهدید | کنترل |
|---|---|---|---|
| TH-X-1 | I | PII/secret در logs/ledger/HANDOFF (AP-6) | **موجود:** scrub کارت (`live_loop.py:271-276`)، ledger content-free (`langar_bridge.py:79-94`, `approval_store.py:17`)، `verify_no_pii_in_signals` (`live_loop.py:507-516`)، `test_pii_read_guard.py`؛ `[BUILD]` سیاست redaction رسمی برای مسیر لید: events فقط شناسه/enum، PII فقط در رکورد لید + quarantine با retention |
| TH-X-2 | E | فلگ اشتباهاً روشن/فعال‌سازی بی‌ترتیب | **موجود (انضباط):** همهٔ رفتار نو default-off؛ `[BUILD]` preflight: تا `OCTOPUS_WIRE_CB_TOKEN` + `OCTOPUS_WIRE_HUMAN_APPEND_GUARD` + secretهایشان ست نشده، `OCTOPUS_WIRE_LEAD_OUTBOUND` حاضر به روشن‌شدن نیست (fail-closed در کد، نه فقط runbook) → R3 |
| TH-X-3 | T | تست سبزِ دروغ (green-lie) | **موجود (درس ثبت‌شده):** pytest بدون `__main__` خارج PYTEST_TESTS = صفر assertion؛ هر تست جدید باید در `tests/run_all.py` register و executable باشد |
| TH-X-4 | D | قفل AV/concurrent run روی state | **موجود (گوچا):** WAL + retry؛ دو run_all موازی flaky — در CI محلی serialize |

---

## 4. موجودیِ کنترل‌های prior-art (جدول مرجع سریع)

| کنترل | فایل:خط | وضعیت |
|---|---|---|
| Loopback origin guard، secure-by-default، fail-closed | `_ops/httpauth.py:26-29,39-74` | موجود، تست: `test_httpauth.py` |
| Single-use اتمیک صف تأیید + قفل single-writer + sanitize id + expiry | `_ops/telegram_center/approval_store.py:33-45,58-64,149-151,168-189` | موجود، تست: `test_approval_queue_consistency.py`, `test_tg_approval_store.py` |
| توکن HMAC callback (bind محتوا+مالک+انقضا، ثابت‌زمان، fail-closed بی‌secret) | `_ops/telegram_center/callback_token.py:51-74` + enforcement `center.py:1216-1251,1341-1351` | موجود پشت `OCTOPUS_WIRE_CB_TOKEN`؛ تست: `S1-05_test_ap_binding.py`, `test_cb_token_legmiss.py` |
| HumanAppendGuard (append انسانی جعلی → downgrade) | `_ops/chrono.py:446-459`, `_ops/budget/human_append_guard.py` | موجود پشت flag؛ تست: `test_human_append_guard.py`, `test_p0_security_fixes.py` |
| EffectorGate: STOP ارشد، settle فقط با release_ref، sweep | `_ops/chrono.py:344-432` | موجود؛ تست: `test_stop_contract.py`, `test_gate_sweep.py`, `test_master_halt.py` |
| **الگوی رأی per-item fail-closed (single-use + TTL + content-hash bind)** | `_ops/legs/ps_writeback.py:13-15,69-71,285-318,567-581` | موجود؛ تست: `test_ps_writeback_verdict.py` — **الگوی مرجع برای release per-effect لید** |
| Outcome store idempotent/append-only/WAL + taxonomy سنجش | `_ops/outcomes/outcome_store.py:87-107,142-143`, `verdict_recorder.py:26-33,62-96` | موجود؛ تست: `test_verdict_outcome.py`, `test_outcome_spine.py`, `test_tg_verdict_durable.py` |
| کارت با scrub PII + bounded + HTML-escape؛ جدایی scheme دکمه از settle | `_ops/live_loop.py:271-276,300-315` | موجود؛ تست: `test_proposal_buttons.py` |
| Allowlist مالک/چت تلگرام | `_ops/budget/approval_channel.py:143,347` | موجود؛ تست: `test_telegram_group_allowlist.py` |
| Quarantine move-not-delete + سایدکار دلیل | `_ops/legs/lead_sense.py:77-119` | موجود؛ تست: `test_lead_discovery_beat.py` |
| Atomic write + dedup inbox | `_ops/legs/lead_leg_inbox.py:66-80,110-128` | موجود (dead-code امروز)؛ تست: `test_lead_leg_inbox.py` |
| جدایی CONFIRMED از خودگزارشی | `_ops/budget/attribution.py:7-12` | موجود؛ تست: `test_attribution.py` |

---

## 5. کنترل‌هایی که باید ساخته شوند (همه پشت فلگ default-off، stdlib-only)

| # | کنترل | الگوی reuse | فلگ |
|---|---|---|---|
| B1 | سرور boundary امضاشده (HMAC/ts/nonce/idem/allowlist/size/rate/quarantine/receipt) — loopback bind + `httpauth.guard_post` | `callback_token` برای HMAC؛ `outcome_store` برای SQLite؛ `lead_sense` برای quarantine | `OCTOPUS_WIRE_LEAD_BOUNDARY` |
| B2 | consent firewall تابع خالص + clamp ساختاری + enforce سه‌نقطه‌ای | fail-closed ps_writeback؛ خالص مثل lead_scorer | (داخل B1/pipeline — بدون فلگ جدا، چون خالص و بدون side-effect) |
| B3 | release per-effect در EffectorGate (proposal_id-keyed، single-use، TTL) | `ps_writeback.py` per-item verdict | `OCTOPUS_WIRE_LEAD_VERDICT_GATE` |
| B4 | hard-block نوعی `synthetic_test` در settle | — (سه خط، ساختاری) | همراه B3 |
| B5 | suppression table + چک pre-draft و pre-settle | JSONL/SQLite موجود | همراه B2 |
| B6 | ارتقای دکمه‌های کارت لید به cbtok HMAC (به‌جای hash خام `prop:`) | `callback_token.py` + `center.py` enforcement | زیر همان `OCTOPUS_WIRE_CB_TOKEN` |
| B7 | allowlist خروجی LLM parse/draft + پرچم آنومالی draft | قاعدهٔ `llm_note`-only در `wiring.py:1843-1845` | `OCTOPUS_WIRE_LEAD_DRAFT` (موجود) |
| B8 | outbound worker گیت‌خور + provider-result polling-only | `test_effector_idempotency` الگو | `OCTOPUS_WIRE_LEAD_OUTBOUND` (در P0 هرگز روشن نمی‌شود) |
| B9 | preflight فلگ‌های امنیتی (وابستگی سخت B8→CB_TOKEN+HA_GUARD) | فلسفهٔ fail-closed cbtok (`mint=""` بی‌secret) | داخل B8 |
| B10 | purge job برای quarantine/nonce/market_signal (retention_class) | sweep الگوی `chrono.py:416-432` | `OCTOPUS_WIRE_LEAD_RETENTION` |

---

## 6. ریسک‌های باقیمانده — رتبه‌بندی

| رتبه | ID | ریسک | شدت | وضعیت |
|---|---|---|---|---|
| 1 | R0 | **firewall رضایت هنوز وجود ندارد** (صفر کد) — تا ساخته نشود، کل ستون فقرات بلوپرینت خیالی است | بحرانی | build-blocker (B2)؛ milestone 1 بدون آن شروع نشود |
| 2 | R1 | **release دسته‌جمعی گیت** (`chrono.py:384-386`) — رأی A می‌تواند B را آزاد کند؛ برای مسیر پول تلگرام امروز تحمل‌شده، برای ارسال به مشتری قابل‌قبول نیست | بالا | B3 پیش از milestone 2؛ تست T18 |
| 3 | R3 | فلگ‌های امنیتی (`CB_TOKEN`, `HUMAN_APPEND_GUARD`) default-off و secretهایشان mint نشده — پنجرهٔ فعال‌سازیِ بی‌محافظ | بالا | B9 + تصمیم مالک (mint secret) |
| 4 | R9 | suppression هیچ‌جا enforce نمی‌شود (صفر کد) — ریسک Spam Act پس از اولین ارسال واقعی | بالا (فقط از milestone 2) | B5؛ تست T22 |
| 5 | R2 | توکن `prop:` deterministic و بدون owner-binding (`live_loop.py:300-305`) — دفاع فعلی فقط allowlist چت | متوسط-بالا | B6؛ تست T19 |
| 6 | R5 | prompt-injection → فریب مالک (approve خسته) — کنترل‌ها کاهش می‌دهند، صفر نمی‌کنند | متوسط | B7 + آموزش کارت (نمایش خام+draft جدا) |
| 7 | R10 | provider-result ingestion هنوز طراحیِ اجرا نشده — جعل «delivered» در آینده | متوسط (P1) | polling-only (TH-M-1) |
| 8 | R6 | PII plaintext روی دیسک محلی (state/quarantine) | متوسط-پایین | پذیرش P0 با retention (B10) + no-cloud-sync؛ تصمیم مالک |
| 9 | R7 | flood/quarantine growth/nonce growth | پایین-متوسط | B1 caps + B10 purge؛ تست T21 |
| 10 | R8 | `_proposal_cb` in-memory با restart گم می‌شود → دکمهٔ orphan (نه ریسک امنیتی؛ UX) — durable verdict خودش idempotent است | پایین | پذیرفته در P0؛ کارت «از منو دوباره باز کن» |

---

## 7. ماتریس تهدید → تست (۱۷ تست الزامی + شکاف‌ها)

**وضعیت‌ها:** `EXISTS` = امروز سبز در suite؛ `PARTIAL` = هم‌خانوادهٔ generic موجود، نسخهٔ مسیرِ لید باید نوشته شود؛ `WRITE` = باید نوشته شود (کدش هم greenfield است).

| تست (OPUS §REQUIRED TESTS) | تهدیدهای پوشش‌داده | وضعیت | شاهد امروز |
|---|---|---|---|
| 1. کاندید synthetic امضاشده پذیرفته شود | TH-B-1 (مسیر مثبت) | WRITE | — (boundary غایب) |
| 2. امضای نامعتبر رد شود | TH-B-1, TH-B-2, TH-A-1 | WRITE | الگوی assert: `S1-05_test_ap_binding.py` |
| 3. timestamp منقضی رد شود | TH-B-3 | WRITE | الگوی expiry: `test_cb_token_legmiss.py:219-228` |
| 4. nonce تکراری رد شود | TH-B-3 | WRITE | — |
| 5. idempotency تکراری = بدون لید دوم | TH-B-4, TH-D-1 | PARTIAL | dedup متنی: `test_lead_leg_inbox.py` |
| 6. رضایت غایب ⇒ outreach_allowed=false | TH-E-3, TH-D-2 | WRITE | — (firewall غایب — R0) |
| 7. market_signal وارد مسیر outbound نشود | TH-E-1 | WRITE | — |
| 8. public_b2b ≠ رضایت مسکونی | TH-E-2 | WRITE | — |
| 9. STOP اثر بیرونی را می‌بندد | TH-K-2 | EXISTS (generic) + PARTIAL (kind لید) | `test_stop_contract.py`, `test_master_halt.py`, `S1-04_test_cockpit_stop_guard.py` |
| 10. n8n بدون credential/route گیت | TH-A-2 | WRITE (تست منفی route-table + config) | سند: `n8n_wf2_REMOVED_README.md` |
| 11. approve مالک idempotent | TH-I-3 | EXISTS (generic) + PARTIAL (لید) | `test_approval_queue_consistency.py`, `approval_store._move` |
| 12. callback تکراری double-send نسازد | TH-I-3, TH-L-2 | PARTIAL | `S1-05_test_ap_binding.py`, `test_effector_idempotency.py`, `test_proposal_buttons.py` |
| 13. خطای provider ⇒ alert + retry-safe | TH-L-4, TH-M-2 | WRITE (در P0 با provider ساختگی) | — |
| 14. Proposal↔Lead↔Effect correlation | TH-N-3, TH-J-2 | PARTIAL | `test_lead_outcome_wiring.py`, `test_verdict_outcome.py` (lead_id در verdict — `verdict_recorder.py:75`) |
| 15. outcome به لایهٔ measurement برسد | TH-N-1, TH-N-2 | PARTIAL | `test_goal_directed.py`, `test_outcome_spine.py`; قوس ۸۰٪ بسته (RUNTIME-TRUTH §1#18) |
| 16. صفر secret/PII در log | TH-X-1, TH-G-3, TH-B-7 | PARTIAL | `test_pii_read_guard.py`, `live_loop.verify_no_pii_in_signals` |
| 17. تست‌های موجود سبز بمانند | TH-X-3 (regression) | EXISTS | `tests/run_all.py` (۲۳۴/۲۳۵ واقعی؛ گارد green-lie) |

**تست‌های شکاف (الزامیِ این threat model — همه WRITE):**

| ID | تست | تهدید/ریسک |
|---|---|---|
| T18 | approve پیشنهاد A هرگز effect pending B را release نکند (per-effect isolation) | TH-K-3 / R1 |
| T19 | دکمهٔ کارت لید با توکن جعلی/بی‌HMAC رد شود (وقتی CB_TOKEN روشن) | TH-I-4 / R2 |
| T20 | `synthetic_test` در EffectorGate.settle ساختاراً بلاک شود، حتی releasable | TH-K-4 |
| T21 | oversize/flood/منبع غیرallowlist ⇒ رد structured + سقف quarantine | TH-B-5, TH-B-1, R7 |
| T22 | contact در suppression ⇒ صفر draft و صفر settle (هر دو نقطه) | TH-E-4 / R9 |
| T23 | خروجی LLM نتواند consent/candidate_type/score/recipient را تغییر دهد (allowlist فیلد) | TH-G-1, TH-G-2 / R5 |
| T24 | nonce/idempotency پس از restart هم replay را رد کند (durability) | TH-B-3, TH-B-4 |
| T25 | رویداد رسید append-only برای هر submission، حتی رد‌شده (هیچ silent drop) | TH-B-8, TH-C-3, TH-A-3 |
| T26 | preflight: `OCTOPUS_WIRE_LEAD_OUTBOUND` بدون CB_TOKEN+HA_GUARD+secretها fail-closed بماند | TH-X-2 / R3 |
| T27 | هر تست جدید در `run_all.py` register و اجراپذیر باشد (ضد green-lie) | TH-X-3 |

**پوشش:** هر TH-* این سند به دست‌کم یک ردیف بالا نگاشت شده است؛ TH-F-1/2 و TH-H-1..3 و TH-X-4 توسط تست‌های موجود (`test_lead_scorer.py`, `test_live_loop.py`, `test_proposal_buttons.py`, هارنس) پوشش دارند و در milestone 1 فقط smoke مسیر لید به آن‌ها اضافه می‌شود.

---

## 8. پیش‌شرط‌های فعال‌سازی (ترتیب امنیتی — بخشی از 10_OWNER_DECISIONS)

1. پیش از milestone 1 (حلقهٔ synthetic): B1+B2+B4 ساخته و تست‌های 1–8, T20, T23, T25 سبز.
2. پیش از milestone 2 (اولین ارسال واقعی): B3+B5+B6+B9؛ مالک `OCTOPUS_CB_SECRET` و secret گارد append را mint کند؛ فلگ‌های `OCTOPUS_WIRE_CB_TOKEN` و `OCTOPUS_WIRE_HUMAN_APPEND_GUARD` روشن؛ تست‌های 9–12, T18, T19, T22, T26 سبز.
3. `OCTOPUS_WIRE_LEAD_OUTBOUND` تنها فلگی است که «اثر واقعی» می‌سازد — روشن‌کردنش رأی صریح مالک می‌خواهد و preflight کدی دارد (B9).
4. STOP-ORGANISM در تمام مراحل دست‌نخورده و ارشد می‌ماند.

*این سند طراحی است، نه ادعای پیاده‌سازی؛ هیچ ادعای موفقیتی بدون تست و شواهد runtime پذیرفته نیست (OPUS mission، بند پایانی).*
