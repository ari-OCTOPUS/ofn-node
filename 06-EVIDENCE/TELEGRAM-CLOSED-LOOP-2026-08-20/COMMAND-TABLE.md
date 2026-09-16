---
type: evidence
status: active
tags: [telegram, a2, firewall, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# A2 — جدول فرمان محلی

همه `model_allowed: false` · `owner_only: true`. `model_fn` اگر صدا شود تست می‌ترکد.

```yaml
- command: /status
  local_handler: status_text
  reads_memory: true
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-status
  aliases: [/وضعیت]
- command: /health
  local_handler: status_text
  reads_memory: true
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-health
  aliases: [/سلامت]
- command: /memory
  local_handler: memory_text
  reads_memory: true
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-memory
  aliases: [/حافظه]
- command: /help
  local_handler: help_text
  reads_memory: false
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-help
  aliases: [/راهنما]
- command: /capabilities
  local_handler: capabilities_text
  reads_memory: false
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-capabilities
- command: /remember
  local_handler: _remember
  reads_memory: false
  writes_memory: true
  model_allowed: false
  owner_only: true
  expected_receipt: local-remember
- command: /good
  local_handler: _feedback
  reads_memory: false
  writes_memory: true
  model_allowed: false
  owner_only: true
  expected_receipt: local-feedback
- command: /bad
  local_handler: _feedback
  reads_memory: false
  writes_memory: true
  model_allowed: false
  owner_only: true
  expected_receipt: local-feedback
- command: /correct
  local_handler: _feedback
  reads_memory: false
  writes_memory: true
  model_allowed: false
  owner_only: true
  expected_receipt: local-feedback
- command: /stop
  local_handler: _stop
  reads_memory: false
  writes_memory: true
  model_allowed: false
  owner_only: true
  expected_receipt: local-stop
  aliases: [/توقف]
  persist: _ops/state/telegram/owner-stop.flag
- command: /resume
  local_handler: _resume
  reads_memory: false
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-resume
  aliases: [/ادامه]
- command: /why
  local_handler: _why
  reads_memory: true
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-why
  aliases: [/چرا]
- command: /<unknown>
  local_handler: local-help
  reads_memory: false
  writes_memory: false
  model_allowed: false
  owner_only: true
  expected_receipt: local-help
  note: never model fallback
```

تست: فارسی/انگلیسی، whitespace، `/status@bot`، فرمان ناشناخته → راهنما.
