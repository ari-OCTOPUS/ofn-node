---
megaprompt_title: EQUIP موج A1 — گروه ۲ حافظه (Trusted Read-Write Memory Loop)
version: "1.0"
sequence: 1
group: 2
wave: A
next: "MEGAPROMPT-EQUIP-02-G6-OBSERVABILITY-2026-08-16.md"
scan_after: false
written_by: "Cursor Grok 4.6 — 2026-08-16"
audience: یک ایجنت پیاده‌ساز — فقط این گروه
branch_name: "equip/g2-memory-20260816"
---

# پیست

۱) کل `agent-prompts/MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16.md`
۲) سپس کل همین فایل.
اگر فقط همین فایل را گرفتی، اول SHARED را از دیسک بخوان.

ترتیب برنامه: **۲ → ۶ → ۷ → ۸ → ۱ → ۳ → ۴ → ۵ → ۹ → ۱۰**. تو اولی هستی. گروه دیگر را هم‌زمان اجرا نکن.

# ماموریت: Trusted Read-Write Memory Loop

تمام مسیرهای حافظهٔ OCTOPUS را کشف کن. هدف حلقهٔ واقعی:

`observe → retrieve → reason → propose → verify → write → retrieve-back`

نه «ابزار حافظهٔ بیشتر». اول حلقه را ببند.

## حقیقت این vault (2026-08-16) — از اینجا شروع کن

C-012 **فاز صفر resolved است**. `4d_system/brain/automation.py` دیگر write-only نیست:
introspect/create/conclude قبل از تصمیم می‌خوانند؛ dedup؛ read-back؛
`memory_read_before_decision_ratio=1.0` در شاهد 2026-08-15.
نکن: همان فیکس را از نو بنویس.
بکن: Write Gate + provenance + TTL/decay + contradiction (بدون حذف خودکار)
+ hybrid retrieve که از مسیر production برگردد.

مسیرهای اجباری کشف:

- `4d_system/brain/automation.py` — `save_hypothesis` / `save_experiment` / conclude
- `4d_system/brain/memory_read_patch.py` — read/readback/stale/telemetry
- `_ops/memory/retrieval_router.py` + vault RAG (`search_vault_evidence`)
- `_ops/cortex/semantic_trace.py`
- ADR-012 (اینجا = retention policy، INTEGRATE) · ADR-018 multimetric memory
- `04-SYSTEMS/MEMORY-LOOP.md`
- صف ~۱۰۶۲ فرضیهٔ pending: **پاک نکن** (append-only)
- OWNER-PENDING VOTE 1 هنوز باز است: ستون provenance قبل از ورود بیرونی

## الزامات vertical slice

- source of truth هر نوع حافظه را با path بنویس (short-term / episodic /
  semantic / procedural / owner-rule).
- هر record: schema version، source، timestamp، confidence، evidence ref،
  writer agent، content hash.
- مدل حق ندارد مستقیم به long-term بنویسد. Memory Write Gate:
  validate → deduplicate → provenance → quarantine.
- tool/web/prompt خارجی = untrusted.
- hybrid retrieval: lexical (موجود: rg در MCP / BM25 اگر هست) + semantic
  (موجود: vault RAG/Chroma — دوباره Qdrant نساز مگر gap اثبات شود).
- retrieval باید source + freshness برگرداند.
- TTL / decay / superseded / revoked. تعارض را detect کن، خودکار حذف نکن.
- read-after-write test اجباری، با restart process.
- Obsidian Vault authoritative فقط در حوزه‌های configured.
- owner-signed > model memory.

## سناریوی acceptance

یک hypothesis تستی ذخیره کن → process را restart کن → از مسیر production
بازیابی کن → conclude کن → ثابت کن evidence chain و content hash در همهٔ
مراحل یکسان مانده‌اند. مسیر write بدون Gate باید رد و audit شود.

## اسکن تخصصی این گروه

write-only memory · unreachable retrieval · stale embedding · cross-user
leakage · memory poisoning · forged provenance · duplicate records ·
schema drift · vector/metadata inconsistency · deletion/revocation failure.

## TECHNOLOGY OPTIONS — GROUP 2

تحقیق جدا 2026-08-16 (صفحات عمومی GitHub/arXiv/HF). همه را نصب نکن.

PRIMARY (الگو / کتابخانه — نه authority):

- MemOS / MemTensor — https://github.com/MemTensor/MemOS
  مقاله: https://arxiv.org/abs/2507.03724
  hybrid retrieve + MemCube + conflict/dedup/versioning/forgetting.
  **نباید owner rules را بنویسد.**
- kremis — https://github.com/TyKolt/kremis
  گراف قطعی Rust؛ record/associate/retrieve؛ هرگز invent نمی‌کند؛
  BLAKE3 روی state. مناسب لایهٔ grounded facts کنار vault.
- memo (اگر در discovery پیدا شد: Markdown SoT + sqlite-vec + contradiction
  radar) — فقط اگر با Obsidian این vault جور است.

PAPERS:

- EverMemOS 2601.02163 · Mem0 2504.19413 · Zep 2501.13956
- AutoMem 2607.01224 (memory as trainable skill — quarantine first)
- SAM 2605.24468 · AMA-Bench 2602.22769

DO

- SoT بماند Postgres/SQLite موجود + Obsidian. hybrid retrieve + contradiction
  radar + read-after-write. Write Gate اجباری.
- VOTE 1 مالک (provenance) را با این slice هم‌راستا کن؛ enforce تلگرام PEP را
  روشن نکن.

DO NOT

- MemOS/self-evolving memory را به NBB-CP یا owner rules وصل نکن.
- Skill distillation خام را long-term نکن (SkillEvolBench: raw traces often
  بهتر از skill تقطیرشده).
- Qdrant/Weaviate/Milvus را اگر Chroma/pgvector/SQLite موجود است، اضافه نکن
  مگر مقیاس اثبات‌شده.

## خروجی

`06-EVIDENCE/EQUIP-G2-MEMORY-2026-08-16.md` + تست نام‌یکتا در `_ops/tests/`
یا `4d_system/tests/` (ثبت در `run_all.py` ممنوع). merge نکن.
بعد از PASS مشروط، مالک گروه ۶ را به ایجنت **بعدی** می‌دهد.
