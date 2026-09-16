---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-verdict
created_by: agent
relates_to: "[[_ops/ORGANISM-SPEC]] §2.5 Chrono · _ops/chrono.py · [[07 - Knowledge/Time-Architecture/MAP]] (1/f, L(G), γ) · [[07 - Knowledge/Time-Architecture/RFC - HRV bridge]] · [[DOCTOR-BOX-OF-AGENTS-SPEC]] (ChronoUnit γ, ξ)"
tags: [octopus, chrono, rhythm, hrv, noise, bio-inspired, spec, propose-only]
created: 2026-07-08
updated: 2026-07-08
---

# CHRONO-RHYTHM LAYER — HRV-style heartbeat, noise, subjective time (spec, no code)

> A bio-inspired **tempo/attention** layer for the Octopus: a variable HRV-like heartbeat, 1/f (quantum-inspired) noise, subjective time, and mode dynamics — wired to every major component as **modulation**. Architecture only.
> **Hard line (unbreakable):** the ledger clock (`age_tick` + hash-chain, TINV-3/7) stays **deterministic and verifiable**. Rhythm modulates *wall-clock spacing + attention + resource share*, never the recorded logical counter. Rhythm is **advisory**: it settles nothing, bypasses no gate, moves no money.

## 1. Exists vs. new
- **Exists (`_ops/chrono.py`):** HLC, Pacemaker (fixed cadence), phi-accrual failure detector, EffectorGate, `age_tick` (daily, heart-driven).
- **New (this layer, `_ops/chrono/rhythm/`):** HRV-variable beat interval · 1/f noise source · self-HRV health metric · subjective time τ · mode map (CALM/STEADY/FOCUSED × GREEN/AMBER/RED) · Kuramoto coupling · stochastic-resonance detection aid · UnifiedBus rhythm signal.

## 2. Nature templates (bio-inspired backbone — محور ۸)
| template | biology | Octopus mapping |
|---|---|---|
| **HRV** (heart-rate variability) | healthy hearts vary beat-to-beat; low HRV ⇒ stress/rigidity | self-HRV = variability of logical-beat spacing → adaptability/health metric + alarm |
| **RSA / breathing** | heartbeat couples to a slow respiration cycle | two-timescale: fast beat coupled to a slow "breath" (budget/backup cycle) |
| **Circadian** | ~24h cycle | age_tick already daily; circadian modulation of activity level |
| **1/f pink noise (P5)** | ubiquitous, self-similar across scales | the noise source ξ has **1/f spectrum** (not white) — natural jitter |
| **Stochastic resonance** | calibrated noise *improves* weak-signal detection | inject bounded noise so Doctor/spectral-sense catch faint bottlenecks |
| **Kuramoto coupled oscillators** | organs synchronize via phase coupling | each component = a phase oscillator; coherence `r` = system sync |
| **Allostasis** | stability through change (adaptive setpoints) | sustained load shifts rhythm setpoints, not just homeostatic recovery |
| **Quantum-inspired noise** | `[metaphor/SPEC]` structured stochasticity | annealing-style exploration temperature; bounded + seeded |

## 3. The math (pseudo-formulas)
1. **Variable beat interval:** `T_beat(t) = T0 · exp(−κ·readiness + λ·stress) · (1 + ε·ξ_{1/f}(t))` — calm/ready ⇒ slower deliberate beats; stressed ⇒ faster; `ξ_{1/f}` = bounded 1/f jitter. (Sets *wall spacing*, not the age_tick count.)
2. **Self-HRV:** `HRV_t = std(ΔT_beat)` over a window. High ⇒ adaptive/healthy; collapse toward 0 ⇒ rigidity/stress alarm (Warden/Doctor read it).
3. **Subjective time:** `dτ = γ(z)·dt`, `γ = 1 + a·novelty − b·stress` (dilation under novelty, compression under stress — reuses ChronoUnit γ, Time-Architecture C-theory).
4. **Mode map:** `mode = Φ(HRV, σ, stress)` → {CALM, STEADY, FOCUSED} × {GREEN, AMBER, RED} (the Heart operating modes). Drives cycles/min + token share.
5. **Kuramoto coherence:** `θ̇_j = ω_j + (K/N)·Σ_k sin(θ_k−θ_j)`; order parameter `r·e^{iψ} = (1/N)Σ e^{iθ_j}`. High `r` = organs in sync; low `r` = incoherence alarm (maps to Box `coherence` z + `G_t` mood).
6. **Stochastic resonance:** detection signal `= f(x + D·ξ)`; there is an optimal noise `D*` that maximizes faint-bottleneck detection — the Doctor tunes `D` toward `D*`.

## 4. Coupling: rhythm → processing speed / time perception / states
- **Processing speed:** `mode` + `T_beat` set cycles/min and per-cycle token/CPU share; FOCUSED = fewer, deeper cycles; STEADY = default; CALM/BOOT = slow, observe-only.
- **Time perception:** `τ` (subjective) is the clock the system *paces memory, attention, learning-rate* by — separate from deterministic wall/ledger time.
- **System states:** `HRV↓ + σ→1 + stress↑` ⇒ RED/CALM (throttle, observe); healthy ⇒ GREEN/STEADY. Rhythm is the driver of the mode-switch rules already in the Heart role.

