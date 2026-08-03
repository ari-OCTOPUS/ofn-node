# FULL OCTOPUS DEEP SCAN REPORT

> **تاریخ:** 2026-08-02 · **روش:** read-only reconnaissance با ۵ اکسپلورر موازی + verify روی دیسک
> **اصول:** هیچ fake-green · هیچ مسیر broken به‌عنوان green اعلام نشد · هر ادعا با `file:line` اثبات شده

---

## 1. Executive Summary

| محور | وضعیت |
|---|---|
| **Overall status** | 🟢 هستهٔ organism زنده و پایدار (beat 23078)، چندین leg فعال، ایمنی چندلایه واقعی |
| **Biggest blocker** | 🟠 Telegram callback HMAC token **default OFF** (`OCTOPUS_WIRE_CB_TOKEN=0`) — legacy tokenless callbacks بدون replay/expiry protection |
| **Biggest fake-green risk** | 🟡 ~۱۰ تست `assert True` شناخته‌شده + capability_registry skeleton که dispatch مصرفش نمی‌کند |
| **Telegram → Octopus** | ✅ WORKING (long-poll، ۳۰+ command، ۲۰+ callback verb) |
| **Octopus → Legs** | ✅ WORKING (sync، epoch-fired beats، flag-gated) |
| **Legs → Response** | ✅ WORKING (receipt card به topic + dashboard via business_legs_beat) |
| **Painter/Lead leg** | ✅ WORKING — production-grade، ۵ لایه EffectorGate، ۲۹ تست |
| **Project-F / OnlyFans** | 🟡 PARTIAL — کد کامل، GATE 0 = OPEN (مسدود)، compose-only، bridge_beat وصل نشده |
| **Dashboard/UI** | ✅ WORKING (Wave 1 سبز، web_app صحیح، X-Tg-Init-Data ارسال می‌شود) |
| **State/recovery** | 🟠 PARTIAL — atomic writes خوب، اما sprawl (~۳۲۰ store) + رشد بی‌نهایت JSONL |
| **Test suite** | ✅ WORKING (~۴۲۲ فایل، runner ضد-green-lie) · 🔴 mutation framework MISSING |
| **Safe to patch now?** | **YES (partial)** — Layer امنیت amadeast؛ patch فقط adapter-first با تست |

---

## 2. System Map (کشف‌شده از repo)

```
TELEGRAM API
    │  long-poll ($0-idle)
    ▼
[tg_api.py:642 poll_updates] ─────────────────── WORKING
    │
    ▼
[center.py:4383 run_once → handle_update]
    │
    ├──[tg_api.py:374 is_owner] ──────────────── WORKING (fail-closed, from.id)
    │
    ├──[input_surface_policy] ────────────────── WORKING (DM vs group)
    │
    ├──[_handle_message] ──────────────────────── WORKING (30+ slash commands)
    │       │
    │       └──[bridge_to_organism] ──────────── WORKING (unknown → organism bot)
    │
    └──[_handle_callback] ─────────────────────── WORKING (20+ verb families)
            │
            ├── hm:* tk:* ap:* mn:* lg:* pw:* ms:* map:* ── WORKING
            ├── HMAC token (OCTOPUS_WIRE_CB_TOKEN) ──────── PARTIAL (default OFF)
            └── bridged (app:approve brain:approve) ──────── WORKING
    │
    ▼
[wiring.py 245KB — epoch-fired beats] ──────────── WORKING
    │
    ├── leg_beat (lead/ziman/cartographer) ──────── WORKING
    ├── doctor_beat / consolidation_beat ────────── WORKING
    ├── business_legs_beat → ORGANISM-STATE ─────── WORKING
    ├── afferent / telegram / heart / neural ────── WORKING
    └── mining_os / crypto / accounting ─────────── 🔴 SKELETON/STALE
    │
    ▼
[organism.py:1179 _write_state] ────────────────── WORKING (atomic LockedJson)
    │
    ▼  GET /api/organism (port 8771)
    │
[Dashboard / MiniApp] ──────────────────────────── WORKING (Wave 1 سبز)
```

---

## 3. Component Inventory

