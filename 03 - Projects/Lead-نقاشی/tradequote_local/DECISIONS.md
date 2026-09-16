# Decisions log

Short decisions not big enough for a full ADR. (ADR-001 = tech stack.)

- **D-001 Money**: integer AUD cents everywhere; quantities integer
  thousandths (`quantityMilli`); half-up integer rounding. Validated by
  execution: `tool/validate_financial_logic.py` (36/36 PASS, 2026-07-19).
- **D-002 No freezed/json_serializable**: hand-written immutable models +
  toJson/fromJson. Rationale: minimize generated surface since the cloud
  workspace cannot run codegen/compile; drift is the only codegen.
- **D-003 GST method**: total-invoice method (sum taxable line totals, round
  GST once, half-up) — permitted by GST Act s 9-90; simplest to reconcile on
  the printed page. Per-line `gstApplicable` supported; per-line GST amounts
  are not separately rounded.
- **D-004 Numbering**: allocated transactionally when the document row is
  created; unique DB constraint; never reused after void/cancel; gaps from
  abandoned drafts acceptable (no gapless requirement found in ATO guidance
  — see RESEARCH_REPORT §5). Prefix from settings at allocation time.
- **D-005 Issued-document edits**: blocked. Corrections via void+reissue or
  duplicate-as-draft. Matches record-alteration expectations (ATO record
  keeping) and keeps history honest.
- **D-006 One navigation system**: Simple Mode is the default surface;
  "Advanced" only reveals extra Settings entries and detailed editors. Two
  parallel navigation trees were rejected as a reliability risk.
- **D-007 Overpayment**: blocked with a clear message ("This is more than
  the amount owing"). The user can still record up to the balance and note
  the excess in payment notes. Refund/credit workflow = future.
- **D-008 Timestamps**: epoch milliseconds UTC in DB; formatted Australian
  style (dd/MM/yyyy) at display via intl with `en_AU`.
- **D-009 PDF fonts**: pdf package base-14 Helvetica (no embedding) for the
  English-only MVP — zero network/asset risk. Embedding a TTF (and Persian
  support) is documented as a follow-up in FUTURE_EXTENSIONS.md.
- **D-010 Telegram**: via the system share sheet (share_plus 13), not a
  hard-coded Telegram package intent — robust across Telegram variants and
  honest about what Android allows. Button copy tells the user to tap
  Telegram in the sheet.
- **D-011 Gmail**: "Prepare in Gmail" = intent-based compose with
  recipient/subject/body/PDF via flutter_email_sender, share-sheet fallback.
  True Gmail-API drafts: future optional online feature only
  (docs/integrations/GMAIL_COMPOSE.md).
- **D-012 AI (per owner's answer 2026-07-19)**: owner has a real AI API
  ("Fugu"); endpoint/key/model are entered in Settings at runtime, stored in
  flutter_secure_storage, OFF by default. MVP ships ONE AI feature (message
  improvement) behind the toggle, OpenAI-compatible `POST /chat/completions`
  adapter, review-before-apply, graceful offline fallback. Core app is 100%
  functional with AI off/unreachable.
- **D-013 Drafts**: entering the quick flow creates a real draft row after
  the customer step (enables crash recovery + "Continue where you left
  off"); abandoned drafts are listed and deletable; deleting a draft leaves
  a number gap (see D-004).
- **D-014 Platform folders**: android/ etc. are generated on the build
  machine via `flutter create .` so Gradle/AGP always match the installed
  Flutter; the repo carries only Dart code, assets and docs from the cloud
  workspace. Exact steps in docs/BUILD_AND_RELEASE.md.
