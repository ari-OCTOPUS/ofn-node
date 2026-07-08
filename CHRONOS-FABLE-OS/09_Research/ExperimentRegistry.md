# Experiment Registry (L10) — N=1 sealed-prediction protocol

_Closes **MER-3**. Source: `lab_seed_data.json` (uploaded 2026-07-08; snapshot in `_primaries/from-vault/`). This is the project's own quantitative arm: pre-registered N=1 experiments with **sealed predictions** and **blinding** — a working instance of PAT-03 (Claim→Tag→Falsifier→Experiment) and INV-09 (no upgrade to [E] without independent data)._

## Governance (from the seed — enforced, not optional)

- Personal data: only `exp_*` tables on the human side; **no contact with `ailab_*`**.
- Fully offline, rule-based; **no LLM call** in this module.
- **Anti-expectation-leak:** for the 14-day window, no chart/trend/interpretation of experiment data is shown.
- Each prediction stays **sealed until its `end_date`**; `/reveal` verifies the sha256 match.
- An abnormal day is never deleted — only flagged, then excluded from the day-14 analysis.

> **Blinding respected here:** the base64 predictions are **NOT decoded** in this repo. They remain sealed; only the bot reveals them after `end_date` and confirms the sha256. Decoding early would violate the seed's own anti-leak law (and INV-09).

## The three experiments (14 days each)

| id | name | design | metrics logged (buttons) | sealed sha256 (prefix) |
|---|---|---|---|---|
| **exp1** | Coué: image vs will | even day = P_FORCE (willed repetition), odd day = P_IMAGE (effortless imagery); calendar locked at `/start_exp1` | ttf (time-to-focus), switches, abnormal | `48b7832f…` |
| **exp2** | real anchor vs sham anchor | week 1 = practice gesture A daily; week 2 = pre-built A/B alternation (fixed `random.seed`, ≥3 days each) | effect, latency, abnormal | `5ea42e9c…` |
| **exp3** | intrusive thought: strategy A vs B (blind) | odd day = STRAT_A (direct suppression), even day = STRAT_B (name-it, return); labels deliberately neutral | switches, effort, abnormal | `57f4d76b…` |

## Schedule & data plumbing

- Morning message 07:00, evening log 22:00, one nudge after 90 min (max 1). Timezone read from the bot config — never hard-coded.
- **RMSSD (optional):** if a Muse session exists within 3 h before the evening log, auto-attach the last RMSSD; else `null`; user may decline. — this is the concrete **E3 / HRV bridge** the time-research half asked for (`FalsifiableTests.md`).
- CSV export columns: `exp_id, day_index, date, protocol, metric_key, metric_value, rmssd, abnormal, logged_at`.

## What this closes / leaves open

- **Closes MER-3:** the N=1 sealed-prediction template + falsification protocol + telemetry schema now exist (Level A).
- **Still open:** the `rate↔aging` coupling (DOC-B TINV-6) and EEG-based E1/E2 need their own datasets; this seed covers focus/anchor/intrusive-thought experiments + the HRV bridge, not EEG.
- Bot commands implied: `/start_exp1..3`, nightly log, `/reveal <exp>` (post-end-date only). These belong to the **Telegram interface (L11)** — see roadmap.
