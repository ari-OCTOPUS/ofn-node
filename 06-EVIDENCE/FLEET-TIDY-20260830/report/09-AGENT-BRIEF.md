# 09 — بریف ایجنت همکار (ماشین‌خوان)

```yaml
agent_brief:
  schema: octopus-agent-brief/1
  generated: 2026-08-30
  repository: ari-OCTOPUS/ofn-node
  canonical:
    main_sha: c1969bce5384f3371b916470299c991627c3d63c
    baseline_tests: {collected: 2136, passed: 2131, failed: 0, errors: 0, skipped: 5, runner: "pytest>=8"}
  protected_branches:
    - backup/board138-20260830@c1969bce
    - backup/board180-20260830@28209eff
    - backup/board182-20260830@294d51c1
    policy: immutable — هیچ push/merge/delete/rewrite مجاز نیست؛ انحراف = توقف فوری
  workflow:
    branch_from: main (یا SHA کانونیکال)
    branch_naming: "work/<task>-<yyyymmdd>"
    commit_rules:
      - "git add انتخابی؛ هرگز add -A بدون بازبینی diff --cached"
      - "ممنوع در commit: *.db* *.log *.jsonl .env* tokens receipts/ inbox/ outbox/ state/ runtime/ داده مشتری PII"
      - "secret scan قبل از commit — هر hit واقعی = STOP"
    delivery: "PR به main — نه push مستقیم"
  hard_forbidden:
    - force push / rebase / reset --hard / git clean / حذف شاخه یا تگ
    - merge در main بدون PR و مجوز
    - restart/deploy/سرویس systemd روی بردها
    - خواندن یا انتقال رازها؛ چاپ محتوای .env
    - پیام به انسان‌ها (تلگرام/ایمیل)
    - ساخت repo/remote جدید بدون مالک
  live_hosts:
    - {node: 138, ssh: "ari@192.168.0.138", criticality: production, rule: "فقط-خواندنی مگر با مجوز"}
    - {node: 180, ssh: "root@192.168.0.180", criticality: production}
    - {node: 182, ssh: "root@192.168.0.182", criticality: production}
  verification_culture:
    - "هر عدد از فایل خام در 06-EVIDENCE/FLEET-TIDY-20260830/raw"
    - "اثبات‌نشده = NOT_VERIFIED"
  open_items: "06-EVIDENCE/FLEET-TIDY-20260830/report/07-OWNER-DECISIONS.md"
```

## الحاقیهٔ اسکنر (حکم مالک 2026-08-30)
```yaml
secret_scanner_regex_v2:
  positive:
    - '\.(db|sqlite3?|log|env|pem|key)$'
    - '(^|/)(evidence|receipts|inbox|outbox|state|runtime)/[^/]*\.(json|jsonl|txt|log|db)$'
  negative_exceptions:
    - '(^|/)(evidence|runtime)/[^/]*\.py$'
    - 'هر مسیری داخل بسته دارای __init__.py'
  policy:
    BACKUP_BRANCHES: immutable_no_cleanup_ever
    CLEANUP_TARGET: "new branch from current HEAD (git rm --cached + .gitignore)"
    FORBIDDEN: history rewrite (secrets=0)
  gating:
    P4_BOARD182_TEST_DISCOVERY_INIT: "blocked until main ruleset active"
    P5_UNTRACK_RUNTIME_ARTIFACTS: "blocked until main ruleset active (file: patch-proposals/P5-...patch)"
  baseline_manifest: "BASELINE-MANIFEST-TEMPLATE.txt اجباری برای هر اجرای تست؛ شمارش بدون env-manifest معتبر نیست"
```
