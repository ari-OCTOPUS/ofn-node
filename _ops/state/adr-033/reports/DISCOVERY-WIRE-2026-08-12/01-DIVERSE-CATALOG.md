---
type: evidence
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, discovery, diverse-scan, wiring, ui, money, flags, memory, intents]
related:
  - "[[00 - Inbox/2026-08-12 MEGAPROMPT — Discovery Wire Missing Connections (Junior-Safe)]]"
---

# Diverse Discovery Catalog — 2026-08-12 (موج ۲)

> هدف: تنوع شکار — نه فقط dead-output کلاسیک.
> دامنه‌ها: UI · Money · Flags/Proc · Memory · Chrono · Doctor · Intents · Wiring کهنه
> هر ردیف یا روی دیسک VERIFY شد یا از اسکن موازی با شاهد فایل آمده.
> ایجنت بعدی: **هر دور یک FINDING از یک دامنهٔ متفاوت** (rotation).

Evidence قبلی (سیم‌های کلاسیک): [[00-DEEP-SCAN-FINDINGS]]

---

## قانون چرخش دامنه (اجباری برای junior)

```
دور 1 = INTENTS یا UI
دور 2 = FLAGS/PROC
دور 3 = MEMORY
دور 4 = MONEY (فقط گزارش مگر low-risk)
دور 5 = CHRONO/HEART
دور 6 = DOCTOR
دور 7 = WIRING کلاسیک (DW-*)
دور 8 = برگرد به دامنهٔ ۱ با FINDING تازه
```

هرگز ۳ دور پشت‌سرهم از یک دامنه نزن.

---

## A) UI / MiniApp — دروغ سبز و timeout و auth

| id | حکم | شاهد | risk | اقدام junior |
|---|---|---|---|---|
| UI-01 | `aligned` را drift می‌بیند | `app.js` viewHome | ✅ FIXED 2026-08-12: فقط `drift` warm |
| UI-02 | obsidian/tasks بدون status→آرامِ دروغ | viewHome: `missing\|\|[]` بدون `status==="ok"` | high | مثل approvals گیت کن |
| UI-03 | فایل JSON = reachable سبز | `_brain_daemon` / cortex بدون age روی last_tick | med | stale اگر >N دقیقه |
| UI-04 | status پیش‌فرض `"ok"` | `renderSystemHead` | med | default=`unknown` |
| UI-05 | Ask client 45s < زنجیرهٔ سرور | vault45+brain+collab → client abort زود | high | یک بودجهٔ مشترک |
| UI-06 | دکمهٔ action 30s vs apiPost 60s | `act` watchdog | med | هم‌تراز کن |
| UI-07 | 403 auth بدون UX «ببند/باز» | AUTH_MAX_AGE + initData کهنه | high | toast روی 403 |
| UI-08 | chat-log/SSE بی‌auth | `__OCTOPUS__.init_data` ست نمی‌شود؛ `tgHeaders` جداست | high | **✅ FIXED (senior 2026-08-12):** هر دو نقطه به `tgHeaders({})` تغییر کرد — `app.js:2078` و `app.js:2238`؛ node-check OK · gateway PID 1220 |
| UI-09 | Sources فقط روی collab خالص | collab-fallback بدون panel | med | `buildSourcesPanel` برای fallback هم |
| UI-10 | Ask chip ولی جواب collab-fallback | gateway silent fallback | med | chip یا meta صادق |
| UI-11 | GOTO_TAB_FA ناقص + Ask انگلیسی | فقط system/approvals | low | map کامل + برچسب فارسی |

---

## B) Money / Goals / Legs

