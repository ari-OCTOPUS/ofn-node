# Decision Record — expire stale approvals — 2026-08-03T09:48:22.342Z

id: DR-APPROVAL-EXPIRE-20260803T094822Z
date: 2026-08-03T09:48:22.342Z
agent: fugu-ultra
decision_level: D1/D2 state hygiene, no external effect
context: 105 pending approvals included 103 expired items and 2 live medium sgc_action items. Owner agreed to continue with proposed cleanup.
evidence: _octopus/state/approvals.json; before_backup=continuity\backups\approvals.before-expire-20260803T094822Z.json; after_backup=continuity\backups\approvals.after-expire-20260803T094822Z.json
risk: low if no mission executes; high if stale high-risk approvals remain actionable
reversibility: high via before backup
blast_radius: approval queue only
confidence: high
owner_required: yes — granted by chat reply "موافقم"
external_effect: no
chosen_option: move expired pending approvals to rejected[] with status=expired and execution=not_executed
why: expired approvals should not remain actionable; preserving full records avoids data loss
rollback: restore continuity\backups\approvals.before-expire-20260803T094822Z.json to _octopus/state/approvals.json
tests: JSON parse before/after; count verification
result: moved=103; pending_after=2; rejected_after=103; before_sha256=f2193281afd25e6fdd37d919a8f87e34e3706fe7501d1cd2fc3fea485d98448c; after_sha256=dc70b0991fca58c8a2abbbebd612b9130d1b9c31a7bd35d2f6ff9820c44ca68f
status: completed
