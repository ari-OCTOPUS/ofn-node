---
megaprompt_title: EQUIP موج B1 — گروه ۷ هویت و امنیت (Zero-Trust Agent/Tool)
version: "1.0"
sequence: 3
group: 7
wave: B
requires: "Wave A SCAN not FAIL"
next: "MEGAPROMPT-EQUIP-04-G8-CONTAINMENT-2026-08-16.md"
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g7-identity-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
پیش‌نیاز: Wave A (G2+G6) اسکن‌شده و FAIL نیست.

# ماموریت: Zero-Trust Agent and Tool Security

هویت user / agent / service / tool، MCP servers، service accounts، tokens و
policy enforcement points را map کن.

هدف: هر agent فقط کمترین capability لازم برای task فعلی را، برای مدت محدود،
بگیرد. کشف ابزار ≠ مجوز.

## حقیقت این vault

- MCP: ۵ ابزار، deny-by-default با `.agentignore` + `_HARD_DENY`؛ فقدان
  `.agentignore` = fail-closed. CONSTITUTION.md را نقض نکن.
- owner auth روی برخی HTTP (مثلاً conversation hub 403 بدون auth).
- Ed25519 مالک برای TCB و برخی APIها (NBB-V4). کلید را چاپ نکن.
- SPIFFE/Keycloak ممکن است **موجود نباشند** — نساز مگر gap + رأی.
  حداقل slice: جدا کردن authentication از authorization روی مسیر tool موجود.

## الزامات vertical slice

- identity مستقل: user، agent، service، tool.
- deny-by-default. RBAC برای نقش + ABAC برای context/risk.
- capability token محدود به action + resource + duration + Task ID.
- token reuse و confused-deputy را کنترل کن.
- MCP tool discovery خودکار به permission تبدیل نشود.
- tool arguments قبل از اجرا policy-check؛ tool output قبل از ورود به مدل اسکن.
- mTLS یا معادل معتبر را بررسی کن (اجباری نیست اگر stack محلی است؛ gap را ثبت کن).
- secret rotation + revocation path (بدون چرخاندن secret واقعی مگر مالک بگوید).
- همهٔ deny و escalation attemptها audit شوند.

## سناریوی acceptance

یک worker با مجوز read را وادار به write آزمایشی کن. درخواست باید **قبل از
رسیدن به tool** رد شود و policy decision قابل‌ردیابی بسازد.

## اسکن تخصصی

privilege escalation · confused deputy · token replay · overbroad scopes ·
unauthenticated MCP · cross-agent impersonation · policy bypass ·
insecure defaults · stale credentials · unauthorized tool discovery.

## TECHNOLOGY OPTIONS — GROUP 7

تحقیق جدا 2026-08-16.

PRIMARY:

- MCP v2 SEP-990 identity-assertion + RFC 9207 `iss`. jwt-bearer/DPoP در
  SDK v2.0.0 **پیاده نشده** — جعل نکن.
  https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0
- IETF AIMS — مفهوم نه محصول. آخرین پیش‌نویس را از datatracker بخوان
  (`draft-klrc-aiagent-auth`؛ در 2026-08 نسخه‌های 00..03 دیده شد، **بدون
  IETF consensus**).
  https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/
  لایهٔ هویت: SPIFFE SVID = «این فرآیند کدام agent است».
  OAuth access token = «از طرف کدام user با چه scope».
  static API key = antipattern صریح پیش‌نویس.
- scanners (CI، نه runtime authority):
  Snyk Agent Scan / mcp-scan · MCPShield · AgentAuditKit (SARIF) ·
  MCPhound برای مرور هفتگی. فقط اگر به pipeline موجود می‌چسبند.
- الگوها (نصب همه ممنوع): authsec-ai/authsec · AgentValet ·
  clayseal-identity · Policy_Enforced_AI_Agent_Platform
  (Keycloak+SPIRE+OPA+hash-chain) — فقط اگر Octopus هویت سرویسی ندارد
  و مالک SPIRE می‌خواهد. برای slice اول: policy روی `propose_action` و
  tool args کافی است.

DO

- جدا کن «who is the agent» از «on whose behalf».
- capability tokens bound to Task ID. deny-by-default.

DO NOT

- MCP discovery → permission. کلید API بلندمدت برای agent.
- Keycloak/SPIRE را برای یک لپ‌تاپ شخصی بدون justification عملیاتی اضافه نکن.

## خروجی

`06-EVIDENCE/EQUIP-G7-IDENTITY-2026-08-16.md`. merge نکن.
