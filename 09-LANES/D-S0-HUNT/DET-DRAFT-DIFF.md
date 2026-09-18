---
type: det-draft-diff
lane: D-S0-HUNT
measured_at: 2026-09-03T19:45:58+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: Get-NetIPAddress Wi-Fi
scope: this_host_only
claim_type: observation
owner_decision: "و) فقط اختلاف دو هش DET را محلی مقایسه کن — بدون fetch و بدون کپی به والت"
---

# DET draft hash compare (local only)

Lane: **D-S0-HUNT**. Laptop vault host (`DESKTOP-KA9RFN5` / `192.168.0.191`), not board 180.

No `git fetch` / clone / pull / unzip. Neither draft copied into `F:\backup\docs\lanes\` or any vault canonical DET path. Vault path `F:\backup\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` remains **absent** (`Test-Path` this session).

Tools this session: `Test-Path`, `Get-Item`, `Get-FileHash SHA256`, `[IO.File]::ReadAllBytes`, UTF-8 decode + CRLF→LF normalize.

## Verdict (this host)

The two sha256 values are **different files at the byte level** and **the same Unicode text** after newline normalization.

| question | this_host_only | source |
|---|---|---|
| same words / placeholders? | **yes** — newline-normalized strings equal | PowerShell `$aaNorm -eq $ddNorm` → True |
| only line endings? | **yes** — 48 extra `0x0D` bytes on the CRLF copy | raw `2779 − 2731 = 48`; `crlf=48` vs `lf_only=48` |
| visible placeholder tokens differ? | **no** — same set | regex on both bodies |
| which draft is “correct”? | **not declared** | owner reserved |

## 1. Paths reconfirmed

| path | exists | bytes | sha256 | line endings | mtime | source |
|---|---|---|---|---|---|---|
| `F:\ofn-node\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | true | 2779 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 cr_only=0 | 2026-09-02T23:18:58.938+10:00 | `Get-FileHash` + `ReadAllBytes` + `Get-Item` |
| `F:\wt-self-awareness\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | true | 2779 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 cr_only=0 | 2026-09-02T21:25:16.704+10:00 | same |
| `F:\wt-buysw-v03\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | true | 2779 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 cr_only=0 | 2026-09-03T12:15:10.817+10:00 | same |
| `C:\Users\Armin\AppData\Local\Temp\ofn-verify\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | true | 2779 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 cr_only=0 | 2026-09-03T15:55:36.477+10:00 | same — **exact Temp ofn-verify path** |
| `F:\wt-economic-learning\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | true | 2731 | `d7aeb3ebc2cddcb7c01116c01e1a64d7843893a49a7ecd2e44c0ce15c07bda4b` | crlf=0 lf_only=48 cr_only=0 | 2026-09-02T20:54:33.548+10:00 | same |
| `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` | true | 4481 | `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a` | crlf=0 lf_only=74 cr_only=0 | 2026-09-02T22:55:34.306+10:00 | same — third witness, not a draft |
| `F:\backup\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | false | — | — | — | — | `Test-Path` |

Four `aa98fff…` copies are byte-identical to each other (`Get-FileHash` equal this session). UTF-8 strict decode: ok on both draft hashes (no BOM). Both drafts end with a newline. First CR in `aa98fff…` at byte index **75** (`0x0D 0x0A`). `d7aeb3eb…` has **zero** CR bytes.

Content line count after normalize (excluding the empty split part from the trailing newline): **48** on both drafts. Source: PowerShell split of normalized text.

## 2. Text diff (`aa98fff…` vs `d7aeb3eb…`)

### Raw (bytes)

- `aa98fff…` = 2779 B CRLF
- `d7aeb3eb…` = 2731 B LF-only
- delta = **48** B = one extra CR per newline (`2779 − 2731`, source: `ReadAllBytes.Length`)

### Newline-normalized (CRLF→LF, then CR→LF)

| metric | aa98fff… | d7aeb3eb… | source |
|---|---|---|---|
| `System.String.Length` after UTF-8 decode + normalize | 2112 | 2112 | PowerShell `Get-NormText` |
| `norm_texts_equal` | True | True | `-eq` |
| `differing_normalized_lines` | 0 | 0 | line loop |
| `whitespace_stripped_equal` | True | True | regex `\s+` strip |

**Quoted differing lines (wording):** none. After ignoring pure CRLF, there is no line that differs.

**Quoted differing bytes (line endings only):** every line terminator is `CRLF` vs `LF`. No wording sample to quote.

### Placeholders (same on both hashes)

Tokens present in both bodies (regex + literal check this session):

- `[LEGAL BUSINESS NAME]`
- `[ABN]`
- `[NAME]`
- `[PHONE]`
- `[EMAIL]`
- `[BUSINESS NAME]`
- `$[X]m`
- `[1–2 SHORT FACTS — ONLY REAL REFERENCES]`

No ABN-like digit run and no AU-mobile-like run in either draft (`abn_like=0`, `phone_like=0`). One email-like string appears in **both** H1s at the same offset: the DET procurement mailbox already named in the filename (`amprocurement@[det.nsw.edu.au]` — key only). The `[EMAIL]` placeholder in the letter body is still unfilled.

## 3. Third witness — PRICE-RULING letter (do not merge into a winner)

File: `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md`

| field | value | source |
|---|---|---|
| sha256 | `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a` | `Get-FileHash` this session (matches prior reported hash) |
| bytes | 4481 | `ReadAllBytes.Length` |
| newlines | lf_only=74 | `ReadAllBytes` |
| class | owner-ruling **execution receipt** + a **filled** letter block under `# ۳` | file body |
| draft class | placeholder draft (`DRAFT-REPLY-det-nsw-2026-09-02.md`) | file titles / remaining `[…]` tokens |

