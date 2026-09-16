---
megaprompt_title: EQUIP موج D2 — گروه ۵ زیرساخت خودترمیم
version: "1.0"
sequence: 8
group: 5
wave: D
requires: "G4 evidence not FAIL"
next: "MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md (Wave D)"
scan_after: true
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g5-infra-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
deployment production اجرا نکن. فقط dry-run و محیط disposable.

# ماموریت: Reproducible and Self-Recovering Runtime

Docker/Compose، deployment scripts، env، volumes، networks، health checks،
startup order و backupها را بررسی کن.

هدف: runtime از صفر تکرارپذیر بالا بیاید، خرابی جزئی را بازیابی کند،
data loss یا secret leakage نسازد.

## حقیقت این vault

- پنج پروسهٔ زنده با `RESTART-PROCESS.ps1` و watchdogهای ویندوز.
- `_ops/octopus_mcp/server.py` stdio — اگر MCP SDK می‌آید، اینجا health
  vs readiness را جدا کن؛ session Redis برای MCP لازم نیست (spec stateless).
- secrets در `OCTOPUS-flags.cmd` (ignored). در log/dump نیاور.
- backup: restic اگر هست ارزیابی کن؛ وگرنا restore test روی کپی disposable
  از یک volume غیرحیاتی.
- image tag شناور (`:latest`) را در slice خودت pin کن؛ کل stack را یک‌شبه
  به K8s نبر.

## الزامات vertical slice

- service inventory + dependency graph.
- health ≠ readiness ≠ liveness.
- startup روی readiness واقعی.
- configuration schema-validate (Pydantic Settings اگر موجود).
- CPU/RAM/disk/process/network limit حداقل برای سرویس غیرحیاتی.
- volume ownership + retention.
- backup رمزنگاری‌شده + restore test در محیط disposable.
- graceful shutdown + drain queue.
- migration versioned و reversible؛ preflight.
- feature flag برای قابلیت نو.
- deploy فقط dry-run.

## سناریوی acceptance

یک سرویس **غیرحیاتی** را terminate کن (نه organism زندهٔ مالک مگر اجازه).
نشان بده بدون cascade بازیابی می‌شود. backup آزمایشی را restore و integrity
چک کن.

## اسکن تخصصی

privileged container · exposed port · mutable image tag · writable root FS ·
leaked env vars · missing resource limits · unhealthy dependency loop ·
destructive migration · untested backup · insecure volume permissions.

## TECHNOLOGY OPTIONS — GROUP 5

تحقیق جدا 2026-08-16.

PRIMARY:

- MCP Python SDK v2.0.0 — اگر مهاجرت MCP در این موج است:
  stateless، `MCPServer`، OTel default، Resolve(fn)، RFC 9207، SEP-990.
  نه SEP-2663/DPoP/jwt-bearer.
  https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0
  https://py.sdk.modelcontextprotocol.io/migration/
- Docker Compose موجود را محکم کن قبل از Kubernetes.
- Terraform/OpenTofu / Ansible / Vault — فقط اگر از قبل در عملیات هستند.
- Temporal Alpine 3.23.5 اگر Temporal آمد (گروه ۱).
- bex / aegra به‌عنوان PaaS جایگزین LangGraph Cloud — **نصب پیش‌فرض نه**؛
  Octopus روی ویندوز+پروسه‌های محلی است.
- OpenFeature برای flag بدون deploy — اگر flagهای `OCTOPUS-flags.cmd` را
  schema-validate می‌کنی کافی است؛ پلتفرم نو اجباری نیست.
- Trivy برای image/dep scan در CI اگر GitHub Actions موجود است.

DO

- pin images. secrets out of logs. backup restore test.
- health vs readiness split.

DO NOT

- `Mcp-Session-Id` / initialize در کد جدید.
- K8s برای یک نود ویندوزی بدون رأی.
- production deploy.

## خروجی

`06-EVIDENCE/EQUIP-G5-INFRA-2026-08-16.md`.
سپس اسکن Wave D.
