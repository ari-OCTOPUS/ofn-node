# SPRINT 03 — Read-only Coin Scouting v1

Duration: 7-14 days  
Mode: read-only, no execution

## Objective
ساخت اولین pipeline واقعی coin scouting برای CPU/ARM frontier coins، فقط برای گزارش.

## Inputs

- SCOUT-B patterns
- benchmark results from Sprint 02
- Coin Scouting Framework

## Tasks

### Source Adapters
- [ ] Bitcointalk ANN parser/cache
- [ ] MiningPoolStats newcoins parser/cache
- [ ] GitHub/CryptoMiso dev activity check
- [ ] GeckoTerminal/Rug checker adapter

### Candidate Normalization
- [ ] خروجی همه منابع → `CoinCandidate`
- [ ] source_urls اجباری
- [ ] confidence per field

### Scoring
- [ ] algorithm via `algo_classifier`
- [ ] launch age
- [ ] dev activity
- [ ] community evidence
- [ ] network/emission data completeness

### Report
- [ ] `Coin Scout Draft Report.md`
- [ ] top candidates
- [ ] missing evidence list
- [ ] no experiment approval

## Definition of Done

- حداقل ۱۰ candidate بررسی‌شده.
- هر candidate source evidence دارد.
- هیچ pool/wallet/miner execution وجود ندارد.
