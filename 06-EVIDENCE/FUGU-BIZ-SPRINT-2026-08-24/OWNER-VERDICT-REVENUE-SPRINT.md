# OWNER VERDICT — 72-HOUR REVENUE COMPLETION SPRINT
Locked: 2026-08-24 AEST
Deadline: 2026-08-27 (Max period end)
Engine now: Sakana Fugu | Future: DeepSeek V4 Flash via gateway only

Budget: Ziman 38% | Studio 24% | Painting 19% | Lab 14% | Reserve 5%
Lab may not become the main project; same-day consume by >=2 businesses.

Success (runtime truth, not file count):
- Ziman: catalog ready + checkout E2E + first-paid-order readiness (metric paid_order_count)
- Painting: lead→quote→invoice/deposit path (deposit_or_invoice_sent_count, paid_deposit_count)
- Studio: caption queue + TG receipt + OF behind gates (approved_publish_count)
- Lab: provider-agnostic gateway + eval + swap path (model_swap_pass_rate, cost_per_successful_task)
- Octopus: minimal cockpit of queues/errors/revenue/GOs/receipts

Live GO always required for: Shopify mutate, outbound send, TG/OF publish, LIVE/ARM, credentials, spend, price, refund, live merge/restart, external writes.
