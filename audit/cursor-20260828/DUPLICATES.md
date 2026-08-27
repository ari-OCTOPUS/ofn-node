# DUPLICATES

scan: 2026-08-27T23:03Z

## Parallel organisms

1. **board-life-001** (180 lab organism.db + Obsidian child vault)
2. **octopus-mesh cognitive worker** (180 /root/octopus-mesh)
3. **ofn.service pack node** (138 /home/ari/ofn)
4. **ofn-l4 shadow kernel** (180 /opt/octopus/ofn-l4)
5. **182 sensorium + NATS + world-model**
6. **hypno-fugu-mini Telegram app** (138)
7. **langar bot** (GitHub only on this scan)

These are not copies of one function. They **compete for the name “Octopus”** and only (3)+(2) were meant to join for money. Join is incomplete.

## Same config, different policy

- `nodes.json` sha256 match 180=182=cefbd5cafe689382…
- `policy.json` 180=138 prefix e0ffea18… ; **182 eee2812d… DRIFT**

## Same transport, different bin set

138 mesh bin has scheduler/executor/telegram/router.  
180 mesh bin has cognitive_worker/business_cycle/model_adapter/reply_outbox.  
182 mesh bin has witness_worker/verifier.  
None of the three mesh trees is a git repo.

## Prompt / doc duplication

- MEGAPROMPT.md, MEGAPROMPT-UNIFY.md, MEGAPROMPT-UNIFY-FINAL.md, MEGAPROMPT-OWNER-COMPLETE.md, MEGAPROMPT-COMPLETE-FINISH.md, MEGAPROMPT-P1-TO-P4-COMPLETE.md
- AGENT-NEXT-* ×3
- HANDOFF/INDEX/README each with bak-vault and bak-scan

## Painting “sources”

- GitHub Armin (empty-ish)
- 138 packs/lead.yaml + web/lead.html
- 180 QUALITY-DRAFTS-PAINTING.md + business cycle fixtures
- 180 lab painting drafts (three drafts rule; no 138 ledger winner)

Canonical for runtime painting should be **138 lead pack + 180 cycle**, not Armin, until owner says otherwise.

## Telegram

- octopus_telegram_bridge.py (inactive unit)
- hypno-fugu-mini.service (active)
- langar/bot.py (GitHub)
- ofn-alert.service optional Telegram (inactive)

Only one should be the **owner decision** channel. Today none of them is proven to render bizop telegram_decision objects.
