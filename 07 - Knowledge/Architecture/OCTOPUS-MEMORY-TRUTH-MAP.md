---
type: architecture
status: active
created: 2026-08-11
updated: 2026-08-12
tags: [octopus, memory, learning, research, architecture, explanatory]
related:
  - ADR-033
  - ADR-034
  - _ops/memory/gate.py
  - _ops/memory/research_ingest.py
  - _ops/memory/self_loop_ingest.py
  - _ops/cortex/web_research.py
  - _ops/cortex/improve.py
  - architecture/signals-registry.yaml
---

# Octopus Memory Truth Map

> **توضیح‌دهنده است، نه SoT اجرایی.**  
> SoT = MemoryGate + registries + ADR + runtime evidence.  
> هدف: جلوگیری از گم‌شدن یادگیری/تحقیق و drift بین استورها.
>
> Invariants: memory never authorizes · research ADVISORY · self-loop citation-only · neural APPLY=1 (ADR-035 beat-local skip only) · dual stores documented.

## یک‌خطی

تحقیق وب و حلقه‌های خودآگاهی/خودترمیمی/خودبهبودی خروجی می‌سازند؛ `research_ingest` و `self_loop_ingest` آن‌ها را با provenance نگه می‌دارند تا pulseهای overwrite هدر نروند. هیچ‌کدام halt/APPLY/outbound را مجوز نمی‌دهند.

## نقشهٔ استورها (LIVE vs SHADOW)

| Store | مسیر / ماژول | نقش | LIVE؟ | مجوز عمل؟ |
|---|---|---|---|---|
| **MemoryGate + SQLite** | `_ops/memory/gate.py` · `memory.db` | graded write/read؛ namespaces: episodic/semantic/… | LIVE وقتی `OCTOPUS_WIRE_MEMORY_GATE=1` | خیر — فقط شواهد |
| **Decision retrieval** | `retrieval_router.py` | narrowing/veto از `owner_fact`؛ citation | LIVE با `OCTOPUS_WIRE_MEMORY_DECISION` | veto فقط از owner_fact ثبت‌شده |
| **Web research digest** | `state/pulse/research-latest.json` | آخرین دایجست API ($0 DDG/Wiki/arXiv) | LIVE با `OCTOPUS_WIRE_WEB_RESEARCH` | خیر |
| **Research ingest trail** | `state/memory/research-ingest.jsonl` | append-only provenance هر hit | LIVE (پس از هر persist موفق) | خیر |
| **Self-loop ingest trail** | `state/memory/self-loop-ingest.jsonl` | improve/synthesis/self_knowledge/part_loops/selfheal/self_model | LIVE پس از هر persist | خیر |
| **upgrades-digest** | `state/cortex/upgrades-digest.json` | پیشنهادهای خودترمیمی (overwrite) | LIVE | propose / auto-knob فقط با flag |
| **self-knowledge** | `state/doctor/self-knowledge-latest.json` + history jsonl | خودآگاهی دکتر؛ `smallest_fix` | LIVE با wire doctor | خیر — propose-only |
| **part-loops** | `state/cortex/part-loops-latest.json` | اتوماسیون لوپِ هر بخش | LIVE | auto فقط با ACT_AUTO + whitelist |
| **selfheal-events** | `state/selfheal-events.jsonl` | ری‌استارت اندام (append) | LIVE با `OCTOPUS_WIRE_SELFHEAL` | restart leg فقط؛ نه APPLY neural |
| **Discoveries pulse** | `discoveries.record` | جملهٔ فارسی خانه/نوتیف | LIVE (fail-soft) | خیر |
| **Cortex semantic consolidate** | cortex consolidate paths | خلاصه/سنتز | LIVE جزئی | خیر |
| **Neural Hebbian/BCM** | `_ops/neural/*` | وزن + PainAssessment dual-mode | ARMED APPLY=1 (ADR-035) | فقط `protective_skip` beat-local وقتی executable؛ نه EXTERNAL_SEND |
| **Collab episodic** | collaborator paths | تجربهٔ گفتگو | محدود؛ Talk PolicyGate | semantic write از collab ممنوع |
| **Genome ledger** | `07 - Knowledge/genome-system/ledger` | ledger دانش | LIVE append | نه برای control |
| **Capability journal** | `CAPABILITY-JOURNAL` / pulse | کشف ساختاری | LIVE خواندنی | arm نیاز به owner |