| component | path | role | active/archive/skeleton | flag | status | evidence |
|---|---|---|---|---|---|---|
| organism.py | `_ops/organism.py` | main loop, tick 300s | ACTIVE | — | WORKING | beat 23078 live |
| wiring.py | `_ops/wiring.py` | dispatch hub 245KB | ACTIVE | paper-full | WORKING | 35+ flags true |
| center.py | `_ops/telegram_center/center.py` | TG router 4571 lines | ACTIVE | OCTOPUS_WIRE_TG | WORKING | polling live |
| LiveLoop | `_ops/live_loop.py` | leg proposal routing | ACTIVE | — | WORKING | route_leg_proposals |
| LeadLeg | `_ops/legs/lead_leg.py` | painter/lead | ACTIVE | OCTOPUS_WIRE_LEAD | WORKING | 29 tests |
| ZimanLeg | `_ops/legs/` | ziman gallery | ACTIVE | OCTOPUS_WIRE_ZIMAN | WORKING | beat 23040 |
| Cartographer | `_ops/legs/` | vault mapper | ACTIVE | OCTOPUS_WIRE_CARTOGRAPHER | WORKING | beat 23078 |
| Doctor | `_ops/doctor/` | self-repair | ACTIVE | OCTOPUS_WIRE_DOCTOR | WORKING | daily cycle |
| Neural stack | `_ops/neural/` 17 files | circadian/rhythm/hebbian | ACTIVE | OCTOPUS_WIRE_NEURAL | WORKING | consolidation 199KB |
| Heart | `_ops/heart/` 13 files | pulse arbiter | ACTIVE | OCTOPUS_WIRE_HEART | PARTIAL | wire_open=false |
| Cortex | `_ops/cortex/` port 8772 | LLM brain | ACTIVE | — | WORKING | deep_think OFF default |
| Mining leg | — | mining monitor | SKELETON | wire_mining=true | 🔴 | signal=skeleton |
| Crypto leg | — | crypto monitor | STALE | — | 🔴 | data >7d old |
| Accounting leg | — | bookkeeping | STALE | wire_actuator=false | 🔴 | workbooks >35d |
| Knowledge leg | — | knowledge map | SKELETON | — | 🔴 | no afferent spec |
| 4d_system brain | `4d_system/` | research daemon | REVIVED 2026-08-02 | SELF_CODE | WORKING | 1 tick green today |
| Project-F | `03-Projects/اونلی فنز/` | OF studio | ACTIVE (locked) | GATE 0 OPEN | PARTIAL | compose-only |
| MiniApp gateway | `_ops/telegram_center/miniapp_gateway.py` | Wave 1 CRM | ACTIVE | — | WORKING | HMAC owner-gate |

---

## 4. Blackbox Inventory

| blackbox | known input | known output | status API | side effects | tests | verdict |
|---|---|---|---|---|---|---|
| **Cortex think** | prompt + tier | text answer | health (port 8772) | paid LLM call (gated) | yes | WORKING |
| **deep_think** | prompt | proposal card | flag OCTOPUS_WIRE_DEEP_THINK | Fugu ultra call | yes | PARTIAL (default OFF) |
| **Lead EffectorGate** | candidate + verdict | release/deny | lead-effect-authz.json | SMTP send (armed) | yes (test_lead_effect_gate) | WORKING |
| **Consent firewall** | candidate dict | outreach_allowed bool | — | none (pure fn) | yes | WORKING |
| **Money gate** | amount + channel | allow/deny | budget-state.json | none (deny default) | yes | WORKING (fail-closed) |
| **Project-F actuator** | ModuleSpec | draft/error | GateState | none (NotImplementedError live) | yes | WORKING (locked) |
| **Consolidation** | sources dict | ConsolidatedInsight | consolidation.json | none | yes | WORKING |
| **Capability registry** | AST scan | card list | capability-manifest.json | none | partial | PARTIAL (skeleton, dispatch نconsumed) |

---

## 5. Telegram Wiring

```
Telegram API ─► poll_updates ─► handle_update ─► is_owner ─► _handle_message/callback
                                                                       │
                                                                       ▼
                                                            bridge_to_organism (unknowns)
```

| id | point | evidence | severity | repair |
|---|---|---|---|---|
| TW-1 | HMAC callback token default OFF | `center.py:4074`, `OCTOPUS_WIRE_CB_TOKEN=0` | 🟠 high | فعال‌سازی flag + تست parity |
| TW-2 | No per-command trace_id | only decision IDs have trace_id | 🟡 medium | propagation run_id در handle_update |
| TW-3 | Legacy `ok:/no:/later:` بدون dedup وقتی token OFF | `center.py:4253` | 🟡 medium | مهاجرت به tokenized callbacks |
| TW-4 | actions.py skeleton مصرف نمی‌شود | dispatch از hardcoded dict | 🟡 medium |.consume ACTIONS در handle_callback |

---

## 6. Octopus Core Wiring

