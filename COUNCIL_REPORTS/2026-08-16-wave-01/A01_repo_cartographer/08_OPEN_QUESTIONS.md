# 08 OPEN QUESTIONS — A01 Repository Cartographer (2026-08-16)

Questions this agent could not answer with read-only observation. Each states who should answer and what evidence would close it.

## For the owner (decisions only the owner can make)
1. **Q-01 · FREEZE incident response**: Has the owner seen the 20:09 freeze (settle Errno 22)? Root cause was not determinable read-only (needs handle inspection while the live process holds state). After diagnosis: clear, keep, or change freeze policy? (R-01)
2. **Q-02 · NBB-CP canonical home**: Which of the three forks is the real NBB-CP — vault `03 - Projects`, embedded `4d_system/src`, or Desktop `OCTOPUS-NBB-CP-WORKING` (only one with today's commits)? Should the Desktop repo's history be pushed into the germline bare repo instead of a bundle file? (R-02, DUP-001)
3. **Q-03 · genome-system nesting**: Is the nested `.git` in `07 - Knowledge/genome-system` intentional (submodule-like split) or an accident of a past clone? Files are tracked by BOTH repos today. (R-03)
4. **Q-04 · Vocabulary**: Does the owner want to keep the claims language (L0–L8, Sensorium, viability loop, bitemporal) and change code/docs to match, or change the claims to match the real 7-layer organism? (C-01/06/07)
5. **Q-05 · Governance flags**: Owner intent for `OCTOPUS_WIRE_DUAL_VETO`, `OCTOPUS_OBSERVE_4D`, governor-LLM lane, `octopus_v3` WIRED=True someday? Each is dormant by design; arming requires owner word. (R-08)
6. **Q-06 · "4d_system as a brain"**: Is 4d_system supposed to run as a live brain process (MANIFEST says standalone research, not wired), or is the NBB-CP fork the operational brain and 4d_system purely research? The dual-veto design treats both as peers — tonight neither runs. (C-04)
7. **Q-07 · business-legs expectations**: mining/crypto legs are skeletons awaiting owner business specs (hashrate/power/profit for mining; completeness 11% for crypto). Are these still intended to go live? (STUB-011/012)

## For other council agents (evidence they can produce)
8. **Q-08 → A02**: Which scheduled-task actions launch which files? (schtasks /query /v). Do the six live ports all answer? Is there any process on 8768?
9. **Q-09 → A02**: Does `recall_reach` (median 21 events) reflect actual memory read-back into reasoning, or just bookkeeping?
10. **Q-10 → A03**: Does the budget settle path (the one that errored) actually append to the genome ledger, and is the ledger's append lock the culprit behind Errno 22 (two writers, Windows file locking)?
11. **Q-11 → A03**: Are there real "bitemporal" requirements anywhere (ledger consumers needing retroactive corrections), or is the word prose-only?
12. **Q-12 → A04**: Can any code path spend money or emit external messages without passing money_gate/policy_gate? Is `board_cp/config.is_armed()` reachable from outside?
13. **Q-13 → A04**: Is `NotWiredStub` the only ApprovalChannel in the live profile (telegram approval channel is imported in wiring.py — which one wins at runtime)?

## Genuinely unknown (no evidence tonight)
14. **Q-14**: Why is `frozen=true` while `halted=null` and the loop keeps ticking — is the freeze deliberate posture (I3 design) or drift? (Partially answered: FREEZE.flag exists; but the *decision* to leave it for hours is unknown.)
15. **Q-15**: What was the last clean full-suite green state of the combined organism (753 tests per wave-E commit message a31f0d6 is historical; tonight's suite health is unverified)?
16. **Q-16**: Is there any physical/remote actuator capability anywhere (hardware legs, SSH exec, external deploy channels) not visible in the directories scanned tonight? A04 scope.