## جریان یادگیری از API (ضدِ گم‌شدن)

```
heart/work_pump یا caller
  → web_research.run_and_persist (egress فقط اگر flag on)
  → research-latest.json (atomic)
  → discoveries.record (دیده‌شدن)
  → memory.research_ingest.ingest_digest (MemoryGate episodic + jsonl)
  → improve.gather_signals می‌تواند recall_recent بخواند
```

## جریان خودآگاهی / خودترمیمی / اتوماسیون (ضدِ orphan)

```
self_model / self_knowledge / part_loops / synthesis / improve / chrono.selfheal
  → *-latest.json (UI pulse، ممکن است overwrite شود)
  → memory.self_loop_ingest (channel مناسب) → self-loop-ingest.jsonl + episodic
  → improve.gather_signals.self_loop_memory → generate_proposals (propose-only)
```

کانال‌ها: `improve` · `synthesis` · `self_knowledge` · `part_loops` · `selfheal` · `self_model`

قواعد:
1. محتوای خامِ خصوصی/vault وارد query نمی‌شود (sanitize موجود).
2. هر hit: `mkey=research:<sha256>` یا `selfloop:<channel>:<sha>` → dedupe در store.
3. trust episodic = GRADED (auto_scrubbed) — **نه OWNER_CONFIRMED**.
4. هیچ مسیر ingestی `request_protective_halt` / APPLY / EXTERNAL_SEND را صدا نمی‌زند.
5. `ACTIVATION-SELF-IMPROVE-AUTO` فقط knobهای whitelist؛ ingest هرگز auto-apply نمی‌کند.

## مرز اختیار (با Metaphor Decode هم‌تراز)

- استعارهٔ «یادگیری» ≠ قدرت تغییر حالت سیستم.
- سیگنال/حافظه فقط describe / cite / rank.
- عملِ تغییر حالت = PolicyGate + verified state + owner auth + idempotency + audit.

## Ask / Collaborator recall (2026-08-12)

- `memory/owner_recall.recall_for_owner_ask` — cite-only برای همکار و `_self_context`.
- `collaborator.handle` فیلد `data.facts[]` را پر می‌کند (+ خط «شاهد:» در متن وقتی hit باشد).
- خالی → صادق (`facts_rationale=recall خالی`)؛ `may_authorize` همیشه false.
- مسیر Ask خام (`ask_brain`) هنوز MemoryGate مستقیم ندارد؛ collab-fallback و همکار دارند.

## بدهی‌های شناخته‌شده (ننویس به‌عنوان pass)

- دو پشتهٔ consolidate (cortex vs neural) — مستند؛ ادغام بدون ADR ممنوع.
- فیلد shadow `applied` ممکن است خوانش اشتباه بدهد — APPLY واقعی از flag/env است.
- vault_auto_write خارج از Talk PolicyGate — جدا از این نقشه؛ بدون owner arm نکن.
- **2026-08-11:** ingest trails با backfill اولیه روی دیسک آمدند؛ تا controlled reload،
  پروسهٔ organism ممکن است هنوز کد قدیمی بدون hook را اجرا کند — رشد trail را بعد از reload چک کن.
  وضعیت Hearts/4D: `OCTOPUS-HEARTS-BRAINS-4D-STATUS.md`.

## Precedence

اگر این نوت با runtime/registry/ADR تعارض داشت: **runtime + versioned registries برنده**؛ تعارض را ADR/inventory ثبت کن.
