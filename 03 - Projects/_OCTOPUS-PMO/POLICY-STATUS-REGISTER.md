# Policy Status Register

> هدف: جداسازی active/draft/historical/superseded. این فایل policy جدید ایجاد نمی‌کند.

| Policy/موضوع | وضعیت | authority/source | effective date | یادداشت |
|---|---|---|---|---|
| Human sovereignty / external hard gates | active | `RISK-LADDER.md`, owner context | 2026-07-11 baseline | publish/send/spend/trade/lodge/pay/create-account/deploy نیازمند verdict |
| Security Gate rotation | active: LIFTED | `ARCHITECT-ORGANISM-CONTEXT.md` به نقل از Brain/HANDOFF و owner verdict | 2026-07-06 | secret rules و hard gates همچنان فعال |
| README: Security Gate closed | historical/conflicting | `README.md` | snapshot قدیمی | retained; operationally superseded by context بالا |
| Per-tenant manifests: gate closed | historical status fields | tenant `MANIFEST.yaml`ها | 2026-07-11 extraction | باید در sync pass بعدی به historical marker تبدیل شوند؛ فعلاً قراردادهای locked rules حفظ |
| Risk Ladder چهاررنگ | draft baseline pending | `RISK-LADDER.md` | pending VQ-ROOT-003 | Green/Yellow فعلاً مجاز؛ Orange/Red proposal-only |
| Registry Alignment | draft baseline pending | `REGISTRY-ALIGNMENT.md` | pending VQ-ROOT-003 | NBB row باید shadow-only شود |
| NBB relation | active architecture decision | owner conversation, VQ-ROOT-001=A | 2026-07-12 | Portable sibling, non-binding, no mutation |
| Project-F containment | active | project control manifest + root context | 2026-07-10 | بیرون پوشه فقط alias و status/gate |
| 4D autonomous run | inactive/pending | 4D verdict queue | — | readiness review + owner verdict لازم |
| VaultScanner workspace scan | inactive/pending | VQ-MAP-001 | — | CLI contract فعلی با runbook ناسازگار است |

## Conflict rule
- تاریخ حذف نمی‌شود.
- تصمیم دارای authority و effective date، سند قدیمی را operationally supersede می‌کند.
- اگر authority نامعلوم بود: status=`unverified` و automation متوقف.