## 5. Wiring map (rhythm signal → every major component — modulation only)
Published once per beat on the **UnifiedBus** (P5) as an advisory `rhythm = {T_beat, HRV, τ, γ, mode, r, D}`. Consumers read; none bypass safety.
| component | what rhythm modulates | invariant floor (unchanged) |
|---|---|---|
| **Ledger / age_tick** | wall-clock spacing of beats only | logical count + hash-chain deterministic (TINV-3/7) |
| **Gates** (organ/money/capability) | readiness/threshold *softening under arousal* | fail-closed floor + human-append + money-lock unchanged |
| **Doctor** | `run_cycle` cadence ∝ tempo; stress→exploration temp; `D` for stochastic-resonance mining | sandbox, λ_persist<0, human-gated |
| **Box-of-Agents** | debate round tempo + noise (falsifier discovery) | 2% cap, ρ(J)<1, propose-only |
| **Legs** | polling/action pacing | propose-only, human-gated effects |
| **Telegram** | batching cadence (calm=batch, RED=immediate) | human-append is still the only settle path |
| **Spectral-sense** | shares σ / `L(G)` with the rhythm's criticality read | read-only |
| **School Memory** | learning-rate ∝ subjective time τ | read-only mount, propose-only |

## 6. Safety (the whole point)
- **Ledger determinism preserved** — TINV-3/7 intact; a torn/variable rhythm can never change a recorded age_tick or hash.
- Rhythm signal is **read-only advisory**; it cannot settle effects, bypass gates, unlock money, or self-modify.
- Noise is **bounded + seeded** (reproducible in tests); "quantum" is metaphor.
- **Self-HRV only** — the system's own synthetic rhythm. Real human-HRV data stays in the separate, Security-Gated `RFC - HRV bridge` (E3); no PII here.
- kill-switch supreme; kill/STOP freezes rhythm too.

## 7. Roadmap (each sandbox · propose-only · tested · $0 offline first)
- **CR-B0:** offline rhythm core — `T_beat`, 1/f noise, self-HRV, τ, mode map. **Test: deterministic-ledger invariance** (age_tick/hash identical with rhythm on/off), bounded noise, HRV alarm fires.
- **CR-B1:** Kuramoto coupling + coherence `r` + stochastic-resonance detection gain (measured: noise improves faint-bottleneck recall).
- **CR-B2:** publish `rhythm` on UnifiedBus; Doctor/Box read tempo (modulation only). Test: consumers never bypass a gate.
- **CR-B3:** wire gate/leg/telegram pacing (fail-closed floors asserted).
- **CR-B4:** RSA/circadian two-timescale + allostatic setpoint adaptation.

## 8. GLM prompt — CR-B0 (offline, ledger-safe)
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. CR-B0 لایهٔ ریتم: هستهٔ عددیِ آفلاین. propose-only، sandbox، additive، $0. commit با مالک. ساعتِ لجر را نشکن.
گام ۰ ضدِ تکرار: grep -rln "def beat_interval\|def self_hrv\|1/f\|subjective_time\|class Rhythm" _ops/ | grep -v __pycache__ ؛ هرچه بود اثبات بده و رد شو.
گام ۱ بخوان: _ops/chrono.py + CHRONO-RHYTHM-LAYER-SPEC.md (§۳–§۶) + DOCTOR-BOX-OF-AGENTS-SPEC.md (γ). اول PLAN. فایل‌ها زیرِ _ops/chrono/rhythm/.
بساز (فقط عدد): T_beat(readiness,stress,ξ_1/f) · نویزِ 1/f بوجهٔ کران‌دار و seeded · self_hrv=std(ΔT) · subjective_time τ=∫γ dt · mode=Φ(HRV,σ,stress) → CALM/STEADY/FOCUSED×GREEN/AMBER/RED.
خطِ قرمز (نقض=رد): age_tick و hash-chainِ لجر باید با rhythm on/off **یکسان** بماند (TINV-3/7) · rhythm فقط advisory، هیچ settle/gate-bypass/money · نویز بوجهٔ seeded (تستِ بازتولیدپذیر) · هیچ human-HRV واقعی (آن پشتِ Security Gate است) · بدونِ import اثرِ production.
تست‌ها ($0، اثبات نه ادعا): (الف) invarianceِ لجر: توالیِ age_tick/hash با rhythm-on == rhythm-off · (ب) نویز 1/f کران‌دار و با seed بازتولیدپذیر · (ج) HRV پایین → آلارم · (د) τ با novelty بالا کش می‌آید · (ه) mode-map درست سوییچ می‌کند · (و) صفر production-touch. خروجیِ خامِ run_all را paste کن.
Definition of Done: هستهٔ ریتمِ آفلاین تست‌سبز، لجر ثابت‌مانده، rhythm فقط advisory. ORGANISM-SPEC §2.5 آپدیت. هر ابهام → «⚑ برای معمار».
```

## Sources
`_ops/chrono.py` · [[_ops/ORGANISM-SPEC]] §2.5 · [[07 - Knowledge/Time-Architecture/MAP]] (1/f P5, L(G), σ) · [[07 - Knowledge/Time-Architecture/RFC - HRV bridge]] (E3, gated, PII) · [[04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC]] (γ, ξ, ρ(J)) · user brief (session 36)