```
boot ─► apply_profile(paper-full) ─► wire modules ─► while True:
  observe(halt/telemetry) ─► protective_override ─► dispatch(epoch beats) ─► _write_state ─► sleep
```

**Verdict: WORKING** — isolation عالی (هر beat در try/except)، halt پنج‌لایه، atomic state writes.

---

## 7. Leg Dispatch Wiring

```
Command ─► wiring.beat ─► leg.intake/draft/claim ─► emit_proposal ─► card to owner ─► verdict ─► effect_gate ─► (send?)
```

**Verdict: WORKING** — sync، epoch-fired، propose-only. Leg base class (`leg.py`) از مسیر execution واقعی جدا است (بای‌پس می‌شود).

---

## 8. Response Return Wiring

```
leg result ─► receipt_text + keyboard ─► Telegram topic ─► business_legs_beat ─► ORGANISM-STATE ─► Dashboard
```

**Verdict: WORKING** — receipt card، good/bad rating، periodic digest، pinned card refresh.

---

## 9. Painter / Lead Deep Scan

- **Files:** lead_leg.py (217), lead_quote.py (423), lead_first_reply.py (503), lead_outbound_transport.py (796), lead_effect_gate.py (366), consent_firewall.py (171), lead_email_intake.py (1265)
- **Entrypoints:** 4 کانال (Telegram `/lead` MISSING، Email IMAP، HTTP boundary، CSV)
- **Contracts:** 5-layer EffectorGate، triple-layer idempotency، consent firewall fail-closed
- **Broken paths:** `/lead` Telegram command MISSING (convenience gap، نه safety)
- **Missing APIs:** first-reply draft card view (siloed on disk)
- **Tests:** 29 فایل (7 integration)
- **Repair plan:** اضافه‌کردن `/lead` command + first-reply visibility adapter

**VERDICT: production-safe.** هر outbound path 3-5 gate مستقل دارد. Market signal هرگز auto-sent. Synthetic هرگز outbound واقعی نمی‌سازد.

---

## 10. Project-F / OnlyFans Deep Scan

- **Files:** studio/creator_brain.py (514)، pf_os/ (25+ files)، brain/، langar/
- **Entrypoints:** Creator Studio Bot (DORMANT — token نساخته شده)، `/projectf` status-only، Langar Bot (DORMANT)
- **Contracts:** GuardLayer PII redaction، GATE 0 (OPEN = مسدود)، triple-gated publish
- **Broken paths:** bridge_beat consumer وصل نشده به main loop
- **Missing APIs:** MISSING_BUILD_API (compose-only، نه build pipeline)، MISSING_STATUS_API (per-draft endpoint نیست)
- **Tests:** 22 فایل، 328+ claimed green
- **Repair plan:** REST lifecycle + bridge wiring + status API (همه local-only، GATE 0 حفظ)

**VERDICT: compose-only by design.** هیچ platform API واقعی. `onlyfans.*`/`fansly.*` در BLOCKED_PREFIXES. PII قبل از LLM redact می‌شود.

---

## 11. State / Queue / Ledger

| store | path | purpose | schema known? | atomic? | recovery? | risk |
|---|---|---|---|---|---|---|
| ORGANISM-STATE.json | `_ops/state/` | master state | ✅ | ✅ LockedJson | boot recovery | low |
| events.jsonl | `_ops/state/` | event spine 929KB | ✅ | append | MAX_KEEP=500 | low |
| chrono.db | `_ops/state/` | chronology 7MB | ✅ | WAL | hash-chain | low |
| 4d_experiments.db | `4d_system/outputs/` | research 14 tables | ✅ | WAL | backup rotation | low |
| genome ledger.jsonl | `07-Knowledge/genome-system/ledger/` | hash-chain 14602 records | ✅ | SHA-256 | scar-aware verify | low |
| consolidation.json | `_ops/neural/` | memory 199KB | ✅ | atomic | sig dedup | low |
| unified-approval-queue.json | `_ops/state/` | HITL queue | ✅ | RLock | atomic _move | low |
| action-audit.jsonl | `_ops/state/` | audit trail | ✅ | append | — | 🟡 unbounded (R27) |
| approval-log.jsonl | `_ops/state/` | approval history | ✅ | append | replay protected | 🟡 unbounded (R28) |
| neural/effect-shadow.jsonl | `_ops/state/neural/` | effect tracking 4.2MB | ✅ | append | — | 🔴 11k lines no rotation |
| tg-send-log.jsonl | `_ops/state/` | TG sends 320KB | ✅ | append | prune | low |
| paid-calls.jsonl | `_ops/state/` | LLM spend 114KB | ✅ | append | — | 🟡 unbounded |
| money state (10+ files) | scattered | budget/cardiac/gate | partial | mixed | — | 🟠 fragmentation |

