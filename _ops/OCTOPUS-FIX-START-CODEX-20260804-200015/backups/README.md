No backups needed this session. No existing tracked file was modified — every write this
run made was a brand-new file (the eval harness + this report tree). `git revert` on the
eventual commit is sufficient rollback; nothing pre-existing was touched to back up. See
`27-ROLLBACK-PLAN.md`.
