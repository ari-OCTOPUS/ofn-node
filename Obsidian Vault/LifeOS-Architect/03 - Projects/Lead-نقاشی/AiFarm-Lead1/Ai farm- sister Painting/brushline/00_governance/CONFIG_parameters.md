# CONFIG — Parameters (تک‌منبعِ پارامترها)

> WP-G1. هر پارامتری که در KBها پراکنده ارجاع می‌شد، اینجا تک‌منبع است. **هیچ‌جای دیگر hard-code نشود.** مقادیر = پیش‌فرضِ پیشنهادی؛ Operator نهایی می‌کند.

---

## ۱. مالی (KB-02)
| پارامتر | پیش‌فرض | واحد | منبع/وضعیت |
|---|---|---|---|
| `fx_aud_usd` | ۱٫۵۵ | AUD per USD | **verify روز** |
| `spend_cap_per_action` | (Operator) | AUD | INV-3 |
| `spend_cap_per_day` | (Operator) | AUD | INV-3 |
| `model_routing_map` | ساده→Haiku 4.5؛ کلیدی→Sonnet 4.6؛ Opus خاموش (MVP) | — | KB-01/02 |
| `batch_enabled` | true (غیر-فوری) | bool | KB-02 |
| `cache_enabled` | true (KB context) | bool | KB-02 |

## ۲. SLA صف (KB-05)
| پارامتر | پیش‌فرض | منبع |
|---|---|---|
| `sla_lead` | ۱۵ دقیقه | speed-to-lead |
| `sla_review_neg` | ۲ ساعت | شهرت |
| `sla_followup` | per-stage (روز ۲/۵/۱۰) | KB-09 |
| `sla_content` | ۲۴–۴۸ ساعت | — |
| `material_edit_threshold` | تغییرِ ادعا/متنِ تجاری → REGATE | KB-05/07 |

## ۳. انطباق (KB-03/07/09/12)
| پارامتر | پیش‌فرض | وضعیت |
|---|---|---|
| `sender_id_abn_template` | `[Business name] · ABN [..] · unsubscribe: [link]` | KB-03 |
| `unsubscribe_window` | ۵ روز | Spam Act |
| `gate_max_rounds` | ۳ | KB-07 |
| `spam_penalty_units` | — | **verify** |
| `consent_methods` | express, inferred(رابطهٔ تجاری) | KB-09 |

## ۴. memory (KB-04)
| پارامتر | پیش‌فرض |
|---|---|
| `memory_scope` | per-lead / per-task |
| `memory_pii_allowed` | false (INV-2) |
| `memory_ttl` | برچسبِ freshness روی market data |

## ۵. audit / retention (KB-06)
| پارامتر | پیش‌فرض |
|---|---|
| `hash_algo` | (تعریفِ فنی فاز ۳) |
| `retention_consent` | مطابق Spam Act |
| `pii_storage` | hash/ارجاعِ امن فقط |

## ۶. eval (KB-08)
| پارامتر | پیش‌فرض |
|---|---|
| `ab_method` | Wilson lower-bound |
| `anomaly_thresholds` | هزینه/کنشِ خارج از محدوده (Operator) |
| `north_metric` | cost-per-booked-job (AUD) |

> قاعده: تغییرِ هر پارامتر فقط اینجا؛ KBها به CONFIG ارجاع می‌دهند، نه برعکس.
