"""
control_plane — سطحِ واحدِ حاکمیتِ runtime (observe-only در v1).

دکترین: «تمرکزِ کنترل، نه تمرکزِ هوش.»
  • هوش/reasoning/autonomy داخلِ ماژول‌ها (brain/…) می‌ماند — black box محفوظ است.
  • authority/policy/observability/audit/approval/kill-switch این‌جا متمرکز می‌شود.

v1 (این نسخه): فقط «دیدن» — registry + snapshot + channel doctor + policy ladder
(به‌صورتِ داده، نه enforcement). هیچ مسیرِ کدی در این پکیج رفتارِ live را تغییر
نمی‌دهد؛ همه‌ی flagهای live پیش‌فرض خاموش‌اند (control_plane.flags).

نقشه‌ی نسخه‌ها (additive):
  v1 observe-only → v2 shadow policy → v3 approvals برای high-risk →
  v4 pause/resume/kill (روی قراردادِ موجودِ daemon.pause/daemon.stop) → v5 multi-project.

این پکیج به TCB دست نمی‌زند و هرگز .env/secrets را نمی‌خواند.
"""
from __future__ import annotations

__version__ = "0.1.0"  # v1: observe-only

SCHEMA_VERSION = 1
