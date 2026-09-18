---
type: lane-output
lane: A
as_of: 2026-09-03T19:20+10
vantage: this_host_only
may_authorize: false
hold_external: true
send: none
---

# R0_BUSINESS_IDENTITY_REPORT — execute pass

This host is the Windows vault (`DESKTOP-KA9RFN5`, Wi-Fi `192.168.0.191`). ofn-node DET path is not on this disk. Values below are **presence** claims. Identity numbers stay in their source files.

```
DET_DRAFT_PATH = docs/lanes/ECONOMIC-LEARNING/DRAFT-REPLY-det-nsw-2026-09-02.md
DET_DRAFT_ON_THIS_VAULT = false
DET_DRAFT_ON_C_USERS_OFN = false
DET_REPLY_TEXT_ON_VAULT = 06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md
PRICE_REQUIRED = contradicted — see table
VERIFIED_PAYMENT_COUNT = contradicted — see table
R0_CAMPAIGN_BLOCKER = owner-hands send of DET reply + unanswered $306.90 variance
NEXT_OWNER_ACTION = send DET from owner mailbox (R3) after filling [NAME]; optionally ask MP Construct about $306.90
OWNER_ONLY_ACTIONS = send; buy.nsw/SCM0256 clicks; answer $306.90
```

## Field census (this disk)

| field | on this vault | source | note |
|---|---|---|---|
| legal name / ABN / ACN / GST | yes (index) | `company-docs/COMPANY-DOCS-INDEX.md` sha256 `d713283e05b3a4c6b5b0f6f0b8e169d0657645310a33c381a61a1441159cc057` | values not copied here |
| public liability PDF | yes | `company-docs/2026-PUBLIC-LIABILITY-ALLIANZ.pdf` sha256 `53048a13a693d2364f771679a7fcaaf5c3c074e8321667687901c7635a138007` bytes=221248 | matches index row 1 exactly |
| SWMS PDF | yes | `company-docs/2026-SWMS-PAINT-001-REV1.pdf` sha256 `e8f0efc65e55ad10bd87349ecee7289bd90cc4d71a7072f3fbb6f8e1057c21b4` bytes=28238 | matches index row 2 |
| signed subcontract PDF | yes | `company-docs/2026-SUBCONTRACT-INTERNAL-PAINTING-SIGNED.pdf` sha256 `fe7b425d747351d2cda9865709e94103f548b481bda414e440b546c98f6b5cea` bytes=2388824 | matches index row 3 |
| workers compensation cert | no file in `company-docs/` | listing this session | MISSING on vault |
| NSW painter licence | no file found | this session | MISSING / unverified |
| contact phones | yes (index + price-ruling) | same two md files | PII not copied |
| DET reply body | yes | `PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` sha256 `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a` | placeholder `[NAME]` still empty |
| ofn-node DET draft | no | Test-Path false | body_not_on_this_host |
| buy.nsw / SCM0256 pack | yes | `BUYNWS-SUPPLIER-PACK-2026-09-02.md` | registration itself unverified; owner clicks only |
| QT-20260902-001 sqlite row | not on this host | price-ruling claims board138 `painting.sqlite` write 2026-09-02T13:05Z | FILE_VERIFIED claim, not this-host runtime |
| ANZ statement PDF | yes | `payment-receipts/ANZ-654214278-2026-05-06_to-2026-09-02-TRANSACTION-REPORT.pdf` | not opened; name only |
| payment receipt note | yes | `payment-receipts/PAYMENT-VERIFIED-20260902-RECEIPT.md` | see contradiction |

## Contradictions (not resolved)

1. **QT price**
   - value_a: `priced=1` `total_aud=600.00` — `PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md`
   - value_b: unpriced / owner-only price — `OWNER-ORDER-THREE-LANES-2026-09-03.md` + `REV4-EXECUTION-20260902T1250Z-RECEIPT.md`
   - resolution: null · status: open
   - PRICE_REQUIRED for this A pass: **unknown on this host** (no sqlite)

2. **Insurance wording in DET**
   - value_a: "certificates on request" and "no insurance number invented" — price-ruling §2–§3
   - value_b: later Lane A / CURRENT-TRUTH cite a live policy figure from the Allianz PDF index
   - resolution: null · status: open
   - PDF bytes exist and hash-match the index. Whether the DET letter should name the policy is an owner wording choice.

3. **verified_payment_count**
   - value_a: 5 business-wide — `PAYMENT-VERIFIED-20260902-RECEIPT.md` + prior Lane A
   - value_b: 0 under R6 in `company-docs/COMPANY-DOCS-INDEX.md` (contract ≠ receipt)
   - value_c: campaign PAINT-L5-001 = 0 — same payment receipt
   - resolution: null · status: open
   - This lane does not lift the food-first freeze.

4. **$306.90**
   - recorded as bank vs invoice variance in `PAYMENT-VERIFIED-20260902-RECEIPT.md` and `OWNER-PACK-v4-DRAFTS-20260903.md` §2
   - cause: unknown
   - do not put Manly totals in a DET letter until the owner answers

## MISSING_FIELDS (this vault)

- ofn-node DET draft file
- `[NAME]` in the vault DET reply
- workers compensation certificate file
- painter licence file
- live `painting.sqlite` proof of QT row
- buy.nsw supplier registration status (pack exists; account does not)

## fields_owner_must_supply

- first name for `[NAME]`
- send/no-send of the DET reply (R3)
- answer or park the $306.90 question
- whether DET should quote the Allianz PDF figures or keep "on request"

## suggested price slots

Not invented this pass. Price-ruling already wrote a $600 intro-day figure on the board (unverified here). Scope m² still unknown.

## risk notes

- Do not send from this session.
- Do not register on buy.nsw from this session.
- Do not treat business-wide payment rows as PAINT-L5-001 cash.
- Do not copy bank account or policy numbers into new notes.

## Vote items for C (not written into C)

See `VOTE-SLIP-FOR-C.md`. Max intended for the daily packet: the two R0 owner actions already named by C (`C-R0-DET-SEND`, `C-R0-MP-30690`).