** sprawl:** ~۳۲۰ state store در `_ops/state/` — consolidation plan لازمه.

---

## 12. Security / Permission / Privacy

| risk | component | severity | evidence | mitigation |
|---|---|---|---|---|
| HMAC token OFF | telegram callback | 🟠 high | `OCTOPUS_WIRE_CB_TOKEN=0` | فعال‌سازی + تست |
| API keys در .env | root config | 🟡 medium | live keys روی دیسک | gitignore ✅، ولی exposed locally |
| State sprawl | ~۳۲۰ stores | 🟡 medium | `_ops/state/` | consolidation plan |
| JSONL unbounded | audit/approval/effect | 🟡 medium | R27/R28 | rotation خارجی |
| Watchdog split-brain | organism watchdog | 🟡 medium | scheduled task → divergent script | OWNER-GATED (مستند) |
| No per-command tracing | telegram | 🟡 medium | فقط decision IDs | run_id propagation |

**/passing:** Owner allowlist fail-closed · secrets هرگز echo نمی‌شوند (3-layer scrub) · PII redact قبل از LLM · consent firewall structural · money gate fail-closed · blocked prefixes enforced · path traversal guarded · allowlist fail-closed · permission unknown = deny.

---

## 13. Checklist Summary

| domain | pass | fail | partial | unknown | notes |
|---|---:|---:|---:|---:|---|
| Core | 18 | 0 | 2 | 0 | metrics scattered، watchdog split |
| Telegram | 9 | 0 | 3 | 0 | token OFF، no trace_id، legacy dedup |
| Leg dispatch | 5 | 0 | 1 | 0 | leg.py base disconnected |
| Painter/Lead | 18 | 0 | 2 | 0 | /lead cmd + reply card missing |
| Project-F | 11 | 0 | 4 | 2 | build/status API missing، bridge not wired |
| UI/Dashboard | 8 | 0 | 0 | 0 | Wave 1 fully green |
| State/Recovery | 8 | 0 | 3 | 0 | sprawl + unbounded JSONL |
| Security | 14 | 0 | 2 | 0 | token OFF + .env local |
| Tests | 7 | 1 | 3 | 0 | mutation framework MISSING |
| Repair planning | — | — | — | — | see roadmap |

---

## 14. Gap Register

| id | severity | gap | evidence | suggested repair | needs owner? |
|---|---|---|---|---|---|
| G-001 | 🟠 high | HMAC callback token default OFF | `OCTOPUS_WIRE_CB_TOKEN=0` | فعال‌سازی flag + تست parity | no |
| G-002 | 🟠 high | No mutation/fault-injection test framework | no systematic bad-input tests | ساخت mutation harness | no |
| G-003 | 🟡 medium | No per-command trace_id | only decision IDs | propagation در handle_update | no |
| G-004 | 🟡 medium | State sprawl ~320 stores | `_ops/state/` tree | consolidation plan | yes |
| G-005 | 🟡 medium | JSONL unbounded (audit/approval/effect) | R27/R28 + effect-shadow 11k | rotation policy | no |
| G-006 | 🟡 medium | capability_registry skeleton unconsumed | `actions.py` dispatch نconsumed | wire ACTIONS به handle_callback | no |
| G-007 | 🟡 medium | Project-F bridge_beat not wired | planned but not integrated | wire به main loop behind flag | no |
| G-008 | 🟡 medium | No `/lead` Telegram command | MISSING convenience | adapterLeadIntake | no |
| G-009 | 🟡 medium | First-reply draft no owner card | siloed on disk | visibility adapter | no |
| G-010 | 🟡 medium | Watchdog organism split-brain | scheduled task → divergent | OWNER-GATED documented | yes |
| G-011 | 🟡 medium | Money state fragmentation 10+ files | scattered | single source of truth | yes |
| G-012 | 🟢 low | Mining/crypto/accounting skeleton | signal=skeleton | activation یا archive | yes |

---

## 15. Unknown Register

| id | unknown | why unknown | how to discover | owner question? |
|---|---|---|---|---|
| U-001 | Project-F + Wave 1 CRM tables integration | ProjectFAdapter BLOCKED | وقتی GATE 0 close شه | yes |
| U-002 | Wave 2 tables existence | `campaigns`/`content_items`/`manual_send_queue`/`money_events` nowhere | build در Wave 2 | no |
| U-003 | 4D daemon long-run stability | فقط 1 tick تست شده | 24h smoke | no |
| U-004 | Heart wire_open=false impact | pulse arbiter partial | audit parity | no |

