# LANE-REPORT — PAINTING-LEAD-FORM

Lane: **PAINTING-LEAD-FORM** (ofn-node painting A/A2). HOLD_EXTERNAL.

## What was done

Added a store-only public/local painting enquiry form on the existing lead
listener. A stranger POST writes one row into the local painting store
(`LeadStore` / `painting_leads`). No Gmail, no paid ads, no Telegram stranger
path, no ofn-marketing enablement, no new LAN bind.

Verified gap (this checkout):

- No Flutter/Dart sources in the repo (`*.dart` count = 0; this host).
- `web/lead.html` is the Telegram-authenticated partner CRM, not a public
  intake form (`source: web/lead.html`).
- Authenticated create already existed (`ofn/node.py` `create_painting_lead`,
  `ofn/adapters/lead_store.py`).

## What remains

- Tunnel/DNS mapping of `/enquire` on the live lead host is an operator
  concern; this change does not mutate a live node.
- Studio consent → map remains `OWNER_DECISION` (not implemented).
- O9 catalog / commerce flags stay default-off.

## What failed

- `python3 -m pytest` is unavailable in this environment (`No module named
  pytest`). Tests were run with `python3 -m unittest`.
- `git push` was denied by the OCTOPUS HOLD_EXTERNAL hook. Branch is local
  only: `cursor/painting-public-lead-form-01b4`. ManagePullRequest refused
  create until the remote has the commits.

Scoped unittest (this session): 22 passed
(`tests/test_painting_public_lead_form.py` 14 +
`tests/test_no_public_surface.py` 8). Broader neighbour set 48 passed
(same two files plus `test_mutation_ledger_pair`, `test_web_serving`,
`test_painting_outbox`, `test_painting_store`).

## Evidence paths

- `web/painting-lead-form.html`
- `ofn/adapters/http_api.py` (`POST /api/v1/public/painting/leads`)
- `ofn/node.py` (`capture_public_painting_lead`)
- `ofn/run.py` (`load_web` `/enquire` on lead port only)
- `tests/test_painting_public_lead_form.py`
- `tests/test_no_public_surface.py` (allowlist updated)
- `tests/test_stranger.py` (public form in stranger SHELLS)

Follow-up unittest this session: `test_http_api` + `test_owner_api` +
`test_stranger` + `test_shell_contract` = 110 passed; after adding the
form to stranger SHELLS, `test_stranger` + store-row test = 11 passed.

## Rollback steps

1. Revert this branch / drop the PR.
2. No live-node files, flags, or listeners were changed.
3. `serve()` default host remains `127.0.0.1` (`ofn/adapters/http_api.py`).