| id | حکم | شاهد | risk | اقدام |
|---|---|---|---|---|
| MONEY-01 | هدف claimed ساختاراً مسدود | GOALS + fitness claimed=0 + reconcile بی‌CSV + PARK | high | **فقط گزارش**؛ claim جعلی نزن |
| MONEY-02 | تعارض سند: CSV لازم برای claim؟ | OWNER-ACTIONS vs GOALS/attribution.py | med | reconcile docs |
| MONEY-03 | musd=خرج هنوز نام گیج‌کننده | self_knowledge money.musd | med | audit readers |
| MONEY-04 | سقف‌های متناقض؛ پنجره تا 2026-08-13 | SPEND_CAP 200USD vs AU$30 vs daily AU$2 | high | ماتریس سقف برای مالک |
| MONEY-05 | MONEY_FSM / UNCAPPED / VALUE_LEDGER مسلح | flags no-boundary vs rem قبلی hold | high | **فقط گزارش + رأی** |
| MONEY-06 | RECONCILE/FITNESS مسلح ولی خشک | CSV خالی · confirmed=[] | med | armed≠productive |
| MONEY-07 | budget-proposals.jsonl بدون خواننده | center می‌نویسد؛ critique: zero readers | med | گزارش |
| MONEY-08 | fitness صفر و غیرauthoritative | fitness-latest · history `{}` | med | shadow بماند |
| MONEY-09 | پاها «fed» ولی sensed/digested=0 | ORGANISM legs_cultivation / feed.skipped | med | متریک دروغ را گزارش کن |
| MONEY-10 | money_link=active ولی draft=0 | legs propose_only | med | map برچسب≠پول |
| MONEY-11 | لید 667951 منتظر suburb؛ synthetic_test | lead-inbox processed | high | مالک آدرس/ببند |

---

## C) Flags / Process / Orphans

| id | حکم | شاهد | risk | اقدام |
|---|---|---|---|---|
| FLAG-01 | RUNNER_APPLY=1 صفر caller | flags + rg py=0 | high | پیشنهاد =0 |
| FLAG-02 | BUDGET_JUDGE=1 صفر beat caller | heart/budget_judge | med | disarm یا schedule |
| FLAG-03 | MINING_OS 0→1 last-wins | flags 1126 و 1335 | high | رأی مالک کدام؟ |
| FLAG-04 | AUTOAPPLY_LOWRISK=1 با rem «خاموش» | 792/804 vs 1254 | high | **رأی**؛ کد نزن |
| FLAG-05 | PROFILE=`1` (نه paper-full/live) | ORGANISM-STATE profile=1 · VERIFY شد | high | به live یا paper-full برگردان با رأی |
| FLAG-06 | SMTP_FROM/HOST/PORT/USER=`1` سمّ boolean | dark-batch 1285+ | high | پاکسازی با رأی |
| FLAG-07 | CHRONO_RHYTHM در verdicts نه flags.cmd | owner-verdicts vs flags | med | یک منبع حقیقت |
| FLAG-08 | LIMITED_EFFECT_PHASE_N فقط verdict | flags غایب | low | ok اگر env pull عمدی |
| FLAG-09 | capability_classifier فقط تست | rg import | low | وصل به digest یا deprecate |
| FLAG-10 | seed مسلح + کد هست + unsched | DW-02 | high | schedule یا اعلام یتیم |
| FLAG-11 | kernel_bridge مسلح unsched | DW-03 | high | beat fail-soft |
| FLAG-12 | watchdog revive بدون ریشه | STALL_REVIVE · alerts زیاد | med | گزارش thrash |
| FLAG-13 | miniapp START storm در HEARTBEAT | شمارش START زیاد | med | علت thrash نه فقط restart |

---

## D) Memory

| id | حکم | شاهد | risk | اقدام |
|---|---|---|---|---|
| MEM-01 | semantic نوشته می‌شود؛ router نمی‌خواند | retrieval فقط episodic/procedural/owner_fact | med | additive search semantic یا متوقف کن write |
| MEM-02 | procedural جستجو می‌شود؛ ۰ ردیف | store tally | med | ننویس/نجستجو یا seed قانونمند |
| MEM-03 | research-ingest کهنه vs self-loop زنده | jsonl mtime/count | med | چرا research trail خوابیده |
| MEM-04 | vault RAG relevance منفی / موضوع پرت | chroma 4D double pendulum | med | فیلتر دامنه یا خاموش برای collab |
| MEM-05 | session_memory ≠ owner_recall | session فایل دارد؛ recall نمی‌خواند | med | پل cite-only |
| MEM-06 | may_authorize همیشه بسته + grade validator None | gate.py | low | عمدی؟ مستند کن |

---

## E) Chrono / Heart

| id | حکم | شاهد | risk | اقدام |
|---|---|---|---|---|
| CHR-01 | schedule_period_bias مرده | spine می‌نویسد؛ organism فقط rank_bias | med | DW-05 |
| CHR-02 | arbiter docstring «advisory» ولی wire_open می‌راند sleep | pulse_arbiter vs organism | med | docstring/honest |
| CHR-03 | sigma_effective=0 در control_law | shadow jsonl رشد؛ ترمز fragility خاموش | med | منبع σ درست |
| CHR-04 | chrono-rhythm may_affect_routing=false | capability json | low | ok containment |