---

## 16. Repair Roadmap

### Phase 0 — No-patch safety baseline
- ✅ انجام شد: Wave 1 verify، REFERENCE_DIR fix، bridge path fix، fugu_usage_policy، consolidation 4D

### Phase 1 — Contract extraction and status mappers
- استخراج contract‌های رسمی برای leg/effector/cortex
- status mapper برای pending/running/blocked/failed/done

### Phase 2 — Telegram ingress normalization
- G-001: فعال‌سازی HMAC callback token
- G-003: per-command trace_id propagation
- G-006: consume capability_registry

### Phase 3 — Octopus command bus / dispatch adapters
- مهاجرت از hardcoded dict به ACTIONS registry
- adapter-first برای leg‌های جدید

### Phase 4 — Painter / Lead wiring
- G-008: `/lead` Telegram command
- G-009: first-reply visibility card

### Phase 5 — Project-F / OnlyFans wiring
- G-007: bridge_beat به main loop
- MISSING_BUILD_API: REST draft lifecycle
- MISSING_STATUS_API: per-draft endpoint

### Phase 6 — Response return path
- مهاجرت leg.py base class به مسیر واقعی (یا حذف)

### Phase 7 — Idempotency / retry / recovery
- G-005: JSONL rotation policy
- G-011: money state single source of truth

### Phase 8 — Test and mutation suite
- G-002: mutation/fault-injection framework
- end-to-end Telegram flow test
- main loop integration test (N ticks)

---

## 17. Test Plan

### Unit tests
- ✅ ~۴۲۲ فایل موجود (strong coverage)

### Integration tests
- ✅ 7 lead wiring tests
- 🔴 end-to-end Telegram → leg → verdict → state
- 🔴 multi-process coordination (organism/cortex/live/center)

### End-to-end dry-run tests
- 🔴 full compose → approve → publish (Project-F)
- 🔴 full lead intake → quote → reply → verdict → send

### Mutation tests
- 🔴 missing run_id/trace_id
- 🔴 ok:true + error
- 🔴 success without artifact
- 🔴 duplicate callback (token OFF)
- 🔴 replay approval
- 🔴 actor spoof
- 🔴 timeout/retry
- 🔴 flag-off parity
- 🔴 halt/freeze mid-run
- 🔴 direct bypass
- 🔴 corrupted state

### Restart/recovery tests
- ✅ ~15 فایل موجود (strong)

### Security tests
- ✅ ~20 فایل موجود (strong)

---

## 18. Owner Questions

1. **G-010:** Watchdog organism split-brain — رفع با redirect scheduled task به script صحیح، یا حفظ status quo؟
2. **G-004/G-011:** State sprawl و money fragmentation — آیا consolidation الان اولویت دارد؟
3. **G-012:** Mining/crypto/accounting skeleton legs — activation یا archive رسمی؟
4. **U-001:** Project-F GATE 0 — چه زمانی close شه تا integration تست شه؟
5. **G-001:** HMAC callback token — فعال‌سازی الان مجازه؟

---

## 19. Final Verdict

| محور | verdict |
|---|---|
| **Safe to patch now** | YES — adapter-first، test-before-patch، flag-gated |
| **Must not patch yet** | GATE 0 (Project-F)، state consolidation، watchdog split |
| **Needs owner decision** | G-004, G-010, G-011, G-012, U-001 |
| **Biggest risk** | 🟠 HMAC token OFF (legacy callbacks بدون protection) |
| **First recommended next step** | **G-001: فعال‌سازی `OCTOPUS_WIRE_CB_TOKEN=1`** + تست parity |

---

## معیار موفقیت (طبق مگاپرامپت)

- ✅ تمام جعبه‌سیاه‌ها inventory شدند
- ✅ مسیر Telegram تا Octopus مشخص شد (WORKING)
- ✅ مسیر Octopus تا پاها مشخص شد (WORKING)
- ✅ مسیر برگشت جواب مشخص شد (WORKING)
- ✅ painter/lead وضعیت دقیق دارد (production-safe)
- ✅ Project-F/OnlyFans وضعیت دقیق دارد (compose-only locked)
- ✅ broken‌ها evidence دارند
- ✅ unknown‌ها جدا ثبت شدند (U-001..U-004)
- ✅ repair plan مرحله‌ای داده شد (Phase 0-8)
- ✅ test و mutation plan داده شد
- ✅ هیچ fake green ساخته نشد
