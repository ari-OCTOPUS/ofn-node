# EXECUTION-ORDER

| Step | Action | Gate |
|------|--------|------|
| 0 | Owner accepts OWNER-AUTHORIZATION.json | status ACCEPTED |
| 1 | Copy script to board path | file present |
| 2 | Install unit+timer | files under /etc/systemd/system |
| 3 | enable --now timer | active |
| 4 | Run once / wait tick | snapshot JSON valid |
| 5 | Confirm feeds timer untouched; doctor PASS; ARMED=false | no regressions |
| 6 | RECEIPT + FROM-PI copy | done |

Abort → ROLLBACK.md
