---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, germline, hourly-push]
author: "laptop agent — follow-up to Sensorium round-2"
---

# Hourly empty `push err:` — root cause

Host `DESKTOP-KA9RFN5` · 2026-08-18 ~01:52 +10

## Verdict

`git push --all` to `E:\germline\vault.git` is **not** the failure. All 30 local heads already match vault (0 non-fast-forward).

The scheduled command that fails is the **second** line in `germline-hourly.ps1`:

`git push --quiet E:\germline\vault.git --tags`

Rejected tag: **`pre-deploy-2026-07-25`**
- local: `dab81a82`
- vault.git: `9c49f174`

Raw (dry-run, no `--quiet`):

```
! [rejected]        pre-deploy-2026-07-25 -> pre-deploy-2026-07-25 (already exists)
error: failed to push some refs to 'E:/germline/vault.git'
hint: Updates were rejected because the tag already exists in the remote.
```

exit=1

## Why the log shows `push err:` empty

The script records only `$out1` (the `--all` output). `--all` succeeds with `--quiet` → empty. `--tags` fails in `$c2` / `$out2`, which is never logged.

## Sensorium's three suspects

1. `--quiet` swallowing text — **partial**: it hides `--all`; the real error is on `--tags`.
2. Task account ACL — **rejected**: task UserId=`Armin`, same ACL that can write `vault.git`.
3. `--all` one-bad-ref — **rejected for branches**; the one-bad-ref is a **tag**.

Flag `GITWRITE-FAILED` still not deleted. AUTO path still not green until tags push is decided by owner (skip tags / skip this tag / force-update — not done here).
