# DUPLICATIONS (parallel organs)
1. Telegram paths x3: telegram-bridge(dead unit) | alert.py(shadow) | Cockpit V2(live read-only). -> ONE command path in M2 (Owner Control API); archive other units.
2. Routers x2: ofn http_api (business) | octopus-router (mesh). Different domains — KEEP both, document boundary.
3. Memories x4: facts.sqlite | assistant.sqlite(47) | mesh calibration.jsonl+lessons | OCTOPUS vault notes. -> canonical: facts + calibration; assistant/vault MERGE/ARCHIVE.
4. Witness x2: 182 worker (canonical) | in-process gate tests. KEEP 182 canonical.
5. Brains x2: 180 worker (canonical, llama:8081) | ofn assistant runs(21) = tool history, ARCHIVE.
6. Orchestrators x3: scheduler | verify-dispatcher | cycle-settler (+ofn boot). Distinct roles; CONNECT explicitly; build no new one.
7. Truth docs x3: OCTOPUS vault | ofn/docs | mesh docs. -> ofn/docs as single Obsidian root.
8. Backups x4: ofn-backup.timer (canonical) | full-backup dirs | /home/ari/backups tars | snapshots. -> timer canonical; rest ARCHIVE.
9. Constitutions x2: mesh/constitutions (source, immutable) vs ofn/docs published copies — intentional one-way publish; KEEP both.