---

## F) Doctor

| id | حکم | شاهد | risk | اقدام |
|---|---|---|---|---|
| DOC-01 | criticality-v2 فقط run_id=test | jsonl · صفر caller تولیدی | med | live shadow یا خاموش ادعا |
| DOC-02 | self_accuracy فقط clamp confidence | نه actuator | low | display-only صادق |
| DOC-03 | unconscious.json بیرون از `_ops` readers | فقط OCTOPUS-DOCTOR | med | پل digest یا جدا بمان |
| DOC-04 | pending-cards ~85 RFC backlog | pulse/pending-cards.json | med | triage برای مالک |
| DOC-05 | SK در collab/ask نیست | DW-04 · VERIFY | high | تزریق focus+smallest_fix |

---

## G) Intents — VERIFY زنده با `conversation.handle`

| ورودی تست | خروجی واقعی | id |
|---|---|---|
| INT-01 | `یادت باشه … هستم` → memory (دزدی) نه memory-proposal | ✅ FIXED 2026-08-12: SESSION_MEM اول + `هست(?!م)` |
| `این را یادت بماند` | memory-proposal ✅ | — |
| `درباره من چی میدونی` | memory (stub help) | INT-02 |
| `دردم زیاده` | **equation** (چون `درد` در `_EQUATION`) | INT-03 |
| `قلبت کجاست` / `خودآگاه هستی` | **intro** | INT-04 |
| `آخرین improve چی بود` | memory stub | INT-05 |

**ریشه INT-01 (VERIFY):** `_MEMORY_ASK` شامل `یادت.*هست` است → در «یادت باشه من آری **هست**م» match می‌شود؛ و `_MEMORY_ASK` **قبل از** `_SESSION_MEM` اجرا می‌شود (`conversation.py` ~320 سپس ~415).

**INT-06:** center collaborator زود برمی‌گردد → tool_request فقط callback.

---

## H) Wiring کلاسیک (از موج ۱ — تکرار نکن مگر verify)

DW-01..DW-10 در `00-DEEP-SCAN-FINDINGS.md` — smallest_fix دیگر DEAD کامل نیست؛ registry کهنه است.

---

## Top 12 برای شروع متنوع (ترتیب پیشنهادی مالک‌محور)

1. **INT-01** — فیکس regex/order «یادت باشه…هستم» (low-risk، اثر فوری چت)
2. **UI-01** — aligned≠drift در viewHome
3. **UI-08** — initData برای chat-log/SSE
4. **DOC-05 / DW-04** — SK→collab context
5. **FLAG-05+06** — گزارش PROFILE=1 و SMTP=1 (رأی؛ خودت عوض نکن)
6. **MEM-01** — semantic نوشته/نخوانده
7. **MONEY-04+01** — ماتریس سقف + هدف مسدود (گزارش)
8. **CHR-01** — schedule_period_bias
9. **UI-05** — timeout Ask
10. **FLAG-03+04** — last-wins MINING_OS / AUTOAPPLY (رأی)
11. **DOC-01** — criticality فقط test
12. **MONEY-09** — پا fed دروغین

---

## دستورات شکارِ متنوع (هر دامنه یکی)

```powershell
cd F:\backup\_ops
# INTENTS
python -X utf8 -c "from owner_console.conversation import handle; print(handle('یادت باشه من آری هستم'))"
# UI
rg -n "dr!==|init_data|status\|\|.ok" telegram_center/miniapp/app.js
# FLAGS
rg -n "set OCTOPUS_PROFILE=|set OCTOPUS_SMTP_|WIRE_MINING_OS|AUTOAPPLY_LOWRISK" OCTOPUS-flags.cmd
# MEMORY
rg -n "namespace=" memory/retrieval_router.py
# MONEY
python -c "import json;print(json.load(open('state/fitness-latest.json',encoding='utf-8')).get('claimed'))"
# CHRONO
rg -n "schedule_period_bias" . -g "*.py" --glob "!_bak/**"
# DOCTOR
rg -n "CriticalityV2|append_trace" . -g "*.py" --glob "!tests/**" --glob "!_bak/**"
```
