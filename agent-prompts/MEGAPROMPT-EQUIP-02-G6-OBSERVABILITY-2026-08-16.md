---
megaprompt_title: EQUIP موج A2 — گروه ۶ مشاهده‌پذیری (E2E Observability + Evaluation)
version: "1.0"
sequence: 2
group: 6
wave: A
requires: "EQUIP-G2 evidence PASS or CONDITIONAL PASS"
next: "MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md (Wave A)"
scan_after: true
written_by: "Cursor Grok 4.6 — 2026-08-16"
audience: یک ایجنت پیاده‌ساز جدا از گروه ۲
branch_name: "equip/g6-observability-20260816"
---

# پیست

۱) کل SHARED · ۲) کل همین فایل.
پیش‌نیاز: گزارش گروه ۲ در `06-EVIDENCE/EQUIP-G2-MEMORY-2026-08-16.md`.
اگر G2 نیست یا FAIL است، پیاده‌سازی نکن — فقط گزارش مسدود شدن.

# ماموریت: End-to-End Observability and Evaluation

OTLP، Alloy، Grafana، logs، traces، metrics، SOG/DARE telemetry و identity
health موجود را کشف کن.

هدف: یک Trace ID از user intent تا model decision، tool call، policy،
memory access و outcome — بدون secret/PII.

## حقیقت این vault

- MCP فعلی tracer SDK ندارد (`octopus_mcp/server.py` دست‌ساز است).
- `memory_read_patch` رویداد `memory.read` / `memory.readback` با `trace_id` دارد — extend کن، موازی نساز.
- `_ops/cortex/semantic_trace.py` · journal/outcomes در `_ops/state/cortex/`
- SOG/DARE متریک‌های جدا دارند؛ با confidence قاطی نکن (درس IMPROVE-ACF / C-029).
- Grafana/Alloy ممکن است در compose یا docs باشد — discovery اجباری.
- OTLP remote در برخی ADRها off است؛ بدون رأی مالک remote export روشن نکن.

## الزامات vertical slice

- telemetry schema versioned.
- `trace_id` در handoff، queue، tool call حفظ شود.
- spanهای جدا: model / retrieval / policy / tool / approval / memory.
- latency، error rate، retry، token، cost، task outcome.
- `decision_reason` خلاصهٔ قابل‌حسابرسی — نه chain-of-thought خام.
- PII/secrets قبل از export redact.
- dashboard حداقل: health / safety / memory / workflow — اگر Grafana نیست،
  یک digest فایل + query قابل‌بازتولید کافی است (UI کامل اجباری نیست).
- alert برای: retry storm، denied action، kill switch، memory poisoning،
  identity-health regression — ابتدا به فایل alert موجود
  (`_ops/governor/governor-alerts.md` یا معادل) نه SaaS جدید.
- trace replay برای یک workflow واقعی.
- evaluation dataset + baseline versioned.
- SOG، calibration، entropy = متریک‌های مجزا.

## سناریوی acceptance

یک مأموریت end-to-end (ترجیحاً همان hypothesis G2) اجرا کن و با یک Trace ID
همهٔ handoffها، policy decisions، memory reads و tool calls را بازیابی کن.

## اسکن تخصصی

missing spans · broken context propagation · high-cardinality labels ·
secret/PII leakage · incorrect success metrics · silent failures ·
sampling blind spots · dashboard/query drift · unbounded telemetry storage.

## TECHNOLOGY OPTIONS — GROUP 6

تحقیق جدا 2026-08-16.

PRIMARY:

- MCP Python SDK v2.0.0 OpenTelemetry **پیش‌فرض ON** — اگر MCP را لمس می‌کنی
  از همین استفاده کن؛ tracer دوم نساز.
  https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0
- OpenTelemetry GenAI: در **v1.42.0** (2026-06-12) همهٔ `gen_ai.*` از repo
  اصلی خارج و به https://github.com/open-telemetry/semantic-conventions-genai
  منتقل شد. وضعیت spanها (`invoke_agent`, `execute_tool`, `chat`, `retrieve`,
  `validate`) هنوز **Development** است — پایدار رسمی نیست.
  منبع: https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.42.0
  https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/
- `gen_ai.conversation.id` را ثبت کن (در نسخهٔ فعلی اغلب conditionally required).
- namespace رسمی `gen_ai.memory.*` / `gen_ai.team.*` تصویب نشده — schema داخلی
  Octopus برای memory/policy بساز و version کن.
- OWASP Agent Observability Standard (AOS): instrumentable / traceable /
  inspectable (AgBOM). https://aos.owasp.org/aos/
  Guardian Agent را authority نکن؛ hookهای deny را به NBB-CP/PolicyGate وصل کن.
- agent-inspect — https://github.com/rajudandigam/agent-inspect
  (execution trees محلی). فقط اگر gap در replay داری.
- MCPJam inspector — https://github.com/MCPJam/inspector
- LangGraph 1.2.11 `trace_policy` per node (#8523) — فقط اگر LangGraph از
  قبل در tree است.
- Langfuse / Tempo+Loki+Grafana — backend جدید فقط با justification.
  OTLP remote را بی‌رأی روشن نکن.

PAPERS:

- LongHorizon-Harness 2608.01964 — audit loop **بیرون** context.
  https://huggingface.co/papers/2608.01964
- Mechanist 2608.12036 — diagnostic only.

DO

- یک Trace ID از intent → policy → memory → tool → outcome.
- redaction قبل از export. SOG/entropy/confidence جدا.

DO NOT

- raw CoT لاگ نکن. diagnostic span را decision نکن.
- «v1.42 official stable GenAI» ادعا نکن — استخراج شده، هنوز development.

## خروجی

`06-EVIDENCE/EQUIP-G6-OBSERVABILITY-2026-08-16.md`. merge نکن.
پس از این گروه، مالک اسکن Wave A را به ایجنت **مستقل** می‌دهد.
