# Draft PR spec (owner-prescribed; creation blocked on this board)

Base: main
Compare: backup/board138-20260830
Title: Restore board-138 canonical lineage from live system
State: Draft
Merge: BLOCKED

Body must state:
- why main is ~48 commits behind (board work lived on feature branches and the
  old clone was never synced; the board itself was the source of truth)
- board SHA and preservation branch: c1969bce5384f3371b916470299c991627c3d63c
  on backup/board138-20260830 (ls-remote verified)
- revenue paths added: packs/{lead,studio,ziman,hypno}.yaml,
  docs/operations/REVENUE-STAGES.md, business spine modules
- pilot paths added: deploy/, web/ (panels + cockpit-v2), docs/{audit-138,
  discovery-138, spine-138, octopus-rapid}, 06-EVIDENCE red-test .py
- 31 runtime/evidence artifacts deliberately excluded (exit/out/log/txt/json
  under 06-EVIDENCE/runtime-provenance-*)
- test baseline: 2076 collected, 2065 passed, 1 collection/import error
  (tests/test_greeting_name, relative import), 10 skipped, 0 failures
- known error: tests/test_greeting_name loader failure (pre-existing at
  baseline cc7a65b; fix or formal quarantine in a separate commit before merge)
- the red test owner_decision -> outbox is DEFECT EVIDENCE, not a green test

Merge gate (owner): greeting import fix/quarantine commit -> CI on latest SHA ->
GitHub secret scan green -> 3-dot and 2-dot diff review -> runtime paths review ->
human approval -> main branch protection with required checks on latest SHA.