This is FILE_VERIFIED vault text. It is **not** a reason to copy either worktree draft into `docs/lanes/`.

Document-class contrast (not a correctness ruling):

| | two DET drafts (`aa98fff…` / `d7aeb3eb…`) | PRICE-RULING letter fence |
|---|---|---|
| class | placeholder draft | filled supplier reply inside a ruling receipt |
| letter `System.String.Length` (normalized fence body) | 788 | 1123 |
| letter content lines | 25 | 29 |
| remaining placeholders in letter | all of the list in §2 | `[NAME]` only |
| filled keys (redacted) | none | legal name present; `ABN`/`ACN` digits present; two `PHONE` values present; indicative `$35` / `$50` / `$75` / `$600` lines present |

Shared framing lines (exact match, no PII): `Subject: RE: Painting quote — Education sites`; `Good morning,`; `Thank you for your reply and for the opportunity to clarify.`; `Our details for your supplier records:`; the “happy to complete any vendor registration…” opener; `Kind regards,`. Count of identical nonempty lines = **6**. Source: line-set compare this session.

Draft-only letter lines (placeholders; both hashes identical so only one quote):

```
- Business name: [LEGAL BUSINESS NAME]
- ABN: [ABN]
- Contact: [NAME] · [PHONE] · [EMAIL]
- Insurance: Public Liability $[X]m (certificate available on request)
  step you require (e.g., buy.nsw supplier profile / SCM0256
  prequalification scheme for painting services).
We hold experience in [1–2 SHORT FACTS — ONLY REAL REFERENCES] and can
provide site-visit availability at short notice across Sydney metro.
Please let me know which registration path you prefer and we will
complete it the same day.
[NAME]
[BUSINESS NAME] · [PHONE]
```

Ruling-only letter lines (redacted; key names only — values not copied here as “the” DET text):

```
- Business name: [LEGAL_NAME_PRESENT]
- ABN: [ABN_REDACTED] (ACN [ACN_REDACTED]) — GST registered
- Contact: [NAME] · [PHONE_REDACTED] / [PHONE_REDACTED]
- Experience: 25 years in painting and maintenance across Sydney
- Insurance: Public Liability and Workers Compensation certificates
  available on request
  step you require (e.g., buy.nsw supplier profile via Supplier Hub, and
  SCM0256 prequalification under the Painting & Decorating trade category).
Indicative pricing (Sydney market averages, ex GST):
- Interior repaint (walls & ceilings): from $35 per m2
- Exterior repaint: from $50 per m2
- Scheduled maintenance / day works: $75 per hour
  (standard engagement: one painter-day, $600 ex GST)
We can price a trial scope within a few days of receiving details.
[TRADING_NAME_PRESENT]
[PHONE_REDACTED] · [PHONE_REDACTED]
```

No winner declared. Filled ≠ placeholder. Hash `b5bd72e4…` ≠ `aa98fff…` ≠ `d7aeb3eb…`.

## 4. Contradictions still open

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| DET draft byte identity | sha256 `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` · 2779 B · CRLF×48 | four paths in §1 | sha256 `d7aeb3ebc2cddcb7c01116c01e1a64d7843893a49a7ecd2e44c0ce15c07bda4b` · 2731 B · LF×48 | `F:\wt-economic-learning\…\DRAFT-REPLY-det-nsw-2026-09-02.md` | null (same words; two hashes remain) | open |
| DET text vs vault ruling letter | placeholder draft class | both hashes in §1 | filled letter class inside ruling receipt · sha256 `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a` · 4481 B | `PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` | null | open |
| LANE-MATRIX vs D folder | CSV lists L0–L9 only | `09-LANES/LANE-MATRIX.csv` | this lane folder exists | `09-LANES/D-S0-HUNT/SCOPE.md` | null | open |

This session did **not** re-hash `VERIFIED-ECONOMIC-STATES-DESIGN.md` (out of owner decision و). Prior open pair `f415c3a2…` vs `ac3bf90f…` stays **unverified this session**.

## 5. Owner next

Still **no fetch** unless the owner asks. Local compare is complete. Copying either draft into the vault canonical path is still closed.
