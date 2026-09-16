# Changelog

## 0.1.0 (unreleased) — MVP, cloud build session 2026-07-19

- Research: ATO tax-invoice requirements, ABN checksum, GST rounding law,
  record keeping; package health audit (sources + access dates logged).
- Financial engine design validated by execution (Python mirror, 36 cases).
- Architecture: drift schema v1, snapshot-on-issue lifecycle, backup format
  v1, senior-friendly UX plan.
- Implementation: core engine, database, repositories, onboarding,
  customers, quick quote/invoice flow, PDF, sharing (Telegram/share sheet,
  Gmail compose), payments, dashboard, backup/restore, optional AI
  message improvement (off by default).
- Docs: user guide (senior), build & release guide, compliance notes,
  security/privacy, integration notes, tests plan.
- Not compiled in the cloud workspace (toolchain firewalled) — first-build
  steps in docs/BUILD_AND_RELEASE.md.
