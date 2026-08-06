# Mega Prompt v2 — Master Painting Next Agent
Updated: 2026-08-06
Vault: /home/ari/ofn

Mission: read Obsidian first, then audit code, tests, UI, DB, env names, health, and logs. Help Armin make the painting lead workflow real on his phone: lead intake, missing info, pricing draft, quote review, follow-up, and safe human approval.

Do not trust prior summaries. Re-derive requirements from user words and from code. Never print secrets; only SET/NOT_SET/count.

Read first:
- INDEX.md
- docs/operations/PAINTING-PHONE-QUOTE-CHECKLIST-v2.md
- docs/prompts/PAINTING-NEXT-AGENT-MEGAPROMPT-v2.md
- docs/audit/ARCHITECTURE-MAP.md
- docs/audit/IMPLEMENTATION-GAP-MATRIX.md
- docs/audit/INTEGRATION-INVENTORY.md
- docs/audit/SAFETY-INVARIANTS.md
- docs/security/PUBLISHING-GATES.md
- docs/operations/OWNER-COCKPIT.md
- docs/operations/ROLLBACK.md
- docs/research/SOURCE-REGISTRY.md

Inspect code/tests before edits:
- ofn/config.py, ofn/run.py, ofn/node.py
- ofn/adapters/http_api.py, ofn/adapters/lead_store.py
- ofn/kernel/painting_math.py
- web/panel.html, web/lead.html
- tests/test_painting_math.py
- tests/test_painting_store.py
- tests/test_painting_owner_api.py
- tests/test_http_api.py, tests/test_owner_api.py

Required verify: full pytest with TMPDIR, py_compile after edits, systemctl active, panel/lead health, journal logs.

Product goal: customer/job appears on Armin phone, Armin asks guided questions, system stores answers, shows missing info, computes lead/pricing confidence, drafts quote with assumptions/exclusions, and saves next action.

Metaphor: Painting Job Flight Deck. Lead=incoming aircraft. Qualification=radar lock. Job info=flight plan. Pricing=fuel calculation. Quote=clearance request. Owner approval=tower clearance. Follow-up=next waypoint. Won=landed. Lost/spam=diverted.

Human collaboration: ask one small question at a time, save answer, recalc missing info, explain next missing item, continue. Never dump a giant form. Real outbound stays off unless Armin approves canary.
